from django.shortcuts import redirect
from core.models import Organization


class SetupRequiredMiddleware:
    EXEMPT_PATHS = ["/core/setup/", "/admin/", "/static/"]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not Organization.objects.exists():
            if not any(request.path.startswith(p) for p in self.EXEMPT_PATHS):
                return redirect("core:setup_wizard")
        return self.get_response(request)
