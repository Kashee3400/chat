import pytz
from django.utils.timezone import activate

class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated and hasattr(user, 'profile') and user.profile.timezone:
            activate(pytz.timezone(user.profile.timezone))
        else:
            activate(pytz.timezone("UTC"))  # Default to UTC if no timezone is set
        return self.get_response(request)
