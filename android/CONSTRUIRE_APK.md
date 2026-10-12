# Construire l'APK de l'app enfant (Android)

Le code complet est prêt. La compilation se fait sur un PC avec **Android Studio**
(gratuit). Une seule personne (toi) fait ça une fois ; ensuite tu copies l'APK sur
les téléphones des enfants.

## 1) Installer Android Studio
- Télécharge Android Studio (gratuit) et installe-le. Au premier lancement, laisse-le
  télécharger le « Android SDK » (il propose tout seul).

## 2) Ouvrir le projet
- Android Studio → **Open** → choisis le dossier `famille-localisation/android`.
- Il va « synchroniser Gradle » (télécharge les dépendances). Laisse finir (quelques minutes
  la 1ʳᵉ fois). S'il propose de mettre à jour le plugin Gradle, accepte.

## 3) Générer l'APK
- Menu **Build → Build Bundle(s) / APK(s) → Build APK(s)**.
- Quand c'est fini, un message « locate » apparaît : l'APK est dans
  `android/app/build/outputs/apk/debug/app-debug.apk`.

## 4) Installer sur le téléphone de l'enfant
- Copie `app-debug.apk` sur le téléphone (câble USB, WhatsApp, e-mail…).
- Sur le téléphone : ouvre le fichier → autorise « installer des applications inconnues »
  (Android le demande) → installe.

## 5) Enrôler
- Depuis ton espace parent, crée une invitation (bouton « Enrôler un enfant »).
- Envoie le lien `https://famille.wifimobiletv.com/enroll?token=...` à l'enfant.
- Sur le téléphone de l'enfant, **ouvre le lien** : comme l'app est installée, Android
  propose de l'ouvrir avec « Famille ». L'enfant voit l'écran d'accueil → accepte →
  autorise la position (« Toujours autoriser ») → le partage démarre.

## Important (transparence / stores)
- Cet APK n'est PAS sur le Play Store : installation directe, gratuite, usage familial.
- L'enfant voit une **notification permanente** pendant le partage et peut le mettre en
  **pause** à tout moment ; un refus de permission est respecté.
- Vérification du lien automatique (App Links) : pour que le lien ouvre l'app SANS passer
  par le navigateur, il faut mettre l'empreinte SHA-256 de ta signature dans
  `famille.wifimobiletv.com/.well-known/assetlinks.json`. Tant que ce n'est pas fait, le
  lien ouvre la page web (bouton pour ouvrir l'app). Pour un usage familial, l'ouverture
  manuelle suffit — on pourra régler l'empreinte plus tard si tu veux l'automatique.
