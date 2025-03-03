from django.db.models import Q
from django.views.generic import View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from datetime import date, timedelta
from customauth.models import Profile
from chatroom.models.category import (
    ChatRoomModel,
    TextMessage,
    CallLog,
    MediaFile,
    Reaction,
    ReadReceipt,
    SubCategory,
    ChatRoomUser,
    RoomMessage,
    DirectMessage,
    DirectMessageUser,
)
from django.contrib.auth import get_user_model

User = get_user_model()


class ChatRoomView(LoginRequiredMixin, View):
    template_name = "chatroom/room.html"
    model = SubCategory
    login_url = "/auth/login/"

    def get(self, request, *args, **kwargs):
        obj = get_object_or_404(self.model, pk=kwargs.get("pk"))
        message_list = RoomMessage.objects.filter(room=obj)
        try:
            ChatRoomUser.objects.get(user=request.user, room=obj)
        except ChatRoomUser.DoesNotExist:
            if obj.current_users < obj.max_user:
                ChatRoomUser.objects.create(user=request.user, room=obj)
            else:
                messages.warning(request, "This room is full now.")
                return redirect("home")
        chatrooms = ChatRoomUser.objects.filter(user=request.user)
        all_direct_chat = request.user.me.all()
        buddies = all_direct_chat.filter(friend_type="buddies")
        family_members = all_direct_chat.filter(friend_type="family")
        co_workers = all_direct_chat.filter(friend_type="co-workers")
        context = {
            "user": request.user,
            "chatroom": obj,
            "chatrooms": chatrooms,
            "messages": message_list,
            "all_direct_chat": all_direct_chat,
            "buddies": buddies,
            "family_members": family_members,
            "co_workers": co_workers,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        obj = get_object_or_404(self.model, pk=kwargs.get("pk"))
        message_list = RoomMessage.objects.filter(room=obj)
        photo = request.FILES.get("photo")
        name = request.POST.get("name")
        bio = request.POST.get("bio")
        address = request.POST.get("address")
        user = request.user
        if name:
            user.profile.name = name
        if bio:
            user.profile.bio = bio
        if address:
            user.profile.address = address
        if photo:
            user.profile.avatar = photo
        user.profile.save()
        try:
            ChatRoomUser.objects.get(user=request.user, room=obj)
        except ChatRoomUser.DoesNotExist:
            if obj.current_users < obj.max_user:
                ChatRoomUser.objects.create(user=request.user, room=obj)
            else:
                messages.warning(request, "This room is full now.")
                return redirect("home")
        chatrooms = ChatRoomUser.objects.filter(user=request.user)
        context = {
            "user": request.user,
            "chatroom": obj,
            "chatrooms": chatrooms,
            "messages": message_list,
        }
        return render(request, self.template_name, context)


class DirectChatView(LoginRequiredMixin, TemplateView):
    template_name = "chatroom/direct_room.html"
    login_url = "/auth/login/"
    title = "Direct Chat"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Extract parameters
        chatroom_id = kwargs.get("chatroom")
        user_id = kwargs.get("pk")
        # Fetch objects safely
        chatroom = self.get_chatroom(chatroom_id)
        user_obj = self.get_user(user_id)
        # Retrieve required data
        message_list = self.get_messages(user_obj)
        chatroom_data = self.get_user_chatrooms()
        profile_urls = self.get_profile_urls(user_obj)
        room, created = self.get_or_create_one_to_one_chat(self.request.user, user_obj)

        # Add data to context
        context.update(
            {
                "user": self.request.user,
                "obj": user_obj,
                "chatroom": chatroom,
                "messages": message_list,
                **chatroom_data,  # Unpacking dictionary
                **profile_urls,  # Unpacking dictionary
                "today": date.today(),
                "yesterday": date.today() - timedelta(days=1),
                "title": self.title,
                "room": room,
            }
        )
        return context

    def get_chatroom(self, chatroom_id):
        """Fetch chatroom object or return None."""
        return get_object_or_404(SubCategory, pk=chatroom_id)

    def get_user(self, user_id):
        """Fetch user object or return None."""
        return get_object_or_404(User, pk=user_id)

    def get_messages(self, user_obj):
        """Fetch messages between the logged-in user and the selected user."""
        return DirectMessage.objects.filter(
            Q(sender_user=user_obj, receiver_user=self.request.user)
            | Q(sender_user=self.request.user, receiver_user=user_obj)
        ).order_by("created_at")

    def get_user_chatrooms(self):
        """Fetch the logged-in user's chatrooms and direct chat relationships."""
        user = self.request.user
        chatrooms = ChatRoomUser.objects.filter(user=user)
        all_direct_chat = user.me.all()

        return {
            "chatrooms": chatrooms,
            "all_direct_chat": all_direct_chat,
            "buddies": all_direct_chat.filter(friend_type="buddies"),
            "family_members": all_direct_chat.filter(friend_type="family"),
            "co_workers": all_direct_chat.filter(friend_type="co-workers"),
        }

    def get_profile_urls(self, user_obj):
        """Get profile picture URLs for both users."""

        def get_avatar_url(user):
            return (
                user.profile.avatar.url
                if user.profile.avatar
                else "/static/assets/img/avatars/avatar.png"
            )

        return {
            "user_profile_url": get_avatar_url(self.request.user),
            "receiver_profile_url": get_avatar_url(user_obj),
        }

    def get_or_create_one_to_one_chat(self, user1, user2):
        """Fetch or create a one-to-one chat room between two users."""
        user_ids = sorted([user1.id, user2.id])

        # Try to find an existing chat room
        chat_room = (
            ChatRoomModel.objects.filter(
                room_type="one_to_one", participants__id=user_ids[0]
            )
            .filter(participants__id=user_ids[1])
            .first()
        )

        if chat_room:
            return chat_room, False  # False means "not newly created"
        # If no existing room, create a new one
        chat_room = ChatRoomModel.objects.create(room_type="one_to_one")
        chat_room.participants.add(user1, user2)
        return chat_room, True

    def post(self, request, *args, **kwargs):
        # Handle profile updates
        user = request.user
        profile = user.profile
        profile.name = request.POST.get("name", profile.name)
        profile.bio = request.POST.get("bio", profile.bio)
        profile.address = request.POST.get("address", profile.address)
        if "photo" in request.FILES:
            profile.avatar = request.FILES["photo"]
        profile.save()
        # Redirect to the same page after updating
        return self.get(request, *args, **kwargs)


class OneToOneChatView(LoginRequiredMixin, TemplateView):
    template_name = "chatroom/one_to_one_room.html"
    login_url = "/auth/login/"
    title = "One To One Chat"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        online_users = self.get_all_users(self.request.user.pk)
        # Add data to context
        context.update(
            {
                "user": self.request.user,
                "online_users": online_users,
                "today": date.today(),
                "yesterday": date.today() - timedelta(days=1),
                "title": self.title,
            }
        )
        return context

    def get_user(self, user_slug):
        """Fetch user object or return None."""
        profile =  Profile.objects.get(slug=user_slug)
        return profile.user

    def get_all_users(self, user_id):
        """Fetch all users except the current user."""
        return User.objects.exclude(id=user_id)


    def post(self, request, *args, **kwargs):
        # Handle profile updates
        user = request.user
        profile = user.profile
        profile.name = request.POST.get("name", profile.name)
        profile.bio = request.POST.get("bio", profile.bio)
        profile.address = request.POST.get("address", profile.address)
        if "photo" in request.FILES:
            profile.avatar = request.FILES["photo"]
        profile.save()
        # Redirect to the same page after updating
        return self.get(request, *args, **kwargs)


class ChatRoomSidebarView(LoginRequiredMixin, View):
    template_name = "chatroom/userpanel.html"
    model = SubCategory
    login_url = "/auth/login/"

    def get(self, request, *args, **kwargs):
        obj = None
        context = {
            "obj": obj,
        }
        return render(request, self.template_name, context)


class ChatBoxView(LoginRequiredMixin, View):
    template_name = "chatroom/chatbox.html"
    model = SubCategory
    login_url = "/auth/login/"

    def get(self, request, *args, **kwargs):
        obj = get_object_or_404(self.model, pk=kwargs.get("pk"))
        context = {
            "obj": obj,
        }
        return render(request, self.template_name, context)


class ChatUsersView(LoginRequiredMixin, View):
    template_name = "chatroom/chatusers.html"
    model = SubCategory
    login_url = "/auth/login/"

    def get(self, request, *args, **kwargs):
        obj = get_object_or_404(self.model, pk=kwargs.get("pk"))
        context = {
            "obj": obj,
        }
        return render(request, self.template_name, context)


###################################################################################
########                                                            ###############
########       API for chat room to load messages                   ###############
########       By Divyanshu Kumar Kushwaha                          ###############
###################################################################################

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse

def load_chat_room(request, slug):
    """Loads the chat room dynamically"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        user = get_object_or_404(User, profile__slug=slug)
        return render(request, "chatroom/one_to_one_chat.html", {"receiver": user})
    return JsonResponse({"error": "Invalid request"}, status=400)


from django.http import JsonResponse
from django.template.loader import render_to_string
from datetime import date, timedelta

class LoadUserChatView(View):
    """Dynamically loads user-specific chat data via AJAX"""

    def get(self, request, *args, **kwargs):
        user_slug = kwargs.get("slug")
        user_obj = self.get_user(user_slug)  # Get user by slug
        room, _ = self.get_or_create_one_to_one_chat(request.user, user_obj)
        profileUrls = self.get_profile_urls(user_obj=user_obj)

        messages_html = render_to_string("chatroom/partials/_chat_messages.html", {
            "messages": self.get_messages(user_obj),
            "request": request,
            "user":request.user,
            "room":room,
            "receiver_id":user_obj.pk,
            **profileUrls,
            "bg_image":"/static/assets/img/chat_wallpaper1.svg",
        })
        chat_header_html = render_to_string("chatroom/partials/_chat_header.html", {
            "obj": user_obj,
            "room":room,
            "bg_image":"/static/assets/img/chat_wallpaper1.svg"
        })

        return JsonResponse({
            "chat_header_html": chat_header_html,
            "messages_html": messages_html,
            "room_id":room.id
        })
    def get_messages(self, user_obj):
        """Fetch only the latest 15 messages between the logged-in user and the selected user."""
        room, created = self.get_or_create_one_to_one_chat(self.request.user, user_obj)
        return TextMessage.objects.filter(chat_room=room).order_by("-created_at")[:15][::-1]

    def get_user(self, user_slug):
        """Fetch user object or return None."""
        profile =  Profile.objects.get(slug=user_slug)
        return profile.user
    
    def get_profile_urls(self, user_obj):
        """Get profile picture URLs for both users."""

        def get_avatar_url(user):
            return (
                user.profile.avatar.url
                if user.profile.avatar
                else "/static/assets/img/avatars/avatar.png"
            )

        return {
            "user_profile_url": get_avatar_url(self.request.user),
            "receiver_profile_url": get_avatar_url(user_obj),
        }

    def get_or_create_one_to_one_chat(self, user1, user2):
        """Fetch or create a one-to-one chat room between two users."""
        user_ids = sorted([user1.id, user2.id])

        # Try to find an existing chat room
        chat_room = (
            ChatRoomModel.objects.filter(
                room_type="one_to_one", participants__id=user_ids[0]
            )
            .filter(participants__id=user_ids[1])
            .first()
        )

        if chat_room:
            return chat_room, False  # False means "not newly created"
        # If no existing room, create a new one
        room_name = f"one_to_one_{user_ids[0]}_{user_ids[1]}"
        chat_room = ChatRoomModel.objects.create(
            room_name=room_name, room_type="one_to_one"
        )
        chat_room.participants.add(user1, user2)
        return chat_room, True
