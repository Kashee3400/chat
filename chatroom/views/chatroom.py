from django.db.models import Q
from django.views.generic import View,TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from datetime import date, timedelta
from chatroom.models import SubCategory, ChatRoomUser, RoomMessage, DirectMessage
from django.contrib.auth import get_user_model
User = get_user_model()


class ChatRoomView(LoginRequiredMixin, View):
    template_name = "chatroom/room.html"
    model = SubCategory
    login_url = "/auth/login/"

    def get(self, request, *args, **kwargs):
        obj = get_object_or_404(self.model, pk=kwargs.get('pk'))
        message_list = RoomMessage.objects.filter(room=obj)
        try:
            ChatRoomUser.objects.get(
                user=request.user,
                room=obj
            )
        except ChatRoomUser.DoesNotExist:
            if obj.current_users < obj.max_user:
                ChatRoomUser.objects.create(
                    user=request.user,
                    room=obj
                )
            else:
                messages.warning(request, "This room is full now.")
                return redirect('home')
        chatrooms = ChatRoomUser.objects.filter(user=request.user)
        all_direct_chat = request.user.me.all()
        buddies = all_direct_chat.filter(friend_type='buddies')
        family_members = all_direct_chat.filter(friend_type='family')
        co_workers = all_direct_chat.filter(friend_type='co-workers')
        context = {
            'user': request.user,
            'chatroom': obj,
            'chatrooms': chatrooms,
            'messages': message_list,
            'all_direct_chat': all_direct_chat,
            'buddies': buddies,
            'family_members': family_members,
            'co_workers': co_workers
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        obj = get_object_or_404(self.model, pk=kwargs.get('pk'))
        message_list = RoomMessage.objects.filter(room=obj)
        photo = request.FILES.get('photo')
        name = request.POST.get('name')
        bio = request.POST.get('bio')
        address = request.POST.get('address')
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
            ChatRoomUser.objects.get(
                user=request.user,
                room=obj
            )
        except ChatRoomUser.DoesNotExist:
            if obj.current_users < obj.max_user:
                ChatRoomUser.objects.create(
                    user=request.user,
                    room=obj
                )
            else:
                messages.warning(request, "This room is full now.")
                return redirect('home')
        chatrooms = ChatRoomUser.objects.filter(user=request.user)
        context = {
            'user': request.user,
            'chatroom': obj,
            'chatrooms': chatrooms,
            'messages': message_list,
        }
        return render(request, self.template_name, context)


class DirectChatView(LoginRequiredMixin, TemplateView):
    template_name = "chatroom/direct_room.html"
    login_url = "/auth/login/"
    title = "Direct Chat"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Extract chatroom and user IDs from URL
        chatroom_id = kwargs.get('chatroom')
        user_id = kwargs.get('pk')

        # Fetch chatroom and user objects
        chatroom = get_object_or_404(SubCategory, pk=chatroom_id)
        obj = get_object_or_404(User, pk=user_id)

        # Fetch messages between the current user and the selected user
        message_list = DirectMessage.objects.filter(
            Q(sender_user=obj, receiver_user=self.request.user) |
            Q(sender_user=self.request.user, receiver_user=obj)
        ).order_by("created_at")

        # Fetch chatrooms and direct chat relationships
        chatrooms = ChatRoomUser.objects.filter(user=self.request.user)
        all_direct_chat = self.request.user.me.all()
        buddies = all_direct_chat.filter(friend_type="buddies")
        family_members = all_direct_chat.filter(friend_type="family")
        co_workers = all_direct_chat.filter(friend_type="co-workers")

        # Get profile URLs
        user_profile_url = (
            self.request.user.profile.avatar.url
            if self.request.user.profile.avatar
            else "/static/assets/img/avatars/avatar.png"
        )
        receiver_profile_url = (
            obj.profile.avatar.url
            if obj.profile.avatar
            else "/static/assets/img/avatars/avatar.png"
        )

        # Add data to context
        context.update({
            "user": self.request.user,
            "obj": obj,
            "chatroom": chatroom,
            "messages": message_list,
            "chatrooms": chatrooms,
            "all_direct_chat": all_direct_chat,
            "buddies": buddies,
            "family_members": family_members,
            "co_workers": co_workers,
            "user_profile_url": user_profile_url,
            "receiver_profile_url": receiver_profile_url,
            "today": date.today(),
            "yesterday": date.today() - timedelta(days=1),
            "title":self.title
        })

        return context

    def post(self, request, *args, **kwargs):
        # Handle profile updates
        user = request.user
        profile = user.profile
        profile.name = request.POST.get('name', profile.name)
        profile.bio = request.POST.get('bio', profile.bio)
        profile.address = request.POST.get('address', profile.address)
        if 'photo' in request.FILES:
            profile.avatar = request.FILES['photo']
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
            'obj': obj,
        }
        return render(request, self.template_name, context)


class ChatBoxView(LoginRequiredMixin, View):
    template_name = "chatroom/chatbox.html"
    model = SubCategory
    login_url = "/auth/login/"

    def get(self, request, *args, **kwargs):
        obj = get_object_or_404(self.model, pk=kwargs.get('pk'))
        context = {
            'obj': obj,
        }
        return render(request, self.template_name, context)


class ChatUsersView(LoginRequiredMixin, View):
    template_name = "chatroom/chatusers.html"
    model = SubCategory
    login_url = "/auth/login/"

    def get(self, request, *args, **kwargs):
        obj = get_object_or_404(self.model, pk=kwargs.get('pk'))
        context = {
            'obj': obj,
        }
        return render(request, self.template_name, context)
