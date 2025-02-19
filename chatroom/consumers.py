import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

from django.contrib.auth import get_user_model
User = get_user_model()
from chatroom.models import SubCategory, RoomMessage, DirectMessage, DirectmessageUser

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logger.info("WebSocket Connected")
        self.room_id = self.scope['url_route']['kwargs']['roomid']
        self.room_group_name = f'chat_{self.room_id}'
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        logger.info('WebSocket Disconnected')
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        logger.info(data)
        message = data['message']
        email = data['email']
        room = data['room']

        await self.save_message(email, room, message)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'email': email
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        email = event['email']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'email': email
        }))

    @sync_to_async
    def save_message(self, email, room, message):
        user = User.objects.get(email=email)
        room = SubCategory.objects.get(pk=room)
        logger.info(f"{user}--{room}--{message}")
        RoomMessage.objects.create(room=room, user=user, message=message)

from django.utils.timezone import localtime

class DirectMessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logger.info("WebSocket Connected")

        # Get the sender and receiver from the URL
        self.sender_id = int(self.scope['user'].id)  # Get current user
        self.receiver_id = int(self.scope['url_route']['kwargs']['receiver_id'])  # Get receiver from URL

        # Ensure room name is unique and consistent (sorted IDs)
        sorted_ids = sorted([self.sender_id, self.receiver_id])
        self.room_group_name = f"chat_{sorted_ids[0]}_{sorted_ids[1]}"  # Unique room

        # Add user to the WebSocket group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        logger.info('WebSocket Disconnected')
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        logger.info(data)

        message = data['message']
        email = data['email']
        receiver_id = data['receiver']

        saved_message = await self.save_message(email, message, receiver_id)
        local_created_at = localtime(saved_message.created_at).strftime('%Y-%m-%d %H:%M:%S')

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': saved_message.message,
                'email': saved_message.sender_user.email,
                'created_at': local_created_at
            }
        )

    async def chat_message(self, event):
        message = event['message']
        email = event['email']
        created_at = event['created_at']

        await self.send(text_data=json.dumps({
            'message': message,
            'email': email,
            'created_at': created_at
        }))

    @sync_to_async
    def save_message(self, email, message, receiver_id):
        sender_user = User.objects.get(email=email)
        receiver_user = User.objects.get(pk=receiver_id)
        return DirectMessage.objects.create(
            sender_user=sender_user, receiver_user=receiver_user, message=message
        )
