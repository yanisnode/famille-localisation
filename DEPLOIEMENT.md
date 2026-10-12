# Déploiement — Localisation famille (sous-domaine, même VPS que wifimobiletv)

Backend servi sur **https://famille.wifimobiletv.com**, isolé dans ses propres conteneurs
(`famille-backend`, `famille-db`), derrière le **Caddy existant** de wifimobiletv.

## 0) DNS (chez ton registrar)
Créer un enregistrement **A** : `famille` → `184.174.36.141` (TTL court au début).
Vérifier : `ping famille.wifimobiletv.com` doit répondre cette IP.

## 1) Copier le dossier sur le VPS
Déposer `famille-localisation/` dans `/opt/` → `/opt/famille-localisation/`.

## 2) Réglages
```
cd /opt/famille-localisation
cp .env.famille.example .env.famille
nano .env.famille        # SECRET_KEY long, POSTGRES_PASSWORD solide, DATABASE_URL avec ce mdp
```
Vérifier le nom du réseau Docker de wifimobiletv et l'ajuster si besoin dans
`docker-compose.famille.yml` (clé networks → name) :
```
docker network ls | grep wifimobiletv
```

## 3) Greffer le bloc Caddy
Coller le contenu de `infra-caddy-famille.snippet` À LA FIN de
`/opt/wifimobiletv/infra/Caddyfile`, puis recharger Caddy SANS coupure :
```
docker exec wifimobiletv-caddy caddy reload --config /etc/caddy/Caddyfile
```
(Le certificat HTTPS de famille.wifimobiletv.com est obtenu automatiquement.)

## 4) Démarrer la pile famille
```
cd /opt/famille-localisation
docker compose -f docker-compose.famille.yml --env-file .env.famille up -d --build
```
Les migrations tournent au démarrage du conteneur.

## 5) Créer ton compte parent
```
docker compose -f docker-compose.famille.yml exec famille-backend python manage.py createsuperuser
docker compose -f docker-compose.famille.yml exec famille-backend \
  python manage.py shell -c "from django.contrib.auth.models import User; from famille.models import ParentProfile; u=User.objects.first(); ParentProfile.objects.get_or_create(user=u, defaults={'display_name': u.username})"
```

## 6) Vérifier
- Dashboard : https://famille.wifimobiletv.com/parent/  (connexion avec ton compte)
- Liens mobiles :
  - https://famille.wifimobiletv.com/.well-known/assetlinks.json
  - https://famille.wifimobiletv.com/.well-known/apple-app-site-association

## 7) Ménage automatique (positions > 40 j — ici 30 j par défaut)
Ajouter une tâche cron sur le VPS (chaque nuit 4h10) :
```
10 4 * * * cd /opt/famille-localisation && docker compose -f docker-compose.famille.yml exec -T famille-backend python manage.py purge_positions >> /var/log/famille-purge.log 2>&1
```

## Retour arrière (tout annuler, sans toucher wifimobiletv)
```
cd /opt/famille-localisation && docker compose -f docker-compose.famille.yml down
```
Puis retirer le bloc `famille.wifimobiletv.com { … }` du Caddyfile et recharger Caddy.
wifimobiletv n'est jamais modifié (seul un bloc Caddy est ajouté, réversible).

## Avant publication des apps mobiles (plus tard)
- Android : mettre l'empreinte réelle via la variable `ANDROID_SHA256` dans `.env.famille`.
- iOS : mettre le `IOS_TEAM_ID` réel dans `.env.famille`.
