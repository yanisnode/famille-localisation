# Localisation famille — app de localisation d'enfants (transparente, consentie)

Projet SÉPARÉ de wifimobiletv. Pour localiser ses propres enfants mineurs, **au su de l'enfant**,
qui peut **couper le partage** à tout moment. Aucun fonctionnement caché.

## Principes (non négociables)
- L'enfant **voit** le partage (notification permanente Android / indicateur iOS) et peut le **couper**.
- Côté serveur, une remontée est **refusée** si l'enfant a coupé — aucun contournement.
- La recherche « par numéro » ne cherche **que parmi les appareils du parent connecté**, jamais un inconnu.
- Permission manquante → écran qui **propose** les réglages, sans forcer. Un refus est respecté.
- Le menu « Localisation famille » n'apparaît **que pour le compte parent** (super-admin).

## Arborescence
- `backend/`  Django + DRF (autonome, SQLite en dev). Tests : `python manage.py test`.
- `android/`  Squelette Kotlin (App Links, EncryptedSharedPreferences, foreground service, WorkManager).
- `ios/`      Squelette Swift (Universal Links, Keychain, CoreLocation, BGAppRefreshTask).

## Backend — démarrer
```
cd backend
python manage.py migrate
python manage.py createsuperuser        # compte Django du parent
python manage.py shell -c "from django.contrib.auth.models import User; from famille.models import ParentProfile; ParentProfile.objects.get_or_create(user=User.objects.first(), defaults={'display_name':'Parent'})"
python manage.py runserver
```
Créer un jeton d'accès parent (pour l'app parent / le dashboard) :
```
python manage.py drf_create_token <username>
```

## API (résumé)
Côté parent (en-tête `Authorization: Token <...>`) :
- `GET  /api/family/devices/`            mes appareils (option `?phone=` → recherche parmi les miens)
- `GET  /api/family/devices/<id>/`       fiche + positions + apps
- `GET/POST /api/family/invites/`        lister / créer une invitation d'enrôlement

Côté appareil enfant (`device_token`, pas de compte) :
- `POST /api/family/enroll/`   `{invite_token, platform}` → `{device_token}`
- `POST /api/family/ping/`     `{device_token, lat, lon, battery, apps[]}` (409 si partage coupé)
- `POST /api/family/sharing/`  `{device_token, on}` (l'enfant active/coupe)

## Ménage
`python manage.py purge_positions` — efface l'historique > `POSITION_RETENTION_DAYS` (30 j). À planifier chaque nuit.

## À compléter avant production
- Domaine réel + HTTPS ; remplacer `famille.example.com` partout.
- Android : empreinte SHA-256 du certificat dans `.well-known/assetlinks.json`.
- iOS : `TEAMID` réel dans `apple-app-site-association` ; publier ce fichier sous `/.well-known/` du domaine.
- Secret Django, base Postgres, `DEBUG=False`, `ALLOWED_HOSTS`.
