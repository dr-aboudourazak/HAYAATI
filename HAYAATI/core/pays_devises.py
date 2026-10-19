"""
PAYS ET DEVISES (CORE/PAYS_DEVISES.PY) - 15/10/2026

Tous les pays du monde et toutes leurs devises, avec leurs noms dans les 4 langues de l'application
(fr, en, ar, ha). Données : assets/pays/pays.json et assets/pays/devises.json, générées depuis Unicode
CLDR par outils/generer_pays_devises.py. Chaque pays porte sa devise courante (code ISO 4217).

Recherche « pendant la saisie » : insensible à la casse, aux accents et, en arabe, aux voyelles
brèves et aux variantes d'alif, de yâ' et de tâ' marbûta. Ce module ne dépend pas de Flet.
"""
from __future__ import annotations
import json
import os
import sys
import unicodedata
from typing import Optional

LANGUES = ("fr", "en", "ar", "ha")
_cache: dict = {}


def _dossier() -> str:
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "assets", "pays")
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "pays")


def _charger(nom: str):
    if nom not in _cache:
        try:
            with open(os.path.join(_dossier(), nom), "r", encoding="utf-8") as f:
                _cache[nom] = json.load(f)
        except Exception as exc:
            print(f"[PAYS] Échec de chargement de {nom} : {exc}")
            _cache[nom] = [] if nom == "pays.json" else {}
    return _cache[nom]


def normaliser(texte: str) -> str:
    """Forme de comparaison : minuscules, sans accents, sans voyelles arabes, alif/yâ'/tâ' unifiés."""
    if not texte:
        return ""
    t = unicodedata.normalize("NFKD", str(texte)).casefold()
    sortie = []
    for c in t:
        if unicodedata.combining(c) or c in "\u0640":          # accents, voyelles brèves arabes, tatwîl
            continue
        if c in "\u0623\u0625\u0622\u0671":                      # أ إ آ ٱ -> ا
            c = "\u0627"
        elif c == "\u0649":                                      # ى -> ي
            c = "\u064a"
        elif c == "\u0629":                                      # ة -> ه
            c = "\u0647"
        elif c in "-'\u2019\u02bc.,()":
            c = " "
        sortie.append(c)
    return " ".join("".join(sortie).split())


# ------------------------------------------------------------------ pays
def liste_pays() -> list:
    return _charger("pays.json")


def pays_par_code(code: Optional[str]) -> Optional[dict]:
    if not code:
        return None
    code = str(code).upper()
    for p in liste_pays():
        if p["c"] == code:
            return p
    return None


def nom_pays(code: Optional[str], langue: str = "fr") -> str:
    p = pays_par_code(code)
    if not p:
        return ""
    return p["n"].get(str(langue).lower(), p["n"].get("en", p["c"]))


def devise_du_pays(code: Optional[str]) -> Optional[str]:
    p = pays_par_code(code)
    return p.get("d") if p else None


def _score(requete_n: str, noms_n: list) -> Optional[int]:
    """0 = commence par la requête (nom affiché), 1 = un mot commence par la requête, 2 = la contient,
    3 = trouvée seulement dans un autre nom (autre langue ou code ISO) ; None = pas de correspondance."""
    affiche = noms_n[0]
    if affiche.startswith(requete_n):
        return 0
    if any(m.startswith(requete_n) for m in affiche.split()):
        return 1
    if requete_n in affiche:
        return 2
    for autre in noms_n[1:]:
        if autre.startswith(requete_n) or requete_n in autre.split() or requete_n in autre:
            return 3
    return None


def chercher_pays(requete: str, langue: str = "fr", limite: int = 8) -> list:
    """Pays correspondant à ce qui est tapé, du plus pertinent au moins pertinent (nom dans la langue
    de l'utilisateur d'abord, puis les autres langues et le code ISO)."""
    q = normaliser(requete)
    if not q:
        return []
    langue = str(langue).lower() if str(langue).lower() in LANGUES else "fr"
    trouves = []
    for p in liste_pays():
        noms = [normaliser(p["n"].get(langue, p["n"]["en"]))]
        noms += [normaliser(p["n"][l]) for l in LANGUES if l != langue and l in p["n"]]
        noms.append(p["c"].casefold())
        s = _score(q, noms)
        if s is not None:
            trouves.append((s, noms[0], p))
    trouves.sort(key=lambda x: (x[0], x[1]))
    return [p for _s, _n, p in trouves[:limite]]


def deviner_pays(texte: str) -> Optional[str]:
    """Code d'un pays à partir d'un texte libre (ancien profil : « Togo », « togo », « توغو »...), s'il
    correspond exactement à un nom dans l'une des 4 langues ou au code ISO ; sinon None."""
    q = normaliser(texte)
    if not q:
        return None
    for p in liste_pays():
        if q == p["c"].casefold() or any(q == normaliser(n) for n in p["n"].values()):
            return p["c"]
    return None


# ------------------------------------------------------------------ devises
def liste_devises() -> dict:
    return _charger("devises.json")


def nom_devise(code: Optional[str], langue: str = "fr") -> str:
    d = liste_devises().get(str(code).upper()) if code else None
    if not d:
        return str(code or "")
    return d.get(str(langue).lower(), d.get("en", str(code)))


def libelle_devise(code: Optional[str], langue: str = "fr") -> str:
    """« XOF - franc CFA (BCEAO) »"""
    if not code:
        return ""
    nom = nom_devise(code, langue)
    return f"{code} - {nom}" if nom and nom != code else str(code)


# À égalité de pertinence, les devises les plus courantes passent d'abord (« dollar » -> USD avant AUD).
POPULAIRES = ("USD", "EUR", "GBP", "XOF", "XAF", "SAR", "AED", "MAD", "DZD", "TND", "EGP", "NGN", "GHS",
              "CAD", "CHF", "TRY", "QAR", "KWD", "CNY", "INR")


def chercher_devises(requete: str, langue: str = "fr", limite: int = 8) -> list:
    """Codes de devises correspondant à la saisie (code ISO, nom, symbole)."""
    q = normaliser(requete)
    if not q:
        return []
    langue = str(langue).lower() if str(langue).lower() in LANGUES else "fr"
    trouves = []
    for code, d in liste_devises().items():
        noms = [normaliser(code + " " + d.get(langue, d.get("en", code)))]
        noms += [normaliser(d.get(l, "")) for l in LANGUES if l != langue]
        noms.append(normaliser(d.get("s", "")))
        s = _score(q, noms)
        if code.casefold() == q:
            s = -1
        if s is not None:
            rang = POPULAIRES.index(code) if code in POPULAIRES else len(POPULAIRES)
            trouves.append((s, rang, code))
    trouves.sort(key=lambda x: (x[0], x[1], x[2]))
    return [c for _s, _r, c in trouves[:limite]]


def devise_valide(code: Optional[str]) -> bool:
    return bool(code) and str(code).upper() in liste_devises()
