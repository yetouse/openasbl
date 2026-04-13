# OpenASBL Comptabilité — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a simplified accounting web application for small Belgian non-profit associations (ASBL) not subject to VAT.

**Architecture:** Django monolith with 5 apps (core, accounts, accounting, reports, help). SQLite database. HTMX for frontend interactivity. Templates rendered server-side.

**Tech Stack:** Python 3.12+, Django 5.x, HTMX 2.x, WhiteNoise, WeasyPrint (PDF), openpyxl (Excel), SQLite.

---

## File Structure

```
openasbl/
├── manage.py
├── requirements.txt
├── openasbl/                  # Django project settings
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/                      # ASBL configuration
│   ├── __init__.py
│   ├── models.py              # Organization model
│   ├── admin.py
│   ├── forms.py               # Organization setup form
│   ├── views.py               # Setup wizard, org settings
│   ├── urls.py
│   ├── templates/core/
│   │   ├── setup_wizard.html
│   │   └── organization_settings.html
│   └── tests/
│       ├── __init__.py
│       ├── test_models.py
│       └── test_views.py
├── accounts/                  # Auth & permissions
│   ├── __init__.py
│   ├── models.py              # UserProfile with permission level
│   ├── admin.py
│   ├── forms.py               # Login, user management forms
│   ├── views.py               # Login, logout, user CRUD
│   ├── urls.py
│   ├── decorators.py          # Permission-level decorators
│   ├── middleware.py           # Organization context middleware
│   ├── templates/accounts/
│   │   ├── login.html
│   │   └── user_list.html
│   └── tests/
│       ├── __init__.py
│       ├── test_models.py
│       ├── test_views.py
│       └── test_decorators.py
├── accounting/                # Core accounting logic
│   ├── __init__.py
│   ├── models.py              # FiscalYear, Category, Entry, Budget, AssetSnapshot
│   ├── admin.py
│   ├── forms.py               # Entry, Category, Budget, FiscalYear, AssetSnapshot forms
│   ├── views.py               # CRUD views for all accounting models
│   ├── urls.py
│   ├── seed.py                # Default categories for sports club
│   ├── templates/accounting/
│   │   ├── dashboard.html
│   │   ├── entry_list.html
│   │   ├── entry_form.html
│   │   ├── category_list.html
│   │   ├── fiscal_year_list.html
│   │   ├── fiscal_year_close.html
│   │   ├── budget_form.html
│   │   └── asset_snapshot_form.html
│   └── tests/
│       ├── __init__.py
│       ├── test_models.py
│       ├── test_views.py
│       └── test_seed.py
├── reports/                   # Reports & exports
│   ├── __init__.py
│   ├── views.py               # Report generation views
│   ├── urls.py
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── pdf.py             # PDF generation with WeasyPrint
│   │   ├── excel.py           # Excel/CSV generation with openpyxl
│   │   └── xbrl.py            # XBRL export
│   ├── templates/reports/
│   │   ├── report_select.html
│   │   ├── journal_pdf.html          # HTML template for PDF rendering
│   │   ├── patrimony_pdf.html
│   │   ├── annual_accounts_pdf.html
│   │   └── monthly_ca_pdf.html
│   └── tests/
│       ├── __init__.py
│       ├── test_pdf.py
│       ├── test_excel.py
│       └── test_views.py
├── help/                      # Contextual help & assistants
│   ├── __init__.py
│   ├── context.py             # Help text registry
│   ├── views.py               # Help panel HTMX endpoint
│   ├── urls.py
│   ├── templatetags/
│   │   ├── __init__.py
│   │   └── help_tags.py       # {% help "topic" %} template tag
│   ├── templates/help/
│   │   └── help_panel.html
│   └── tests/
│       ├── __init__.py
│       └── test_context.py
├── templates/                 # Shared base templates
│   ├── base.html
│   ├── navbar.html
│   └── partials/
│       ├── messages.html
│       └── pagination.html
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── htmx.min.js
```

---

## Task 1: Django Project Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `openasbl/settings.py`
- Create: `openasbl/urls.py`
- Create: `openasbl/wsgi.py`
- Create: `openasbl/__init__.py`
- Create: `manage.py`
- Create: `templates/base.html`
- Create: `static/css/style.css`

- [ ] **Step 1: Create requirements.txt**

```
Django>=5.0,<5.1
django-htmx>=1.17
whitenoise>=6.6
weasyprint>=61
openpyxl>=3.1
gunicorn>=21
```

- [ ] **Step 2: Create virtual environment and install dependencies**

Run:
```bash
cd /home/yac/openasbl
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

- [ ] **Step 3: Create Django project**

Run:
```bash
django-admin startproject openasbl .
```

This creates `manage.py`, `openasbl/__init__.py`, `openasbl/settings.py`, `openasbl/urls.py`, `openasbl/wsgi.py`, `openasbl/asgi.py`.

- [ ] **Step 4: Configure settings.py**

Replace `openasbl/settings.py` with:

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-dev-only-change-in-production",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() in ("true", "1")

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
            ],
        },
    },
]

WSGI_APPLICATION = "openasbl.wsgi.application"

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
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"
```

- [ ] **Step 5: Download HTMX and create base template**

Run:
```bash
mkdir -p static/css static/js templates/partials
curl -sL https://unpkg.com/htmx.org@2.0.4/dist/htmx.min.js -o static/js/htmx.min.js
```

Create `templates/base.html`:

```html
{% load static i18n %}
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}OpenASBL{% endblock %}</title>
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
    <script src="{% static 'js/htmx.min.js' %}" defer></script>
</head>
<body>
    {% include "navbar.html" %}
    <main>
        {% include "partials/messages.html" %}
        {% block content %}{% endblock %}
    </main>
</body>
</html>
```

Create `templates/navbar.html`:

```html
{% load i18n %}
<nav>
    <a href="/">OpenASBL</a>
    {% if user.is_authenticated %}
        <a href="{% url 'accounting:entry_list' %}">{% trans "Écritures" %}</a>
        <a href="{% url 'reports:report_select' %}">{% trans "Rapports" %}</a>
        <a href="{% url 'accounts:logout' %}">{% trans "Déconnexion" %}</a>
    {% endif %}
</nav>
```

Create `templates/partials/messages.html`:

```html
{% if messages %}
<div class="messages">
    {% for message in messages %}
    <div class="message {{ message.tags }}">{{ message }}</div>
    {% endfor %}
</div>
{% endif %}
```

Create `templates/partials/pagination.html`:

```html
{% if page_obj.has_other_pages %}
<nav class="pagination">
    {% if page_obj.has_previous %}
    <a href="?page={{ page_obj.previous_page_number }}">« Précédent</a>
    {% endif %}
    <span>Page {{ page_obj.number }} sur {{ page_obj.paginator.num_pages }}</span>
    {% if page_obj.has_next %}
    <a href="?page={{ page_obj.next_page_number }}">Suivant »</a>
    {% endif %}
</nav>
{% endif %}
```

Create `static/css/style.css`:

```css
*,
*::before,
*::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

:root {
    --color-primary: #2563eb;
    --color-success: #16a34a;
    --color-danger: #dc2626;
    --color-bg: #f8fafc;
    --color-surface: #ffffff;
    --color-text: #1e293b;
    --color-muted: #64748b;
    --color-border: #e2e8f0;
    --radius: 0.5rem;
    --space: 1rem;
}

body {
    font-family: system-ui, -apple-system, sans-serif;
    background: var(--color-bg);
    color: var(--color-text);
    line-height: 1.6;
}

nav {
    background: var(--color-surface);
    border-bottom: 1px solid var(--color-border);
    padding: var(--space);
    display: flex;
    gap: var(--space);
    align-items: center;
}

nav a {
    color: var(--color-primary);
    text-decoration: none;
    font-weight: 500;
}

main {
    max-width: 960px;
    margin: 0 auto;
    padding: var(--space);
}

.messages .message {
    padding: 0.75rem var(--space);
    border-radius: var(--radius);
    margin-bottom: var(--space);
}

.message.success { background: #dcfce7; color: #166534; }
.message.error { background: #fef2f2; color: #991b1b; }
.message.warning { background: #fefce8; color: #854d0e; }
.message.info { background: #eff6ff; color: #1e40af; }

table {
    width: 100%;
    border-collapse: collapse;
    background: var(--color-surface);
    border-radius: var(--radius);
    overflow: hidden;
}

th, td {
    padding: 0.75rem var(--space);
    text-align: left;
    border-bottom: 1px solid var(--color-border);
}

th { background: var(--color-bg); font-weight: 600; }

.btn {
    display: inline-block;
    padding: 0.5rem 1rem;
    border-radius: var(--radius);
    border: none;
    cursor: pointer;
    font-size: 0.875rem;
    font-weight: 500;
    text-decoration: none;
}

.btn-primary { background: var(--color-primary); color: white; }
.btn-success { background: var(--color-success); color: white; }
.btn-danger { background: var(--color-danger); color: white; }

form label {
    display: block;
    font-weight: 500;
    margin-bottom: 0.25rem;
}

form input, form select, form textarea {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
    font-size: 1rem;
    margin-bottom: var(--space);
}

.form-group { margin-bottom: var(--space); }

.card {
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
    padding: calc(var(--space) * 1.5);
    margin-bottom: var(--space);
}

.text-muted { color: var(--color-muted); }
.text-success { color: var(--color-success); }
.text-danger { color: var(--color-danger); }

.amount-positive { color: var(--color-success); font-weight: 600; }
.amount-negative { color: var(--color-danger); font-weight: 600; }

.pagination {
    display: flex;
    gap: var(--space);
    align-items: center;
    justify-content: center;
    padding: var(--space) 0;
}

@media (max-width: 640px) {
    nav { flex-wrap: wrap; }
    main { padding: 0.5rem; }
    table { font-size: 0.875rem; }
    th, td { padding: 0.5rem; }
}
```

- [ ] **Step 6: Create the 5 Django apps**

Run:
```bash
python manage.py startapp core
python manage.py startapp accounts
python manage.py startapp accounting
python manage.py startapp reports
python manage.py startapp help
```

- [ ] **Step 7: Create initial URL config**

Replace `openasbl/urls.py`:

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounting.urls")),
    path("core/", include("core.urls")),
    path("accounts/", include("accounts.urls")),
    path("reports/", include("reports.urls")),
    path("help/", include("help.urls")),
]
```

Create empty URL files for each app:

`core/urls.py`:
```python
from django.urls import path

app_name = "core"
urlpatterns = []
```

`accounts/urls.py`:
```python
from django.urls import path

app_name = "accounts"
urlpatterns = []
```

`accounting/urls.py`:
```python
from django.urls import path

app_name = "accounting"
urlpatterns = []
```

`reports/urls.py`:
```python
from django.urls import path

app_name = "reports"
urlpatterns = []
```

`help/urls.py`:
```python
from django.urls import path

app_name = "help"
urlpatterns = []
```

- [ ] **Step 8: Create .gitignore**

Create `.gitignore`:

```
__pycache__/
*.py[cod]
*.sqlite3
db.sqlite3
venv/
.env
staticfiles/
media/
*.log
```

- [ ] **Step 9: Run migrations and verify**

Run:
```bash
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Expected: Server starts without errors. Visit http://localhost:8000 — should show a blank page with the base template.

- [ ] **Step 10: Commit**

```bash
git add .gitignore requirements.txt manage.py openasbl/ core/ accounts/ accounting/ reports/ help/ templates/ static/
git commit -m "feat: scaffold Django project with 5 apps and base templates"
```

---

## Task 2: Core App — Organization Model

**Files:**
- Modify: `core/models.py`
- Create: `core/tests/__init__.py`
- Create: `core/tests/test_models.py`
- Modify: `core/admin.py`

- [ ] **Step 1: Create tests directory**

Run:
```bash
rm core/tests.py
mkdir -p core/tests
touch core/tests/__init__.py
```

- [ ] **Step 2: Write the failing test**

Create `core/tests/test_models.py`:

```python
from django.test import TestCase

from core.models import Organization


class OrganizationModelTest(TestCase):
    def test_create_organization(self):
        org = Organization.objects.create(
            name="Royal Cercle de Voile de Dave",
            address="Dave, Namur",
            enterprise_number="0123.456.789",
            email="info@rcvd.be",
            phone="+32 81 123456",
        )
        self.assertEqual(org.name, "Royal Cercle de Voile de Dave")
        self.assertEqual(str(org), "Royal Cercle de Voile de Dave")

    def test_enterprise_number_optional(self):
        org = Organization.objects.create(
            name="Test ASBL",
            address="Bruxelles",
        )
        self.assertEqual(org.enterprise_number, "")

    def test_only_one_organization(self):
        """The app supports a single ASBL per instance."""
        Organization.objects.create(name="First ASBL", address="Namur")
        org2 = Organization(name="Second ASBL", address="Liège")
        with self.assertRaises(Exception):
            org2.full_clean()
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python manage.py test core.tests.test_models -v 2`
Expected: FAIL — `ImportError: cannot import name 'Organization' from 'core.models'`

- [ ] **Step 4: Write the Organization model**

Replace `core/models.py`:

```python
from django.core.exceptions import ValidationError
from django.db import models


class Organization(models.Model):
    name = models.CharField("Nom de l'ASBL", max_length=255)
    address = models.TextField("Adresse du siège social")
    enterprise_number = models.CharField(
        "Numéro d'entreprise (BCE)", max_length=20, blank=True, default=""
    )
    email = models.EmailField("Email", blank=True, default="")
    phone = models.CharField("Téléphone", max_length=30, blank=True, default="")

    class Meta:
        verbose_name = "Organisation"
        verbose_name_plural = "Organisations"

    def __str__(self):
        return self.name

    def clean(self):
        if not self.pk and Organization.objects.exists():
            raise ValidationError(
                "Une seule organisation peut être configurée par instance."
            )
```

- [ ] **Step 5: Register in admin**

Replace `core/admin.py`:

```python
from django.contrib import admin

from core.models import Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "enterprise_number", "email")
```

- [ ] **Step 6: Migrate and run tests**

Run:
```bash
python manage.py makemigrations core
python manage.py migrate
python manage.py test core.tests.test_models -v 2
```

Expected: All 3 tests PASS.

- [ ] **Step 7: Commit**

```bash
git add core/
git commit -m "feat(core): add Organization model with single-instance constraint"
```

---

## Task 3: Accounts App — UserProfile & Permissions

**Files:**
- Modify: `accounts/models.py`
- Create: `accounts/decorators.py`
- Create: `accounts/tests/__init__.py`
- Create: `accounts/tests/test_models.py`
- Create: `accounts/tests/test_decorators.py`
- Modify: `accounts/admin.py`

- [ ] **Step 1: Create tests directory**

Run:
```bash
rm accounts/tests.py
mkdir -p accounts/tests
touch accounts/tests/__init__.py
```

- [ ] **Step 2: Write failing tests for UserProfile**

Create `accounts/tests/test_models.py`:

```python
from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import PermissionLevel, UserProfile
from core.models import Organization


class UserProfileModelTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            name="Test ASBL", address="Namur"
        )
        self.user = User.objects.create_user(
            username="tresorier", password="testpass123"
        )

    def test_create_profile(self):
        profile = UserProfile.objects.create(
            user=self.user,
            organization=self.org,
            permission_level=PermissionLevel.ADMIN,
        )
        self.assertEqual(profile.permission_level, PermissionLevel.ADMIN)
        self.assertEqual(str(profile), "tresorier (Admin)")

    def test_permission_levels(self):
        self.assertEqual(PermissionLevel.LECTURE, "lecture")
        self.assertEqual(PermissionLevel.GESTION, "gestion")
        self.assertEqual(PermissionLevel.VALIDATION, "validation")
        self.assertEqual(PermissionLevel.ADMIN, "admin")

    def test_can_edit(self):
        profile = UserProfile.objects.create(
            user=self.user,
            organization=self.org,
            permission_level=PermissionLevel.GESTION,
        )
        self.assertTrue(profile.can_edit)
        profile.permission_level = PermissionLevel.LECTURE
        self.assertFalse(profile.can_edit)

    def test_can_validate(self):
        profile = UserProfile.objects.create(
            user=self.user,
            organization=self.org,
            permission_level=PermissionLevel.VALIDATION,
        )
        self.assertTrue(profile.can_validate)
        profile.permission_level = PermissionLevel.GESTION
        self.assertFalse(profile.can_validate)

    def test_can_manage_users(self):
        profile = UserProfile.objects.create(
            user=self.user,
            organization=self.org,
            permission_level=PermissionLevel.ADMIN,
        )
        self.assertTrue(profile.can_manage_users)
        profile.permission_level = PermissionLevel.VALIDATION
        self.assertFalse(profile.can_manage_users)
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python manage.py test accounts.tests.test_models -v 2`
Expected: FAIL — `ImportError`

- [ ] **Step 4: Write the UserProfile model**

Replace `accounts/models.py`:

```python
from django.contrib.auth.models import User
from django.db import models


class PermissionLevel(models.TextChoices):
    LECTURE = "lecture", "Lecture"
    GESTION = "gestion", "Gestion"
    VALIDATION = "validation", "Validation"
    ADMIN = "admin", "Admin"


LEVEL_ORDER = [
    PermissionLevel.LECTURE,
    PermissionLevel.GESTION,
    PermissionLevel.VALIDATION,
    PermissionLevel.ADMIN,
]


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    organization = models.ForeignKey(
        "core.Organization", on_delete=models.CASCADE, related_name="members"
    )
    permission_level = models.CharField(
        "Niveau de permission",
        max_length=20,
        choices=PermissionLevel.choices,
        default=PermissionLevel.LECTURE,
    )

    class Meta:
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateurs"

    def __str__(self):
        return f"{self.user.username} ({self.get_permission_level_display()})"

    def _has_level(self, minimum):
        return LEVEL_ORDER.index(self.permission_level) >= LEVEL_ORDER.index(minimum)

    @property
    def can_edit(self):
        return self._has_level(PermissionLevel.GESTION)

    @property
    def can_validate(self):
        return self._has_level(PermissionLevel.VALIDATION)

    @property
    def can_manage_users(self):
        return self._has_level(PermissionLevel.ADMIN)
```

- [ ] **Step 5: Run model tests**

Run: `python manage.py makemigrations accounts && python manage.py migrate && python manage.py test accounts.tests.test_models -v 2`
Expected: All 5 tests PASS.

- [ ] **Step 6: Write failing tests for decorators**

Create `accounts/tests/test_decorators.py`:

```python
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.http import HttpResponse

from accounts.decorators import require_permission
from accounts.models import PermissionLevel, UserProfile
from core.models import Organization


@require_permission(PermissionLevel.GESTION)
def gestion_view(request):
    return HttpResponse("OK")


@require_permission(PermissionLevel.ADMIN)
def admin_view(request):
    return HttpResponse("OK")


class RequirePermissionTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.org = Organization.objects.create(name="Test", address="Namur")

    def _make_user(self, level):
        user = User.objects.create_user(
            username=f"user_{level}", password="testpass123"
        )
        UserProfile.objects.create(
            user=user, organization=self.org, permission_level=level
        )
        return user

    def test_sufficient_permission(self):
        request = self.factory.get("/")
        request.user = self._make_user(PermissionLevel.GESTION)
        response = gestion_view(request)
        self.assertEqual(response.status_code, 200)

    def test_insufficient_permission(self):
        request = self.factory.get("/")
        request.user = self._make_user(PermissionLevel.LECTURE)
        response = gestion_view(request)
        self.assertEqual(response.status_code, 403)

    def test_admin_only(self):
        request = self.factory.get("/")
        request.user = self._make_user(PermissionLevel.VALIDATION)
        response = admin_view(request)
        self.assertEqual(response.status_code, 403)
```

- [ ] **Step 7: Run decorator tests to verify they fail**

Run: `python manage.py test accounts.tests.test_decorators -v 2`
Expected: FAIL — `ImportError: cannot import name 'require_permission'`

- [ ] **Step 8: Write the permission decorator**

Create `accounts/decorators.py`:

```python
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
            if LEVEL_ORDER.index(profile.permission_level) < LEVEL_ORDER.index(
                minimum_level
            ):
                return HttpResponseForbidden("Accès refusé.")
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
```

- [ ] **Step 9: Run all accounts tests**

Run: `python manage.py test accounts.tests -v 2`
Expected: All 8 tests PASS.

- [ ] **Step 10: Register in admin**

Replace `accounts/admin.py`:

```python
from django.contrib import admin

from accounts.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "permission_level")
    list_filter = ("permission_level",)
```

- [ ] **Step 11: Commit**

```bash
git add accounts/
git commit -m "feat(accounts): add UserProfile with 4-level permission system"
```

---

## Task 4: Accounts App — Login/Logout & User Management Views

**Files:**
- Modify: `accounts/forms.py`
- Modify: `accounts/views.py`
- Modify: `accounts/urls.py`
- Create: `accounts/templates/accounts/login.html`
- Create: `accounts/templates/accounts/user_list.html`
- Create: `accounts/tests/test_views.py`

- [ ] **Step 1: Write failing tests for auth views**

Create `accounts/tests/test_views.py`:

```python
from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import PermissionLevel, UserProfile
from core.models import Organization


class LoginViewTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Test", address="Namur")
        self.user = User.objects.create_user(
            username="tresorier", password="testpass123"
        )
        UserProfile.objects.create(
            user=self.user,
            organization=self.org,
            permission_level=PermissionLevel.ADMIN,
        )

    def test_login_page_loads(self):
        response = self.client.get("/accounts/login/")
        self.assertEqual(response.status_code, 200)

    def test_login_success(self):
        response = self.client.post(
            "/accounts/login/",
            {"username": "tresorier", "password": "testpass123"},
        )
        self.assertEqual(response.status_code, 302)

    def test_login_failure(self):
        response = self.client.post(
            "/accounts/login/",
            {"username": "tresorier", "password": "wrong"},
        )
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        self.client.login(username="tresorier", password="testpass123")
        response = self.client.post("/accounts/logout/")
        self.assertEqual(response.status_code, 302)


class UserListViewTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Test", address="Namur")
        self.admin_user = User.objects.create_user(
            username="admin", password="testpass123"
        )
        UserProfile.objects.create(
            user=self.admin_user,
            organization=self.org,
            permission_level=PermissionLevel.ADMIN,
        )
        self.reader_user = User.objects.create_user(
            username="reader", password="testpass123"
        )
        UserProfile.objects.create(
            user=self.reader_user,
            organization=self.org,
            permission_level=PermissionLevel.LECTURE,
        )

    def test_admin_can_see_user_list(self):
        self.client.login(username="admin", password="testpass123")
        response = self.client.get("/accounts/users/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "admin")
        self.assertContains(response, "reader")

    def test_reader_cannot_see_user_list(self):
        self.client.login(username="reader", password="testpass123")
        response = self.client.get("/accounts/users/")
        self.assertEqual(response.status_code, 403)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test accounts.tests.test_views -v 2`
Expected: FAIL

- [ ] **Step 3: Write forms**

Replace `accounts/forms.py`:

```python
from django import forms
from django.contrib.auth.models import User

from accounts.models import PermissionLevel, UserProfile


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")
    permission_level = forms.ChoiceField(
        choices=PermissionLevel.choices, label="Niveau de permission"
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")
        labels = {
            "username": "Nom d'utilisateur",
            "first_name": "Prénom",
            "last_name": "Nom",
            "email": "Email",
        }
```

- [ ] **Step 4: Write views**

Replace `accounts/views.py`:

```python
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.decorators import require_permission
from accounts.models import PermissionLevel, UserProfile


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"


class LogoutView(auth_views.LogoutView):
    pass


@login_required
@require_permission(PermissionLevel.ADMIN)
def user_list(request):
    profiles = UserProfile.objects.select_related("user").all()
    return render(request, "accounts/user_list.html", {"profiles": profiles})
```

- [ ] **Step 5: Write URLs**

Replace `accounts/urls.py`:

```python
from django.urls import path

from accounts import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("users/", views.user_list, name="user_list"),
]
```

- [ ] **Step 6: Create templates**

Create `accounts/templates/accounts/login.html`:

```html
{% extends "base.html" %}
{% load i18n %}

{% block title %}Connexion — OpenASBL{% endblock %}

{% block content %}
<div class="card" style="max-width: 400px; margin: 2rem auto;">
    <h1>{% trans "Connexion" %}</h1>
    <form method="post">
        {% csrf_token %}
        {% for field in form %}
        <div class="form-group">
            <label for="{{ field.id_for_label }}">{{ field.label }}</label>
            {{ field }}
            {% if field.errors %}
            <p class="text-danger">{{ field.errors.0 }}</p>
            {% endif %}
        </div>
        {% endfor %}
        {% if form.non_field_errors %}
        <p class="text-danger">{{ form.non_field_errors.0 }}</p>
        {% endif %}
        <button type="submit" class="btn btn-primary">{% trans "Se connecter" %}</button>
    </form>
</div>
{% endblock %}
```

Create `accounts/templates/accounts/user_list.html`:

```html
{% extends "base.html" %}
{% load i18n %}

{% block title %}Utilisateurs — OpenASBL{% endblock %}

{% block content %}
<h1>{% trans "Utilisateurs" %}</h1>
<table>
    <thead>
        <tr>
            <th>{% trans "Nom d'utilisateur" %}</th>
            <th>{% trans "Nom" %}</th>
            <th>{% trans "Permission" %}</th>
        </tr>
    </thead>
    <tbody>
        {% for profile in profiles %}
        <tr>
            <td>{{ profile.user.username }}</td>
            <td>{{ profile.user.get_full_name }}</td>
            <td>{{ profile.get_permission_level_display }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% endblock %}
```

- [ ] **Step 7: Run tests**

Run: `python manage.py test accounts.tests.test_views -v 2`
Expected: All 6 tests PASS.

- [ ] **Step 8: Commit**

```bash
git add accounts/
git commit -m "feat(accounts): add login/logout and user management views"
```

---

## Task 5: Accounting App — Models (FiscalYear, Category, Entry, Budget, AssetSnapshot)

**Files:**
- Modify: `accounting/models.py`
- Create: `accounting/tests/__init__.py`
- Create: `accounting/tests/test_models.py`
- Modify: `accounting/admin.py`

- [ ] **Step 1: Create tests directory**

Run:
```bash
rm accounting/tests.py
mkdir -p accounting/tests
touch accounting/tests/__init__.py
```

- [ ] **Step 2: Write failing tests**

Create `accounting/tests/test_models.py`:

```python
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from accounting.models import (
    AssetSnapshot,
    Budget,
    Category,
    CategoryType,
    Entry,
    FiscalYear,
    FiscalYearStatus,
)
from core.models import Organization


class FiscalYearModelTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="RCVD", address="Dave")

    def test_create_fiscal_year(self):
        fy = FiscalYear.objects.create(
            organization=self.org,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        self.assertEqual(fy.status, FiscalYearStatus.OPEN)
        self.assertEqual(str(fy), "2026-01-01 → 2026-12-31")

    def test_end_date_after_start_date(self):
        fy = FiscalYear(
            organization=self.org,
            start_date=date(2026, 12, 31),
            end_date=date(2026, 1, 1),
        )
        with self.assertRaises(ValidationError):
            fy.full_clean()

    def test_close_fiscal_year(self):
        fy = FiscalYear.objects.create(
            organization=self.org,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        fy.status = FiscalYearStatus.CLOSED
        fy.save()
        self.assertEqual(fy.status, FiscalYearStatus.CLOSED)


class CategoryModelTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="RCVD", address="Dave")

    def test_create_income_category(self):
        cat = Category.objects.create(
            organization=self.org,
            name="Cotisations membres",
            category_type=CategoryType.INCOME,
        )
        self.assertEqual(str(cat), "Cotisations membres (Recette)")

    def test_create_expense_category(self):
        cat = Category.objects.create(
            organization=self.org,
            name="Entretien péniche",
            category_type=CategoryType.EXPENSE,
        )
        self.assertEqual(str(cat), "Entretien péniche (Dépense)")


class EntryModelTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="RCVD", address="Dave")
        self.fy = FiscalYear.objects.create(
            organization=self.org,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        self.category = Category.objects.create(
            organization=self.org,
            name="Cotisations",
            category_type=CategoryType.INCOME,
        )
        self.user = User.objects.create_user(username="tresorier", password="test123")

    def test_create_entry(self):
        entry = Entry.objects.create(
            fiscal_year=self.fy,
            category=self.category,
            date=date(2026, 3, 15),
            amount=Decimal("50.00"),
            description="Cotisation annuelle — Jean Dupont",
            created_by=self.user,
        )
        self.assertEqual(entry.amount, Decimal("50.00"))
        self.assertEqual(entry.entry_type, CategoryType.INCOME)

    def test_entry_date_within_fiscal_year(self):
        entry = Entry(
            fiscal_year=self.fy,
            category=self.category,
            date=date(2025, 6, 15),
            amount=Decimal("50.00"),
            description="Hors exercice",
            created_by=self.user,
        )
        with self.assertRaises(ValidationError):
            entry.full_clean()

    def test_entry_on_closed_fiscal_year(self):
        self.fy.status = FiscalYearStatus.CLOSED
        self.fy.save()
        entry = Entry(
            fiscal_year=self.fy,
            category=self.category,
            date=date(2026, 3, 15),
            amount=Decimal("50.00"),
            description="Test",
            created_by=self.user,
        )
        with self.assertRaises(ValidationError):
            entry.full_clean()

    def test_amount_must_be_positive(self):
        entry = Entry(
            fiscal_year=self.fy,
            category=self.category,
            date=date(2026, 3, 15),
            amount=Decimal("-10.00"),
            description="Négatif",
            created_by=self.user,
        )
        with self.assertRaises(ValidationError):
            entry.full_clean()


class BudgetModelTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="RCVD", address="Dave")
        self.fy = FiscalYear.objects.create(
            organization=self.org,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        self.category = Category.objects.create(
            organization=self.org,
            name="Cotisations",
            category_type=CategoryType.INCOME,
        )

    def test_create_budget(self):
        budget = Budget.objects.create(
            fiscal_year=self.fy,
            category=self.category,
            planned_amount=Decimal("5000.00"),
        )
        self.assertEqual(budget.planned_amount, Decimal("5000.00"))

    def test_unique_budget_per_category_per_year(self):
        Budget.objects.create(
            fiscal_year=self.fy,
            category=self.category,
            planned_amount=Decimal("5000.00"),
        )
        with self.assertRaises(Exception):
            Budget.objects.create(
                fiscal_year=self.fy,
                category=self.category,
                planned_amount=Decimal("6000.00"),
            )


class AssetSnapshotModelTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="RCVD", address="Dave")
        self.fy = FiscalYear.objects.create(
            organization=self.org,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )

    def test_create_snapshot(self):
        snapshot = AssetSnapshot.objects.create(
            fiscal_year=self.fy,
            date=date(2026, 12, 31),
            cash=Decimal("1200.00"),
            bank=Decimal("15000.00"),
            receivables=Decimal("500.00"),
            debts=Decimal("300.00"),
        )
        self.assertEqual(snapshot.net_worth, Decimal("16400.00"))

    def test_net_worth_calculation(self):
        snapshot = AssetSnapshot(
            cash=Decimal("100.00"),
            bank=Decimal("200.00"),
            receivables=Decimal("50.00"),
            debts=Decimal("150.00"),
        )
        self.assertEqual(snapshot.net_worth, Decimal("200.00"))
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python manage.py test accounting.tests.test_models -v 2`
Expected: FAIL — `ImportError`

- [ ] **Step 4: Write the models**

Replace `accounting/models.py`:

```python
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from decimal import Decimal


class FiscalYearStatus(models.TextChoices):
    OPEN = "open", "Ouvert"
    CLOSED = "closed", "Clôturé"


class CategoryType(models.TextChoices):
    INCOME = "income", "Recette"
    EXPENSE = "expense", "Dépense"


class FiscalYear(models.Model):
    organization = models.ForeignKey(
        "core.Organization", on_delete=models.CASCADE, related_name="fiscal_years"
    )
    start_date = models.DateField("Date de début")
    end_date = models.DateField("Date de fin")
    status = models.CharField(
        "Statut",
        max_length=10,
        choices=FiscalYearStatus.choices,
        default=FiscalYearStatus.OPEN,
    )

    class Meta:
        verbose_name = "Exercice comptable"
        verbose_name_plural = "Exercices comptables"
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.start_date} → {self.end_date}"

    def clean(self):
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValidationError("La date de fin doit être postérieure à la date de début.")


class Category(models.Model):
    organization = models.ForeignKey(
        "core.Organization", on_delete=models.CASCADE, related_name="categories"
    )
    name = models.CharField("Nom", max_length=255)
    category_type = models.CharField(
        "Type", max_length=10, choices=CategoryType.choices
    )
    description = models.TextField("Description", blank=True, default="")

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ["category_type", "name"]
        unique_together = [("organization", "name")]

    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"


class Entry(models.Model):
    fiscal_year = models.ForeignKey(
        FiscalYear, on_delete=models.CASCADE, related_name="entries"
    )
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="entries"
    )
    date = models.DateField("Date")
    amount = models.DecimalField(
        "Montant",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    description = models.CharField("Description", max_length=500)
    attachment = models.FileField(
        "Justificatif", upload_to="attachments/%Y/%m/", blank=True
    )
    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="entries"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Écriture"
        verbose_name_plural = "Écritures"
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.date} — {self.description} ({self.amount}€)"

    @property
    def entry_type(self):
        return self.category.category_type

    def clean(self):
        if self.fiscal_year_id and self.fiscal_year.status == FiscalYearStatus.CLOSED:
            raise ValidationError("Impossible d'ajouter une écriture sur un exercice clôturé.")
        if (
            self.fiscal_year_id
            and self.date
            and not (self.fiscal_year.start_date <= self.date <= self.fiscal_year.end_date)
        ):
            raise ValidationError(
                "La date de l'écriture doit être comprise dans l'exercice comptable."
            )


class Budget(models.Model):
    fiscal_year = models.ForeignKey(
        FiscalYear, on_delete=models.CASCADE, related_name="budgets"
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="budgets"
    )
    planned_amount = models.DecimalField(
        "Montant prévu", max_digits=12, decimal_places=2
    )

    class Meta:
        verbose_name = "Budget"
        verbose_name_plural = "Budgets"
        unique_together = [("fiscal_year", "category")]

    def __str__(self):
        return f"Budget {self.category.name} — {self.planned_amount}€"


class AssetSnapshot(models.Model):
    fiscal_year = models.ForeignKey(
        FiscalYear, on_delete=models.CASCADE, related_name="asset_snapshots"
    )
    date = models.DateField("Date du relevé")
    cash = models.DecimalField("Caisse", max_digits=12, decimal_places=2, default=Decimal("0"))
    bank = models.DecimalField("Banque", max_digits=12, decimal_places=2, default=Decimal("0"))
    receivables = models.DecimalField("Créances", max_digits=12, decimal_places=2, default=Decimal("0"))
    debts = models.DecimalField("Dettes", max_digits=12, decimal_places=2, default=Decimal("0"))
    notes = models.TextField("Notes", blank=True, default="")

    class Meta:
        verbose_name = "État du patrimoine"
        verbose_name_plural = "États du patrimoine"
        ordering = ["-date"]

    def __str__(self):
        return f"Patrimoine au {self.date}"

    @property
    def net_worth(self):
        return self.cash + self.bank + self.receivables - self.debts
```

- [ ] **Step 5: Register in admin**

Replace `accounting/admin.py`:

```python
from django.contrib import admin

from accounting.models import (
    AssetSnapshot,
    Budget,
    Category,
    Entry,
    FiscalYear,
)


@admin.register(FiscalYear)
class FiscalYearAdmin(admin.ModelAdmin):
    list_display = ("__str__", "status", "organization")
    list_filter = ("status",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "category_type", "organization")
    list_filter = ("category_type",)


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ("date", "description", "amount", "category", "created_by")
    list_filter = ("category__category_type", "fiscal_year")
    date_hierarchy = "date"


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ("category", "planned_amount", "fiscal_year")


@admin.register(AssetSnapshot)
class AssetSnapshotAdmin(admin.ModelAdmin):
    list_display = ("date", "cash", "bank", "receivables", "debts", "net_worth")
```

- [ ] **Step 6: Migrate and run tests**

Run:
```bash
python manage.py makemigrations accounting
python manage.py migrate
python manage.py test accounting.tests.test_models -v 2
```

Expected: All 12 tests PASS.

- [ ] **Step 7: Commit**

```bash
git add accounting/
git commit -m "feat(accounting): add FiscalYear, Category, Entry, Budget, AssetSnapshot models"
```

---

## Task 6: Accounting App — Default Categories Seed

**Files:**
- Create: `accounting/seed.py`
- Create: `accounting/management/__init__.py`
- Create: `accounting/management/commands/__init__.py`
- Create: `accounting/management/commands/seed_categories.py`
- Create: `accounting/tests/test_seed.py`

- [ ] **Step 1: Write failing test**

Create `accounting/tests/test_seed.py`:

```python
from django.test import TestCase

from accounting.models import Category, CategoryType
from accounting.seed import DEFAULT_CATEGORIES, seed_categories
from core.models import Organization


class SeedCategoriesTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="RCVD", address="Dave")

    def test_seed_creates_categories(self):
        seed_categories(self.org)
        self.assertEqual(
            Category.objects.filter(organization=self.org).count(),
            len(DEFAULT_CATEGORIES),
        )

    def test_seed_is_idempotent(self):
        seed_categories(self.org)
        seed_categories(self.org)
        self.assertEqual(
            Category.objects.filter(organization=self.org).count(),
            len(DEFAULT_CATEGORIES),
        )

    def test_seed_has_income_and_expense(self):
        seed_categories(self.org)
        income = Category.objects.filter(
            organization=self.org, category_type=CategoryType.INCOME
        ).count()
        expense = Category.objects.filter(
            organization=self.org, category_type=CategoryType.EXPENSE
        ).count()
        self.assertGreater(income, 0)
        self.assertGreater(expense, 0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test accounting.tests.test_seed -v 2`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Write seed module**

Create `accounting/seed.py`:

```python
from accounting.models import Category, CategoryType


DEFAULT_CATEGORIES = [
    (CategoryType.INCOME, "Cotisations membres"),
    (CategoryType.INCOME, "Subsides communaux/régionaux"),
    (CategoryType.INCOME, "Stages voile"),
    (CategoryType.INCOME, "Régates (inscriptions)"),
    (CategoryType.INCOME, "Buvette/bar"),
    (CategoryType.INCOME, "Événements"),
    (CategoryType.INCOME, "Dons"),
    (CategoryType.INCOME, "Divers recettes"),
    (CategoryType.EXPENSE, "Entretien bateaux"),
    (CategoryType.EXPENSE, "Entretien péniche/clubhouse"),
    (CategoryType.EXPENSE, "Assurances"),
    (CategoryType.EXPENSE, "Loyer"),
    (CategoryType.EXPENSE, "Charges (eau/électricité)"),
    (CategoryType.EXPENSE, "Matériel nautique"),
    (CategoryType.EXPENSE, "Frais administratifs"),
    (CategoryType.EXPENSE, "Événements"),
    (CategoryType.EXPENSE, "Formation moniteurs"),
    (CategoryType.EXPENSE, "Divers dépenses"),
]


def seed_categories(organization):
    for category_type, name in DEFAULT_CATEGORIES:
        Category.objects.get_or_create(
            organization=organization,
            name=name,
            defaults={"category_type": category_type},
        )
```

- [ ] **Step 4: Create management command**

Run:
```bash
mkdir -p accounting/management/commands
touch accounting/management/__init__.py
touch accounting/management/commands/__init__.py
```

Create `accounting/management/commands/seed_categories.py`:

```python
from django.core.management.base import BaseCommand

from accounting.seed import seed_categories
from core.models import Organization


class Command(BaseCommand):
    help = "Seed default accounting categories for the organization"

    def handle(self, *args, **options):
        try:
            org = Organization.objects.get()
        except Organization.DoesNotExist:
            self.stderr.write("Aucune organisation configurée. Créez-en une d'abord.")
            return
        seed_categories(org)
        self.stdout.write(self.style.SUCCESS("Catégories par défaut créées."))
```

- [ ] **Step 5: Run tests**

Run: `python manage.py test accounting.tests.test_seed -v 2`
Expected: All 3 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add accounting/seed.py accounting/management/ accounting/tests/test_seed.py
git commit -m "feat(accounting): add default categories seed for sports clubs"
```

---

## Task 7: Accounting App — Entry CRUD Views

**Files:**
- Modify: `accounting/forms.py`
- Modify: `accounting/views.py`
- Modify: `accounting/urls.py`
- Create: `accounting/templates/accounting/dashboard.html`
- Create: `accounting/templates/accounting/entry_list.html`
- Create: `accounting/templates/accounting/entry_form.html`
- Create: `accounting/tests/test_views.py`

- [ ] **Step 1: Write failing tests**

Create `accounting/tests/test_views.py`:

```python
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import PermissionLevel, UserProfile
from accounting.models import Category, CategoryType, Entry, FiscalYear
from core.models import Organization


class DashboardViewTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="RCVD", address="Dave")
        self.user = User.objects.create_user(username="tresorier", password="test123")
        UserProfile.objects.create(
            user=self.user,
            organization=self.org,
            permission_level=PermissionLevel.ADMIN,
        )
        self.client.login(username="tresorier", password="test123")

    def test_dashboard_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_dashboard_requires_login(self):
        self.client.logout()
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)


class EntryListViewTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="RCVD", address="Dave")
        self.user = User.objects.create_user(username="tresorier", password="test123")
        UserProfile.objects.create(
            user=self.user,
            organization=self.org,
            permission_level=PermissionLevel.ADMIN,
        )
        self.fy = FiscalYear.objects.create(
            organization=self.org,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        self.client.login(username="tresorier", password="test123")

    def test_entry_list_loads(self):
        response = self.client.get(f"/entries/?fiscal_year={self.fy.pk}")
        self.assertEqual(response.status_code, 200)


class EntryCreateViewTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="RCVD", address="Dave")
        self.user = User.objects.create_user(username="tresorier", password="test123")
        UserProfile.objects.create(
            user=self.user,
            organization=self.org,
            permission_level=PermissionLevel.GESTION,
        )
        self.fy = FiscalYear.objects.create(
            organization=self.org,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        self.category = Category.objects.create(
            organization=self.org,
            name="Cotisations",
            category_type=CategoryType.INCOME,
        )
        self.client.login(username="tresorier", password="test123")

    def test_create_entry(self):
        response = self.client.post(
            "/entries/create/",
            {
                "fiscal_year": self.fy.pk,
                "category": self.category.pk,
                "date": "2026-03-15",
                "amount": "50.00",
                "description": "Cotisation Jean Dupont",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Entry.objects.count(), 1)
        entry = Entry.objects.first()
        self.assertEqual(entry.amount, Decimal("50.00"))
        self.assertEqual(entry.created_by, self.user)

    def test_reader_cannot_create_entry(self):
        self.user.profile.permission_level = PermissionLevel.LECTURE
        self.user.profile.save()
        response = self.client.post(
            "/entries/create/",
            {
                "fiscal_year": self.fy.pk,
                "category": self.category.pk,
                "date": "2026-03-15",
                "amount": "50.00",
                "description": "Test",
            },
        )
        self.assertEqual(response.status_code, 403)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test accounting.tests.test_views -v 2`
Expected: FAIL

- [ ] **Step 3: Write forms**

Replace `accounting/forms.py`:

```python
from django import forms

from accounting.models import AssetSnapshot, Budget, Category, Entry, FiscalYear


class EntryForm(forms.ModelForm):
    class Meta:
        model = Entry
        fields = ("fiscal_year", "category", "date", "amount", "description", "attachment")
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "amount": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "category_type", "description")


class FiscalYearForm(forms.ModelForm):
    class Meta:
        model = FiscalYear
        fields = ("start_date", "end_date")
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ("category", "planned_amount")
        widgets = {
            "planned_amount": forms.NumberInput(attrs={"step": "0.01"}),
        }


class AssetSnapshotForm(forms.ModelForm):
    class Meta:
        model = AssetSnapshot
        fields = ("date", "cash", "bank", "receivables", "debts", "notes")
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "cash": forms.NumberInput(attrs={"step": "0.01"}),
            "bank": forms.NumberInput(attrs={"step": "0.01"}),
            "receivables": forms.NumberInput(attrs={"step": "0.01"}),
            "debts": forms.NumberInput(attrs={"step": "0.01"}),
        }
```

- [ ] **Step 4: Write views**

Replace `accounting/views.py`:

```python
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import require_permission
from accounts.models import PermissionLevel
from accounting.forms import EntryForm
from accounting.models import CategoryType, Entry, FiscalYear


@login_required
def dashboard(request):
    org = request.user.profile.organization
    fiscal_years = FiscalYear.objects.filter(organization=org)
    current_fy = fiscal_years.filter(status="open").first()

    summary = {}
    if current_fy:
        income = (
            Entry.objects.filter(
                fiscal_year=current_fy, category__category_type=CategoryType.INCOME
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )
        expenses = (
            Entry.objects.filter(
                fiscal_year=current_fy, category__category_type=CategoryType.EXPENSE
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )
        summary = {
            "income": income,
            "expenses": expenses,
            "balance": income - expenses,
            "entry_count": Entry.objects.filter(fiscal_year=current_fy).count(),
        }

    return render(
        request,
        "accounting/dashboard.html",
        {
            "fiscal_years": fiscal_years,
            "current_fy": current_fy,
            "summary": summary,
        },
    )


@login_required
def entry_list(request):
    org = request.user.profile.organization
    fiscal_year_id = request.GET.get("fiscal_year")
    entries = Entry.objects.select_related("category", "created_by")

    if fiscal_year_id:
        entries = entries.filter(fiscal_year_id=fiscal_year_id)
    else:
        entries = entries.filter(fiscal_year__organization=org)

    fiscal_years = FiscalYear.objects.filter(organization=org)
    return render(
        request,
        "accounting/entry_list.html",
        {
            "entries": entries,
            "fiscal_years": fiscal_years,
            "selected_fy": fiscal_year_id,
        },
    )


@login_required
@require_permission(PermissionLevel.GESTION)
def entry_create(request):
    org = request.user.profile.organization
    if request.method == "POST":
        form = EntryForm(request.POST, request.FILES)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.created_by = request.user
            entry.full_clean()
            entry.save()
            messages.success(request, "Écriture enregistrée.")
            return redirect("accounting:entry_list")
    else:
        form = EntryForm()
    form.fields["fiscal_year"].queryset = FiscalYear.objects.filter(
        organization=org, status="open"
    )
    form.fields["category"].queryset = org.categories.all()
    return render(request, "accounting/entry_form.html", {"form": form, "title": "Nouvelle écriture"})


@login_required
@require_permission(PermissionLevel.GESTION)
def entry_edit(request, pk):
    entry = get_object_or_404(Entry, pk=pk)
    org = request.user.profile.organization
    if request.method == "POST":
        form = EntryForm(request.POST, request.FILES, instance=entry)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.full_clean()
            entry.save()
            messages.success(request, "Écriture modifiée.")
            return redirect("accounting:entry_list")
    else:
        form = EntryForm(instance=entry)
    form.fields["fiscal_year"].queryset = FiscalYear.objects.filter(
        organization=org, status="open"
    )
    form.fields["category"].queryset = org.categories.all()
    return render(request, "accounting/entry_form.html", {"form": form, "title": "Modifier l'écriture"})


@login_required
@require_permission(PermissionLevel.GESTION)
def entry_delete(request, pk):
    entry = get_object_or_404(Entry, pk=pk)
    if request.method == "POST":
        entry.delete()
        messages.success(request, "Écriture supprimée.")
    return redirect("accounting:entry_list")
```

- [ ] **Step 5: Write URLs**

Replace `accounting/urls.py`:

```python
from django.urls import path

from accounting import views

app_name = "accounting"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("entries/", views.entry_list, name="entry_list"),
    path("entries/create/", views.entry_create, name="entry_create"),
    path("entries/<int:pk>/edit/", views.entry_edit, name="entry_edit"),
    path("entries/<int:pk>/delete/", views.entry_delete, name="entry_delete"),
]
```

- [ ] **Step 6: Create templates**

Create `accounting/templates/accounting/dashboard.html`:

```html
{% extends "base.html" %}
{% load i18n %}

{% block title %}Tableau de bord — OpenASBL{% endblock %}

{% block content %}
<h1>{% trans "Tableau de bord" %}</h1>

{% if current_fy %}
<div class="card">
    <h2>Exercice en cours : {{ current_fy }}</h2>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--space);">
        <div class="card">
            <p class="text-muted">Recettes</p>
            <p class="amount-positive">{{ summary.income }} €</p>
        </div>
        <div class="card">
            <p class="text-muted">Dépenses</p>
            <p class="amount-negative">{{ summary.expenses }} €</p>
        </div>
        <div class="card">
            <p class="text-muted">Solde</p>
            <p class="{% if summary.balance >= 0 %}amount-positive{% else %}amount-negative{% endif %}">
                {{ summary.balance }} €
            </p>
        </div>
        <div class="card">
            <p class="text-muted">Écritures</p>
            <p>{{ summary.entry_count }}</p>
        </div>
    </div>
</div>

<div style="margin-top: var(--space);">
    <a href="{% url 'accounting:entry_create' %}" class="btn btn-primary">Nouvelle écriture</a>
    <a href="{% url 'accounting:entry_list' %}?fiscal_year={{ current_fy.pk }}" class="btn btn-primary">Voir les écritures</a>
</div>
{% else %}
<div class="card">
    <p>Aucun exercice comptable ouvert. Créez-en un pour commencer.</p>
</div>
{% endif %}
{% endblock %}
```

Create `accounting/templates/accounting/entry_list.html`:

```html
{% extends "base.html" %}
{% load i18n %}

{% block title %}Écritures — OpenASBL{% endblock %}

{% block content %}
<h1>{% trans "Écritures" %}</h1>

<div style="margin-bottom: var(--space);">
    <form method="get" style="display: inline-flex; gap: 0.5rem; align-items: center;">
        <select name="fiscal_year" onchange="this.form.submit()">
            <option value="">Tous les exercices</option>
            {% for fy in fiscal_years %}
            <option value="{{ fy.pk }}" {% if selected_fy == fy.pk|stringformat:"d" %}selected{% endif %}>
                {{ fy }}
            </option>
            {% endfor %}
        </select>
    </form>
    <a href="{% url 'accounting:entry_create' %}" class="btn btn-primary">Nouvelle écriture</a>
</div>

<table>
    <thead>
        <tr>
            <th>{% trans "Date" %}</th>
            <th>{% trans "Description" %}</th>
            <th>{% trans "Catégorie" %}</th>
            <th>{% trans "Montant" %}</th>
            <th>{% trans "Actions" %}</th>
        </tr>
    </thead>
    <tbody>
        {% for entry in entries %}
        <tr>
            <td>{{ entry.date }}</td>
            <td>{{ entry.description }}</td>
            <td>{{ entry.category.name }}</td>
            <td class="{% if entry.entry_type == 'income' %}amount-positive{% else %}amount-negative{% endif %}">
                {% if entry.entry_type == 'expense' %}-{% endif %}{{ entry.amount }} €
            </td>
            <td>
                <a href="{% url 'accounting:entry_edit' entry.pk %}">Modifier</a>
                <form method="post" action="{% url 'accounting:entry_delete' entry.pk %}" style="display:inline;">
                    {% csrf_token %}
                    <button type="submit" class="btn btn-danger" onclick="return confirm('Supprimer cette écriture ?')">Supprimer</button>
                </form>
            </td>
        </tr>
        {% empty %}
        <tr><td colspan="5" class="text-muted">Aucune écriture.</td></tr>
        {% endfor %}
    </tbody>
</table>
{% endblock %}
```

Create `accounting/templates/accounting/entry_form.html`:

```html
{% extends "base.html" %}
{% load i18n %}

{% block title %}{{ title }} — OpenASBL{% endblock %}

{% block content %}
<div class="card" style="max-width: 600px;">
    <h1>{{ title }}</h1>
    <form method="post" enctype="multipart/form-data">
        {% csrf_token %}
        {% for field in form %}
        <div class="form-group">
            <label for="{{ field.id_for_label }}">{{ field.label }}</label>
            {{ field }}
            {% if field.errors %}
            <p class="text-danger">{{ field.errors.0 }}</p>
            {% endif %}
        </div>
        {% endfor %}
        <button type="submit" class="btn btn-success">Enregistrer</button>
        <a href="{% url 'accounting:entry_list' %}" class="btn">Annuler</a>
    </form>
</div>
{% endblock %}
```

- [ ] **Step 7: Run tests**

Run: `python manage.py test accounting.tests.test_views -v 2`
Expected: All 5 tests PASS.

- [ ] **Step 8: Commit**

```bash
git add accounting/
git commit -m "feat(accounting): add entry CRUD views with dashboard"
```

---

## Task 8: Accounting App — FiscalYear, Category, Budget, AssetSnapshot Views

**Files:**
- Modify: `accounting/views.py`
- Modify: `accounting/urls.py`
- Create: `accounting/templates/accounting/fiscal_year_list.html`
- Create: `accounting/templates/accounting/fiscal_year_close.html`
- Create: `accounting/templates/accounting/category_list.html`
- Create: `accounting/templates/accounting/budget_form.html`
- Create: `accounting/templates/accounting/asset_snapshot_form.html`

- [ ] **Step 1: Write failing tests**

Add to `accounting/tests/test_views.py`:

```python
from accounting.models import Budget, AssetSnapshot, FiscalYearStatus


class FiscalYearViewTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="RCVD", address="Dave")
        self.user = User.objects.create_user(username="admin", password="test123")
        UserProfile.objects.create(
            user=self.user,
            organization=self.org,
            permission_level=PermissionLevel.ADMIN,
        )
        self.client.login(username="admin", password="test123")

    def test_fiscal_year_list(self):
        FiscalYear.objects.create(
            organization=self.org,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        response = self.client.get("/fiscal-years/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2026")

    def test_create_fiscal_year(self):
        response = self.client.post(
            "/fiscal-years/create/",
            {"start_date": "2026-01-01", "end_date": "2026-12-31"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(FiscalYear.objects.count(), 1)

    def test_close_fiscal_year(self):
        fy = FiscalYear.objects.create(
            organization=self.org,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        response = self.client.post(f"/fiscal-years/{fy.pk}/close/")
        self.assertEqual(response.status_code, 302)
        fy.refresh_from_db()
        self.assertEqual(fy.status, FiscalYearStatus.CLOSED)

    def test_gestion_cannot_close_fiscal_year(self):
        self.user.profile.permission_level = PermissionLevel.GESTION
        self.user.profile.save()
        fy = FiscalYear.objects.create(
            organization=self.org,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        response = self.client.post(f"/fiscal-years/{fy.pk}/close/")
        self.assertEqual(response.status_code, 403)


class CategoryViewTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="RCVD", address="Dave")
        self.user = User.objects.create_user(username="admin", password="test123")
        UserProfile.objects.create(
            user=self.user,
            organization=self.org,
            permission_level=PermissionLevel.GESTION,
        )
        self.client.login(username="admin", password="test123")

    def test_category_list(self):
        response = self.client.get("/categories/")
        self.assertEqual(response.status_code, 200)

    def test_create_category(self):
        response = self.client.post(
            "/categories/create/",
            {"name": "Test", "category_type": "income", "description": ""},
        )
        self.assertEqual(response.status_code, 302)


class BudgetViewTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="RCVD", address="Dave")
        self.user = User.objects.create_user(username="admin", password="test123")
        UserProfile.objects.create(
            user=self.user,
            organization=self.org,
            permission_level=PermissionLevel.GESTION,
        )
        self.fy = FiscalYear.objects.create(
            organization=self.org,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        self.category = Category.objects.create(
            organization=self.org,
            name="Cotisations",
            category_type=CategoryType.INCOME,
        )
        self.client.login(username="admin", password="test123")

    def test_create_budget(self):
        response = self.client.post(
            f"/fiscal-years/{self.fy.pk}/budget/create/",
            {"category": self.category.pk, "planned_amount": "5000.00"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Budget.objects.count(), 1)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test accounting.tests.test_views -v 2`
Expected: FAIL on new tests

- [ ] **Step 3: Add views to accounting/views.py**

Append to `accounting/views.py`:

```python
from accounting.forms import (
    AssetSnapshotForm,
    BudgetForm,
    CategoryForm,
    FiscalYearForm,
)
from accounting.models import AssetSnapshot, Budget, Category, FiscalYear, FiscalYearStatus


@login_required
def fiscal_year_list(request):
    org = request.user.profile.organization
    fiscal_years = FiscalYear.objects.filter(organization=org)
    return render(request, "accounting/fiscal_year_list.html", {"fiscal_years": fiscal_years})


@login_required
@require_permission(PermissionLevel.GESTION)
def fiscal_year_create(request):
    org = request.user.profile.organization
    if request.method == "POST":
        form = FiscalYearForm(request.POST)
        if form.is_valid():
            fy = form.save(commit=False)
            fy.organization = org
            fy.full_clean()
            fy.save()
            messages.success(request, "Exercice comptable créé.")
            return redirect("accounting:fiscal_year_list")
    else:
        form = FiscalYearForm()
    return render(request, "accounting/entry_form.html", {"form": form, "title": "Nouvel exercice"})


@login_required
@require_permission(PermissionLevel.VALIDATION)
def fiscal_year_close(request, pk):
    fy = get_object_or_404(FiscalYear, pk=pk)
    if request.method == "POST":
        fy.status = FiscalYearStatus.CLOSED
        fy.save()
        messages.success(request, f"Exercice {fy} clôturé.")
        return redirect("accounting:fiscal_year_list")
    return render(request, "accounting/fiscal_year_close.html", {"fiscal_year": fy})


@login_required
def category_list(request):
    org = request.user.profile.organization
    categories = Category.objects.filter(organization=org)
    return render(request, "accounting/category_list.html", {"categories": categories})


@login_required
@require_permission(PermissionLevel.GESTION)
def category_create(request):
    org = request.user.profile.organization
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            cat = form.save(commit=False)
            cat.organization = org
            cat.save()
            messages.success(request, "Catégorie créée.")
            return redirect("accounting:category_list")
    else:
        form = CategoryForm()
    return render(request, "accounting/entry_form.html", {"form": form, "title": "Nouvelle catégorie"})


@login_required
@require_permission(PermissionLevel.GESTION)
def budget_create(request, fiscal_year_pk):
    fy = get_object_or_404(FiscalYear, pk=fiscal_year_pk)
    org = request.user.profile.organization
    if request.method == "POST":
        form = BudgetForm(request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.fiscal_year = fy
            budget.save()
            messages.success(request, "Budget enregistré.")
            return redirect("accounting:fiscal_year_list")
    else:
        form = BudgetForm()
    form.fields["category"].queryset = org.categories.all()
    return render(request, "accounting/budget_form.html", {"form": form, "fiscal_year": fy})


@login_required
@require_permission(PermissionLevel.VALIDATION)
def asset_snapshot_create(request, fiscal_year_pk):
    fy = get_object_or_404(FiscalYear, pk=fiscal_year_pk)
    if request.method == "POST":
        form = AssetSnapshotForm(request.POST)
        if form.is_valid():
            snapshot = form.save(commit=False)
            snapshot.fiscal_year = fy
            snapshot.save()
            messages.success(request, "État du patrimoine enregistré.")
            return redirect("accounting:fiscal_year_list")
    else:
        form = AssetSnapshotForm()
    return render(request, "accounting/asset_snapshot_form.html", {"form": form, "fiscal_year": fy})
```

- [ ] **Step 4: Update URLs**

Replace `accounting/urls.py`:

```python
from django.urls import path

from accounting import views

app_name = "accounting"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("entries/", views.entry_list, name="entry_list"),
    path("entries/create/", views.entry_create, name="entry_create"),
    path("entries/<int:pk>/edit/", views.entry_edit, name="entry_edit"),
    path("entries/<int:pk>/delete/", views.entry_delete, name="entry_delete"),
    path("fiscal-years/", views.fiscal_year_list, name="fiscal_year_list"),
    path("fiscal-years/create/", views.fiscal_year_create, name="fiscal_year_create"),
    path("fiscal-years/<int:pk>/close/", views.fiscal_year_close, name="fiscal_year_close"),
    path("fiscal-years/<int:fiscal_year_pk>/budget/create/", views.budget_create, name="budget_create"),
    path("fiscal-years/<int:fiscal_year_pk>/asset-snapshot/create/", views.asset_snapshot_create, name="asset_snapshot_create"),
    path("categories/", views.category_list, name="category_list"),
    path("categories/create/", views.category_create, name="category_create"),
]
```

- [ ] **Step 5: Create templates**

Create `accounting/templates/accounting/fiscal_year_list.html`:

```html
{% extends "base.html" %}
{% load i18n %}

{% block title %}Exercices comptables — OpenASBL{% endblock %}

{% block content %}
<h1>{% trans "Exercices comptables" %}</h1>
<a href="{% url 'accounting:fiscal_year_create' %}" class="btn btn-primary">Nouvel exercice</a>

<table style="margin-top: var(--space);">
    <thead>
        <tr>
            <th>{% trans "Période" %}</th>
            <th>{% trans "Statut" %}</th>
            <th>{% trans "Actions" %}</th>
        </tr>
    </thead>
    <tbody>
        {% for fy in fiscal_years %}
        <tr>
            <td>{{ fy }}</td>
            <td>{{ fy.get_status_display }}</td>
            <td>
                {% if fy.status == "open" %}
                <a href="{% url 'accounting:budget_create' fy.pk %}">Budget</a>
                <a href="{% url 'accounting:asset_snapshot_create' fy.pk %}">Patrimoine</a>
                <a href="{% url 'accounting:fiscal_year_close' fy.pk %}" class="btn btn-danger">Clôturer</a>
                {% endif %}
                <a href="{% url 'accounting:entry_list' %}?fiscal_year={{ fy.pk }}">Écritures</a>
            </td>
        </tr>
        {% empty %}
        <tr><td colspan="3" class="text-muted">Aucun exercice.</td></tr>
        {% endfor %}
    </tbody>
</table>
{% endblock %}
```

Create `accounting/templates/accounting/fiscal_year_close.html`:

```html
{% extends "base.html" %}
{% load i18n %}

{% block title %}Clôturer l'exercice — OpenASBL{% endblock %}

{% block content %}
<div class="card" style="max-width: 500px;">
    <h1>{% trans "Clôturer l'exercice" %}</h1>
    <p>Êtes-vous sûr de vouloir clôturer l'exercice <strong>{{ fiscal_year }}</strong> ?</p>
    <p class="text-danger">Cette action est irréversible. Aucune écriture ne pourra être ajoutée après la clôture.</p>
    <form method="post">
        {% csrf_token %}
        <button type="submit" class="btn btn-danger">Confirmer la clôture</button>
        <a href="{% url 'accounting:fiscal_year_list' %}" class="btn">Annuler</a>
    </form>
</div>
{% endblock %}
```

Create `accounting/templates/accounting/category_list.html`:

```html
{% extends "base.html" %}
{% load i18n %}

{% block title %}Catégories — OpenASBL{% endblock %}

{% block content %}
<h1>{% trans "Catégories" %}</h1>
<a href="{% url 'accounting:category_create' %}" class="btn btn-primary">Nouvelle catégorie</a>

<h2 style="margin-top: var(--space);">Recettes</h2>
<table>
    <tbody>
        {% for cat in categories %}
        {% if cat.category_type == "income" %}
        <tr><td>{{ cat.name }}</td><td class="text-muted">{{ cat.description }}</td></tr>
        {% endif %}
        {% endfor %}
    </tbody>
</table>

<h2 style="margin-top: var(--space);">Dépenses</h2>
<table>
    <tbody>
        {% for cat in categories %}
        {% if cat.category_type == "expense" %}
        <tr><td>{{ cat.name }}</td><td class="text-muted">{{ cat.description }}</td></tr>
        {% endif %}
        {% endfor %}
    </tbody>
</table>
{% endblock %}
```

Create `accounting/templates/accounting/budget_form.html`:

```html
{% extends "base.html" %}
{% load i18n %}

{% block title %}Budget — OpenASBL{% endblock %}

{% block content %}
<div class="card" style="max-width: 500px;">
    <h1>Budget — {{ fiscal_year }}</h1>
    <form method="post">
        {% csrf_token %}
        {% for field in form %}
        <div class="form-group">
            <label for="{{ field.id_for_label }}">{{ field.label }}</label>
            {{ field }}
            {% if field.errors %}<p class="text-danger">{{ field.errors.0 }}</p>{% endif %}
        </div>
        {% endfor %}
        <button type="submit" class="btn btn-success">Enregistrer</button>
    </form>
</div>
{% endblock %}
```

Create `accounting/templates/accounting/asset_snapshot_form.html`:

```html
{% extends "base.html" %}
{% load i18n %}

{% block title %}État du patrimoine — OpenASBL{% endblock %}

{% block content %}
<div class="card" style="max-width: 500px;">
    <h1>État du patrimoine — {{ fiscal_year }}</h1>
    <form method="post">
        {% csrf_token %}
        {% for field in form %}
        <div class="form-group">
            <label for="{{ field.id_for_label }}">{{ field.label }}</label>
            {{ field }}
            {% if field.errors %}<p class="text-danger">{{ field.errors.0 }}</p>{% endif %}
        </div>
        {% endfor %}
        <button type="submit" class="btn btn-success">Enregistrer</button>
    </form>
</div>
{% endblock %}
```

- [ ] **Step 6: Run all tests**

Run: `python manage.py test accounting.tests.test_views -v 2`
Expected: All tests PASS.

- [ ] **Step 7: Commit**

```bash
git add accounting/
git commit -m "feat(accounting): add fiscal year, category, budget and asset snapshot views"
```

---

## Task 9: Reports App — PDF Generation

**Files:**
- Create: `reports/generators/__init__.py`
- Create: `reports/generators/pdf.py`
- Create: `reports/tests/__init__.py`
- Create: `reports/tests/test_pdf.py`
- Create: `reports/templates/reports/journal_pdf.html`
- Create: `reports/templates/reports/patrimony_pdf.html`
- Create: `reports/templates/reports/monthly_ca_pdf.html`

- [ ] **Step 1: Create directory structure**

Run:
```bash
rm reports/tests.py
mkdir -p reports/tests reports/generators reports/templates/reports
touch reports/tests/__init__.py reports/generators/__init__.py
```

- [ ] **Step 2: Write failing tests**

Create `reports/tests/test_pdf.py`:

```python
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from accounting.models import (
    AssetSnapshot,
    Category,
    CategoryType,
    Entry,
    FiscalYear,
)
from core.models import Organization
from reports.generators.pdf import generate_journal_pdf, generate_patrimony_pdf, generate_monthly_ca_pdf


class JournalPDFTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="RCVD", address="Dave")
        self.fy = FiscalYear.objects.create(
            organization=self.org,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        self.cat = Category.objects.create(
            organization=self.org, name="Cotisations", category_type=CategoryType.INCOME
        )
        self.user = User.objects.create_user(username="test", password="test123")
        Entry.objects.create(
            fiscal_year=self.fy,
            category=self.cat,
            date=date(2026, 3, 15),
            amount=Decimal("50.00"),
            description="Test cotisation",
            created_by=self.user,
        )

    def test_generate_journal_pdf(self):
        pdf_bytes = generate_journal_pdf(self.fy)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_journal_pdf_empty_year(self):
        empty_fy = FiscalYear.objects.create(
            organization=self.org,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
        )
        pdf_bytes = generate_journal_pdf(empty_fy)
        self.assertIsInstance(pdf_bytes, bytes)


class PatrimonyPDFTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="RCVD", address="Dave")
        self.fy = FiscalYear.objects.create(
            organization=self.org,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        AssetSnapshot.objects.create(
            fiscal_year=self.fy,
            date=date(2026, 12, 31),
            cash=Decimal("1200.00"),
            bank=Decimal("15000.00"),
            receivables=Decimal("500.00"),
            debts=Decimal("300.00"),
        )

    def test_generate_patrimony_pdf(self):
        pdf_bytes = generate_patrimony_pdf(self.fy)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))


class MonthlyCAPDFTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="RCVD", address="Dave")
        self.fy = FiscalYear.objects.create(
            organization=self.org,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        self.cat = Category.objects.create(
            organization=self.org, name="Cotisations", category_type=CategoryType.INCOME
        )
        self.user = User.objects.create_user(username="test", password="test123")
        Entry.objects.create(
            fiscal_year=self.fy,
            category=self.cat,
            date=date(2026, 3, 15),
            amount=Decimal("50.00"),
            description="Test",
            created_by=self.user,
        )

    def test_generate_monthly_ca_pdf(self):
        pdf_bytes = generate_monthly_ca_pdf(self.fy, 2026, 3)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python manage.py test reports.tests.test_pdf -v 2`
Expected: FAIL — `ImportError`

- [ ] **Step 4: Create PDF HTML templates**

Create `reports/templates/reports/journal_pdf.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: sans-serif; font-size: 11pt; }
        h1 { font-size: 16pt; margin-bottom: 5mm; }
        h2 { font-size: 13pt; margin-top: 8mm; }
        table { width: 100%; border-collapse: collapse; margin-top: 3mm; }
        th, td { border: 1px solid #ccc; padding: 2mm 3mm; text-align: left; }
        th { background: #f0f0f0; }
        .amount { text-align: right; }
        .total { font-weight: bold; background: #f8f8f8; }
        .footer { margin-top: 10mm; font-size: 9pt; color: #666; }
    </style>
</head>
<body>
    <h1>Journal des recettes et dépenses</h1>
    <p><strong>{{ org.name }}</strong> — Exercice {{ fiscal_year }}</p>

    <table>
        <thead>
            <tr>
                <th>Date</th>
                <th>Description</th>
                <th>Catégorie</th>
                <th class="amount">Recette</th>
                <th class="amount">Dépense</th>
            </tr>
        </thead>
        <tbody>
            {% for entry in entries %}
            <tr>
                <td>{{ entry.date }}</td>
                <td>{{ entry.description }}</td>
                <td>{{ entry.category.name }}</td>
                <td class="amount">{% if entry.entry_type == "income" %}{{ entry.amount }} €{% endif %}</td>
                <td class="amount">{% if entry.entry_type == "expense" %}{{ entry.amount }} €{% endif %}</td>
            </tr>
            {% endfor %}
            <tr class="total">
                <td colspan="3">Total</td>
                <td class="amount">{{ total_income }} €</td>
                <td class="amount">{{ total_expenses }} €</td>
            </tr>
            <tr class="total">
                <td colspan="3">Solde</td>
                <td class="amount" colspan="2">{{ balance }} €</td>
            </tr>
        </tbody>
    </table>

    <p class="footer">Généré par OpenASBL — {{ generated_at }}</p>
</body>
</html>
```

Create `reports/templates/reports/patrimony_pdf.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: sans-serif; font-size: 11pt; }
        h1 { font-size: 16pt; margin-bottom: 5mm; }
        table { width: 60%; border-collapse: collapse; margin-top: 3mm; }
        th, td { border: 1px solid #ccc; padding: 2mm 3mm; }
        th { background: #f0f0f0; text-align: left; }
        .amount { text-align: right; }
        .total { font-weight: bold; background: #f8f8f8; }
        .footer { margin-top: 10mm; font-size: 9pt; color: #666; }
    </style>
</head>
<body>
    <h1>État du patrimoine</h1>
    <p><strong>{{ org.name }}</strong> — Au {{ snapshot.date }}</p>

    <h2>Avoirs</h2>
    <table>
        <tr><td>Caisse</td><td class="amount">{{ snapshot.cash }} €</td></tr>
        <tr><td>Banque</td><td class="amount">{{ snapshot.bank }} €</td></tr>
        <tr><td>Créances</td><td class="amount">{{ snapshot.receivables }} €</td></tr>
        <tr class="total"><td>Total avoirs</td><td class="amount">{{ total_assets }} €</td></tr>
    </table>

    <h2>Dettes</h2>
    <table>
        <tr><td>Dettes</td><td class="amount">{{ snapshot.debts }} €</td></tr>
    </table>

    <h2>Patrimoine net</h2>
    <table>
        <tr class="total"><td>Actif net</td><td class="amount">{{ snapshot.net_worth }} €</td></tr>
    </table>

    {% if snapshot.notes %}
    <p style="margin-top: 5mm;"><strong>Notes :</strong> {{ snapshot.notes }}</p>
    {% endif %}

    <p class="footer">Généré par OpenASBL — {{ generated_at }}</p>
</body>
</html>
```

Create `reports/templates/reports/monthly_ca_pdf.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: sans-serif; font-size: 11pt; }
        h1 { font-size: 16pt; margin-bottom: 5mm; }
        h2 { font-size: 13pt; margin-top: 8mm; }
        table { width: 100%; border-collapse: collapse; margin-top: 3mm; }
        th, td { border: 1px solid #ccc; padding: 2mm 3mm; }
        th { background: #f0f0f0; text-align: left; }
        .amount { text-align: right; }
        .total { font-weight: bold; background: #f8f8f8; }
        .footer { margin-top: 10mm; font-size: 9pt; color: #666; }
    </style>
</head>
<body>
    <h1>Rapport mensuel — Conseil d'Administration</h1>
    <p><strong>{{ org.name }}</strong> — {{ month_name }} {{ year }}</p>

    <h2>Résumé du mois</h2>
    <table>
        <tr><td>Recettes du mois</td><td class="amount">{{ month_income }} €</td></tr>
        <tr><td>Dépenses du mois</td><td class="amount">{{ month_expenses }} €</td></tr>
        <tr class="total"><td>Solde du mois</td><td class="amount">{{ month_balance }} €</td></tr>
    </table>

    <h2>Détail par catégorie</h2>
    <table>
        <thead>
            <tr><th>Catégorie</th><th class="amount">Prévu</th><th class="amount">Réalisé</th><th class="amount">Écart</th></tr>
        </thead>
        <tbody>
            {% for row in category_breakdown %}
            <tr>
                <td>{{ row.name }}</td>
                <td class="amount">{{ row.planned }} €</td>
                <td class="amount">{{ row.actual }} €</td>
                <td class="amount">{{ row.diff }} €</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <h2>Écritures du mois</h2>
    <table>
        <thead>
            <tr><th>Date</th><th>Description</th><th>Catégorie</th><th class="amount">Montant</th></tr>
        </thead>
        <tbody>
            {% for entry in entries %}
            <tr>
                <td>{{ entry.date }}</td>
                <td>{{ entry.description }}</td>
                <td>{{ entry.category.name }}</td>
                <td class="amount">{% if entry.entry_type == "expense" %}-{% endif %}{{ entry.amount }} €</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <p class="footer">Généré par OpenASBL — {{ generated_at }}</p>
</body>
</html>
```

- [ ] **Step 5: Write PDF generator**

Create `reports/generators/pdf.py`:

```python
from datetime import datetime
from decimal import Decimal

from django.db.models import Sum
from django.template.loader import render_to_string

import weasyprint

from accounting.models import (
    AssetSnapshot,
    Budget,
    CategoryType,
    Entry,
)

MONTH_NAMES_FR = [
    "", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]


def generate_journal_pdf(fiscal_year):
    org = fiscal_year.organization
    entries = (
        Entry.objects.filter(fiscal_year=fiscal_year)
        .select_related("category")
        .order_by("date")
    )
    total_income = (
        entries.filter(category__category_type=CategoryType.INCOME).aggregate(
            t=Sum("amount")
        )["t"]
        or Decimal("0")
    )
    total_expenses = (
        entries.filter(category__category_type=CategoryType.EXPENSE).aggregate(
            t=Sum("amount")
        )["t"]
        or Decimal("0")
    )

    html = render_to_string(
        "reports/journal_pdf.html",
        {
            "org": org,
            "fiscal_year": fiscal_year,
            "entries": entries,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "balance": total_income - total_expenses,
            "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        },
    )
    return weasyprint.HTML(string=html).write_pdf()


def generate_patrimony_pdf(fiscal_year):
    org = fiscal_year.organization
    snapshot = (
        AssetSnapshot.objects.filter(fiscal_year=fiscal_year).order_by("-date").first()
    )
    if not snapshot:
        snapshot = AssetSnapshot(
            cash=Decimal("0"),
            bank=Decimal("0"),
            receivables=Decimal("0"),
            debts=Decimal("0"),
        )

    html = render_to_string(
        "reports/patrimony_pdf.html",
        {
            "org": org,
            "fiscal_year": fiscal_year,
            "snapshot": snapshot,
            "total_assets": snapshot.cash + snapshot.bank + snapshot.receivables,
            "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        },
    )
    return weasyprint.HTML(string=html).write_pdf()


def generate_monthly_ca_pdf(fiscal_year, year, month):
    org = fiscal_year.organization
    entries = (
        Entry.objects.filter(
            fiscal_year=fiscal_year, date__year=year, date__month=month
        )
        .select_related("category")
        .order_by("date")
    )
    month_income = (
        entries.filter(category__category_type=CategoryType.INCOME).aggregate(
            t=Sum("amount")
        )["t"]
        or Decimal("0")
    )
    month_expenses = (
        entries.filter(category__category_type=CategoryType.EXPENSE).aggregate(
            t=Sum("amount")
        )["t"]
        or Decimal("0")
    )

    budgets = {
        b.category_id: b.planned_amount
        for b in Budget.objects.filter(fiscal_year=fiscal_year)
    }
    category_totals = (
        entries.values("category__id", "category__name")
        .annotate(total=Sum("amount"))
        .order_by("category__name")
    )
    category_breakdown = []
    for ct in category_totals:
        planned = budgets.get(ct["category__id"], Decimal("0"))
        actual = ct["total"]
        category_breakdown.append(
            {
                "name": ct["category__name"],
                "planned": planned,
                "actual": actual,
                "diff": actual - planned,
            }
        )

    html = render_to_string(
        "reports/monthly_ca_pdf.html",
        {
            "org": org,
            "fiscal_year": fiscal_year,
            "year": year,
            "month_name": MONTH_NAMES_FR[month],
            "entries": entries,
            "month_income": month_income,
            "month_expenses": month_expenses,
            "month_balance": month_income - month_expenses,
            "category_breakdown": category_breakdown,
            "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        },
    )
    return weasyprint.HTML(string=html).write_pdf()
```

- [ ] **Step 6: Run tests**

Run: `python manage.py test reports.tests.test_pdf -v 2`
Expected: All 4 tests PASS.

- [ ] **Step 7: Commit**

```bash
git add reports/
git commit -m "feat(reports): add PDF generation for journal, patrimony and monthly CA reports"
```

---

## Task 10: Reports App — Excel/CSV Export

**Files:**
- Create: `reports/generators/excel.py`
- Create: `reports/tests/test_excel.py`

- [ ] **Step 1: Write failing tests**

Create `reports/tests/test_excel.py`:

```python
from datetime import date
from decimal import Decimal
from io import BytesIO

from django.contrib.auth.models import User
from django.test import TestCase

import openpyxl

from accounting.models import Category, CategoryType, Entry, FiscalYear
from core.models import Organization
from reports.generators.excel import generate_journal_excel, generate_journal_csv


class JournalExcelTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="RCVD", address="Dave")
        self.fy = FiscalYear.objects.create(
            organization=self.org,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        self.cat = Category.objects.create(
            organization=self.org, name="Cotisations", category_type=CategoryType.INCOME
        )
        self.user = User.objects.create_user(username="test", password="test123")
        Entry.objects.create(
            fiscal_year=self.fy,
            category=self.cat,
            date=date(2026, 3, 15),
            amount=Decimal("50.00"),
            description="Cotisation test",
            created_by=self.user,
        )

    def test_generate_excel(self):
        excel_bytes = generate_journal_excel(self.fy)
        self.assertIsInstance(excel_bytes, bytes)
        wb = openpyxl.load_workbook(BytesIO(excel_bytes))
        ws = wb.active
        self.assertEqual(ws.cell(row=1, column=1).value, "Date")
        self.assertEqual(ws.cell(row=2, column=2).value, "Cotisation test")

    def test_generate_csv(self):
        csv_text = generate_journal_csv(self.fy)
        self.assertIsInstance(csv_text, str)
        self.assertIn("Date", csv_text)
        self.assertIn("Cotisation test", csv_text)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test reports.tests.test_excel -v 2`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Write Excel/CSV generator**

Create `reports/generators/excel.py`:

```python
import csv
import io
from decimal import Decimal

from django.db.models import Sum

import openpyxl

from accounting.models import CategoryType, Entry


def generate_journal_excel(fiscal_year):
    entries = (
        Entry.objects.filter(fiscal_year=fiscal_year)
        .select_related("category")
        .order_by("date")
    )

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Journal"

    headers = ["Date", "Description", "Catégorie", "Type", "Montant"]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = openpyxl.styles.Font(bold=True)

    for entry in entries:
        ws.append([
            entry.date.isoformat(),
            entry.description,
            entry.category.name,
            entry.category.get_category_type_display(),
            float(entry.amount),
        ])

    total_income = (
        entries.filter(category__category_type=CategoryType.INCOME)
        .aggregate(t=Sum("amount"))["t"] or Decimal("0")
    )
    total_expenses = (
        entries.filter(category__category_type=CategoryType.EXPENSE)
        .aggregate(t=Sum("amount"))["t"] or Decimal("0")
    )

    ws.append([])
    ws.append(["", "", "", "Total recettes", float(total_income)])
    ws.append(["", "", "", "Total dépenses", float(total_expenses)])
    ws.append(["", "", "", "Solde", float(total_income - total_expenses)])

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def generate_journal_csv(fiscal_year):
    entries = (
        Entry.objects.filter(fiscal_year=fiscal_year)
        .select_related("category")
        .order_by("date")
    )

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Date", "Description", "Catégorie", "Type", "Montant"])

    for entry in entries:
        writer.writerow([
            entry.date.isoformat(),
            entry.description,
            entry.category.name,
            entry.category.get_category_type_display(),
            str(entry.amount),
        ])

    return output.getvalue()
```

- [ ] **Step 4: Run tests**

Run: `python manage.py test reports.tests.test_excel -v 2`
Expected: All 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add reports/generators/excel.py reports/tests/test_excel.py
git commit -m "feat(reports): add Excel and CSV export for journal"
```

---

## Task 11: Reports App — Views & Report Selection Page

**Files:**
- Modify: `reports/views.py`
- Modify: `reports/urls.py`
- Create: `reports/templates/reports/report_select.html`
- Create: `reports/tests/test_views.py`

- [ ] **Step 1: Write failing tests**

Create `reports/tests/test_views.py`:

```python
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import PermissionLevel, UserProfile
from accounting.models import Category, CategoryType, Entry, FiscalYear
from core.models import Organization


class ReportSelectViewTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="RCVD", address="Dave")
        self.user = User.objects.create_user(username="test", password="test123")
        UserProfile.objects.create(
            user=self.user,
            organization=self.org,
            permission_level=PermissionLevel.LECTURE,
        )
        self.fy = FiscalYear.objects.create(
            organization=self.org,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        self.client.login(username="test", password="test123")

    def test_report_select_page(self):
        response = self.client.get("/reports/")
        self.assertEqual(response.status_code, 200)

    def test_download_journal_pdf(self):
        response = self.client.get(f"/reports/journal/pdf/?fiscal_year={self.fy.pk}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_download_journal_excel(self):
        response = self.client.get(f"/reports/journal/excel/?fiscal_year={self.fy.pk}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("spreadsheet", response["Content-Type"])

    def test_download_journal_csv(self):
        response = self.client.get(f"/reports/journal/csv/?fiscal_year={self.fy.pk}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("csv", response["Content-Type"])

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get("/reports/")
        self.assertEqual(response.status_code, 302)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test reports.tests.test_views -v 2`
Expected: FAIL

- [ ] **Step 3: Write views**

Replace `reports/views.py`:

```python
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from accounting.models import FiscalYear
from reports.generators.excel import generate_journal_csv, generate_journal_excel
from reports.generators.pdf import (
    generate_journal_pdf,
    generate_monthly_ca_pdf,
    generate_patrimony_pdf,
)


@login_required
def report_select(request):
    org = request.user.profile.organization
    fiscal_years = FiscalYear.objects.filter(organization=org)
    return render(
        request, "reports/report_select.html", {"fiscal_years": fiscal_years}
    )


@login_required
def journal_pdf(request):
    fy = get_object_or_404(FiscalYear, pk=request.GET.get("fiscal_year"))
    pdf = generate_journal_pdf(fy)
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="journal_{fy.start_date.year}.pdf"'
    return response


@login_required
def journal_excel(request):
    fy = get_object_or_404(FiscalYear, pk=request.GET.get("fiscal_year"))
    excel = generate_journal_excel(fy)
    response = HttpResponse(
        excel,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="journal_{fy.start_date.year}.xlsx"'
    return response


@login_required
def journal_csv(request):
    fy = get_object_or_404(FiscalYear, pk=request.GET.get("fiscal_year"))
    csv_text = generate_journal_csv(fy)
    response = HttpResponse(csv_text, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="journal_{fy.start_date.year}.csv"'
    return response


@login_required
def patrimony_pdf(request):
    fy = get_object_or_404(FiscalYear, pk=request.GET.get("fiscal_year"))
    pdf = generate_patrimony_pdf(fy)
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="patrimoine_{fy.start_date.year}.pdf"'
    return response


@login_required
def monthly_ca_pdf(request):
    fy = get_object_or_404(FiscalYear, pk=request.GET.get("fiscal_year"))
    year = int(request.GET.get("year"))
    month = int(request.GET.get("month"))
    pdf = generate_monthly_ca_pdf(fy, year, month)
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="rapport_ca_{year}_{month:02d}.pdf"'
    return response
```

- [ ] **Step 4: Write URLs**

Replace `reports/urls.py`:

```python
from django.urls import path

from reports import views

app_name = "reports"

urlpatterns = [
    path("", views.report_select, name="report_select"),
    path("journal/pdf/", views.journal_pdf, name="journal_pdf"),
    path("journal/excel/", views.journal_excel, name="journal_excel"),
    path("journal/csv/", views.journal_csv, name="journal_csv"),
    path("patrimony/pdf/", views.patrimony_pdf, name="patrimony_pdf"),
    path("monthly-ca/pdf/", views.monthly_ca_pdf, name="monthly_ca_pdf"),
]
```

- [ ] **Step 5: Create report selection template**

Create `reports/templates/reports/report_select.html`:

```html
{% extends "base.html" %}
{% load i18n %}

{% block title %}Rapports — OpenASBL{% endblock %}

{% block content %}
<h1>{% trans "Rapports" %}</h1>

<div class="card">
    <h2>Sélectionner un exercice</h2>
    <form id="report-form">
        <div class="form-group">
            <label for="fiscal_year">Exercice comptable</label>
            <select name="fiscal_year" id="fiscal_year">
                {% for fy in fiscal_years %}
                <option value="{{ fy.pk }}">{{ fy }} ({{ fy.get_status_display }})</option>
                {% endfor %}
            </select>
        </div>
    </form>
</div>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: var(--space); margin-top: var(--space);">
    <div class="card">
        <h3>Journal des recettes/dépenses</h3>
        <p class="text-muted">Toutes les écritures de l'exercice</p>
        <div style="display: flex; gap: 0.5rem; margin-top: 0.5rem;">
            <a href="#" class="btn btn-primary report-link" data-url="{% url 'reports:journal_pdf' %}">PDF</a>
            <a href="#" class="btn btn-success report-link" data-url="{% url 'reports:journal_excel' %}">Excel</a>
            <a href="#" class="btn report-link" data-url="{% url 'reports:journal_csv' %}">CSV</a>
        </div>
    </div>

    <div class="card">
        <h3>État du patrimoine</h3>
        <p class="text-muted">Avoirs et dettes à la clôture</p>
        <a href="#" class="btn btn-primary report-link" data-url="{% url 'reports:patrimony_pdf' %}">PDF</a>
    </div>

    <div class="card">
        <h3>Rapport mensuel CA</h3>
        <p class="text-muted">Résumé pour le conseil d'administration</p>
        <div style="display: flex; gap: 0.5rem; align-items: center; margin-top: 0.5rem;">
            <select id="report-month">
                <option value="1">Janvier</option>
                <option value="2">Février</option>
                <option value="3">Mars</option>
                <option value="4">Avril</option>
                <option value="5">Mai</option>
                <option value="6">Juin</option>
                <option value="7">Juillet</option>
                <option value="8">Août</option>
                <option value="9">Septembre</option>
                <option value="10">Octobre</option>
                <option value="11">Novembre</option>
                <option value="12">Décembre</option>
            </select>
            <input type="number" id="report-year" value="2026" style="width: 100px;">
            <a href="#" class="btn btn-primary" id="monthly-ca-link" data-url="{% url 'reports:monthly_ca_pdf' %}">PDF</a>
        </div>
    </div>
</div>

<script>
document.querySelectorAll('.report-link').forEach(link => {
    link.addEventListener('click', e => {
        e.preventDefault();
        const fy = document.getElementById('fiscal_year').value;
        window.open(link.dataset.url + '?fiscal_year=' + fy, '_blank');
    });
});
document.getElementById('monthly-ca-link').addEventListener('click', e => {
    e.preventDefault();
    const fy = document.getElementById('fiscal_year').value;
    const month = document.getElementById('report-month').value;
    const year = document.getElementById('report-year').value;
    window.open(e.target.dataset.url + '?fiscal_year=' + fy + '&year=' + year + '&month=' + month, '_blank');
});
</script>
{% endblock %}
```

- [ ] **Step 6: Run tests**

Run: `python manage.py test reports.tests.test_views -v 2`
Expected: All 5 tests PASS.

- [ ] **Step 7: Commit**

```bash
git add reports/
git commit -m "feat(reports): add report selection page and download views"
```

---

## Task 12: Help App — Contextual Help System

**Files:**
- Create: `help/context.py`
- Modify: `help/views.py`
- Modify: `help/urls.py`
- Create: `help/templatetags/__init__.py`
- Create: `help/templatetags/help_tags.py`
- Create: `help/templates/help/help_panel.html`
- Create: `help/tests/__init__.py`
- Create: `help/tests/test_context.py`

- [ ] **Step 1: Create directory structure**

Run:
```bash
rm help/tests.py
mkdir -p help/tests help/templatetags help/templates/help
touch help/tests/__init__.py help/templatetags/__init__.py
```

- [ ] **Step 2: Write failing tests**

Create `help/tests/test_context.py`:

```python
from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import PermissionLevel, UserProfile
from core.models import Organization
from help.context import get_help_text, HELP_TEXTS


class HelpContextTest(TestCase):
    def test_known_topic(self):
        text = get_help_text("entry_create")
        self.assertIsInstance(text, str)
        self.assertTrue(len(text) > 0)

    def test_unknown_topic(self):
        text = get_help_text("nonexistent_topic")
        self.assertEqual(text, "")

    def test_all_topics_are_strings(self):
        for topic, text in HELP_TEXTS.items():
            self.assertIsInstance(text, str, f"Topic '{topic}' is not a string")


class HelpViewTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Test", address="Namur")
        self.user = User.objects.create_user(username="test", password="test123")
        UserProfile.objects.create(
            user=self.user,
            organization=self.org,
            permission_level=PermissionLevel.LECTURE,
        )
        self.client.login(username="test", password="test123")

    def test_help_panel_loads(self):
        response = self.client.get("/help/panel/?topic=entry_create")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "écriture")
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python manage.py test help.tests.test_context -v 2`
Expected: FAIL — `ImportError`

- [ ] **Step 4: Write help context registry**

Create `help/context.py`:

```python
HELP_TEXTS = {
    "entry_create": (
        "Une écriture correspond à une opération financière : une recette "
        "(argent qui entre) ou une dépense (argent qui sort). "
        "Choisissez la catégorie correspondante, indiquez la date, le montant TTC "
        "et une description claire. Vous pouvez joindre un justificatif (ticket, facture)."
    ),
    "entry_list": (
        "Le journal liste toutes vos écritures. Vous pouvez filtrer par exercice "
        "comptable. Les recettes apparaissent en vert, les dépenses en rouge."
    ),
    "fiscal_year": (
        "Un exercice comptable couvre une période définie (souvent une année). "
        "Toutes les écritures doivent être rattachées à un exercice. "
        "Une fois clôturé, aucune modification n'est possible."
    ),
    "fiscal_year_close": (
        "La clôture d'un exercice est définitive. Avant de clôturer, assurez-vous "
        "que toutes les écritures sont saisies et que l'état du patrimoine est à jour. "
        "Vous devrez ensuite déposer les comptes annuels au greffe."
    ),
    "category": (
        "Les catégories permettent de classer vos recettes et dépenses. "
        "Des catégories par défaut sont fournies, mais vous pouvez en ajouter "
        "selon les besoins de votre ASBL."
    ),
    "budget": (
        "Le budget prévisionnel vous permet de planifier les recettes et dépenses "
        "par catégorie pour un exercice. Le suivi budgétaire compare ensuite "
        "le prévu au réalisé."
    ),
    "asset_snapshot": (
        "L'état du patrimoine recense vos avoirs (caisse, banque, créances) "
        "et vos dettes à une date donnée. Il est obligatoire à la clôture "
        "de chaque exercice."
    ),
    "reports": (
        "Les rapports vous permettent de générer les documents obligatoires "
        "(journal, état du patrimoine, comptes annuels) ainsi que le rapport "
        "mensuel pour le conseil d'administration. Disponibles en PDF, Excel et CSV."
    ),
    "dashboard": (
        "Le tableau de bord affiche un résumé de l'exercice en cours : "
        "total des recettes, des dépenses, solde et nombre d'écritures."
    ),
}


def get_help_text(topic):
    return HELP_TEXTS.get(topic, "")
```

- [ ] **Step 5: Write help view**

Replace `help/views.py`:

```python
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from help.context import get_help_text


@login_required
def help_panel(request):
    topic = request.GET.get("topic", "")
    text = get_help_text(topic)
    return render(request, "help/help_panel.html", {"topic": topic, "text": text})
```

- [ ] **Step 6: Write URLs**

Replace `help/urls.py`:

```python
from django.urls import path

from help import views

app_name = "help"

urlpatterns = [
    path("panel/", views.help_panel, name="help_panel"),
]
```

- [ ] **Step 7: Write template tag**

Create `help/templatetags/help_tags.py`:

```python
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def help_button(topic):
    return mark_safe(
        f'<button class="btn" '
        f'hx-get="/help/panel/?topic={topic}" '
        f'hx-target="#help-panel" '
        f'hx-swap="innerHTML" '
        f'title="Aide">?</button>'
    )
```

- [ ] **Step 8: Write help panel template**

Create `help/templates/help/help_panel.html`:

```html
{% if text %}
<div class="card" style="background: #eff6ff; border-color: #bfdbfe;">
    <p>{{ text }}</p>
</div>
{% else %}
<div class="card">
    <p class="text-muted">Aucune aide disponible pour ce sujet.</p>
</div>
{% endif %}
```

- [ ] **Step 9: Run tests**

Run: `python manage.py test help.tests.test_context -v 2`
Expected: All 4 tests PASS.

- [ ] **Step 10: Commit**

```bash
git add help/
git commit -m "feat(help): add contextual help system with HTMX panel"
```

---

## Task 13: Core App — Setup Wizard

**Files:**
- Modify: `core/forms.py`
- Modify: `core/views.py`
- Modify: `core/urls.py`
- Create: `core/templates/core/setup_wizard.html`
- Create: `core/templates/core/organization_settings.html`
- Create: `core/tests/test_views.py`
- Modify: `accounts/middleware.py`

- [ ] **Step 1: Write failing tests**

Create `core/tests/test_views.py`:

```python
from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import PermissionLevel, UserProfile
from core.models import Organization


class SetupWizardTest(TestCase):
    def test_wizard_shows_when_no_org(self):
        response = self.client.get("/core/setup/")
        self.assertEqual(response.status_code, 200)

    def test_wizard_creates_org_and_admin(self):
        response = self.client.post(
            "/core/setup/",
            {
                "org_name": "RCVD",
                "org_address": "Dave, Namur",
                "org_enterprise_number": "0123.456.789",
                "org_email": "info@rcvd.be",
                "org_phone": "",
                "admin_username": "tresorier",
                "admin_password": "securepass123",
                "admin_first_name": "Jean",
                "admin_last_name": "Dupont",
                "admin_email": "jean@rcvd.be",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Organization.objects.exists())
        self.assertTrue(User.objects.filter(username="tresorier").exists())
        profile = User.objects.get(username="tresorier").profile
        self.assertEqual(profile.permission_level, PermissionLevel.ADMIN)

    def test_wizard_blocked_when_org_exists(self):
        Organization.objects.create(name="Exists", address="Test")
        response = self.client.get("/core/setup/")
        self.assertEqual(response.status_code, 302)


class OrganizationSettingsTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="RCVD", address="Dave")
        self.user = User.objects.create_user(username="admin", password="test123")
        UserProfile.objects.create(
            user=self.user,
            organization=self.org,
            permission_level=PermissionLevel.ADMIN,
        )
        self.client.login(username="admin", password="test123")

    def test_settings_page_loads(self):
        response = self.client.get("/core/settings/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "RCVD")

    def test_non_admin_cannot_access(self):
        self.user.profile.permission_level = PermissionLevel.GESTION
        self.user.profile.save()
        response = self.client.get("/core/settings/")
        self.assertEqual(response.status_code, 403)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test core.tests.test_views -v 2`
Expected: FAIL

- [ ] **Step 3: Write forms**

Replace `core/forms.py`:

```python
from django import forms

from core.models import Organization


class SetupWizardForm(forms.Form):
    org_name = forms.CharField(label="Nom de l'ASBL", max_length=255)
    org_address = forms.CharField(label="Adresse du siège social", widget=forms.Textarea(attrs={"rows": 2}))
    org_enterprise_number = forms.CharField(label="Numéro d'entreprise (BCE)", max_length=20, required=False)
    org_email = forms.EmailField(label="Email de l'ASBL", required=False)
    org_phone = forms.CharField(label="Téléphone", max_length=30, required=False)
    admin_username = forms.CharField(label="Nom d'utilisateur admin", max_length=150)
    admin_password = forms.CharField(label="Mot de passe admin", widget=forms.PasswordInput)
    admin_first_name = forms.CharField(label="Prénom", max_length=150, required=False)
    admin_last_name = forms.CharField(label="Nom", max_length=150, required=False)
    admin_email = forms.EmailField(label="Email admin", required=False)


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ("name", "address", "enterprise_number", "email", "phone")
```

- [ ] **Step 4: Write views**

Replace `core/views.py`:

```python
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render

from accounts.decorators import require_permission
from accounts.models import PermissionLevel, UserProfile
from accounting.seed import seed_categories
from core.forms import OrganizationForm, SetupWizardForm
from core.models import Organization


def setup_wizard(request):
    if Organization.objects.exists():
        return redirect("accounting:dashboard")

    if request.method == "POST":
        form = SetupWizardForm(request.POST)
        if form.is_valid():
            org = Organization.objects.create(
                name=form.cleaned_data["org_name"],
                address=form.cleaned_data["org_address"],
                enterprise_number=form.cleaned_data.get("org_enterprise_number", ""),
                email=form.cleaned_data.get("org_email", ""),
                phone=form.cleaned_data.get("org_phone", ""),
            )
            user = User.objects.create_user(
                username=form.cleaned_data["admin_username"],
                password=form.cleaned_data["admin_password"],
                first_name=form.cleaned_data.get("admin_first_name", ""),
                last_name=form.cleaned_data.get("admin_last_name", ""),
                email=form.cleaned_data.get("admin_email", ""),
            )
            UserProfile.objects.create(
                user=user,
                organization=org,
                permission_level=PermissionLevel.ADMIN,
            )
            seed_categories(org)
            login(request, user)
            return redirect("accounting:dashboard")
    else:
        form = SetupWizardForm()

    return render(request, "core/setup_wizard.html", {"form": form})


@login_required
@require_permission(PermissionLevel.ADMIN)
def organization_settings(request):
    org = request.user.profile.organization
    if request.method == "POST":
        form = OrganizationForm(request.POST, instance=org)
        if form.is_valid():
            form.save()
            return redirect("core:organization_settings")
    else:
        form = OrganizationForm(instance=org)
    return render(request, "core/organization_settings.html", {"form": form})
```

- [ ] **Step 5: Write URLs**

Replace `core/urls.py`:

```python
from django.urls import path

from core import views

app_name = "core"

urlpatterns = [
    path("setup/", views.setup_wizard, name="setup_wizard"),
    path("settings/", views.organization_settings, name="organization_settings"),
]
```

- [ ] **Step 6: Create templates**

Create `core/templates/core/setup_wizard.html`:

```html
{% extends "base.html" %}
{% load i18n %}

{% block title %}Configuration initiale — OpenASBL{% endblock %}

{% block content %}
<div class="card" style="max-width: 600px; margin: 2rem auto;">
    <h1>{% trans "Bienvenue dans OpenASBL" %}</h1>
    <p>Configurez votre ASBL et créez le compte administrateur.</p>

    <form method="post">
        {% csrf_token %}
        <h2>Votre ASBL</h2>
        {% for field in form %}
        {% if field.name|slice:":3" == "org" %}
        <div class="form-group">
            <label for="{{ field.id_for_label }}">{{ field.label }}</label>
            {{ field }}
            {% if field.errors %}<p class="text-danger">{{ field.errors.0 }}</p>{% endif %}
        </div>
        {% endif %}
        {% endfor %}

        <h2 style="margin-top: var(--space);">Compte administrateur</h2>
        {% for field in form %}
        {% if field.name|slice:":5" == "admin" %}
        <div class="form-group">
            <label for="{{ field.id_for_label }}">{{ field.label }}</label>
            {{ field }}
            {% if field.errors %}<p class="text-danger">{{ field.errors.0 }}</p>{% endif %}
        </div>
        {% endif %}
        {% endfor %}

        <button type="submit" class="btn btn-primary" style="margin-top: var(--space);">Démarrer</button>
    </form>
</div>
{% endblock %}
```

Create `core/templates/core/organization_settings.html`:

```html
{% extends "base.html" %}
{% load i18n %}

{% block title %}Paramètres — OpenASBL{% endblock %}

{% block content %}
<div class="card" style="max-width: 600px;">
    <h1>{% trans "Paramètres de l'ASBL" %}</h1>
    <form method="post">
        {% csrf_token %}
        {% for field in form %}
        <div class="form-group">
            <label for="{{ field.id_for_label }}">{{ field.label }}</label>
            {{ field }}
            {% if field.errors %}<p class="text-danger">{{ field.errors.0 }}</p>{% endif %}
        </div>
        {% endfor %}
        <button type="submit" class="btn btn-success">Enregistrer</button>
    </form>
</div>
{% endblock %}
```

- [ ] **Step 7: Run tests**

Run: `python manage.py test core.tests.test_views -v 2`
Expected: All 4 tests PASS.

- [ ] **Step 8: Commit**

```bash
git add core/
git commit -m "feat(core): add setup wizard and organization settings"
```

---

## Task 14: Integration — Navigation, Middleware & Final Wiring

**Files:**
- Modify: `templates/navbar.html`
- Create: `accounts/middleware.py`
- Modify: `openasbl/settings.py`
- Modify: `openasbl/urls.py`

- [ ] **Step 1: Write setup redirect middleware**

Create `accounts/middleware.py`:

```python
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
```

- [ ] **Step 2: Add middleware to settings**

In `openasbl/settings.py`, add after `XFrameOptionsMiddleware`:

```python
    "accounts.middleware.SetupRequiredMiddleware",
```

- [ ] **Step 3: Update navbar**

Replace `templates/navbar.html`:

```html
{% load i18n %}
<nav>
    <a href="{% url 'accounting:dashboard' %}"><strong>OpenASBL</strong></a>
    {% if user.is_authenticated %}
        <a href="{% url 'accounting:dashboard' %}">{% trans "Tableau de bord" %}</a>
        <a href="{% url 'accounting:entry_list' %}">{% trans "Écritures" %}</a>
        <a href="{% url 'accounting:fiscal_year_list' %}">{% trans "Exercices" %}</a>
        <a href="{% url 'accounting:category_list' %}">{% trans "Catégories" %}</a>
        <a href="{% url 'reports:report_select' %}">{% trans "Rapports" %}</a>
        {% if user.profile.can_manage_users %}
        <a href="{% url 'accounts:user_list' %}">{% trans "Utilisateurs" %}</a>
        <a href="{% url 'core:organization_settings' %}">{% trans "Paramètres" %}</a>
        {% endif %}
        <div style="margin-left: auto;">
            <span class="text-muted">{{ user.get_full_name|default:user.username }}</span>
            <form method="post" action="{% url 'accounts:logout' %}" style="display: inline;">
                {% csrf_token %}
                <button type="submit" class="btn">{% trans "Déconnexion" %}</button>
            </form>
        </div>
    {% endif %}
</nav>
<div id="help-panel"></div>
```

- [ ] **Step 4: Run full test suite**

Run: `python manage.py test -v 2`
Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add templates/navbar.html accounts/middleware.py openasbl/settings.py
git commit -m "feat: add navigation, setup redirect middleware and final wiring"
```

---


**Files:**



```markdown


## Project

OpenASBL — simplified accounting web application for small Belgian non-profit associations (ASBL) not subject to VAT.

## Stack

- Python 3.12+, Django 5.x, SQLite, HTMX 2.x, WeasyPrint, openpyxl
- Templates: Django templates + HTMX (no JS framework)
- Static files: WhiteNoise

## Commands

```bash
# Setup
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000

# Tests
python manage.py test                          # all tests
python manage.py test accounting.tests.test_models  # single test module
python manage.py test accounting.tests.test_models.EntryModelTest.test_create_entry  # single test

# Seed default categories
python manage.py seed_categories

# Migrations
python manage.py makemigrations
python manage.py migrate
```

## Architecture

5 Django apps:
- `core` — Organization model (single-instance), setup wizard, settings
- `accounts` — UserProfile with 4-level permissions (lecture/gestion/validation/admin), login/logout
- `accounting` — FiscalYear, Category, Entry, Budget, AssetSnapshot models + CRUD views
- `reports` — PDF (WeasyPrint), Excel (openpyxl), CSV generation; journal, patrimony, monthly CA reports
- `help` — contextual help system with HTMX panel and `{% help_button "topic" %}` template tag

## Key Design Decisions

- All amounts are TTC (no VAT) — `DecimalField` everywhere, no tax fields
- Single organization per instance (enforced by model validation)
- Permission system uses ordered levels, not named roles: lecture < gestion < validation < admin
- `@require_permission(PermissionLevel.GESTION)` decorator for view protection
- Fiscal year dates are configurable (not hardcoded to calendar year)
- `SetupRequiredMiddleware` redirects to setup wizard when no organization exists
- French UI, prepared for i18n (all strings wrapped in {% trans %})
```

- [ ] **Step 2: Run full test suite one final time**

Run: `python manage.py test -v 2`
Expected: All tests PASS.

- [ ] **Step 3: Commit**

```bash
```

- [ ] **Step 4: Push to remote**

```bash
git push origin main
```
