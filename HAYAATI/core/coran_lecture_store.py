"""
ÉTAT DE LECTURE DU CORAN (CORE/CORAN_LECTURE_STORE.PY) - lot 7, 09/10/2026

Réglages de lecture, signets et progression, enregistrés dans un petit fichier JSON du dossier de
données de l'application (core.emplacements_donnees), indépendamment de tout compte : le Coran se
lit aussi sans être connecté.

Contenu :
  mode          "page" (feuilletage latéral, un écran = une page de mushaf) ou "liste" (défilement continu)
  taille        taille du texte coranique
  police        "amiri" (Amiri Quran) ou "naskh" (Noto Naskh Arabic) : police du texte coranique
  entete_replie en-tête de lecture replié (plus de place pour la page) ou déployé
  tajweed       couleurs du tajweed allumées ou non
  derniere_page dernière page de mushaf affichée (pour « Reprendre la lecture »)
  signets       signets : une page (marqueur de page) ou un VERSET précis (sourate + verset + page)
  pages_lues    pages comptées comme lues (voir marquer_page_lue)

Ce module ne dépend pas de Flet (testable seul). Toute erreur de lecture ou d'écriture est
journalisée et ignorée : un fichier illisible ne doit jamais empêcher de lire le Coran.
"""
from __future__ import annotations
import json
import os

NB_PAGES = 604
NOM_FICHIER = "coran_lecture.json"
TAILLES_VALIDES = (16, 18, 20, 22, 24, 28, 32)

_DEFAUTS = {
    "version": 1,
    "mode": "page",
    "taille": 20,
    "police": "amiri",
    "entete_replie": False,
    "tajweed": False,
    "derniere_page": None,
    "signets": [],          # [{"p": page}, {"p": page, "s": sourate, "v": verset}, ...]
    "pages_lues": [],
}

_etat: dict | None = None
_chemin_force: str | None = None   # tests


def _chemin() -> str:
    if _chemin_force:
        return _chemin_force
    from core.emplacements_donnees import dossier_donnees_application
    return os.path.join(dossier_donnees_application(), NOM_FICHIER)


def _page_valide(valeur) -> bool:
    return isinstance(valeur, int) and not isinstance(valeur, bool) and 1 <= valeur <= NB_PAGES


def _nettoyer(brut: dict) -> dict:
    """Ramène le contenu du fichier à des valeurs sûres (fichier édité ou ancien)."""
    etat = dict(_DEFAUTS)
    etat["signets"] = []
    etat["pages_lues"] = []
    if not isinstance(brut, dict):
        return etat
    if brut.get("mode") in ("page", "liste"):
        etat["mode"] = brut["mode"]
    if brut.get("taille") in TAILLES_VALIDES:
        etat["taille"] = brut["taille"]
    if brut.get("police") in ("amiri", "naskh"):
        etat["police"] = brut["police"]
    etat["entete_replie"] = bool(brut.get("entete_replie", False))
    etat["tajweed"] = bool(brut.get("tajweed", False))
    if _page_valide(brut.get("derniere_page")):
        etat["derniere_page"] = brut["derniere_page"]
    if isinstance(brut.get("signets"), list):
        etat["signets"] = _nettoyer_signets(brut["signets"])
    if isinstance(brut.get("pages_lues"), list):
        etat["pages_lues"] = sorted({p for p in brut["pages_lues"] if _page_valide(p)})
    return etat


def _nettoyer_signets(liste: list) -> list:
    """Accepte l'ancien format (liste de numéros de page) et le nouveau (dictionnaires)."""
    propres, vus = [], set()
    for brut in liste:
        if _page_valide(brut):                       # ancien format : un signet de page
            entree = {"p": brut}
        elif isinstance(brut, dict) and _page_valide(brut.get("p")):
            entree = {"p": brut["p"]}
            s_, v_ = brut.get("s"), brut.get("v")
            if isinstance(s_, int) and isinstance(v_, int) and not isinstance(s_, bool) \
                    and not isinstance(v_, bool) and 1 <= s_ <= 114 and 1 <= v_ <= 286:
                entree["s"], entree["v"] = s_, v_
        else:
            continue
        cle = (entree["p"], entree.get("s"), entree.get("v"))
        if cle not in vus:
            vus.add(cle)
            propres.append(entree)
    propres.sort(key=lambda e: (e["p"], e.get("v", 0)))
    return propres


def charger() -> dict:
    global _etat
    if _etat is not None:
        return _etat
    try:
        with open(_chemin(), "r", encoding="utf-8") as f:
            _etat = _nettoyer(json.load(f))
    except FileNotFoundError:
        _etat = _nettoyer({})
    except Exception as exc:
        print(f"[CORAN-LECTURE] Fichier illisible, valeurs par défaut utilisées : {exc}")
        _etat = _nettoyer({})
    return _etat


def sauvegarder() -> None:
    etat = charger()
    try:
        chemin = _chemin()
        temporaire = chemin + ".tmp"
        with open(temporaire, "w", encoding="utf-8") as f:
            json.dump(etat, f, ensure_ascii=False, separators=(",", ":"))
        os.replace(temporaire, chemin)   # écriture atomique : jamais de fichier à moitié écrit
    except Exception as exc:
        print(f"[CORAN-LECTURE] Enregistrement impossible : {exc}")


def lire(cle: str):
    return charger().get(cle)


def definir(cle: str, valeur) -> None:
    etat = charger()
    if cle not in _DEFAUTS or cle == "version":
        return
    if cle == "derniere_page" and valeur is not None and not _page_valide(valeur):
        return
    if cle == "mode" and valeur not in ("page", "liste"):
        return
    if cle == "taille" and valeur not in TAILLES_VALIDES:
        return
    if cle == "police" and valeur not in ("amiri", "naskh"):
        return
    if cle in ("entete_replie", "tajweed"):
        valeur = bool(valeur)
    if etat.get(cle) == valeur:
        return
    etat[cle] = valeur
    sauvegarder()


# ---------------------------------------------------------------- signets
def _trouver(etat: dict, page: int, sourate=None, verset=None):
    for e in etat["signets"]:
        if e["p"] == page and e.get("s") == sourate and e.get("v") == verset:
            return e
    return None


def est_signet(page: int) -> bool:
    """Signet de PAGE (marqueur de page entière)."""
    return _trouver(charger(), page) is not None


def est_signet_verset(sourate: int, verset: int) -> bool:
    return any(e.get("s") == sourate and e.get("v") == verset for e in charger()["signets"])


def basculer_signet(page: int) -> bool:
    """Ajoute ou retire le signet de PAGE. Retourne True si le signet existe après l'appel."""
    if not _page_valide(page):
        return False
    etat = charger()
    existant = _trouver(etat, page)
    if existant is not None:
        etat["signets"].remove(existant)
        ajoute = False
    else:
        etat["signets"].append({"p": page})
        etat["signets"].sort(key=lambda e: (e["p"], e.get("v", 0)))
        ajoute = True
    sauvegarder()
    return ajoute


def basculer_signet_verset(sourate: int, verset: int, page: int) -> bool:
    """Ajoute ou retire le signet d'un VERSET précis. Retourne True s'il existe après l'appel."""
    if not _page_valide(page):
        return False
    etat = charger()
    existant = _trouver(etat, page, sourate, verset)
    if existant is not None:
        etat["signets"].remove(existant)
        ajoute = False
    else:
        etat["signets"].append({"p": page, "s": sourate, "v": verset})
        etat["signets"].sort(key=lambda e: (e["p"], e.get("v", 0)))
        ajoute = True
    sauvegarder()
    return ajoute


def signets() -> list:
    """Copie de tous les signets, triés par page puis par verset."""
    return [dict(e) for e in charger()["signets"]]


# ---------------------------------------------------------------- progression
def marquer_page_lue(page: int) -> None:
    """Compte une page comme lue (appelé par l'écran quand le lecteur y est resté assez longtemps)."""
    if not _page_valide(page):
        return
    etat = charger()
    if page not in etat["pages_lues"]:
        etat["pages_lues"].append(page)
        etat["pages_lues"].sort()
        sauvegarder()


def progression() -> tuple:
    """(nombre de pages lues, 604)."""
    return len(charger()["pages_lues"]), NB_PAGES


def reinitialiser_progression() -> None:
    """Remet la progression à zéro (nouvelle lecture complète). Signets et réglages sont conservés."""
    etat = charger()
    etat["pages_lues"] = []
    etat["derniere_page"] = None
    sauvegarder()
