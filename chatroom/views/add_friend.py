from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model

User = get_user_model()
from chatroom.models import DirectMessageUser, ChatRoomUser, ChatRoomModel, TextMessage
from django.db.models import Q


class AddFriendView(LoginRequiredMixin, View):
    def get(self, request, userid, *args, **kwargs):
        user = User.objects.get(pk=userid)
        friend = DirectMessageUser.objects.get_or_create(me=request.user, friends=user)
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


class MakeFriendView(LoginRequiredMixin, View):

    def get(self, request, userid, *args, **kwargs):
        user = User.objects.get(pk=userid)
        friend = DirectMessageUser.objects.get(me=request.user, friends=user)
        friend.friend_type = "buddies"
        friend.save()
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


class MakeFamilyMemberView(LoginRequiredMixin, View):

    def get(self, request, userid, *args, **kwargs):
        user = User.objects.get(pk=userid)
        friend = DirectMessageUser.objects.get(me=request.user, friends=user)
        friend.friend_type = "family"
        friend.save()
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


class MakeCoWorkerView(LoginRequiredMixin, View):

    def get(self, request, userid, *args, **kwargs):
        user = User.objects.get(pk=userid)
        friend = DirectMessageUser.objects.get(me=request.user, friends=user)
        friend.friend_type = "co-workers"
        friend.save()
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt


@login_required
def send_friend_request(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)
    receiver_id = request.POST.get("request_id")
    if not receiver_id:
        return JsonResponse({"error": "Receiver ID is required"}, status=400)

    try:
        receiver = User.objects.get(pk=receiver_id)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

    # Check if request already exists
    obj, created = DirectMessageUser.send_friend_request(request.user, receiver)

    return (
        JsonResponse(
            {"message": "Friend request sent successfully!"}, status=201
        )
        if created
        else JsonResponse({"error": "Friend request already sent"}, status=400)
    )


@login_required
def update_friend_status(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)
    status = request.POST.get("status")
    request_id = request.POST.get("request_id")
    if not status:
        return JsonResponse({"error": "Status is required"}, status=400)
    if not request_id:
        return JsonResponse({"error": "Request id is required"}, status=400)
    obj = DirectMessageUser.objects.get(id=request_id)
    obj.update_status(status=status)
    return JsonResponse({"message": f"{obj.status.capitalize()}"}, status=200)


def get_last_message(user_id1, user_id2):
    user_ids = sorted([user_id1, user_id2])
    room_name = f"one_to_one_{user_ids[0]}_{user_ids[1]}"
    chat_room = ChatRoomModel.objects.filter(
        room_name=room_name
    ).first()
    text_message = (
        TextMessage.objects.filter(chat_room=chat_room).order_by("-created_at").first()
    )
    return text_message.msg if text_message is not None else ""


def friends_list_api(request):
    """API endpoint to return friends list as JSON."""
    user = request.user
    friends = DirectMessageUser.objects.filter(
        Q(me=user, status=DirectMessageUser.FriendStatus.ACCEPTED)
        | Q(friends=user, status=DirectMessageUser.FriendStatus.ACCEPTED)
    )
    friends_data = [
        {
            "id": friend.friends.id if friend.me == user else friend.me.id,
            "name": (
                friend.friends.profile.name
                if friend.me == user
                else friend.me.profile.name
            ),
            "avatar": (
                friend.friends.profile.avatar.url
                if friend.me == user and friend.friends.profile.avatar
                else (
                    friend.me.profile.avatar.url
                    if friend.friends == user and friend.me.profile.avatar
                    else "/static/assets/img/avatars/avatar.png"
                )
            ),
            "last_message": get_last_message(friend.friends.pk, friend.me.pk),
        }
        for friend in friends
    ]

    return JsonResponse({"friends": friends_data})
