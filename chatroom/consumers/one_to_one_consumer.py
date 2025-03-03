import json
import logging
from django.utils import timesince, timezone
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from chatroom.models import (
    User,
    DirectMessageUser,
    ReportUserModel,
    BlockedUser,
    UserStatusModel,
)
from chatroom.models.category import (
    Reaction,
    ReadReceipt,
    TextMessage,
    CallLog,
    ChatRoomModel,
)
from django.db import transaction

logger = logging.getLogger(__name__)


class OneToOneChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handles WebSocket connection."""
        self.sender = self.scope["user"]
        self.sender_id = self.sender.id
        self.room_id = int(self.scope["url_route"]["kwargs"]["room_id"])
        self.receiver_id = int(self.scope["url_route"]["kwargs"]["receiver_id"])
        self.room_group_name = f"chat_{self.room_id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        result = await self.update_bulk_message_status(self.sender_id, self.room_id, "seen_at")
        if result:  # ✅ Now `None` check works correctly
            messages, status_field = result
            for message in messages:
                await self._send_status_update(message=message, status_field=status_field)

        await self.accept()

    async def disconnect(self, close_code):
        """Handles WebSocket disconnection."""
        logger.info("WebSocket Disconnected")
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """Handles incoming WebSocket messages."""
        data = json.loads(text_data)
        action = data.get("action")
        if action == "send_message":
            await self.handle_send_message(data)
        elif action in ["seen", "delivered"]:
            await self.handle_mark_read(data)

    async def handle_send_message(self, data):
        """Handles message sending."""
        message, email, receiver_id = (
            data.get("message"),
            data.get("email"),
            data.get("receiver"),
        )
        if not message or not receiver_id:
            return  # Exit if data is missing
        receiver = await self.get_user_object(receiver_id)
        if not receiver:
            return  # Exit if receiver does not exist

        # Check friendship asynchronously
        are_friends, sender_name, receiver_name = await self.are_friends_async(
            self.sender, receiver
        )
        if not are_friends:
            await self.send_system_message(
                email,
                f"Hey {sender_name}, you need to add {receiver_name} as a friend before sending messages. Send a friend request to start chatting! 😊",
            )
            return
        saved_message = await self.save_message(email, message)
        if saved_message:
            await self.broadcast_message(saved_message)

    @sync_to_async
    def are_friends_async(self, user1, user2):
        """Checks if two users are friends asynchronously."""
        return (
            DirectMessageUser.are_friends(user1=user1, user2=user2),
            user1.profile.name,
            user2.profile.name,
        )

    async def handle_mark_read(self, data):
        """Marks messages as read in a conversation."""
        result = await self.mark_message_status(self.sender_id, self.room_id, data)
        if result:  # Ensure result is not None before unpacking
            message, status_field = result
            await self._send_status_update(message=message, status_field=status_field)

    async def send_system_message(self, email, message):
        """Sends a system notification message directly to the user."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "system_message",
                    "message": message,
                    "email": email,
                    "created_at": "",
                }
            )
        )

    async def broadcast_message(self, saved_message):
        """Broadcasts a new message and updates unread count efficiently."""

        def format_timestamp(timestamp):
            """Formats timestamp if it's not None."""
            return (
                timezone.localtime(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                if timestamp
                else None
            )

        message_data = {
            "type": "chat_message",
            "id": saved_message.pk,
            "message": saved_message.msg,
            "email": saved_message.sender.email,
            "created_at": format_timestamp(saved_message.created_at),
            "receiver_id": self.sender_id,  # Current user is receiver
            "sender_id": saved_message.sender.pk,
            "delivered_at": format_timestamp(saved_message.delivered_at),
            "seen_at": format_timestamp(saved_message.seen_at),
        }

        await self.channel_layer.group_send(self.room_group_name, message_data)

    async def chat_message(self, event):
        """Sends chat messages to the WebSocket connection."""
        await self.send(text_data=json.dumps(event))

    @sync_to_async
    def save_message(self, email, message):
        """Saves a message to the database."""
        sender_user = User.objects.get(email=email)
        receiver = User.objects.get(id=self.receiver_id)
        delivered_at = timezone.now() if receiver.status.is_online else None
        return TextMessage.objects.create(
            chat_room_id=self.room_id,
            sender=sender_user,
            msg=message,
            delivered_at=delivered_at,
        )

    @sync_to_async
    def mark_message_status(self, sender_id, room_id, data):
        """Marks messages as delivered or seen based on action type and message ID (if provided)."""
        message_id = data.get("id")
        action = data.get("action")
        receiver_id = data.get("receiverId")
        if action == "seen" and message_id:
            result = self._update_message_status(message_id, receiver_id, "seen_at")
            if result:  # Ensure result is not None
                message, status_field = result
                return message, status_field
        return None, None

    def _update_message_status(self, message_id, receiver_id, status_field):
        """Marks a single message as seen if the receiver is not the sender."""
        try:
            message = TextMessage.objects.get(pk=message_id)
            if receiver_id != self.sender_id and not getattr(message, status_field):
                with transaction.atomic():
                    setattr(message, status_field, timezone.now())
                    message.save(update_fields=[status_field])
                return message, status_field  # Correct return value
            return None  # Instead of None, None, just return None
        except TextMessage.DoesNotExist:
            logger.error(f"Message {message_id} not found")
            return None

    @sync_to_async(thread_sensitive=True)
    def update_bulk_message_status(self, receiver_id, room_id, status_field):
        """Marks all unread messages as delivered or seen when the receiver opens the chat."""
        messages = TextMessage.objects.filter(
            **{f"{status_field}__isnull": True},
            chat_room_id=room_id,
        ).exclude(sender_id=receiver_id)

        if messages.exists():
            with transaction.atomic():
                updated_messages = list(messages)
                for msg in updated_messages:
                    setattr(msg, status_field, timezone.now())
                TextMessage.objects.bulk_update(updated_messages, [status_field])
            
            return updated_messages, status_field  # ✅ Return messages

        return None  # ✅ Return None when no messages are found

    async def _send_status_update(self, message, status_field):
        if message is not None:
            logger.info(
                f"Sending WebSocket update for message {message.pk}: {status_field}={getattr(message, status_field)}"
            )
            status_data = {
                "type": "update_message_status",
                "id": message.pk,
                status_field: getattr(message, status_field).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            }
            await self.channel_layer.group_send(self.room_group_name, status_data)

    async def update_message_status(self, event):
        message_id = event["id"]
        await self.send(text_data=json.dumps(event))  # FIXED: Used `json.dumps`

    @sync_to_async
    def get_user_object(self, user_id):
        """Fetches a user object by ID."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class FriendConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope["user"].id
        self.room_group_name = f"user_{self.user_id}"

        # Join the group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.update_user_status(status=True)
        await self.accept()

    async def disconnect(self, close_code):
        await self.update_user_status(status=False)
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def update_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def friend_request(self, event):
        await self.send(text_data=json.dumps(event))

    @sync_to_async
    def update_user_status(self, status=False):
        """Updates the user's online status."""
        user = User.objects.get(pk=self.user_id)
        from django.utils import timezone

        UserStatusModel.objects.update_or_create(
            user=user, defaults={"is_online": status, "last_online": timezone.now()}
        )
