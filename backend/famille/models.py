"""Localisation famille — modèles.

Principe : TRANSPARENCE + CONSENTEMENT. Chaque appareil enfant est enrôlé via un lien
(token) dans le compte parent, AVEC l'accord affiché de l'enfant. L'enfant peut couper
le partage à tout moment (sharing_on = False) ; le parent le voit, aucun contournement.
"""
import secrets

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


def _token():
    return secrets.token_urlsafe(32)


class ParentProfile(models.Model):
    """Le parent (= super-admin de SON cercle). Rattaché à un compte Django."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="parent_profile")
    display_name = models.CharField("Nom affiché", max_length=120, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.display_name or self.user.username


class EnrollInvite(models.Model):
    """Invitation par lien : un token à usage unique pour enrôler un appareil enfant."""
    parent = models.ForeignKey(ParentProfile, on_delete=models.CASCADE, related_name="invites")
    token = models.CharField(max_length=64, unique=True, default=_token, db_index=True)
    child_label = models.CharField("Nom de l'enfant", max_length=120)
    phone = models.CharField("Numéro lié", max_length=30, blank=True, default="")
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_used(self):
        return self.used_at is not None


class ChildDevice(models.Model):
    """Un appareil enfant enrôlé. device_token sert à authentifier les 'ping' de l'app."""
    parent = models.ForeignKey(ParentProfile, on_delete=models.CASCADE, related_name="devices")
    label = models.CharField("Nom de l'enfant", max_length=120)
    phone = models.CharField("Numéro lié", max_length=30, blank=True, default="", db_index=True)
    device_token = models.CharField(max_length=64, unique=True, default=_token, db_index=True)
    platform = models.CharField(max_length=10, blank=True, default="")  # android / ios
    # Consentement VISIBLE : l'enfant peut couper. Jamais contourné côté serveur.
    sharing_on = models.BooleanField("Partage activé par l'enfant", default=True)
    sharing_changed_at = models.DateTimeField(null=True, blank=True)
    # Dernier état connu (dénormalisé pour un affichage rapide côté parent).
    last_lat = models.FloatField(null=True, blank=True)
    last_lon = models.FloatField(null=True, blank=True)
    last_battery = models.IntegerField(null=True, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["label"]

    def set_sharing(self, on: bool):
        self.sharing_on = bool(on)
        self.sharing_changed_at = timezone.now()
        self.save(update_fields=["sharing_on", "sharing_changed_at"])


class Position(models.Model):
    """Historique des positions (purge selon POSITION_RETENTION_DAYS)."""
    device = models.ForeignKey(ChildDevice, on_delete=models.CASCADE, related_name="positions")
    lat = models.FloatField()
    lon = models.FloatField()
    battery = models.IntegerField(null=True, blank=True)
    recorded_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-recorded_at"]


class InstalledApp(models.Model):
    """Liste des apps installées sur l'appareil enfant (remplacée à chaque remontée)."""
    device = models.ForeignKey(ChildDevice, on_delete=models.CASCADE, related_name="apps")
    package = models.CharField(max_length=200)
    name = models.CharField(max_length=200, blank=True, default="")

    class Meta:
        unique_together = [("device", "package")]
        ordering = ["name", "package"]
