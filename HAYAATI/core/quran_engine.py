"""
MOTEUR DE LECTURE CORANIQUE (CORE/QURAN_ENGINE.PY) - v2 du 08/10/2026

Charge l'index des 114 sourates et le texte de chaque sourate à la demande depuis
assets/quran/ (voir assets/quran/LICENCE_SOURCE.md pour la provenance et les conditions
d'attribution).

v2 : texte Tanzil 1.1 (signes de pause, ۩ et ۞ intégrés au texte), pages du mushaf de
Médine, annotations de tajweed. Le texte de chaque verset est stocké VERBATIM ; la basmala
(que Tanzil place au début du verset 1 de chaque sourate sauf 1 et 9) est mise à part dans
le champ "basmalah" de la sourate.

v3 (lot 7) : lecture « page de mushaf » : une page (1-604) peut contenir la fin d'une sourate et le
début de la suivante ; pages.json donne, pour chaque page, ses segments [sourate, 1er verset, dernier].

Format d'un fichier surah_NNN.json :
  numero, nom_arabe, basmalah (str | None), basmalah_tajweed (liste, absent pour 1 et 9),
  versets : [{numero, texte, page, tajweed: [[debut, fin, code], ...]}]

Ce module ne dépend pas de Flet (testable seul).
"""
from __future__ import annotations
import json
import os
import sys
from typing import Optional

from core.quran_tajweed import indice_famille

_cache_index: Optional[list] = None
_cache_sourates: dict = {}
_cache_pages: Optional[dict] = None

NB_PAGES = 604

SOURATES_SANS_BASMALAH = {1, 9}  # 1 : la basmala y est le verset 1 ; 9 : n'en a traditionnellement pas

SIGNE_SAJDA = "\u06e9"      # ۩ (déjà présent dans le texte Tanzil des 15 versets de prosternation)
SIGNE_HIZB = "\u06de"       # ۞
SIGNES_PAUSE = "\u06d6\u06d7\u06d8\u06d9\u06da\u06db"   # ۖ ۗ ۘ ۙ ۚ ۛ
ESPACE_INSECABLE = "\u00a0"

# Parenthèses ornées du numéro de verset. ORDRE LOGIQUE, tel qu'il est écrit dans la chaîne : dans un
# paragraphe de droite à gauche, le premier caractère s'affiche à DROITE. Avec ces valeurs on voit,
# de gauche à droite, « ( ١٢ ) » : la parenthèse ouvrante à gauche, la fermante à droite, comme dans
# un mushaf. Si un appareil affichait l'inverse (moteur de texte qui reflèterait ces deux
# caractères), il suffit d'échanger ces deux constantes : c'est le SEUL endroit à modifier.
MARQUEUR_PREMIER = "\ufd3f"    # ﴿ U+FD3F - affiché à droite en RTL
MARQUEUR_DERNIER = "\ufd3e"    # ﴾ U+FD3E - affiché à gauche en RTL

_CHIFFRES_ARABES = str.maketrans("0123456789", "\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669")


def chiffres_arabes(nombre: int) -> str:
    """12 -> ١٢ (chiffres arabes-indiens, comme dans un mushaf)."""
    return str(nombre).translate(_CHIFFRES_ARABES)


def marqueur_verset(numero: int) -> str:
    """Marqueur de fin de verset : espace insécable devant (le numéro ne se retrouve jamais seul en
    début de ligne), parenthèses ornées autour du numéro en chiffres arabes-indiens, espace normale
    derrière (point de retour à la ligne autorisé)."""
    return f"{ESPACE_INSECABLE}{MARQUEUR_PREMIER}{chiffres_arabes(numero)}{MARQUEUR_DERNIER} "


def _chemin_dossier_quran() -> str:
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "assets", "quran")
    racine_projet = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(racine_projet, "assets", "quran")


def charger_index_sourates() -> list:
    """Les 114 entrées (numéro, nom arabe, translittération, nom anglais, nombre de
    versets, type de révélation), mises en cache après le premier chargement."""
    global _cache_index
    if _cache_index is not None:
        return _cache_index
    chemin = os.path.join(_chemin_dossier_quran(), "index.json")
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            _cache_index = json.load(f)
    except Exception as exc:
        print(f"[QURAN] Échec de chargement de l'index ({chemin}) : {exc}")
        _cache_index = []
    return _cache_index


def charger_sourate(numero: int) -> Optional[dict]:
    """Texte complet d'une sourate (1 à 114), mis en cache après le premier chargement.
    Chaque verset reçoit en plus le booléen "sajda" (le signe ۩ figure dans son texte)."""
    if numero in _cache_sourates:
        return _cache_sourates[numero]
    chemin = os.path.join(_chemin_dossier_quran(), f"surah_{numero:03d}.json")
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            donnees = json.load(f)
        for verset in donnees.get("versets", []):
            verset["sajda"] = SIGNE_SAJDA in verset["texte"]
        _cache_sourates[numero] = donnees
        return donnees
    except Exception as exc:
        print(f"[QURAN] Échec de chargement de la sourate {numero} ({chemin}) : {exc}")
        return None


def _charger_pages() -> dict:
    """pages.json : {"juz_par_page": [None, juz de la page 1, ...], "segments": [None, [[s, a1, a2], ...], ...]}."""
    global _cache_pages
    if _cache_pages is None:
        chemin = os.path.join(_chemin_dossier_quran(), "pages.json")
        try:
            with open(chemin, "r", encoding="utf-8") as f:
                _cache_pages = json.load(f)
        except Exception as exc:
            print(f"[QURAN] Échec de chargement de pages.json : {exc}")
            _cache_pages = {"juz_par_page": [], "segments": []}
    return _cache_pages


def juz_de_page(page: int) -> Optional[int]:
    """Numéro du juz (1-30) qui contient la page de mushaf donnée (1-604)."""
    juz = _charger_pages().get("juz_par_page", [])
    return juz[page] if 0 < page < len(juz) else None


def segments_de_page(page: int) -> list:
    """[[sourate, premier verset, dernier verset], ...] de la page de mushaf (1-604)."""
    segments = _charger_pages().get("segments", [])
    return segments[page] if 0 < page < len(segments) and segments[page] else []


def _nom_sourate(numero: int) -> str:
    for entree in charger_index_sourates():
        if entree.get("numero") == numero:
            return entree.get("nom_arabe", "")
    return ""


def versets_de_page(page: int) -> list:
    """Contenu d'une page de mushaf, dans l'ordre de lecture, un élément par sourate présente :
    {"sourate", "nom_arabe", "debut" (la sourate commence sur cette page), "basmalah",
     "basmalah_tajweed", "versets": [...]}. Liste vide si la page est inconnue ou si les données
    sont absentes."""
    resultat = []
    for sourate, premier, dernier in segments_de_page(page):
        donnees = charger_sourate(sourate)
        if not donnees:
            continue
        versets = [v for v in donnees["versets"] if premier <= v["numero"] <= dernier]
        resultat.append({
            "sourate": sourate,
            "nom_arabe": _nom_sourate(sourate),
            "debut": premier == 1,
            "basmalah": donnees.get("basmalah") if premier == 1 else None,
            "basmalah_tajweed": donnees.get("basmalah_tajweed") if premier == 1 else None,
            "versets": versets,
        })
    return resultat


def page_de_verset(sourate: int, verset: int) -> Optional[int]:
    """Page de mushaf (1-604) qui contient le verset donné, ou None s'il n'existe pas."""
    donnees = charger_sourate(sourate)
    if not donnees:
        return None
    for v in donnees["versets"]:
        if v["numero"] == verset:
            return v.get("page")
    return None


def premiere_page_sourate(sourate: int) -> Optional[int]:
    """Page de mushaf où commence la sourate."""
    return page_de_verset(sourate, 1)


def pages_de_sourate(sourate: int) -> list:
    """Pages de mushaf (distinctes, dans l'ordre) que couvre la sourate."""
    donnees = charger_sourate(sourate)
    if not donnees:
        return []
    pages: list = []
    for v in donnees["versets"]:
        p = v.get("page")
        if not pages or pages[-1] != p:
            pages.append(p)
    return pages


def sourate_de_page(page: int) -> Optional[int]:
    """Sourate du premier verset de la page (celle que le mushaf imprime en en-tête)."""
    segments = segments_de_page(page)
    return segments[0][0] if segments else None


def regrouper_par_page(versets: list) -> list:
    """[(numero_de_page, [versets...]), ...] dans l'ordre de lecture. Une page du mushaf
    peut ne contenir qu'une partie de la sourate (début ou fin) : on ne regroupe que les
    versets de la sourate ouverte."""
    groupes: list = []
    for verset in versets:
        page = verset.get("page")
        if groupes and groupes[-1][0] == page:
            groupes[-1][1].append(verset)
        else:
            groupes.append((page, [verset]))
    return groupes


def preparer_texte_affichage(texte: str) -> str:
    """Anti-orphelins, À L'AFFICHAGE SEULEMENT (le texte stocké reste verbatim) : l'espace qui
    précède un signe de pause ou ۩, et celle qui suit ۞, devient insécable, pour qu'un de ces
    signes ne se retrouve jamais seul en début ou en fin de ligne. Remplacement d'un caractère
    par un autre : les positions des annotations tajweed restent valables."""
    chars = list(texte)
    for i, c in enumerate(chars):
        if c == " ":
            suivant = chars[i + 1] if i + 1 < len(chars) else ""
            precedent = chars[i - 1] if i > 0 else ""
            if suivant and (suivant in SIGNES_PAUSE or suivant == SIGNE_SAJDA):
                chars[i] = ESPACE_INSECABLE
            elif precedent == SIGNE_HIZB:
                chars[i] = ESPACE_INSECABLE
    return "".join(chars)


def segments_verset(texte: str, annotations: Optional[list], avec_tajweed: bool) -> list:
    """Découpe le texte (déjà préparé pour l'affichage) en segments [(texte, famille)] où
    famille est l'indice de couleur (0-4) ou -1 pour le texte ordinaire. Sans tajweed : un
    seul segment. Chevauchements : la première annotation (par position) l'emporte."""
    if not avec_tajweed or not annotations:
        return [(texte, -1)]
    familles = [-1] * len(texte)
    for debut, fin, code in annotations:
        fam = indice_famille(code)
        if fam < 0:
            continue
        for i in range(max(0, debut), min(len(texte), fin)):
            if familles[i] == -1:
                familles[i] = fam
    segments = []
    debut = 0
    for i in range(1, len(texte) + 1):
        if i == len(texte) or familles[i] != familles[debut]:
            segments.append((texte[debut:i], familles[debut]))
            debut = i
    return segments
