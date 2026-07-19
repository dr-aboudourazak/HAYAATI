"""
LOGIQUE ATOMIQUE - ZAKAT AGRICOLE (CORE/ZAKAT/AGRICULTURE.PY)
Version 2.1 - Application du Nissab, taux d'irrigation et alias d'importation pour l'interface.
"""

def evaluer_recolte_agricole(poids_kg, methode_irrigation="pluie"):
    """
    Détermine l'exigibilité de la Zakat sur les céréales et denrées stockables.
    - Irrigation par la pluie / source naturelle : 10%
    - Irrigation artificielle / motopompe (coût financier) : 5%
    """
    NISSAB_AGRICULTURE_KG = 653.0
    
    if poids_kg < NISSAB_AGRICULTURE_KG:
        return {
            "est_imposable": False,
            "zakat_kg": 0.0,
            "taux_pourcentage": 0.0
        }
        
    # Choix du taux selon la méthode d'irrigation
    if methode_irrigation == "pluie":
        taux = 0.10
    else:
        taux = 0.05  # Cas des motopompes

    zakat_due_kg = poids_kg * taux

    return {
        "est_imposable": True,
        "zakat_kg": zakat_due_kg,
        "taux_pourcentage": taux * 100
    }

def _calculer_elevage_ovins_compat(nombre_ovins):
    """Barème d'évaluation interne pour la compatibilité de l'interface."""
    note_ovins = "Exempté (< 40)"
    if nombre_ovins >= 40:
        if nombre_ovins <= 120: note_ovins = "1 brebis due"
        elif nombre_ovins <= 200: note_ovins = "2 brebis dues"
        else: note_ovins = "3 brebis dues"
    return {"notation_ovins": note_ovins}

# -------------------------------------------------------------------------
# ALIAS DE COMPATIBILITÉ ASCENDANTS IMPÉRATIFS POUR L'INTERFACE EXISTANTE
# -------------------------------------------------------------------------
evaluer_zakat_agricole = evaluer_recolte_agricole
evaluer_zakat_elevage_ovins = _calculer_elevage_ovins_compat
