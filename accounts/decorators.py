from functools import wraps

from django.http import HttpResponseForbidden

from accounts.models import LEVEL_ORDER


def require_permission(minimum_level):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not hasattr(request.user, "profile"):
                return HttpResponseForbidden("Accès refusé.")
            profile = request.user.profile
            if LEVEL_ORDER.index(profile.permission_level) < LEVEL_ORDER.index(minimum_level):
                return HttpResponseForbidden("Accès refusé.")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
