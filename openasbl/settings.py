import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Mode dual: "server" (défaut) ou "desktop" (usage local via Electron) ---
OPENASBL_RUNTIME_MODE = os.environ.get("OPENASBL_RUNTIME_MODE", "server")
OPENASBL_IS_DESKTOP = OPENASBL_RUNTIME_MODE == "desktop"

DEFAULT_SECRET_KEY = "django-insecure-dev-only-change-in-production"

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", DEFAULT_SECRET_KEY)

DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() in ("true", "1")

if OPENASBL_IS_DESKTOP:
    # Mode desktop: écoute locale uniquement
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
    # Répertoire de données utilisateur (base de tout en mode desktop)
    OPENASBL_DATA_DIR = Path(
        os.environ.get("OPENASBL_DATA_DIR", Path.home() / ".openasbl")
    )
    OPENASBL_DATA_DIR.mkdir(parents=True, exist_ok=True)
else:
    ALLOWED_HOSTS = [
        host.strip()
        for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
        if host.strip()
    ]

# --- Sécurité du mode serveur en production ---------------------------------
# Le mode serveur sans DEBUG suppose un déploiement derrière un reverse proxy
# qui termine le TLS (nginx + certbot). Sans ces réglages, Django croit parler
# en clair et rejette tous les POST au contrôle d'origine CSRF.
if not OPENASBL_IS_DESKTOP and not DEBUG:
    if SECRET_KEY == DEFAULT_SECRET_KEY:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY doit être défini en mode serveur. "
            "Générez une clé : python3 -c \"import secrets; print(secrets.token_urlsafe(50))\""
        )

    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

    # Origines autorisées pour le contrôle CSRF, déduites des hôtes servis.
    _csrf_origins = os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "")
    if _csrf_origins:
        CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins.split(",") if o.strip()]
    else:
        CSRF_TRUSTED_ORIGINS = [
            f"https://{host}"
            for host in ALLOWED_HOSTS
            if host not in ("localhost", "127.0.0.1") and not host.startswith(".")
        ]

    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True

    # HSTS : désactivé par défaut car irréversible côté navigateur pendant sa
    # durée de vie. À activer une fois le TLS confirmé (ex : 31536000).
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", "0"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_htmx",
    "core",
    "accounts",
    "accounting",
    "reports",
    "help",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "accounts.middleware.SetupRequiredMiddleware",
]

ROOT_URLCONF = "openasbl.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.organization",
                "core.context_processors.version",
            ],
        },
    },
]

WSGI_APPLICATION = "openasbl.wsgi.application"

if OPENASBL_IS_DESKTOP:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": OPENASBL_DATA_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr"
TIME_ZONE = "Europe/Brussels"
USE_I18N = True
USE_TZ = True

LOCALE_PATHS = [BASE_DIR / "locale"]

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = (OPENASBL_DATA_DIR / "staticfiles") if OPENASBL_IS_DESKTOP else (BASE_DIR / "staticfiles")
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = "media/"
MEDIA_ROOT = (OPENASBL_DATA_DIR / "media") if OPENASBL_IS_DESKTOP else (BASE_DIR / "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

OPENASBL_UPDATE_CHECK_URL = os.environ.get(
    "OPENASBL_UPDATE_CHECK_URL",
    "https://raw.githubusercontent.com/yetouse/openasbl/main/VERSION",
)
OPENASBL_UPDATE_CHECK_TIMEOUT = float(os.environ.get("OPENASBL_UPDATE_CHECK_TIMEOUT", "1.5"))
_env_update_enabled = os.environ.get("OPENASBL_UPDATE_CHECK_ENABLED", "")
OPENASBL_UPDATE_CHECK_ENABLED = (
    _env_update_enabled.lower() in ("true", "1") if _env_update_enabled else OPENASBL_IS_DESKTOP
)
