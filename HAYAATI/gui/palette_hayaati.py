"""
PALETTE DE COULEURS CENTRALISÉE (GUI/PALETTE_HAYAATI.PY)
Version 1.0 - Identité visuelle "vive et chaleureuse" (terracotta / ocre / vert).
Toute nouvelle interface doit puiser ses couleurs ici plutôt que de coder
des codes hexadécimaux en dur, pour que l'appli reste visuellement cohérente
d'un écran à l'autre.
"""

# --- Couleur historique de l'application (barre d'outils, accents "validé") ---
VERT_PROFOND = "#064e3b"
VERT_CLAIR = "#0f766e"

# --- Nouvelle identité chaude, inspirée des motifs sahéliens ---
TERRACOTTA = "#C1502E"
TERRACOTTA_CLAIR = "#F4E4DC"
TERRACOTTA_FONCE = "#6B2712"

OCRE = "#D9A441"
OCRE_CLAIR = "#FBF0DA"
OCRE_FONCE = "#7A5510"

# --- Texte de corps sur fond coloré ou clair : contraste maximal, jamais coloré lui-même.
# (Le retour utilisateur a signalé qu'un texte coloré-sur-clair devient difficile à lire
# dès qu'il y a beaucoup à lire — cette couleur remplace OCRE_FONCE/TERRACOTTA_FONCE
# pour tout corps de texte long ; les couleurs de marque restent réservées aux titres courts.)
TEXTE_FONCE = "#2b1607"

# --- Neutres et fonds ---
SABLE = "#FBF6EE"
BLANC = "#ffffff"
GRIS_TEXTE = "#374151"
GRIS_CLAIR = "#f3f4f6"

# --- Signalétique sémantique (succès / échec / attention) ---
VERT_SUCCES = "#27500A"
ROUGE_ERREUR = "#791F1F"
AMBRE_ATTENTE = "#d97706"
