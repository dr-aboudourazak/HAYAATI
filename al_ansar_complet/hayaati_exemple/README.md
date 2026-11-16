# hayaati_exemple

Application d'exemple en Flutter pur : Al Ansâr, Madrassa et Le Coran, sans Flet ni Python. Elle teste les mêmes
paquets que HAYAATI (`al_ansar_flutter`, `hayaati_coran`, `hayaati_ui`), directement depuis `F:\al_ansar_complet`.

## Première mise en route (une seule fois)

Les dossiers `android\` et `windows\` sont générés par Flutter, pas fournis :

    cd F:\al_ansar_complet\hayaati_exemple
    flutter create --platforms=android,windows --project-name hayaati_exemple .
    flutter pub get

`flutter create .` ne touche ni `lib\main.dart` ni `pubspec.yaml` s'ils existent déjà dans le dossier (il ajoute les
fichiers de plateforme) : vérifiez tout de même avec `git status` ou en relisant `lib\main.dart`.

## Lancer

    flutter run -d windows        (ou)        flutter run -d <téléphone>

Pendant que l'application tourne : `r` recharge à chaud, `R` redémarre.

## Position GPS (mosquées proches)

Cet exemple ne branche pas le GPS. Pour le tester sur téléphone, il faudrait déclarer les permissions de localisation
dans `android\app\src\main\AndroidManifest.xml` et fournir `fluxPositionGeolocator` à `AlAnsarConfig`.
