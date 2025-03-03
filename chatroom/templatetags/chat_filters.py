from django import template
from chatroom.models.category import ChatRoomModel, TextMessage, DirectMessageUser
from django.contrib.auth import get_user_model
from django.utils.timezone import localdate,localtime,make_aware,make_naive
User = get_user_model()
from django.db.models import Q
import pytz

register = template.Library()


@register.filter
def is_sender(user_email, message_sender_email):
    """Checks if the given message was sent by the current user."""
    return user_email.lower() == message_sender_email.lower()


@register.filter
def index(sequence, position):
    try:
        return sequence[position]
    except (IndexError, TypeError):
        return None


@register.inclusion_tag("chatroom/templatetag/online_users.html", takes_context=True)
def online_users(context, user_id=None):
    request = context.get("request")
    online_users = User.objects.exclude(id=request.user.pk)
    return {"request": request, "online_users": online_users, "user_id": user_id}

@register.inclusion_tag("chatroom/templatetag/_friends_list.html", takes_context=True)
def user_friends(context):
    request = context.get("request")
    return {"request": request}


@register.inclusion_tag("chatroom/templatetag/_friend_req.html", takes_context=True)
def friend_request(
    context,
):
    request = context.get("request")
    requests = DirectMessageUser.get_pending_requests(user=request.user)
    return {"title": "Friend Request", "requests": requests}


@register.inclusion_tag("chatroom/navbar.html", takes_context=True)
def load_navbar(
    context,
):
    request = context.get("request")
    request_count = DirectMessageUser.get_pending_requests(user=request.user).count()
    friends_count = DirectMessageUser.get_friends(user=request.user).count()
    return {
        "title": "Friend Request",
        "request_count": request_count,
        "friends_count": friends_count,
        "request": request,
    }


@register.simple_tag
def get_friends(user):
    """Returns a list of formatted friend objects for the given user using list comprehension."""
    friends = DirectMessageUser.objects.filter(
        Q(me=user, status=DirectMessageUser.FriendStatus.ACCEPTED)
        | Q(friends=user, status=DirectMessageUser.FriendStatus.ACCEPTED)
    )

    return [
        {
            "pk": friend.friends.pk if friend.me == user else friend.me.pk,
            "name": (
                (
                    friend.friends.profile.name
                    if friend.me == user
                    else friend.me.profile.name
                )
                if (friend.friends.profile and friend.me.profile)
                else "Unknown"
            ),
            "avatar": (
                (
                    friend.friends.profile.avatar.url
                    if friend.me == user
                    else friend.me.profile.avatar.url
                )
                if (
                    friend.friends.profile
                    and friend.me.profile
                    and friend.friends.profile.avatar
                    and friend.me.profile.avatar
                )
                else "/static/assets/img/avatars/avatar.png"
            ),
            "slug": (
                (
                    friend.friends.profile.slug
                    if friend.me == user
                    else friend.me.profile.slug
                )
                if (friend.friends.profile and friend.me.profile)
                else "#"
            ),
            # Get last message and timestamp
            **dict(
                zip(
                    ["last_message", "last_message_time"],
                    get_last_message(
                        user.id,
                        friend.friends.id if friend.me == user else friend.me.id,
                    ),
                )
            ),
        }
        for friend in friends
    ]

def get_last_message(user_id1, user_id2):
    user_ids = sorted([user_id1, user_id2])
    room_name = f"one_to_one_{user_ids[0]}_{user_ids[1]}"
    chat_room = ChatRoomModel.objects.filter(room_name=room_name).first()

    text_message = (
        TextMessage.objects.filter(chat_room=chat_room).order_by("-created_at").first()
    )

    if text_message:
        message_preview = (
            f"{text_message.msg[:30]}..."
            if len(text_message.msg) > 10
            else text_message.msg
        )
        message_time = localtime(text_message.created_at).strftime("%I:%M %p")  # Format: 10:30 AM

        return message_preview, message_time  # Returning both message and time

    return "", ""  # Return empty values if no message is found


@register.filter
def localtime_filter(value, timezone="UTC"):
    return localtime(value, pytz.timezone(timezone))
