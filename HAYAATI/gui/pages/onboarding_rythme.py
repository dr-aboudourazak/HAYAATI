"""
RYTHME DE LECTURE DE L'ACCUEIL (GUI/PAGES/ONBOARDING_RYTHME.PY)
Version 1.0 - 05/10/2026

Les messages des carrousels et le bandeau verset/hadith défilaient trop vite pour être lus.
La durée d'affichage dépend maintenant de la longueur du message : un texte long reste plus longtemps.
"""
from __future__ import annotations


def duree_lecture(texte, minimum: float = 10.0, maximum: float = 28.0,
                  base: float = 3.0, caracteres_par_seconde: float = 11.0) -> float:
    """Secondes d'affichage : une base fixe + le temps de lecture, bornées entre minimum et maximum."""
    n = len(str(texte or "").strip())
    return max(minimum, min(maximum, base + n / caracteres_par_seconde))


def duree_lecture_bandeau(texte) -> float:
    """Bandeau verset / hadith (textes plus longs, souvent bilingues) : lecture plus lente."""
    return duree_lecture(texte, minimum=16.0, maximum=40.0, base=5.0, caracteres_par_seconde=9.0)
