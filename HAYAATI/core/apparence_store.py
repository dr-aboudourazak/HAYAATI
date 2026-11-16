"""
APPARENCE DE L'APPLICATION (CORE/APPARENCE_STORE.PY) - lot D, 03/11/2026

Arrière-plan (clair, papier ou sombre) et couleur principale (vert, terracotta ou ocre) choisis par l'utilisateur,
enregistrés dans un petit fichier JSON du dossier de données de l'application (core.emplacements_donnees), comme
l'état de lecture du Coran : indépendamment de tout compte.

Le thème « clair » avec la couleur « vert » est la charte officielle de HAYAATI : c'est la valeur par défaut et celle
que l'on retrouve si le fichier est absent, édité ou illisible. Le même format JSON est lu par les modules Flutter
(ApparenceHayaati.depuisJson dans le paquet hayaati_ui).

Ce module ne dépend pas de Flet (testable seul). Toute erreur de lecture ou d'écriture est journalisée et ignorée.
"""
from __future__ import annotations
import json
import os

NOM_FICHIER = "apparence.json"
FONDS = ("clair", "papier", "sombre")
COULEURS = ("vert", "terracotta", "ocre")

_DEFAUTS = {"version": 1, "fond": "clair", "couleur": "vert"}

_etat: dict | None = None
_chemin_force: str | None = None   # tests


def _chemin() -> str:
    if _chemin_force:
        return _chemin_force
    from core.emplacements_donnees import dossier_donnees_application
    return os.path.join(dossier_donnees_application(), NOM_FICHIER)


def _nettoyer(brut) -> dict:
    """Ramène le contenu du fichier à des valeurs sûres (fichier édité ou ancien)."""
    etat = dict(_DEFAUTS)
    if isinstance(brut, dict):
        if brut.get("fond") in FONDS:
            etat["fond"] = brut["fond"]
        if brut.get("couleur") in COULEURS:
            etat["couleur"] = brut["couleur"]
    return etat


def charger() -> dict:
    """Apparence en cours (copie). Lit le fichier une seule fois."""
    global _etat
    if _etat is None:
        brut = None
        try:
            chemin = _chemin()
            if os.path.exists(chemin):
                with open(chemin, "r", encoding="utf-8") as f:
                    brut = json.load(f)
        except Exception as exc:
            print(f"[APPARENCE] Lecture impossible, valeurs par défaut : {exc}")
        _etat = _nettoyer(brut)
    return dict(_etat)


def sauvegarder() -> None:
    try:
        chemin = _chemin()
        os.makedirs(os.path.dirname(chemin) or ".", exist_ok=True)
        temporaire = chemin + ".tmp"
        with open(temporaire, "w", encoding="utf-8") as f:
            json.dump(_etat or dict(_DEFAUTS), f, ensure_ascii=False, separators=(",", ":"))
        os.replace(temporaire, chemin)  # remplacement d'un bloc : jamais de fichier à moitié écrit
    except Exception as exc:
        print(f"[APPARENCE] Enregistrement impossible : {exc}")


def definir(fond: str | None = None, couleur: str | None = None) -> bool:
    """Change l'arrière-plan et/ou la couleur principale. Retourne vrai si quelque chose a changé."""
    global _etat
    charger()
    neuf = dict(_etat)
    if fond is not None and fond in FONDS:
        neuf["fond"] = fond
    if couleur is not None and couleur in COULEURS:
        neuf["couleur"] = couleur
    if neuf == _etat:
        return False
    _etat = neuf
    sauvegarder()
    return True


def remplacer(brut) -> None:
    """Remplace l'apparence par celle que renvoie un module Flutter (contenu nettoyé avant d'être enregistré)."""
    global _etat
    if not isinstance(brut, dict):
        return
    nouveau = _nettoyer(brut)
    if _etat is not None and nouveau == _etat:
        return
    _etat = nouveau
    sauvegarder()


def est_sombre() -> bool:
    return charger()["fond"] == "sombre"


def json_texte() -> str:
    """Apparence en JSON, à transmettre aux modules Flutter (propriété apparence_json)."""
    return json.dumps(charger(), ensure_ascii=False)
