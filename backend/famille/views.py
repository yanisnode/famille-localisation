"""Localisation famille — API.

Deux familles d'endpoints :
  • CÔTÉ PARENT (super-admin) : auth par Token Django, ne voit QUE ses propres appareils
    (isolation stricte via request.user.parent_profile). Menu réservé au parent.
  • CÔTÉ APPAREIL ENFANT : auth par device_token (pas de compte), sert à enrôler, à
    remonter la position (ping) et à couper/reprendre le partage (consentement visible).

Règles non négociables : aucune remontée n'est acceptée si l'enfant a coupé le partage
(sharing_on = False) ; la recherche « par numéro » ne cherche QUE parmi les appareils du
parent connecté — jamais un numéro inconnu.
"""
import os

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ChildDevice, EnrollInvite, InstalledApp, ParentProfile, Position
from .serializers import AppSerializer, DeviceSerializer, InviteSerializer, PositionSerializer


def _parent(request):
    """Profil parent du compte connecté, ou None (→ accès refusé au menu super-admin)."""
    return ParentProfile.objects.filter(user=request.user).first()


# ───────────────────────── CÔTÉ PARENT (super-admin) ─────────────────────────
class DeviceListView(APIView):
    """GET : mes appareils. Recherche optionnelle ?phone= PARMI MES appareils seulement."""
    def get(self, request):
        parent = _parent(request)
        if parent is None:
            return Response({"detail": "Réservé au compte parent."}, status=403)
        qs = ChildDevice.objects.filter(parent=parent)
        phone = (request.query_params.get("phone") or "").strip()
        if phone:
            digits = "".join(c for c in phone if c.isdigit())
            qs = [d for d in qs if "".join(c for c in d.phone if c.isdigit()).endswith(digits[-8:])] if digits else []
        return Response(DeviceSerializer(qs, many=True).data)


class DeviceDetailView(APIView):
    """GET : une fiche appareil + dernières positions + apps (si le partage est actif)."""
    def get(self, request, pk):
        parent = _parent(request)
        if parent is None:
            return Response({"detail": "Réservé au compte parent."}, status=403)
        device = get_object_or_404(ChildDevice, pk=pk, parent=parent)
        data = DeviceSerializer(device).data
        data["positions"] = PositionSerializer(device.positions.all()[:50], many=True).data
        data["apps"] = AppSerializer(device.apps.all(), many=True).data
        return Response(data)


class InviteView(APIView):
    """POST : créer une invitation (lien d'enrôlement) pour un enfant. GET : lister."""
    def get(self, request):
        parent = _parent(request)
        if parent is None:
            return Response({"detail": "Réservé au compte parent."}, status=403)
        return Response(InviteSerializer(parent.invites.all(), many=True).data)

    def post(self, request):
        parent = _parent(request)
        if parent is None:
            return Response({"detail": "Réservé au compte parent."}, status=403)
        label = (request.data.get("child_label") or "").strip()
        if not label:
            return Response({"detail": "Nom de l'enfant requis."}, status=400)
        inv = EnrollInvite.objects.create(parent=parent, child_label=label,
                                          phone=(request.data.get("phone") or "").strip())
        return Response(InviteSerializer(inv).data, status=201)


# ─────────────────────── CÔTÉ APPAREIL ENFANT (device_token) ───────────────────────
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def enroll(request):
    """L'app enfant échange un token d'invitation (vu et accepté par l'enfant) contre un
    device_token durable. L'appareil apparaît alors dans le compte parent."""
    token = (request.data.get("invite_token") or "").strip()
    inv = EnrollInvite.objects.filter(token=token, used_at__isnull=True).first()
    if inv is None:
        return Response({"detail": "Invitation invalide ou déjà utilisée."}, status=400)
    device = ChildDevice.objects.create(
        parent=inv.parent, label=inv.child_label, phone=inv.phone,
        platform=(request.data.get("platform") or "").strip()[:10],
    )
    inv.used_at = timezone.now()
    inv.save(update_fields=["used_at"])
    return Response({"device_token": device.device_token, "device_id": device.id,
                     "label": device.label}, status=201)


def _device_from_token(request):
    tok = (request.data.get("device_token") or request.query_params.get("device_token") or "").strip()
    return ChildDevice.objects.filter(device_token=tok).first()


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def ping(request):
    """Remontée périodique depuis l'app enfant : position + batterie + liste d'apps.
    REFUSÉE si l'enfant a coupé le partage — aucun contournement."""
    device = _device_from_token(request)
    if device is None:
        return Response({"detail": "Appareil inconnu."}, status=401)
    if not device.sharing_on:
        return Response({"detail": "Partage coupé par l'enfant.", "sharing_on": False}, status=409)
    try:
        lat = float(request.data["lat"]); lon = float(request.data["lon"])
    except (KeyError, TypeError, ValueError):
        return Response({"detail": "lat/lon requis."}, status=400)
    battery = request.data.get("battery")
    battery = int(battery) if battery not in (None, "") else None
    Position.objects.create(device=device, lat=lat, lon=lon, battery=battery)
    device.last_lat, device.last_lon = lat, lon
    device.last_battery, device.last_seen_at = battery, timezone.now()
    device.save(update_fields=["last_lat", "last_lon", "last_battery", "last_seen_at"])
    apps = request.data.get("apps")
    if isinstance(apps, list):
        InstalledApp.objects.filter(device=device).delete()
        InstalledApp.objects.bulk_create([
            InstalledApp(device=device, package=str(a.get("package", ""))[:200],
                         name=str(a.get("name", ""))[:200])
            for a in apps if a.get("package")])
    return Response({"ok": True})


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def set_sharing(request):
    """L'enfant active/coupe le partage depuis son app (bouton visible)."""
    device = _device_from_token(request)
    if device is None:
        return Response({"detail": "Appareil inconnu."}, status=401)
    device.set_sharing(bool(request.data.get("on", True)))
    return Response({"sharing_on": device.sharing_on})


# ─────────────────────── Vérification des liens (App Links / Universal Links) ───────────────────────
from django.http import JsonResponse  # noqa: E402


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def assetlinks(request):
    """Android App Links. Remplacer l'empreinte SHA-256 par celle du certificat de signature."""
    sha = os.environ.get("ANDROID_SHA256", "REMPLACER_PAR_EMPREINTE_SHA256")
    return JsonResponse([{
        "relation": ["delegate_permission/common.handle_all_urls"],
        "target": {"namespace": "android_app",
                   "package_name": "com.famille.localisation",
                   "sha256_cert_fingerprints": [sha]},
    }], safe=False)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def aasa(request):
    """iOS Universal Links. Remplacer TEAMID par l'identifiant de l'équipe Apple."""
    team = os.environ.get("IOS_TEAM_ID", "TEAMID")
    return JsonResponse({"applinks": {"apps": [], "details": [
        {"appID": f"{team}.com.famille.localisation", "paths": ["/enroll*"]}]}})
