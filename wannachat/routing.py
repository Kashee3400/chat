from django.urls import path,re_path

from chatroom.consumers import consumers,one_to_one_consumer as chat_con

websocket_urlpatterns = [
    path('ws/<int:roomid>/', consumers.ChatConsumer.as_asgi()),
    # path('ws2/<int:roomid>/', consumers.DirectMessageConsumer.as_asgi()),
    path('ws/chat/<int:receiver_id>/', consumers.DirectMessageConsumer.as_asgi()),
    path('ws/one-to-one-chat/<int:receiver_id>/<uuid:room_id>/', chat_con.OneToOneChatConsumer.as_asgi()),
    path("ws/friends/<int:user_id>/", chat_con.FriendConsumer.as_asgi()),
]
