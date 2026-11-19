# al_ansar (module Flutter)

Module Al Ansâr de HAYAATI : annuaire (madrassas, boutique, accompagnement), cours avec jours et
horaires, recherche dans un autre pays ou une autre ville, mosquées proches pour les voyageurs,
propositions de nouvelles mosquées et corrections de position.

## Charte graphique HAYAATI

- Palette : `lib/src/commun/gui/theme/palette.dart`, copie exacte de `gui/palette_hayaati.py` (test `charte_test.dart`).
- Thème : `themeHayaati()`, appliqué par le module lui-même, donc identique en essai autonome et dans HAYAATI.
  Bandeau vert profond (`#064E3B`) comme la barre d'outils, fond sable, cartes blanches, texte `#2B1607`,
  accents terracotta (actions) et ocre (progression, filtres).
- Icône : `assets/images/Icone-Hayaati.png`, le même fichier que la barre d'outils de l'application.
- Icône de lancement de l'application d'essai : `assets/icon/icon.png` de HAYAATI.
- Police arabe : `NotoSansArabic`, déclarée par l'hôte Flet (déjà le cas) ou par l'exemple.

Toute nouvelle couleur doit venir de `PaletteHayaati`, jamais d'un code hexadécimal en dur.

## Essai autonome

```powershell
$flutter = "C:\Users\gebruiker\flutter\3.44.7\bin\flutter.bat"
cd F:\al_ansar_complet\al_ansar_flutter
& $flutter pub get
& $flutter analyze
& $flutter test

cd example
& $flutter pub get
& "C:\Users\gebruiker\flutter\3.44.7\bin\dart.bat" run flutter_launcher_icons   # icône HAYAATI (Android et Windows)
& $flutter run -d <identifiant>               # GPS réel de l'appareil
& $flutter run -d <identifiant> --dart-define=POS=10.8627,0.2076   # position simulée à Dapaong
```

### Réglages Android (une seule fois)

```powershell
cd F:\al_ansar_complet\al_ansar_flutter\example
powershell -ExecutionPolicy Bypass -File F:\al_ansar_complet\al_ansar_flutter\example\preparer_android.ps1
```

Le script ajoute au manifeste les permissions Internet et localisation, et renomme l'application « HAYAATI ».
Sans lui, Android n'accorde aucune permission et le relevé GPS échoue : le module l'indique par
« permissions non déclarées dans le manifeste ». Dans HAYAATI, les permissions viennent déjà de `flet_geolocator`.

## Positions des mosquées et propositions

- Chaque position a une source (`releve_sur_place`, `communaute`, `openstreetmap`, `estimee`), une précision
  en mètres si connue, et un indicateur « vérifiée ». Tant qu'elle ne l'est pas, la liste affiche « position à vérifier ».
- « Proposer une mosquée » (bouton + de l'écran des mosquées) et « Corriger la position » (menu de chaque mosquée) :
  l'utilisateur se place à l'entrée, relève le GPS, puis envoie un message WhatsApp au responsable
  (ou le copie s'il n'y a pas de numéro). Il voit le message avant l'envoi ; rien ne part sans son geste.
- Le responsable traite le message avec `traiter_proposition.py` (voir LISEZMOI.md à la racine).

## Lieu de recherche

« Autour de moi » (GPS), une ville, ou tout le pays. En mode « autour de moi », les fiches sont classées par distance
(rayon 10, 50, 200 km ou tous), les services à distance suivent. L'écran des mosquées part du GPS tant que
l'utilisateur n'a pas choisi une ville. Hadj et Omra : forfaits à fiche de coûts standardisée, score de transparence
et comparateur (jusqu'à 3 forfaits).

## Madrassa (apprentissage) en Flutter

Hub Madrassa, Encyclopédie avec quiz et badges, Langue arabe (alphabet, vocabulaire, conjugaison, grammaire, lecture), Sciences islamiques
(91 leçons, chronologies) et Caravane du Savoir. Le contenu et la progression viennent de l'hôte (`MadrassaHote`) : dans HAYAATI, des fichiers de langue
et du SyncEngine ; dans l'exemple, `assets/al_ansar/madrassa_demo.json` (copie française). Aucune traduction n'est dupliquée.

Les moteurs Python (`jeu_educatif_engine`, `langue_arabe_engine`, `caravane_savoir_engine`) sont portés à l'identique dans `lib/src/fonctionnalites/madrassa/core/moteurs.dart`.
`test/madrassa_moteurs_test.dart` rejoue des cas générés par les moteurs Python (`test/fixtures/madrassa_vecteurs.json`) : si un moteur Python évolue,
régénérez les vecteurs et mettez le port à jour. Pour ouvrir l'exemple sur Madrassa : `flutter run -d <identifiant> --dart-define=ECRAN=madrassa`.

## Mode démo

`AlAnsarConfig.modeDemo` : `null` (défaut) suit les données : un fichier marqué `"demonstration": true` affiche ses fiches fictives ; `true` affiche aussi les
brouillons ; `false` les masque. Les fichiers réels n'ont pas ce drapeau, et `valider_annuaire.py --production` refuse les fichiers de démonstration.

## Principes techniques

- Données : `manifest.json` (léger), puis `annuaire_XX.json` et `mosquees_XX.json`, téléchargés seulement si la
  version a augmenté, vérifiés par empreinte SHA-256, mis en cache. Un seul pays en mémoire à la fois.
- La position GPS de départ vient de l'hôte (HAYAATI la connaît déjà pour les heures de prière). Pour relever
  une position sur place, l'hôte fournit une fonction `fournisseurPosition` (flet_geolocator dans HAYAATI,
  geolocator dans l'exemple).
- Si la position tombe dans un autre pays du manifeste (`bbox`), ce pays est chargé automatiquement.
- Itinéraire : lien `geo:` ouvert dans l'application de cartes de l'utilisateur.

## Reste à faire

- Intégration Flet : contrôle Python, passage de langue, position et fonction de relevé GPS, bouton retour Android.
- Traduction du haoussa (`ha`), relecture de l'arabe.
- Écrans Boutique et Accompagnement plus riches (filtres propres à chaque service).
- Photos des fiches (WebP réduit) avec chargement paresseux.
- Phase 1 : propositions reçues par un serveur (Supabase) avec vote de confirmation par plusieurs utilisateurs.
