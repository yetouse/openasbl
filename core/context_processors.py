from core.models import Organization


def organization(request):
    """Make the organization available in all templates."""
    try:
        org = Organization.objects.first()
    except Exception:
        org = None
    return {"organization": org}
