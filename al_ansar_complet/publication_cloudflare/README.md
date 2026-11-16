# Publier les données d'Al Ansâr (Cloudflare Pages)

Al Ansâr lit trois sortes de fichiers publics : `manifest.json`, `annuaire_XX.json`, `mosquees_XX.json`.
Un hébergement statique suffit : Cloudflare Pages convient (gratuit, rapide en Afrique de l'Ouest, HTTPS inclus).
Le même site pourra accueillir plus tard la présentation de HAYAATI et un téléchargement de l'application hors Play Store.

## Étapes

1. **Créer le projet** dans Cloudflare (Workers et Pages, Pages, « Upload assets » : aucun dépôt n'est nécessaire).
   Choisissez le nom du projet : l'adresse sera `https://<projet>.pages.dev`.
2. **Préparer le dossier** depuis la racine du zip :
   ```powershell
   python donnees\publier_donnees.py --annuaire donnees\annuaire_TG.json --mosquees donnees\mosquees_TG.json `
       --sortie publication_cloudflare\site\al-ansar --base-url https://<projet>.pages.dev/al-ansar/ --production
   ```
   Le script valide les fichiers, calcule les empreintes SHA-256, met à jour `manifest.json` (les autres pays sont conservés)
   et écrit `_headers` (cache court pour le manifeste, une heure pour les données).
   Les fichiers `*.exemple.json` sont fictifs : `--production` les refuse. Remplacez-les par vos vraies données.
3. **Mettre en ligne** le dossier `publication_cloudflare\site` (glisser-déposer dans Pages, ou `wrangler pages deploy`).
4. **Brancher l'application** : dans `gui/pages/page_alansar.py`, `URL_DONNEES_AL_ANSAR = "https://<projet>.pages.dev/al-ansar/"`, puis reconstruire.
5. **Mettre à jour** plus tard : modifier les fichiers, incrémenter `version_donnees`, relancer l'étape 2 et mettre en ligne.
   Les téléphones ne retéléchargent que si la version a augmenté.

## À savoir

- Tout ce qui est dans `site/` est public. Aucun numéro personnel sans le consentement de la personne (le validateur le contrôle pour les mosquées).
- Sans adresse renseignée, l'application fonctionne avec les données embarquées (fictives, visibles seulement en mode démo).
- Prochaine étape à construire ensemble : le site de présentation de HAYAATI et la page de téléchargement de l'APK
  (signature, empreinte SHA-256 affichée, consignes d'installation « sources inconnues », mise à jour manuelle).
