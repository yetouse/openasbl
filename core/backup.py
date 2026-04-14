"""
Export / Import system for OpenASBL.

Export creates a ZIP file containing:
  - manifest.json  (version, date, org name)
  - data.json      (all database records as serializable dicts)
  - media/         (logo + entry attachments)

Import reads that ZIP and restores everything.
"""

import hashlib
import io
import json
import zipfile
from datetime import date, datetime
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import transaction

from accounting.models import AssetSnapshot, Budget, Category, Entry, FiscalYear
from accounts.models import UserProfile
from core.models import Organization


EXPORT_VERSION = "1.0"


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


# ---------------------------------------------------------------------------
# EXPORT
# ---------------------------------------------------------------------------

def generate_export_zip():
    """Return bytes of a ZIP containing all application data and media."""
    org = Organization.objects.first()
    if not org:
        raise ValueError("Aucune organisation configurée.")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        data = _build_data(org)
        data_json = json.dumps(data, cls=DecimalEncoder, ensure_ascii=False, indent=2)
        zf.writestr("data.json", data_json)

        media_files = _collect_media(org, zf)

        manifest = {
            "version": EXPORT_VERSION,
            "exported_at": datetime.now().isoformat(),
            "organization": org.name,
            "data_checksum": hashlib.sha256(data_json.encode()).hexdigest(),
            "media_files": len(media_files),
        }
        zf.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))

    buf.seek(0)
    return buf.getvalue()


def _build_data(org):
    """Serialize all models to a dict."""
    # Organization
    org_data = {
        "name": org.name,
        "address": org.address,
        "enterprise_number": org.enterprise_number,
        "email": org.email,
        "phone": org.phone,
        "logo": org.logo.name if org.logo else "",
    }

    # Users + profiles
    users_data = []
    for profile in UserProfile.objects.select_related("user").filter(organization=org):
        u = profile.user
        users_data.append({
            "username": u.username,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "email": u.email,
            "is_active": u.is_active,
            "password_hash": u.password,
            "permission_level": profile.permission_level,
        })

    # Categories
    categories_data = []
    for cat in Category.objects.filter(organization=org):
        categories_data.append({
            "id": cat.pk,
            "name": cat.name,
            "category_type": cat.category_type,
            "description": cat.description,
        })

    # Fiscal years
    fiscal_years_data = []
    for fy in FiscalYear.objects.filter(organization=org):
        fiscal_years_data.append({
            "id": fy.pk,
            "start_date": fy.start_date,
            "end_date": fy.end_date,
            "status": fy.status,
        })

    # Entries
    entries_data = []
    for entry in Entry.objects.filter(fiscal_year__organization=org).select_related("category", "created_by"):
        entries_data.append({
            "fiscal_year_id": entry.fiscal_year_id,
            "category_id": entry.category_id,
            "date": entry.date,
            "amount": entry.amount,
            "description": entry.description,
            "attachment": entry.attachment.name if entry.attachment else "",
            "created_by_username": entry.created_by.username,
            "created_at": entry.created_at,
            "updated_at": entry.updated_at,
        })

    # Budgets
    budgets_data = []
    for budget in Budget.objects.filter(fiscal_year__organization=org):
        budgets_data.append({
            "fiscal_year_id": budget.fiscal_year_id,
            "category_id": budget.category_id,
            "planned_amount": budget.planned_amount,
        })

    # Asset snapshots
    snapshots_data = []
    for snap in AssetSnapshot.objects.filter(fiscal_year__organization=org):
        snapshots_data.append({
            "fiscal_year_id": snap.fiscal_year_id,
            "date": snap.date,
            "cash": snap.cash,
            "bank": snap.bank,
            "receivables": snap.receivables,
            "debts": snap.debts,
            "notes": snap.notes,
        })

    return {
        "organization": org_data,
        "users": users_data,
        "categories": categories_data,
        "fiscal_years": fiscal_years_data,
        "entries": entries_data,
        "budgets": budgets_data,
        "asset_snapshots": snapshots_data,
    }


def _collect_media(org, zf):
    """Add media files to the ZIP. Returns list of paths added."""
    media_root = settings.MEDIA_ROOT
    added = []

    # Logo
    if org.logo and org.logo.name:
        path = media_root / org.logo.name
        if path.exists():
            zf.write(str(path), f"media/{org.logo.name}")
            added.append(org.logo.name)

    # Attachments
    for entry in Entry.objects.filter(fiscal_year__organization=org):
        if entry.attachment and entry.attachment.name:
            path = media_root / entry.attachment.name
            if path.exists():
                zf.write(str(path), f"media/{entry.attachment.name}")
                added.append(entry.attachment.name)

    return added


# ---------------------------------------------------------------------------
# IMPORT
# ---------------------------------------------------------------------------

def validate_import_zip(file_obj):
    """
    Validate the uploaded ZIP. Returns (data_dict, zip_bytes) or raises ValueError.
    """
    zip_bytes = file_obj.read()
    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile:
        raise ValueError("Le fichier n'est pas un ZIP valide.")

    names = zf.namelist()
    if "manifest.json" not in names:
        raise ValueError("Fichier manifest.json manquant dans l'archive.")
    if "data.json" not in names:
        raise ValueError("Fichier data.json manquant dans l'archive.")

    manifest = json.loads(zf.read("manifest.json"))
    data_json = zf.read("data.json")

    # Verify checksum
    actual_checksum = hashlib.sha256(data_json).hexdigest()
    if manifest.get("data_checksum") and actual_checksum != manifest["data_checksum"]:
        raise ValueError("Le checksum des données ne correspond pas — fichier corrompu ?")

    data = json.loads(data_json)

    # Basic structure validation
    required_keys = {"organization", "users", "categories", "fiscal_years", "entries", "budgets", "asset_snapshots"}
    missing = required_keys - set(data.keys())
    if missing:
        raise ValueError(f"Clés manquantes dans data.json : {', '.join(missing)}")

    zf.close()
    return data, zip_bytes


@transaction.atomic
def restore_from_zip(zip_bytes):
    """
    Restore all data from a validated ZIP.
    Deletes existing data and replaces it entirely.
    """
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    data = json.loads(zf.read("data.json"))

    # --- 1. Clear existing data (order matters for FK) ---
    Entry.objects.all().delete()
    Budget.objects.all().delete()
    AssetSnapshot.objects.all().delete()
    FiscalYear.objects.all().delete()
    Category.objects.all().delete()
    UserProfile.objects.all().delete()
    # Delete all users except the current superuser doing the import
    # Actually, we delete all non-superuser users; superusers are kept
    User.objects.filter(is_superuser=False).delete()
    Organization.objects.all().delete()

    # --- 2. Organization ---
    org_data = data["organization"]
    org = Organization(
        name=org_data["name"],
        address=org_data["address"],
        enterprise_number=org_data.get("enterprise_number", ""),
        email=org_data.get("email", ""),
        phone=org_data.get("phone", ""),
    )
    org.save()

    # Restore logo
    logo_name = org_data.get("logo", "")
    if logo_name:
        media_path = f"media/{logo_name}"
        if media_path in zf.namelist():
            org.logo.save(logo_name.split("/")[-1], ContentFile(zf.read(media_path)), save=True)

    # --- 3. Users + profiles ---
    username_to_user = {}
    for u_data in data["users"]:
        user, created = User.objects.get_or_create(
            username=u_data["username"],
            defaults={
                "first_name": u_data.get("first_name", ""),
                "last_name": u_data.get("last_name", ""),
                "email": u_data.get("email", ""),
                "is_active": u_data.get("is_active", True),
            },
        )
        if created and u_data.get("password_hash"):
            user.password = u_data["password_hash"]
            user.save(update_fields=["password"])
        username_to_user[u_data["username"]] = user

        # Create profile if it doesn't exist
        UserProfile.objects.get_or_create(
            user=user,
            defaults={
                "organization": org,
                "permission_level": u_data.get("permission_level", "lecture"),
            },
        )

    # --- 4. Categories (need ID mapping for entries/budgets) ---
    old_cat_id_to_new = {}
    for cat_data in data["categories"]:
        cat = Category.objects.create(
            organization=org,
            name=cat_data["name"],
            category_type=cat_data["category_type"],
            description=cat_data.get("description", ""),
        )
        old_cat_id_to_new[cat_data["id"]] = cat.pk

    # --- 5. Fiscal years (need ID mapping) ---
    old_fy_id_to_new = {}
    for fy_data in data["fiscal_years"]:
        fy = FiscalYear(
            organization=org,
            start_date=fy_data["start_date"],
            end_date=fy_data["end_date"],
            status=fy_data.get("status", "open"),
        )
        fy.save()
        old_fy_id_to_new[fy_data["id"]] = fy.pk

    # --- 6. Entries ---
    for e_data in data["entries"]:
        new_fy_id = old_fy_id_to_new.get(e_data["fiscal_year_id"])
        new_cat_id = old_cat_id_to_new.get(e_data["category_id"])
        created_by = username_to_user.get(e_data.get("created_by_username"))
        if not new_fy_id or not new_cat_id or not created_by:
            continue  # skip orphaned entries

        entry = Entry(
            fiscal_year_id=new_fy_id,
            category_id=new_cat_id,
            date=e_data["date"],
            amount=Decimal(e_data["amount"]),
            description=e_data["description"],
            created_by=created_by,
        )
        entry.save()

        # Restore attachment
        att_name = e_data.get("attachment", "")
        if att_name:
            media_path = f"media/{att_name}"
            if media_path in zf.namelist():
                entry.attachment.save(att_name.split("/")[-1], ContentFile(zf.read(media_path)), save=True)

    # --- 7. Budgets ---
    for b_data in data["budgets"]:
        new_fy_id = old_fy_id_to_new.get(b_data["fiscal_year_id"])
        new_cat_id = old_cat_id_to_new.get(b_data["category_id"])
        if not new_fy_id or not new_cat_id:
            continue
        Budget.objects.create(
            fiscal_year_id=new_fy_id,
            category_id=new_cat_id,
            planned_amount=Decimal(b_data["planned_amount"]),
        )

    # --- 8. Asset snapshots ---
    for s_data in data["asset_snapshots"]:
        new_fy_id = old_fy_id_to_new.get(s_data["fiscal_year_id"])
        if not new_fy_id:
            continue
        AssetSnapshot.objects.create(
            fiscal_year_id=new_fy_id,
            date=s_data["date"],
            cash=Decimal(s_data["cash"]),
            bank=Decimal(s_data["bank"]),
            receivables=Decimal(s_data["receivables"]),
            debts=Decimal(s_data["debts"]),
            notes=s_data.get("notes", ""),
        )

    zf.close()
    return org
