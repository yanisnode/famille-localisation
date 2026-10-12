
## 2026-10-12 — App enfant : enrôlement manuel (coller le lien) + 1er ping immédiat
- CAUSE racine « enfant visible mais aucune position/apps » : l'APK de test n'a pas d'empreinte de signature fixe, donc le lien https d'invitation s'ouvre dans le NAVIGATEUR (page enroll web-test) au lieu de l'app. La fiche « web-test » apparaît côté parent mais ne ping jamais.
- FIX app Android :
  - MainActivity.infoScreen() : champ de saisie + bouton « Rejoindre la famille » ; on colle le lien complet (…/enroll?token=XXX) OU le code brut. extractToken() gère les deux. On ne dépend plus de l'App Link.
  - LocationWorker : kickNow() (OneTimeWork) = 1er envoi immédiat ; lastLocation() → repli getCurrentLocation(HIGH_ACCURACY) si pas de cache (évite la remontée vide).
  - LocationService.onStartCommand() : kickNow() avant schedule().
- Parcours corrigé : ouvrir l'app directement → coller le lien → consentement → permission « Toujours » → position/apps remontent tout de suite.
- À faire côté user : supprimer la fiche fantôme « web-test » dans le tableau de bord parent.
