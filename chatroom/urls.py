from django.urls import path

from chatroom import views

app_name = "chatroom"


urlpatterns = [
    path("", views.ChatDashboardView.as_view(), name="chat_dashboard"),
    path("<int:pk>/", views.ChatRoomView.as_view(), name="room"),
    path(
        "<int:chatroom>/direct/<int:pk>/",
        views.DirectChatView.as_view(),
        name="direct_chat",
    ),
    path(
        "discover/home/",
        views.OneToOneChatView.as_view(),
        name="direct_chatting",
    ),
    path("sidebar/", views.ChatRoomSidebarView.as_view(), name="sidebar"),
    path("<int:pk>/chatbox/", views.ChatBoxView.as_view(), name="chatbox"),
    path("<int:pk>/users/", views.ChatUsersView.as_view(), name="users"),
    path(
        "send-room-message/",
        views.SendRoomMessageView.as_view(),
        name="send_room_message",
    ),
    path(
        "send-direct-message/int:<receiver_id>/",
        views.SendDirectMessageView.as_view(),
        name="send_direct_message",
    ),
    path("ajax/custom/room/", views.ajax_custom_room, name="ajax_custom_room"),
    path("add-friend/<int:userid>/", views.AddFriendView.as_view(), name="add_friend"),
    path(
        "make-friend/<int:userid>/", views.MakeFriendView.as_view(), name="make_friend"
    ),
    path(
        "make-family/<int:userid>/",
        views.MakeFamilyMemberView.as_view(),
        name="make_family",
    ),
    path(
        "make-co-worker/<int:userid>/",
        views.MakeCoWorkerView.as_view(),
        name="make_co_worker",
    ),
    path("send-friend-request/", views.send_friend_request, name="send_friend_request"),
    path("update-friend-request/", views.update_friend_status, name="update_friend_status"),
    path("friends_list_api/", views.friends_list_api, name="friends_list_api"),
    path("load-chat/discover/<slug:slug>/", views.LoadUserChatView.as_view(), name="load_chat"),
]
