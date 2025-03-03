from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import DirectMessageUser
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json
from .models import TextMessage
import json


@receiver(post_save, sender=DirectMessageUser)
def send_friend_request_notification(sender, instance, created, **kwargs):
    """Send real-time notification when a friend request is sent."""
    if created:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{instance.friends.id}",
            {
                "type": "friend_request",
                "action":"friend_request",
                "message": f"You have a new friend request from {instance.me.username}",
                "sender_id": instance.me.id,
                "sender_name": instance.me.username,
                "friend_type": instance.get_friend_type_display(),
            },
        )


@receiver(post_save, sender=TextMessage)
def notify_unread_messages(sender, instance, **kwargs):
    """Triggers FriendConsumer to update unread messages count and reorder the user list."""

    sender_id = instance.sender.id  # The user who sent the message

    # Get receiver (the other participant in the chat)
    chat_room = instance.chat_room
    receiver = chat_room.participants.exclude(
        id=sender_id
    ).first()  # Get the other user in chat
    if not receiver:
        return  # No receiver found (shouldn't happen in a valid chat)

    receiver_id = receiver.id  # The logged-in user who will receive the message

    # Get the WebSocket channel layer
    channel_layer = get_channel_layer()

    # Get unread count for the receiver
    unread_count = TextMessage.objects.filter(
        sender=sender_id, chat_room=chat_room, seen_at=None
    ).count()
    local_created_at = timezone.localtime(instance.created_at).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    if unread_count>0:
        async_to_sync(channel_layer.group_send)(
            f"user_{receiver_id}",
            {
                "type": "update_message",
                "action": "friend_update",
                "unread_count": unread_count,
                "sender_id": sender_id,
                "receiver_id":receiver_id,
                "created_at": local_created_at,
                "last_message": instance.msg,
                "time":timezone.localtime(instance.created_at).strftime("%I:%M %p")
            },
        )
