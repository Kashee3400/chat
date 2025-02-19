from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
User = get_user_model()
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid



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


class DirectmessageUser(models.Model):
    TYPE_CHOICES = (
        ('buddies', 'Buddies'),
        ('family', 'Family'),
        ('co-workers', 'Co-Workers'),
    )
    me = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='me'
    )
    friends = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='friends'
    )
    friend_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='buddies')
    is_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.me}"


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

class BaseModel(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, verbose_name=_("ID")
    )
    slug = models.SlugField(unique=True, blank=True, null=True, verbose_name=_("Slug"))
    is_deleted = models.BooleanField(default=False, verbose_name=_("Is Delete"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
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

from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class ChatRoomModel(models.Model):
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
            return f"OneToOne:{participant_ids[0]}_{participant_ids[1]}"
        elif self.room_type == 'group' and not self.room_name:
            participant_names = [user.username for user in self.participants.all()]
            return f"Group: {', '.join(participant_names[:3])}"  # Show first 3 participants
        return self.room_name or f"Chat Room {self.id}"

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
        AbstractChatModel,
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