# Brancher Al Ansâr dans HAYAATI (Flet 0.86.5)

## À lire avant chaque nouvelle livraison : deux endroits peuvent rester périmés

Votre `pyproject.toml` installe l'extension depuis `file:///F:/hayaati_alnsar` (comme `hayaati-alarm` depuis `F:/hayaati_alarm`). Une livraison dézippée
ailleurs (par exemple `F:\al_ansar_complet`) ne met donc **pas** à jour ce que HAYAATI construit. Deux couches à garder à jour :

1. **L'endroit d'installation** (`F:\hayaati_alnsar`) : il doit contenir l'extension de la livraison.
2. **Le cache de `flet build`** : si les dépendances n'ont pas changé, `flet build` réutilise `build\flutter-packages` du build précédent
   (code Dart et données de l'extension inclus). Les textes de langue, côté Python de l'application, se mettent à jour, pas l'extension :
   c'est ce qui donnait « traductions corrigées, mais toujours pas de Hadj et Omra ni de contenu d'exemple ».

Une seule commande vérifie les deux et corrige :

```powershell
cd F:\al_ansar_complet\integration_flet
python diagnostic_installation.py F:\chemin\vers\HAYAATI             # diagnostic seul
python diagnostic_installation.py F:\chemin\vers\HAYAATI --corriger  # recopie l'extension dans F:\hayaati_alnsar et vide le cache
```

Ensuite, reconstruisez avec `build_android.ps1`. Après le build, l'accueil d'Al-Ansâr (mode démo) affiche en bas :
`Module 0.4.0 · données : embarqué v4 · 4 fiches (4 visibles) · 2 forfaits · démo : oui`. Si la ligne manque ou si la version diffère, l'ancien module tourne encore.
La console affiche aussi `[AL-ANSÂR] extension hayaati-alnsar 0.4.0 chargée`.

**Faut-il ajouter `[tool.flet.dev_packages]` ?** Non, pas nécessairement. Ce n'est pas un doublon : Flet ne crée pas une seconde dépendance, il remplace la
source de la ligne `hayaati-alnsar` déjà présente dans `dependencies` (la ligne doit rester, avec exactement ce nom). Mais il force une réinstallation
complète de tous les paquets Python à chaque build, sans cache : plus long sur une machine de 3 Go. Utilisez plutôt `diagnostic_installation.py --corriger`
à chaque livraison. Si vous préférez `dev_packages`, écrivez le chemin avec des `/` ou entre apostrophes (`'F:\...'`) : dans un TOML, `"\a"` est une erreur.

## Ce que contient `integration_flet`

| Élément | Rôle |
|---|---|
| `hayaati_alnsar/` | Extension Flet (comme `hayaati_alarm`) : contrôle Python `HayaatiAlAnsar` + pont Dart, avec le module Flutter embarqué dans `src/flutter/hayaati_alnsar/packages/al_ansar/` |
| `diagnostic_installation.py` | Détecte un cache `flet build` périmé et le vide (`--nettoyer`) |
| `synchroniser_module.py` | Recopie `../al_ansar_flutter` dans l'extension (à relancer après toute modification du module ; `--verifier` contrôle la copie) |
| `HAYAATI_patch/appliquer_integration.py` | Modifie HAYAATI : écrans, barre à 5 boutons, bouton retour, textes traduits |
| `HAYAATI_patch/gui/pages/` | `page_alansar.py` et `page_hub_simple.py` (hubs Calculs et Mon espace) |
| `HAYAATI_patch/ajouts_locales.json` | Textes fr, en, ar, ha (générés depuis `i18n.dart`) |

## Étapes

1. **Tester le module seul d'abord** (voir `al_ansar_flutter/README.md`) : `flutter analyze`, `flutter test`, `flutter run`.
2. **Installer l'extension** comme `hayaati-alarm` : copiez `hayaati_alnsar/` à côté de `hayaati_alarm/` dans votre dépôt, puis
   déclarez-la dans l'application de la même façon (dépendance locale du projet et de l'environnement de build).
3. **Brancher HAYAATI** (une fois, relançable sans danger) :
   ```powershell
   python HAYAATI_patch\appliquer_integration.py F:\chemin\vers\HAYAATI
   ```
   Chaque fichier modifié est sauvegardé une fois en `.avant_alansar`.
4. **Régler `gui/pages/page_alansar.py`** :
   - `URL_DONNEES_AL_ANSAR` : adresse où vous publiez `manifest.json`, `annuaire_TG.json`, `mosquees_TG.json` (terminée par `/`). Vide : données embarquées seulement.
   - `MODE_DEMO_AL_ANSAR = False` pour la publication : les fiches « brouillon » et fictives disparaissent.
5. **Reconstruire** avec `build_android.ps1` (comme d'habitude, caches sur F:).

## Ce que fait l'intégration

- Barre à 5 boutons validée : visiteur = Accueil, Prière, Coran, **Calculs** (Zakat, Succession), **Al-Ansâr** ; connecté = Accueil, Prière, Coran, **Mon espace** (Devoirs, Inventaire), **Al-Ansâr**. Le bouton d'un hub reste en surbrillance dans ses sous-écrans.
- Madrassa devient un raccourci en tête de l'accueil d'Al-Ansâr.
- **Langue** : la page transmet la langue active et la section `al_ansar` du fichier de langue. Les textes manquants retombent sur le français. Le haoussa (23 textes) est à relire par vos soins ; ajoutez les autres textes de la section `al_ansar` de `ha.json` au fur et à mesure.
- **Position** : le module reprend la dernière position connue de HAYAATI (cache des heures de prière) et relève le GPS lui-même quand l'utilisateur choisit « Autour de moi » ou propose une mosquée. Les permissions de localisation sont déjà celles de `flet_geolocator`.
- **Retour Android** : si Al-Ansâr a des écrans empilés, le retour en ferme un ; sinon HAYAATI reprend la main comme avant.

## Langues : toutes complètes

Les textes d'Al Ansâr ont une source unique, `al_ansar_flutter/traductions/al_ansar.json` (fr, en, ar, ha : 157 textes dans chaque langue).
`appliquer_integration.py` les écrit dans la section `al_ansar` de chaque fichier de langue de HAYAATI et **signale toute langue de HAYAATI
qui n'a pas encore ses textes** (votre dépôt public n'en contient que quatre ; si votre version locale en a davantage, ajoutez-les : voir
`al_ansar_flutter/traductions/README.md`). Un texte manquant dans une langue empêche la génération et fait échouer `flutter test` :
la dette de traduction ne peut plus s'accumuler. L'arabe et le haoussa sont des propositions à faire relire.

## Sans adresse de publication (cas actuel)

Vous pouvez construire et tester la version fusionnée dès maintenant avec `build_android.ps1` :

- Laissez `URL_DONNEES_AL_ANSAR = ""` et `MODE_DEMO_AL_ANSAR = True` dans `gui/pages/page_alansar.py`.
- Le module lit alors les données embarquées dans l'extension (fiches fictives : une madrassa, une librairie, un cabinet,
  une agence Hadj et Omra avec deux forfaits, quatre mosquées). Le mode démo les rend visibles.
- Tout fonctionne : Autour de moi, filtres, comparateur Hadj et Omra, relevé GPS, propositions de mosquées.
- Ce qui attend l'adresse : les mises à jour de données et le changement de pays automatique pour un voyageur
  (il lit le manifeste). Le choix d'un autre pays propose pour l'instant le seul Togo.
- Les propositions de mosquées n'ont pas de numéro de responsable dans les données embarquées : le bouton **copie** le message.
  Pour tester l'envoi WhatsApp, ajoutez dans `src/flutter/hayaati_alnsar/assets/al_ansar/mosquees_TG.json` la ligne
  `"moderation": {"whatsapp": "+228XXXXXXXX"}` avec votre numéro, puis reconstruisez.
- Quand le site Cloudflare existera : `publication_cloudflare/README.md`, puis renseigner `URL_DONNEES_AL_ANSAR`.

## Aspect de la page dans HAYAATI

Le contrôle est en mode `integre` : pas de second bandeau vert (celui de HAYAATI reste le seul), un titre « Al Ansâr » en tête de page,
et des écrans internes avec un bandeau clair et la flèche de retour.

## Erreur de build « The generated bindings expect package:jni ^1.1.0, but 1.0.x was imported »

Constat sur votre build du 25/10 : l'extension est bien installée et compilée (« Found Flutter extension at ...\hayaati_alnsar »), mais pub a
résolu `shared_preferences_android 2.5.3`, qui utilise Pigeon JNI depuis la version 2.5.0 et exige `jni ^1.1.0`, alors que Flet 0.86.5 impose `jni 1.0.0`.
C'est le même piège que celui que vous aviez déjà documenté dans `pyproject.toml` pour `path_provider_android`. Il est apparu maintenant parce que la
résolution des dépendances a été refaite à neuf après le nettoyage du cache.

Ajoutez dans `pyproject.toml`, sous `[tool.flet.flutter.pubspec.dependency_overrides]` (à côté de `path_provider_android`) :

```toml
shared_preferences_android = "2.3.4"
```

**2.3.4 est la version que vous avez validée : votre build a abouti avec elle.** Mes propositions précédentes (`2.4.29`, puis `>=2.4.0 <2.5.0`) étaient
fondées sur un changelog et n'ont pas été éprouvées ; `appliquer_integration.py` ne touche plus à une valeur déjà présente, sauf l'ancienne `2.4.29`.
Si une erreur identique apparaît pour un autre plugin (`xxx_android ... expect package:jni ^1.1.0`), même remède : épingler ce plugin sur sa dernière version
antérieure à la migration JNI ; envoyez-moi le nom du paquet.

**Sauvegardes** : le script sauvegarde chaque fichier modifié une seule fois dans `F:\sauvegardes_alansar\<projet>\` (hors du projet : dans `gui\` ou `assets\`,
elles seraient embarquées dans l'APK). Les anciens `*.avant_alansar` laissés dans le projet par la version précédente sont déplacés automatiquement.

## Madrassa en Flutter

L'écran « MADRASSA » est maintenant le hub Madrassa du module Flutter (Encyclopédie et quiz, Langue arabe en six étapes, Sciences islamiques, Caravane du Savoir).
Le contenu vient des fichiers de langue de HAYAATI (aucune copie, aucune dette de traduction) ; la progression reste dans le SyncEngine, au même format.
Les trois moteurs Python sont portés en Dart à l'identique et testés contre eux (`flutter test` rejoue des cas générés par les moteurs Python).
L'ancien écran Python (`page_madrassa.py`) reste dans le code, non utilisé : vous pourrez le supprimer quand la version Flutter sera validée.

## Si les données du Togo n'apparaissent pas

Le mode démo suit désormais **les données** : les fichiers d'exemple portent `"demonstration": true` et affichent leurs fiches fictives sans dépendre d'un réglage
transmis par Flet. Un fichier réel (sans ce drapeau) n'affiche que les fiches publiées. En mode démo, le bas de l'accueil affiche par exemple
`Module 0.4.0 · données : embarqué v4 · 4 fiches (4 visibles) · 2 forfaits · démo : oui` ; si une liste est vide parce que des brouillons sont masqués, elle l'indique.


Cause trouvée sur votre test : Flet n'envoie pas à Dart les propriétés restées à leur valeur par défaut ; le dossier des données embarquées
était donc cherché au mauvais endroit. C'est corrigé. En mode démo, si les données restent introuvables, l'accueil d'Al Ansâr affiche
« Détail technique : » avec le chemin exact essayé : envoyez-moi cette ligne.

## Points à surveiller au premier build

- **Résolution des dépendances Dart** : le module utilise `geolocator` (">=13.0.0"), `http`, `crypto`, `path_provider`, `url_launcher`. Si `flet_geolocator` impose une autre version de `geolocator`, le message de `pub get` l'indique ; envoyez-le moi.
- **Mémoire** : le module n'ajoute que du code Dart. La RAM de HAYAATI ne baissera qu'avec la migration progressive hors de Python.
- **Données de démonstration** : les fichiers embarqués sont fictifs ; ils ne s'affichent qu'avec `MODE_DEMO_AL_ANSAR = True`.

## Si une étape échoue

Envoyez la sortie complète de la commande (surtout `appliquer_integration.py` ou `flutter pub get` dans le dossier de build).
