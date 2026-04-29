import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Mode dual: "server" (défaut) ou "desktop" (usage local via Electron) ---
OPENASBL_RUNTIME_MODE = os.environ.get("OPENASBL_RUNTIME_MODE", "server")
OPENASBL_IS_DESKTOP = OPENASBL_RUNTIME_MODE == "desktop"

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-dev-only-change-in-production",
)

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
    ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

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
