"""Localisation famille — tests. Couvre : enrôlement par lien, ping, recherche par
numéro (isolée au parent), coupure du partage par l'enfant (honnête, refus serveur),
purge de l'historique, et isolation stricte entre parents."""
from datetime import timedelta
from unittest import mock

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import ChildDevice, EnrollInvite, ParentProfile, Position


def _parent(username):
    u = User.objects.create_user(username=username, password="x")
    p = ParentProfile.objects.create(user=u, display_name=username)
    api = APIClient()
    api.credentials(HTTP_AUTHORIZATION="Token " + Token.objects.create(user=u).key)
    return p, api


class EnrollTests(TestCase):
    def test_invite_then_enroll_links_device(self):
        parent, api = _parent("yanis")
        r = api.post("/api/family/invites/", {"child_label": "Awa", "phone": "0782000000"})
        self.assertEqual(r.status_code, 201)
        token = r.data["token"]
        pub = APIClient()
        r2 = pub.post("/api/family/enroll/", {"invite_token": token, "platform": "android"})
        self.assertEqual(r2.status_code, 201)
        self.assertTrue(r2.data["device_token"])
        self.assertEqual(ChildDevice.objects.get().parent, parent)

    def test_invite_token_single_use(self):
        parent, api = _parent("yanis")
        token = api.post("/api/family/invites/", {"child_label": "Awa"}).data["token"]
        pub = APIClient()
        self.assertEqual(pub.post("/api/family/enroll/", {"invite_token": token}).status_code, 201)
        self.assertEqual(pub.post("/api/family/enroll/", {"invite_token": token}).status_code, 400)


class PingTests(TestCase):
    def setUp(self):
        self.parent, self.api = _parent("yanis")
        self.dev = ChildDevice.objects.create(parent=self.parent, label="Awa", phone="0782000000")

    def _ping(self, **kw):
        body = {"device_token": self.dev.device_token, "lat": 48.1, "lon": 2.3, "battery": 74}
        body.update(kw)
        return APIClient().post("/api/family/ping/", body, format="json")

    def test_ping_records_position(self):
        self.assertEqual(self._ping().status_code, 200)
        self.dev.refresh_from_db()
        self.assertEqual(self.dev.last_battery, 74)
        self.assertEqual(Position.objects.filter(device=self.dev).count(), 1)

    def test_ping_refused_when_child_paused_sharing(self):
        self.dev.set_sharing(False)
        r = self._ping()
        self.assertEqual(r.status_code, 409)           # honnête : refus, pas de contournement
        self.assertEqual(Position.objects.count(), 0)

    def test_ping_replaces_app_list(self):
        self._ping(apps=[{"package": "com.youtube", "name": "YouTube"}])
        self._ping(apps=[{"package": "com.whatsapp", "name": "WhatsApp"}])
        self.assertEqual(list(self.dev.apps.values_list("package", flat=True)), ["com.whatsapp"])

    def test_unknown_device_token_rejected(self):
        self.assertEqual(APIClient().post("/api/family/ping/",
                         {"device_token": "nope", "lat": 1, "lon": 1}, format="json").status_code, 401)


class SharingTests(TestCase):
    def test_child_can_pause_and_resume(self):
        parent, _ = _parent("yanis")
        dev = ChildDevice.objects.create(parent=parent, label="Awa")
        pub = APIClient()
        pub.post("/api/family/sharing/", {"device_token": dev.device_token, "on": False}, format="json")
        dev.refresh_from_db(); self.assertFalse(dev.sharing_on)
        pub.post("/api/family/sharing/", {"device_token": dev.device_token, "on": True}, format="json")
        dev.refresh_from_db(); self.assertTrue(dev.sharing_on)


class SearchAndIsolationTests(TestCase):
    def test_search_by_phone_only_my_devices(self):
        p1, api1 = _parent("yanis")
        p2, _ = _parent("autre")
        ChildDevice.objects.create(parent=p1, label="Awa", phone="0782000000")
        ChildDevice.objects.create(parent=p2, label="Zoe", phone="0782000000")  # même numéro, autre parent
        r = api1.get("/api/family/devices/?phone=0782000000")
        self.assertEqual(len(r.data), 1)
        self.assertEqual(r.data[0]["label"], "Awa")

    def test_parent_cannot_open_other_parents_device(self):
        p1, api1 = _parent("yanis")
        p2, _ = _parent("autre")
        d2 = ChildDevice.objects.create(parent=p2, label="Zoe")
        self.assertEqual(api1.get(f"/api/family/devices/{d2.id}/").status_code, 404)

    def test_non_parent_account_denied(self):
        u = User.objects.create_user(username="sans_profil", password="x")
        api = APIClient()
        api.credentials(HTTP_AUTHORIZATION="Token " + Token.objects.create(user=u).key)
        self.assertEqual(api.get("/api/family/devices/").status_code, 403)

    def test_paused_device_reports_status(self):
        p1, api1 = _parent("yanis")
        d = ChildDevice.objects.create(parent=p1, label="Awa", phone="07")
        d.set_sharing(False)
        r = api1.get("/api/family/devices/?phone=07")
        self.assertEqual(r.data[0]["status"], "paused")


class PurgeTests(TestCase):
    def test_purge_removes_old_positions(self):
        parent, _ = _parent("yanis")
        dev = ChildDevice.objects.create(parent=parent, label="Awa")
        old = Position.objects.create(device=dev, lat=1, lon=1)
        Position.objects.filter(pk=old.pk).update(recorded_at=timezone.now() - timedelta(days=40))
        Position.objects.create(device=dev, lat=2, lon=2)
        call_command("purge_positions")
        self.assertEqual(Position.objects.count(), 1)


class ParentWebTests(TestCase):
    def test_login_returns_token(self):
        User.objects.create_user(username="yanis", password="secret")
        r = APIClient().post("/api/family/login/", {"username": "yanis", "password": "secret"})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data["token"])

    def test_login_bad_password(self):
        User.objects.create_user(username="yanis", password="secret")
        r = APIClient().post("/api/family/login/", {"username": "yanis", "password": "nope"})
        self.assertEqual(r.status_code, 400)

    def test_parent_page_served(self):
        r = APIClient().get("/parent/")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Localisation famille", r.content)

    def test_device_detail_lists_all_apps(self):
        from .models import ChildDevice, InstalledApp
        parent, api = _parent("yanis2")
        dev = ChildDevice.objects.create(parent=parent, label="Awa")
        InstalledApp.objects.bulk_create([
            InstalledApp(device=dev, package=f"com.app{i}", name=f"App {i}") for i in range(40)])
        r = api.get(f"/api/family/devices/{dev.id}/")
        self.assertEqual(len(r.data["apps"]), 40)        # liste COMPLÈTE, pas tronquée
