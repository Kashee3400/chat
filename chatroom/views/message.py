from django.views.generic import View
from django.http import HttpResponse
from django.contrib.auth import get_user_model
User = get_user_model()

from chatroom.models import SubCategory, ChatRoomUser, RoomMessage, DirectMessage


class SendRoomMessageView(View):

    def get(self, request, *args, **kwargs):
        roomid = request.GET.get('roomid')
        email = request.GET.get('email')
        message = request.GET.get('message')
        room = SubCategory.objects.get(id=roomid)
        message_list = RoomMessage.objects.create(
            room=room,
            user=request.user,
            message=message,
        )
        return HttpResponse('SUCCESS')


class SendDirectMessageView(View):
    def get(self, request, *args, **kwargs):
        receiver = request.GET.get('receiver_id')
        message = request.GET.get('message')
        receiver_user = User.objects.get(id=receiver)
        DirectMessage.objects.create(
            sender_user=request.user,
            receiver_user=receiver_user,
            message=message
        )
        return HttpResponse('SUCCESS')
