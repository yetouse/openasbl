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
