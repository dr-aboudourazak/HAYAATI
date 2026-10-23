# hayaati-alnsar

Contrôle Flet `HayaatiAlAnsar` : le module Al Ansâr de HAYAATI (annuaire, cours, mosquées proches,
Hadj et Omra), écrit en Flutter natif et affiché dans l'application Flet.

Le code Flutter du module vit dans `al_ansar_flutter/` (source de vérité, avec ses tests).
`synchroniser_module.py` en copie les fichiers dans `src/flutter/hayaati_alnsar/packages/al_ansar/`,
dossier embarqué par l'extension. Ne modifiez jamais cette copie à la main.
