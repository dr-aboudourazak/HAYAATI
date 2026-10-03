"""
MOTEUR DE LECTURE CORANIQUE (CORE/QURAN_ENGINE.PY)

Charge l'index des 114 sourates et le texte de chaque sourate à la
demande depuis assets/quran/ (généré depuis les fichiers sources
Tanzil — voir assets/quran/LICENCE_SOURCE.md pour la provenance et les
conditions d'attribution).

Texte arabe complet : ~1,8 Mo pour les 114 fichiers, chargés un par un
à l'ouverture de chaque sourate plutôt que tous en mémoire — même
principe de sobriété que le reste du projet.

Résolution du dossier assets/ : même mécanique que gui/langues.py
(sys._MEIPASS pour un exécutable PyInstaller sur PC, sinon un chemin
relatif à ce fichier), déjà éprouvée sur PC comme sur Android pour
assets/locales/.
"""
from __future__ import annotations
import json
import os
import sys
from typing import Optional

_cache_index: Optional[list] = None
_cache_sourates: dict = {}

# 🆕 26/09/2026 : le texte source Tanzil n'inclut la Basmalah que dans
# le verset 1 d'Al-Fatiha (sourate 1) — pour toutes les autres
# sourates, elle est absente du texte des versets (confirmé en
# inspectant directement les fichiers générés : le verset 1 de la
# sourate 2 commence bien par "الٓمٓ", pas par la Basmalah). Selon la
# tradition, elle doit pourtant précéder chaque sourate à l'exception
# de la 9 (At-Tawbah), qui n'en a jamais eu. Ajoutée ici, à la source,
# comme un élément distinct du verset 1 (jamais fusionnée dedans, pour
# ne pas fausser la numérotation ni le texte verbatim des versets).
BASMALAH_TEXTE = "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ"
SOURATES_SANS_BASMALAH = {1, 9}  # 1 : déjà son propre verset 1 ; 9 : n'en a traditionnellement pas

# 🆕 27/09/2026 : versets de prosternation (sajdat at-tilawah) — sans eux,
# le texte n'est pas encore un vrai Coran tel qu'imprimé. Source : Tanzil
# officiel (sources/1.0/quran-data.xml, balise <sajdas>) — la même source
# déjà utilisée pour le texte et l'index, numérotation garantie cohérente
# avec le reste du jeu de données (vérifiée : les 15 versets existent bien
# à ces numéros exacts dans nos fichiers générés).
# 14 sont unanimement reconnus par les 4 écoles ; le 15e (22:77) est
# spécifique à l'école chaféite (Shafi'i) — divergence connue, non
# affichée verset par verset : un vrai Mushaf imprimé porte le signe ۩
# aux 15 endroits sans distinction visuelle selon l'école, la
# prosternation effective à cet endroit précis relevant de la pratique
# personnelle du lecteur, pas de l'affichage du texte.
VERSETS_SAJDA = frozenset({
    (7, 206), (13, 15), (16, 50), (17, 109), (19, 58),
    (22, 18), (22, 77), (25, 60), (27, 26), (32, 15),
    (38, 24), (41, 38), (53, 62), (84, 21), (96, 19),
})
SIGNE_SAJDA = "۩"


def _chemin_dossier_quran() -> str:
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "assets", "quran")
    racine_projet = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(racine_projet, "assets", "quran")


def charger_index_sourates() -> list:
    """Les 114 entrées (numéro, nom arabe, translittération, nom
    anglais, nombre de versets, type de révélation) — mis en cache après
    le premier chargement, ~15 Ko, aucune raison de relire le disque à
    chaque ouverture de la liste."""
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
    """Texte complet d'une sourate (1 à 114) — mis en cache après le
    premier chargement pour une navigation aller-retour sans relire le
    disque à chaque fois. Le cache de 114 sourates tiendrait ~1,8 Mo au
    pire des cas (toutes consultées dans une même session) — négligeable."""
    if numero in _cache_sourates:
        return _cache_sourates[numero]
    chemin = os.path.join(_chemin_dossier_quran(), f"surah_{numero:03d}.json")
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            donnees = json.load(f)
        donnees["basmalah"] = None if numero in SOURATES_SANS_BASMALAH else BASMALAH_TEXTE
        for verset in donnees.get("versets", []):
            verset["sajda"] = (numero, verset["numero"]) in VERSETS_SAJDA
        _cache_sourates[numero] = donnees
        return donnees
    except Exception as exc:
        print(f"[QURAN] Échec de chargement de la sourate {numero} ({chemin}) : {exc}")
        return None
