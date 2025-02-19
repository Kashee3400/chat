from django import template

register = template.Library()

@register.filter
def is_sender(user_email, message_sender_email):
    """Checks if the given message was sent by the current user."""
    return user_email.lower() == message_sender_email.lower()



@register.filter
def index(sequence, position):
    try:
        return sequence[position]
    except (IndexError, TypeError):
        return None  # Return None if index is out of range or invalid