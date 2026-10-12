"""Ménage : efface l'historique de positions plus vieux que POSITION_RETENTION_DAYS.
À lancer chaque nuit (cron / timer systemd)."""
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from famille.models import Position


class Command(BaseCommand):
    help = "Efface les positions trop anciennes."

    def handle(self, *args, **opts):
        days = int(getattr(settings, "POSITION_RETENTION_DAYS", 30))
        cutoff = timezone.now() - timedelta(days=days)
        n, _ = Position.objects.filter(recorded_at__lt=cutoff).delete()
        self.stdout.write(f"purge_positions : {n} position(s) effacée(s) (> {days} j).")
