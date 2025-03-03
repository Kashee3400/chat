from django.shortcuts import HttpResponse
from customauth.models import User
from chatroom.models.category import DirectMessageUser


def ajax_custom_room(request):
    data = request.GET.get('id')
    data = data.split(' ')
    user = User.objects.get(pk=data[0])
    try:
        custom = DirectMessageUser.objects.get(
            friends=user, me=request.user
        )
    except Exception as e:
        custom = DirectMessageUser.objects.create(
            friends=user, friend_type='buddies', me=request.user
        )
    return HttpResponse(user.pk)