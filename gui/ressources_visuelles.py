"""
GESTION DES RESSOURCES VISUELLES (GUI/RESSOURCES_VISUELLES.PY)
Version 1.0 - Chargement mis en cache du logo et de l'icône HAYAATI (dossier
images/ à la racine), à la taille demandée. Les objets PhotoImage doivent
être conservés en mémoire sous peine d'être silencieusement ramassés par le
garbage collector Tkinter et de disparaître de l'écran — ce module centralise
ces références pour éviter ce piège classique.
"""
import os

try:
    from PIL import Image, ImageTk
    _PIL_DISPONIBLE = True
except ImportError:
    _PIL_DISPONIBLE = False

_CHEMIN_LOGO = os.path.join("images", "Logo-Hayaati.png")
_CHEMIN_ICONE = os.path.join("images", "Icone Hayaati.png")
_CACHE = {}


def _charger(chemin, taille):
    if not _PIL_DISPONIBLE or not os.path.exists(chemin):
        return None
    cle = (chemin, taille)
    if cle not in _CACHE:
        try:
            image = Image.open(chemin).convert("RGBA")
            image = image.resize((taille, taille), Image.LANCZOS)
            _CACHE[cle] = ImageTk.PhotoImage(image)
        except Exception as e:
            print(f"[RESSOURCES VISUELLES] Impossible de charger {chemin} : {e}")
            return None
    return _CACHE[cle]


def logo(taille=120):
    """Le logo complet (783x783 source), pour les écrans d'accueil et de bienvenue."""
    return _charger(_CHEMIN_LOGO, taille)


def icone(taille=32):
    """L'icône compacte (550x550 source), pour la barre d'outils et les petits espaces."""
    return _charger(_CHEMIN_ICONE, taille)
