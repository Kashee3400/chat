from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import Profile,SecuritySettings,NotificationSettings
from django.contrib.auth import get_user_model

from django.contrib.auth.signals import user_logged_in
from django.contrib.sessions.models import Session
from django.utils.timezone import now
from django.conf import settings
User = get_user_model()

@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    if created:
        profile, _ = Profile.objects.get_or_create(
            user=instance, 
            defaults={"timezone": settings.TIME_ZONE}
        )
        SecuritySettings.objects.get_or_create(user=instance)
        NotificationSettings.objects.get_or_create(user=instance)
    instance.profile.save()


@receiver(user_logged_in)
def enforce_single_session(sender, request, user, **kwargs):
    """ Log out the previous session when a user logs in from a new device. """
    # Get the current session key
    current_session_key = request.session.session_key

    # Check if the user has another active session
    previous_sessions = Session.objects.filter(expire_date__gte=now())  # Get active sessions
    for session in previous_sessions:
        data = session.get_decoded()
        if data.get('_auth_user_id') == str(user.id) and session.session_key != current_session_key:
            session.delete()  # Log out the previous session
