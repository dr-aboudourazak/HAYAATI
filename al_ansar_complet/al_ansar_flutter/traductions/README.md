# Traductions d'Al Ansâr : une seule source, zéro dette

`al_ansar.json` contient tous les textes : une clé, et son texte dans chaque langue (`fr`, `en`, `ar`, `ha`).

## Ajouter ou modifier un texte

1. Éditer `al_ansar.json` : la clé doit avoir un texte dans **toutes** les langues listées dans `_langues`.
2. `python outils/generer_traductions.py` : le script refuse (et liste ce qui manque) tant qu'une traduction est absente ou
   qu'un marqueur comme `{nom}` diffère du français. Il génère `lib/src/i18n_donnees.dart` et `integration_flet/HAYAATI_patch/ajouts_locales.json`.
3. `flutter test` : `test/traductions_test.dart` échoue lui aussi si une langue n'est pas complète.
4. `python integration_flet/synchroniser_module.py`, puis `python integration_flet/HAYAATI_patch/appliquer_integration.py <dossier HAYAATI>`.

## Ajouter une langue

Ajouter son code dans `_langues`, remplir sa colonne pour toutes les clés, ajouter ses libellés de menu dans `MENU`
(`outils/generer_traductions.py`). `appliquer_integration.py` signale toute langue de HAYAATI qui n'a pas ses textes Al Ansâr.

## Statut des relectures

Voir `_statut` dans `al_ansar.json`. Le français est la référence ; l'anglais est relu ; l'arabe et le haoussa sont des propositions à faire relire
par un locuteur natif (dont les libellés de menu haoussa « Lissafi » et « Wurina »).
