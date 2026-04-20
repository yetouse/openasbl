from django.conf import settings

from core.models import Organization


def organization(request):
    """Make the organization available in all templates."""
    try:
        org = Organization.objects.first()
    except Exception:
        org = None
    return {"organization": org}


def version(request):
    """Make the app version available in all templates."""
    version_file = settings.BASE_DIR / "VERSION"
    try:
        return {"app_version": version_file.read_text(encoding="utf-8").strip()}
    except OSError:
        return {"app_version": ""}
