from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.utils.text import slugify
from django.contrib.auth import get_user_model
User = get_user_model()
import pytz
from django.conf import settings

def avatar_upload_path(instance, filename):
    return f'avatars/{instance.pk}_{filename}'


class Profile(models.Model):
    """Stores user profile details"""

    GENDER_CHOICES = (
        ('male', _('Male')),
        ('female', _('Female')),
        ('other', _('Other')),
    )
    TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.all_timezones]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile", verbose_name=_("User")
    )
    name = models.CharField(
        _("Full Name"), max_length=255, blank=True, null=True
    )
    slug = models.SlugField(
        _("Slug"), max_length=255, unique=True, blank=True, help_text="Auto-generated from name"
    )
    gender = models.CharField(
        _("Gender"), max_length=10, choices=GENDER_CHOICES, default='male'
    )
    country = models.ForeignKey(
        'chatroom.Country', on_delete=models.SET_NULL, null=True, verbose_name=_("Country")
    )
    state = models.ForeignKey(
        'chatroom.State', on_delete=models.SET_NULL, null=True, verbose_name=_("State")
    )
    avatar = models.ImageField(
        _("Profile Picture"), upload_to='avatars/', null=True, blank=True
    )
    bio = models.TextField(
        _("Bio"), max_length=500, blank=True, validators=[MinLengthValidator(10)]
    )
    address = models.CharField(
        _("Address"), max_length=255, blank=True, null=True
    )
    birth_date = models.DateField(
        _("Date of Birth"), null=True, blank=True
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True,null=True, blank=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    timezone = models.CharField(_("Timezone"), max_length=50, choices=TIMEZONE_CHOICES, default=settings.TIME_ZONE)  # Add Timezone Field

    class Meta:
        verbose_name = _("Profile")
        verbose_name_plural = _("Profiles")
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['slug']),
        ]
        ordering = ['name']

    def save(self, *args, **kwargs):
        """Auto-generate slug from name"""
        if not self.slug and self.name:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - Profile"


class SecuritySettings(models.Model):
    """Stores user security preferences and login history"""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="security_settings", verbose_name=_("User")
    )
    is_2fa_enabled = models.BooleanField(_("Two-Factor Authentication"), default=False)
    is_verified = models.BooleanField(_("Account Verified"), default=False)
    login_history = models.JSONField(_("Login History"), default=list, blank=True)

    class Meta:
        verbose_name = _("Security Setting")
        verbose_name_plural = _("Security Settings")

    def __str__(self):
        return f"Security Settings for {self.user.username}"



class NotificationSettings(models.Model):
    """Stores user notification preferences"""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="notification_settings", verbose_name=_("User")
    )
    receive_notifications = models.BooleanField(_("Receive Notifications"), default=True)
    show_typing_status = models.BooleanField(_("Show Typing Status"), default=True)
    read_receipts = models.BooleanField(_("Read Receipts Enabled"), default=True)
    message_preview = models.BooleanField(_("Message Preview Enabled"), default=True)

    class Meta:
        verbose_name = _("Notification Setting")
        verbose_name_plural = _("Notification Settings")

    def __str__(self):
        return f"Notification Settings for {self.user.username}"
