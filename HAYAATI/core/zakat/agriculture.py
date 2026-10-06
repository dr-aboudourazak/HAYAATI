"""
LOGIQUE ATOMIQUE - ZAKAT AGRICOLE ET ELEVAGE (CORE/ZAKAT/AGRICULTURE.PY)
Version 3.0 - Irrigation a trois modes (pluie 10 %, artificielle 5 %, mixte 7,5 %)
et elevage ovin au-dela de 399 tetes.

Irrigation : si une recolte est arrosee a parts egales par la pluie et par un moyen
artificiel (motopompe, puits a frais), le taux est de 7,5 % (trois quarts de dime).
Si l'une des deux sources domine nettement, on suit la source dominante.
"""

NISSAB_AGRICULTURE_KG = 653.0
TAUX_PLUIE = 0.10
TAUX_ARTIFICIEL = 0.05
TAUX_MIXTE = 0.075
MODES_IRRIGATION = ("pluie", "artificielle", "mixte")


def normaliser_mode_irrigation(mode):
    """Ramene toute valeur (cle technique, ancien booleen, texte) a pluie / artificielle / mixte.
    Compatibilite : l'ancien code traitait tout ce qui n'etait pas "pluie" comme 5 %."""
    if isinstance(mode, bool):
        return "artificielle" if mode else "pluie"
    m = str(mode or "pluie").strip().lower()
    if m in ("pluie", "naturelle", "naturel", "rain"):
        return "pluie"
    if m in ("mixte", "mixed"):
        return "mixte"
    return "artificielle"


def evaluer_recolte_agricole(poids_kg, methode_irrigation="pluie"):
    """
    Determine l'exigibilite de la Zakat sur les cereales et denrees stockables.
    - Pluie / source naturelle : 10 %
    - Irrigation artificielle (motopompe, cout financier) : 5 %
    - Mixte, a parts egales : 7,5 %
    """
    poids = float(poids_kg or 0.0)
    mode = normaliser_mode_irrigation(methode_irrigation)

    if poids < NISSAB_AGRICULTURE_KG:
        return {
            "est_imposable": False,
            "zakat_kg": 0.0,
            "taux_pourcentage": 0.0,
            "mode_irrigation": mode,
        }

    taux = {"pluie": TAUX_PLUIE, "artificielle": TAUX_ARTIFICIEL, "mixte": TAUX_MIXTE}[mode]
    return {
        "est_imposable": True,
        "zakat_kg": poids * taux,
        "taux_pourcentage": taux * 100,
        "mode_irrigation": mode,
    }


def nombre_brebis_dues(nombre_ovins):
    """Bareme des ovins : 40-120 : 1 ; 121-200 : 2 ; 201-399 : 3 ; a partir de 400 : 1 par centaine."""
    n = int(nombre_ovins or 0)
    if n < 40:
        return 0
    if n <= 120:
        return 1
    if n <= 200:
        return 2
    if n <= 399:
        return 3
    return n // 100


def _calculer_elevage_ovins_compat(nombre_ovins):
    """Bareme d'evaluation interne pour la compatibilite de l'interface."""
    dues = nombre_brebis_dues(nombre_ovins)
    if dues == 0:
        note_ovins = "Exempte (< 40)"
    elif dues == 1:
        note_ovins = "1 brebis due"
    else:
        note_ovins = f"{dues} brebis dues"
    return {"notation_ovins": note_ovins}


# -------------------------------------------------------------------------
# ALIAS DE COMPATIBILITE ASCENDANTS POUR L'INTERFACE EXISTANTE
# -------------------------------------------------------------------------
evaluer_zakat_agricole = evaluer_recolte_agricole
evaluer_zakat_elevage_ovins = _calculer_elevage_ovins_compat
