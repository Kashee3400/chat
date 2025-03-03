from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid
from django.db.models import Q

from django.contrib.auth import get_user_model
User = get_user_model()

class BaseModel(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, verbose_name=_("ID")
    )
    slug = models.SlugField(unique=True, blank=True, null=True, verbose_name=_("Slug"))
    is_deleted = models.BooleanField(default=False, verbose_name=_("Is Delete"))
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True, verbose_name=_("Updated At"))
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_created",
        verbose_name=_("Created By"),
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_updated",
        verbose_name=_("Updated By"),
    )
    deleted_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Deleted At")
    )

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        self.is_deleted = None
        self.deleted_at = None
        self.save()

    def generate_slug(self):
        return str(self.id)


class Category(models.Model):
    TYPE_CHOICES = (
        ('post', 'Post'),
        ('chatroom', 'Chat Room'),
    )
    FEE_STATUS_CHOICES = (
        ('free', 'Free'),
        ('paid', 'Paid'),
    )
    country = models.ForeignKey(
        "chatroom.Country", on_delete=models.SET_NULL, null=True,
        related_name='chatroom'
    )
    name = models.CharField(max_length=255)
    category_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    fee_status = models.CharField(max_length=20, choices=FEE_STATUS_CHOICES)
    ordering = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['country', 'name']
        ordering = ('ordering', )

    def __str__(self):
        return f"{self.name} - ({self.country.name})"

    @property
    def total_sub_category(self):
        return self.sub_categories.all().count()

    def category_type_display(self):
        return dict(self.TYPE_CHOICES)[self.category_type]

    def fee_status_display(self):
        return dict(self.FEE_STATUS_CHOICES)[self.fee_status]


class SubCategory(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='sub_categories'
    )
    name = models.CharField(max_length=255)
    max_user = models.PositiveIntegerField(default=35)
    max_previous_message = models.PositiveIntegerField(default=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['category', 'name']
        ordering = ('name', )

    def __str__(self):
        return f"{self.category.name} ({self.name})"

    @property
    def current_users(self):
        return self.chatroom.count()


class ChatRoomUser(models.Model):
    room = models.ForeignKey(
        SubCategory, on_delete=models.CASCADE, related_name='chatroom'
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='chatroom_users'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.room.name}"

    @property
    def get_last_message(self):
        return RoomMessage.objects.filter(room=self.room, user=self.user).last()


class DirectMessageUser(models.Model):
    """Model to manage friendships, requests, and statuses between users."""

    class FriendStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        HIDDEN = "hidden", "Hidden"
        BLOCKED = "blocked", "Blocked"

    class FriendType(models.TextChoices):
        BUDDIES = "buddies", "Buddies"
        FAMILY = "family", "Family"
        CO_WORKERS = "co-workers", "Co-Workers"

    me = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="me",verbose_name="Sender"
    )
    friends  = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="friends",verbose_name="Receiver"
    )
    friend_type = models.CharField(
        max_length=50, choices=FriendType.choices, default=FriendType.BUDDIES
    )
    status = models.CharField(
        max_length=20, choices=FriendStatus.choices, default=FriendStatus.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("me", "friends")

    def __str__(self):
        return f"{self.me} → {self.friends } ({self.get_status_display()})"
            
    def update_status(self,status):
        """Update the user request."""
        self.status = status
        self.save()


    @classmethod
    def send_friend_request(cls, sender, receiver, friend_type="buddies"):
        """Creates a new friend request if one doesn't already exist."""
        obj, created = cls.objects.get_or_create(
            me=sender, friends=receiver,
            defaults={"friend_type": friend_type, "status": cls.FriendStatus.PENDING},
        )
        return obj, created

    @classmethod
    def are_friends(cls, user1, user2):
        """Checks if two users are friends (Accepted status)."""
        return cls.objects.filter(
            me=user1, friends=user2, status=cls.FriendStatus.ACCEPTED
        ).exists() or cls.objects.filter(
            me=user2, friends=user1, status=cls.FriendStatus.ACCEPTED
        ).exists()

    @classmethod
    def get_friends(cls, user):
        """Returns a queryset of a user's accepted friends."""
        return cls.objects.filter(
            Q(me=user, status=cls.FriendStatus.ACCEPTED) | 
            Q(friends=user, status=cls.FriendStatus.ACCEPTED)
        ).distinct()

    @classmethod
    def get_pending_requests(cls, user):
        """Returns all incoming pending requests for a user."""
        return cls.objects.filter(friends=user, status=cls.FriendStatus.PENDING).order_by('-created_at')

    @classmethod
    def get_blocked_users(cls, user):
        """Returns all users that the given user has blocked."""
        return cls.objects.filter(me=user, status=cls.FriendStatus.BLOCKED)

    @classmethod
    def get_hidden_users(cls, user):
        """Returns all users that the given user has blocked."""
        return cls.objects.filter(me=user, status=cls.FriendStatus.HIDDEN)

class RoomMessage(models.Model):
    room = models.ForeignKey(
        SubCategory, on_delete=models.CASCADE, related_name='message_rooms'
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='user_room_messages'
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.room.name}"


class DirectMessage(models.Model):
    sender_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sender_users'
    )
    receiver_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='receiver_users'
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.sender_user}"

class ChatRoomModel(BaseModel):
    """Model representing a chat room, can be one-to-one or group chat"""

    ROOM_TYPE_CHOICES = (
        ('one_to_one', _('One to One')),
        ('group', _('Group')),
    )

    room_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Room Name'),
        help_text=_('Optional name for the group chat')
    )
    room_type = models.CharField(
        max_length=10,
        choices=ROOM_TYPE_CHOICES,
        default='one_to_one',
        verbose_name=_('Room Type'),
        help_text=_('Defines if the room is a one-to-one chat or a group chat')
    )
    participants = models.ManyToManyField(
        User,
        blank=True,
        related_name='chat_rooms',
        verbose_name=_('Participants'),
        help_text=_('Users participating in this chat room')
    )

    class Meta:
        db_table = "chat_rooms"
        ordering = ['-id']
        verbose_name = _('Chat Room')
        verbose_name_plural = _('Chat Rooms')
        indexes = [
            models.Index(fields=['room_type']),
        ]

    def __str__(self):
        """Returns a human-readable representation of the room."""
        return self.get_room_name()

    def get_room_name(self):
        """
        Generates a default room name:
        - For one-to-one chats: "OneToOne:<user1_id>_<user2_id>"
        - For group chats: "Group: <participant1>, <participant2>, ..."
        """
        if self.room_type == 'one_to_one' and self.participants.count() == 2:
            participant_ids = sorted([str(user.id) for user in self.participants.all()])
            return f"one_to_one_{participant_ids[0]}_{participant_ids[1]}"
        elif self.room_type == 'group' and not self.room_name:
            participant_names = [user.username for user in self.participants.all()]
            return f"Group: {', '.join(participant_names[:3])}"  # Show first 3 participants
        return self.room_name or f"Chat Room {self.id}"
    
    @property
    def last_message(self):
        """Returns the last message in the chat room."""
        return TextMessage.objects.filter(chat_room=self).order_by("-id").first()

    def clean(self):
        """Validation to ensure one-to-one chats have exactly two participants."""
        if self.room_type == 'one_to_one' and self.participants.count() != 2:
            raise ValidationError("One-to-one chats must have exactly two participants.")


class AbstractChatModel(models.Model):
    """Abstract base model for chat messages."""

    MESSAGE_TYPE_CHOICES = (
        ('text', _('Text')),
        ('image', _('Image')),
        ('video', _('Video')),
        ('call', _('Call')),
    )

    slug = models.SlugField(unique=True, blank=True, null=True, verbose_name=_("Slug"))
    chat_room = models.ForeignKey(
        ChatRoomModel,
        on_delete=models.CASCADE,
        related_name="%(class)s_messages",
        verbose_name=_('Chat Room'),
        help_text=_('The chat room to which the message belongs')
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('Sender'),
        help_text=_('The user who sent the message')
    )
    sent_at = models.DateTimeField(
        verbose_name=_('Sent Time'),
        auto_now_add=True,
        help_text=_('The time the message was sent')
    )
    delivered_at = models.DateTimeField(
        verbose_name=_('Delivered Time'),
        null=True,
        blank=True,
        help_text=_('The time the message was delivered to the recipient')
    )
    seen_at = models.DateTimeField(
        verbose_name=_('Seen Time'),
        null=True,
        blank=True,
        help_text=_('The time the message was seen by the recipient')
    )
    is_deleted = models.BooleanField(default=False, verbose_name=_("Is Delete"))
    created_at = models.DateTimeField(auto_now_add=True, null=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, null=True, verbose_name=_("Updated At"))
    deleted_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Deleted At")
    )
    message_type = models.CharField(
        max_length=100,
        choices=MESSAGE_TYPE_CHOICES,
        default='text',
        help_text=_("Type of the message. For ex:- call, text, media")
    )
    synced = models.BooleanField(
        default=True,
        help_text=_("This handles the message syncing with mobile database to the server database")
    )

    class Meta:
        abstract = True
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['chat_room', 'sent_at']),
            models.Index(fields=['sender', 'sent_at']),
        ]


class TextMessage(AbstractChatModel):
    """Model for storing text messages in a chat, with support for replies and media."""
    msg = models.TextField(
        verbose_name=_('Message Text'),
        help_text=_('The content of the message'),
        blank=True,
        null=True
    )
    is_edited = models.BooleanField(
        default=False,
        verbose_name=_('Edited'),
        help_text=_('Indicates whether the message has been edited')
    )
    old_msg = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Previous Message Text'),
        help_text=_('The content of the message before it was edited')
    )
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="replies",
        verbose_name=_('Reply To'),
        help_text=_('The message this one is replying to')
    )

    def __str__(self):
        """Returns a human-readable representation of the message."""
        if self.reply_to:
            return f"Reply to {self.reply_to.id} by {self.sender}"
        return f"Text Message by {self.sender}"

    class Meta(AbstractChatModel.Meta):
        db_table = "chat_text_messages"


class MediaFile(models.Model):
    """Model for storing media files associated with messages."""

    message = models.ForeignKey(
        TextMessage,
        on_delete=models.CASCADE,
        related_name='media_files',
        verbose_name=_('Message')
    )
    file_path = models.CharField(
        max_length=255,
        verbose_name=_('File Path'),
        help_text=_('Path to the media file on the server')
    )
    local_path = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Local Path'),
        help_text=_('Path to the media file on the local device')
    )

    def __str__(self):
        return f"Media File for Message {self.message.id}"


class Reaction(models.Model):
    """Model for storing reactions to messages."""

    REACTION_CHOICES = (
        ('like', _('Like')),
        ('love', _('Love')),
        ('laugh', _('Laugh')),
        ('wow', _('Wow')),
    )

    message = models.ForeignKey(
        TextMessage,
        on_delete=models.CASCADE,
        related_name='reactions',
        verbose_name=_('Message')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('User')
    )
    reaction_type = models.CharField(
        max_length=50,
        choices=REACTION_CHOICES,
        verbose_name=_('Reaction Type')
    )
    class Meta:
        db_table = "chat_reactions"
        verbose_name = _("Chat Reaction")
        verbose_name_plural = _("Chat Reactions")


    def __str__(self):
        return f"{self.user.username} reacted with {self.reaction_type} to Message {self.message.id}"


class CallLog(models.Model):
    """Model for storing call logs."""

    CALL_TYPE_CHOICES = (
        ('voice', _('Voice Call')),
        ('video', _('Video Call')),
    )

    STATUS_CHOICES = (
        ('missed', _('Missed')),
        ('answered', _('Answered')),
        ('declined', _('Declined')),
    )

    chat_room = models.ForeignKey(
        ChatRoomModel,
        on_delete=models.CASCADE,
        related_name='call_logs',
        verbose_name=_('Chat Room')
    )
    caller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='outgoing_calls',
        verbose_name=_('Caller')
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='incoming_calls',
        verbose_name=_('Receiver')
    )
    started_at = models.DateTimeField(verbose_name=_('Started At'))
    ended_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Ended At')
    )
    call_type = models.CharField(
        max_length=50,
        choices=CALL_TYPE_CHOICES,
        verbose_name=_('Call Type')
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        verbose_name=_('Call Status')
    )
    class Meta:
        db_table = "chat_call log"
        verbose_name = _("Call Log")
        verbose_name_plural = _("Call Logs")

    def __str__(self):
        return f"Call from {self.caller.username} to {self.receiver.username} ({self.status})"


class ReadReceipt(models.Model):
    """Model for storing read receipts for messages."""

    message = models.ForeignKey(
        TextMessage,
        on_delete=models.CASCADE,
        related_name='read_receipts',
        verbose_name=_('Message')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('User')
    )
    read_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Read At')
    )
    class Meta:
        unique_together = ('message', 'user')
        db_table = "chat_read_receipt"
        verbose_name = _("Read Receipt")
        verbose_name_plural = _("Read Receipts")

    def __str__(self):
        return f"{self.user.username} read Message {self.message.id} at {self.read_at}"
    
    
import os
class MediaType(BaseModel):
    """Model for defining media types with additional attributes."""

    type = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Media Type Name'),
        help_text=_('The name of the media type (e.g., Image, Video, etc.)')
    )
    icon = models.ImageField(
        upload_to='media_icons/',
        blank=True,
        null=True,
        verbose_name=_('Icon'),
        help_text=_('Icon representing the media type')
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description'),
        help_text=_('Description of the media type and its usage')
    )
    allowed_extensions = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Allowed Extensions'),
        help_text=_('Comma-separated list of allowed file extensions (e.g., .jpg, .png)'),
    )

    def __str__(self):
        return self.type

    def is_extension_allowed(self,media_type, file_name):
        """Check if the file extension is allowed for the specified media type."""
        extensions = media_type.allowed_extensions.split(',')
        file_extension = os.path.splitext(file_name)[1].lower()  # Get file extension
        return file_extension in [ext.strip() for ext in extensions]


    class Meta:
        db_table = 'media_types'
        verbose_name = _('Media Type')
        verbose_name_plural = _('Media Types')

from django.db.models import JSONField

class MediaSettings(models.Model):
    media_type = models.ForeignKey(
        MediaType,
        related_name='settings',
        on_delete=models.CASCADE,
        verbose_name=_('Media Type'),
        help_text=_('The type of media to restrict')
    )
    max_size = models.PositiveIntegerField(
        verbose_name=_('Max Size (bytes)'),
        help_text=_('Maximum allowed size for the media file in bytes'),
    )
    max_length = models.PositiveIntegerField(
        verbose_name=_('Max Length (seconds)'),
        help_text=_('Maximum allowed length for media files in seconds (for videos/audio)'),
        null=True,
        blank=True,
    )
    max_files = models.PositiveIntegerField(
        verbose_name=_('Max Number of Files'),
        help_text=_('Maximum number of files allowed in a single message'),
        null=True,
        blank=True,
    )
    additional_fields = JSONField(default=dict, blank=True, verbose_name=_('Additional Fields'))

    def __str__(self):
        return f"{self.media_type.type} - Max Size: {self.max_size} bytes"
    
    class Meta:
        db_table = 'media_settings'
        verbose_name = _('Media Setting')
        verbose_name_plural = _('Media Settings')

class BlockedUserLog(models.Model):
    """Log model to track block/unblock actions."""
    chat_room = models.ForeignKey(
        'ChatRoomModel',
        on_delete=models.CASCADE,
        verbose_name=_('Chat Room')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('User')
    )
    action = models.CharField(max_length=20, verbose_name=_('Action'), help_text=_('block or unblock'))
    performed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='block_actions_performed',
        verbose_name=_('Performed By')
    )
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_('Timestamp'))

    class Meta:
        verbose_name = _('Blocked User Log')
        verbose_name_plural = _('Blocked User Logs')
        indexes = [
            models.Index(fields=['chat_room', 'user', 'action'], name='chat_room_user_action_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} {self.action} in {self.chat_room.room_name} by {self.performed_by.username}"

    @classmethod
    def log_action(cls, chat_room, user, action, performed_by=None):
        """Log a block/unblock action."""
        cls.objects.create(
            chat_room=chat_room,
            user=user,
            action=action,
            performed_by=performed_by
        )

class BlockedUser(BaseModel):
    """Model to track blocked users in chat rooms."""
    chat_room = models.ForeignKey(
        'ChatRoomModel',
        on_delete=models.CASCADE,
        related_name='blocked_users',
        verbose_name=_('Chat Room'),
        help_text=_('The chat room in which the user is blocked')
    )
    blocked_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blocked_in_rooms',
        verbose_name=_('Blocked User'),
        help_text=_('The user that is blocked in this chat room')
    )
    blocked_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Blocked At'))
    unblocked_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Unblocked At'))

    class Meta:
        unique_together = ('chat_room', 'blocked_user')  # Ensure each user can only be blocked once per chat room
        verbose_name = _('Blocked User')
        verbose_name_plural = _('Blocked Users')
        indexes = [
            models.Index(fields=['chat_room', 'blocked_user'], name='chat_room_blocked_user_idx'),
        ]

    def __str__(self):
        return f"{self.blocked_user.username} blocked in {self.chat_room.room_name}"

    @classmethod
    def block_user(cls, chat_room, user_to_block, blocked_by=None):
        """Block a user in a specific chat room."""
        if not cls.objects.filter(chat_room=chat_room, blocked_user=user_to_block).exists():
            blocked_user = cls.objects.create(chat_room=chat_room, blocked_user=user_to_block)
            BlockedUserLog.log_action(chat_room, user_to_block, 'block', blocked_by)
            return True
        return False

    @classmethod
    def unblock_user(cls, chat_room, user_to_unblock, unblocked_by=None):
        """Unblock a user in a specific chat room."""
        blocked_entry = cls.objects.filter(chat_room=chat_room, blocked_user=user_to_unblock).first()
        if blocked_entry and not blocked_entry.unblocked_at:
            blocked_entry.unblocked_at = timezone.now()
            blocked_entry.save()
            BlockedUserLog.log_action(chat_room, user_to_unblock, 'unblock', unblocked_by)
            return True
        return False

    @classmethod
    def is_user_blocked(cls, chat_room, user_to_check):
        """Check if a user is blocked in a specific chat room."""
        return cls.objects.filter(chat_room=chat_room, blocked_user=user_to_check, unblocked_at__isnull=True).exists()

    @classmethod
    def get_blocked_users(cls, chat_room):
        """Get all currently blocked users in a chat room."""
        return cls.objects.filter(chat_room=chat_room, unblocked_at__isnull=True)


class ReportUserModel(BaseModel):
    """Report users for inappropriate behavior"""
    REPORT_ITEMS = (
        ('inappropriate', _('Inappropriate Behavior')),
        ('spam', _('Spam')),
        ('others', _('Other Reasons')),
    )
    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reported_by',
        verbose_name=_('Reporter'),
        help_text=_('The user reporting the issue')
    )
    reported_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reported_user',
        verbose_name=_('Reported User'),
        help_text=_('The user being reported')
    )
    reason = models.CharField(
        max_length=15,
        choices=REPORT_ITEMS,
        verbose_name=_('Report Reason'),
        help_text=_('The reason for the report')
    )
    description = models.TextField(
        verbose_name=_('Report Description'),
        help_text=_('Description of the issue in the report')
    )

    class Meta:
        db_table = "user_reports"
        ordering = ['-id']
        verbose_name = _('User Report')
        verbose_name_plural = _('User Reports')
        indexes = [
            models.Index(fields=['reporter', 'reported_user']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['reporter', 'reported_user', 'reason'], name='unique_report')
        ]

    def __str__(self):
        return f"Report by {self.reporter} against {self.reported_user}"

class UserStatusModel(BaseModel):
    """Model to store the user's online status and scheduled availability"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='status',
        verbose_name=_('User'),
        help_text=_('The user whose status is being stored')
    )
    is_online = models.BooleanField(
        default=False,
        verbose_name=_('Online Status'),
        help_text=_('Indicates if the user is currently online')
    )
    last_online = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Last Online'),
        help_text=_('The last time the user was online')
    )
    scheduled_start = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Scheduled Start Time'),
        help_text=_('The time the user has scheduled to come online')
    )
    scheduled_end = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Scheduled End Time'),
        help_text=_('The time the user has scheduled to go offline')
    )
    custom_status = models.CharField(
        _("Custom Status"), max_length=255, blank=True, null=True
    )
    chat_theme = models.CharField(_("Chat Theme"), max_length=20, default='light')


    class Meta:
        db_table = "user_status"
        ordering = ['user']
        verbose_name = _('User Status')
        verbose_name_plural = _('Users\' Statuses')
        indexes = [
            models.Index(fields=['user']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['user'], name='unique_user_status')
        ]

    def __str__(self):
        return f"{self.user.username}'s status"
