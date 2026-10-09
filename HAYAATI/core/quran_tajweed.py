"""
TAJWEED (CORE/QURAN_TAJWEED.PY) - 08/10/2026

Définition des 18 règles annotées dans assets/quran/surah_NNN.json (champ "tajweed" :
[[debut, fin, code], ...]) et leur regroupement en 5 familles de couleurs.

Les codes sont écrits dans les fichiers de données : l'ORDRE de REGLES ne doit jamais
changer (il est identique à celui de generer_coran.py).

Source des annotations : https://github.com/cpfair/quran-tajweed (Creative Commons
Attribution 4.0), classifieur appliqué au texte Tanzil 1.1. Ce sont des annotations
AUTOMATIQUES, destinées à aider la lecture : elles ne remplacent pas l'apprentissage
auprès d'un enseignant qualifié.
"""
from __future__ import annotations

REGLES = (
    "ghunnah", "idghaam_ghunnah", "idghaam_no_ghunnah", "idghaam_shafawi",
    "idghaam_mutajanisayn", "idghaam_mutaqaribayn", "ikhfa", "ikhfa_shafawi", "iqlab",
    "qalqalah", "madd_2", "madd_246", "madd_6", "madd_muttasil", "madd_munfasil",
    "hamzat_wasl", "lam_shamsiyyah", "silent",
)

# (clé de famille, couleur, clé de libellé dans assets/locales/*.json section "coran")
FAMILLES = (
    ("madd", "#C62828", "famille_madd"),
    ("ghunna_idgham", "#2E7D32", "famille_ghunna_idgham"),
    ("ikhfa_iqlab", "#EF6C00", "famille_ikhfa_iqlab"),
    ("qalqala", "#1565C0", "famille_qalqala"),
    ("muettes", "#9E9E9E", "famille_muettes"),
)
_FAMILLE_DE_REGLE = {
    "ghunnah": 1, "idghaam_ghunnah": 1, "idghaam_no_ghunnah": 1, "idghaam_shafawi": 1,
    "idghaam_mutajanisayn": 1, "idghaam_mutaqaribayn": 1,
    "ikhfa": 2, "ikhfa_shafawi": 2, "iqlab": 2,
    "qalqalah": 3,
    "madd_2": 0, "madd_246": 0, "madd_6": 0, "madd_muttasil": 0, "madd_munfasil": 0,
    "hamzat_wasl": 4, "lam_shamsiyyah": 4, "silent": 4,
}

# index = code - 1  ->  indice de famille
FAMILLE_PAR_CODE = tuple(_FAMILLE_DE_REGLE[nom] for nom in REGLES)


def indice_famille(code: int) -> int:
    """Indice (0-4) de la famille d'un code de règle (1-18) ; -1 si code inconnu."""
    if 1 <= code <= len(FAMILLE_PAR_CODE):
        return FAMILLE_PAR_CODE[code - 1]
    return -1


def couleur_famille(indice: int) -> str | None:
    return FAMILLES[indice][1] if 0 <= indice < len(FAMILLES) else None
