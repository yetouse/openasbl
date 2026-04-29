from django.conf import settings

from core.models import Organization
from core.update_checker import check_for_update


def organization(request):
    """Make the organization available in all templates."""
    try:
        org = Organization.objects.first()
    except Exception:
        org = None
    return {"organization": org}


def version(request):
    """Make the app version and update info available in all templates."""
    version_file = settings.BASE_DIR / "VERSION"
    try:
        app_version = version_file.read_text(encoding="utf-8").strip()
    except OSError:
        app_version = ""

    context = {
        "app_version": app_version,
        "update_available": False,
        "current_version": app_version,
        "latest_version": "",
        "update_url": "",
        "update_command": "",
    }

    if not getattr(settings, "OPENASBL_UPDATE_CHECK_ENABLED", False):
        return context

    update_context = check_for_update()
    context.update(update_context)
    if not context.get("current_version"):
        context["current_version"] = app_version
    return context
