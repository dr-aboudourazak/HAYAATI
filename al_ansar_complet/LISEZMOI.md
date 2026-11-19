# Al Ansâr : livraison complète

## Mise en place

```powershell
cd F:\al_ansar_complet
Expand-Archive -Force <chemin>\al_ansar_complet.zip .
# Ancienne organisation à plat : ces fichiers vivent désormais dans donnees\
Remove-Item al_ansar_annuaire.schema.json, al_ansar_proposition.schema.json, annuaire_TG.exemple.json, mosquees_TG.exemple.json, manifest.exemple.json, valider_annuaire.py, traiter_proposition.py, LISEZMOI.md.bak -ErrorAction SilentlyContinue
```
`-Force` conserve les dossiers `android` et `windows` déjà générés dans `al_ansar_flutter\example`.

## Organisation

| Dossier | Contenu |
|---|---|
| `donnees\` | Schémas, exemples fictifs, `valider_annuaire.py`, `traiter_proposition.py`, `publier_donnees.py` |
| `al_ansar_flutter\` | Module Flutter, tests, application d'essai (`example\`) |
| `integration_flet\` | Extension Flet `hayaati-alnsar` et script d'intégration à HAYAATI (`INSTALLATION.md`) |
| `publication_cloudflare\` | Procédure et dossier `site\` à mettre en ligne (`README.md`) |

## Les trois étapes, dans l'ordre

1. **Application d'essai** (`al_ansar_flutter\README.md`). Sur Android, lancer une fois `example\preparer_android.ps1` : sans lui, l'application n'a aucune permission et le GPS échoue.
2. **Fusion avec HAYAATI** (`integration_flet\INSTALLATION.md`). L'adresse de publication n'est pas nécessaire pour ce test : voir la section « Sans adresse de publication ».
3. **Publication des données** (`publication_cloudflare\README.md`), quand le site Cloudflare existe.

## Important : où HAYAATI installe l'extension, et le cache de `flet build`

HAYAATI installe l'extension depuis le dossier indiqué dans son `pyproject.toml` (`F:/hayaati_alnsar`), pas depuis ce zip, et `flet build` peut réutiliser un cache périmé.
Après chaque livraison : `python integration_flet\diagnostic_installation.py <projet HAYAATI> --corriger`, puis `build_android.ps1`. Détails dans `integration_flet\INSTALLATION.md`.

## Madrassa en Flutter

Le hub Madrassa (Encyclopédie, Langue arabe, Sciences islamiques, Caravane du Savoir) est dans le module Flutter, au même format de progression que l'ancien écran Python.
`integration_flet\\INSTALLATION.md` explique le branchement ; `al_ansar_flutter\\README.md` les moteurs et leurs tests de parité avec Python.

## Traductions

Source unique : `al_ansar_flutter\traductions\al_ansar.json` (voir son `README.md`). Chaque texte doit exister dans toutes les langues, sinon
la génération refuse et `flutter test` échoue.

## Données

- Valider : `python donnees\valider_annuaire.py donnees\mosquees_TG.exemple.json`
- Traiter une proposition reçue par WhatsApp : coller le message dans `proposition.txt`, puis
  `python donnees\traiter_proposition.py donnees\mosquees_TG.json proposition.txt` (analyse),
  puis ajouter `--appliquer` (brouillon), `--appliquer --publier`, ou `--appliquer --confirmer --par pf-dapaong-01`.
- Publier : `python donnees\publier_donnees.py ...` (voir `publication_cloudflare\README.md`).
