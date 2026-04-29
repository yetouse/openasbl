import urllib.request

from django.conf import settings

_cache = None
_RELEASES_URL = "https://github.com/yetouse/openasbl/releases/latest"


def _parse_version(v):
    try:
        return tuple(int(x) for x in v.strip().split("."))
    except (ValueError, AttributeError):
        return (0,)


def check_for_update():
    global _cache
    if _cache is not None:
        return _cache

    try:
        current = (settings.BASE_DIR / "VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        current = ""

    check_url = getattr(
        settings,
        "OPENASBL_UPDATE_CHECK_URL",
        "https://raw.githubusercontent.com/yetouse/openasbl/main/VERSION",
    )
    timeout = getattr(settings, "OPENASBL_UPDATE_CHECK_TIMEOUT", 1.5)
    is_desktop = getattr(settings, "OPENASBL_IS_DESKTOP", False)
    update_command = "./install-desktop.sh" if is_desktop else "sudo ./install-server.sh"

    latest = current
    try:
        with urllib.request.urlopen(check_url, timeout=timeout) as resp:
            latest = resp.read().decode("utf-8").strip()
    except Exception:
        pass

    _cache = {
        "update_available": bool(
            current and latest and _parse_version(latest) > _parse_version(current)
        ),
        "current_version": current,
        "latest_version": latest,
        "update_url": _RELEASES_URL,
        "update_command": update_command,
    }
    return _cache
