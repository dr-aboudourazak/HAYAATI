"""
MOTEUR DE RÉAJUSTEMENT MATHÉMATIQUE (CORE/HERITAGE/MATH_ADJUST.PY)
Gestion des anomalies fractionnaires : Al-Aoul (Surcharge) et Al-Radd (Restitution).
"""

def ajuster_proportions_legales(dictionnaire_fractions, liste_residuels=None):
    """
    Analyse la somme des fractions. Si elle dévie de 1.0 (100%), applique
    les méthodes correctrices traditionnelles Al-Aoul ou Al-Radd.
    """
    if liste_residuels is None:
        liste_residuels = []
        
    somme_actuelle = sum(dictionnaire_fractions.values())
    fractions_ajustees = dictionnaire_fractions.copy()
    ajustement_applique = "Aucun (Fractions en équilibre parfait)"

    # --- CRITÉRE A : L'AL-AOUL (La somme des parts dépasse 100%) ---
    # On tolère une infime marge d'erreur liée aux flottants informatiques (1.0001)
    if somme_actuelle > 1.0001:
        ajustement_applique = "Al-Aoul (Surcharge - Réduction proportionnelle des parts)"
        # La formule divise chaque part individuelle par la somme totale pour forcer le total à valoir exactement 1.0
        for heritier in fractions_ajustees:
            fractions_ajustees[heritier] = fractions_ajustees[heritier] / somme_actuelle

    # --- CRITÉRE B : L'AL-RADD (La somme est inférieure à 100% et aucun Asabah n'est là) ---
    elif somme_actuelle < 0.9999 and not liste_residuels:
        # Le surplus doit être redistribué à tout le monde SAUF aux conjoints (époux/épouse)
        heritiers_eligibles_radd = [h for h in fractions_ajustees if h not in ["epouse", "epoux"]]
        
        if heritiers_eligibles_radd:
            ajustement_applique = "Al-Radd (Excédent - Restitution proportionnelle aux membres de sang)"
            # Somme des parts des personnes de sang uniquement
            somme_sang = sum(fractions_ajustees[h] for h in heritiers_eligibles_radd)
            part_conjoint = fractions_ajustees.get("epouse", 0) + fractions_ajustees.get("epoux", 0)
            
            # Le reste disponible après avoir payé le conjoint
            reste_a_partager = 1.0 - part_conjoint
            
            # Recalcul des parts des héritiers de sang basées sur leur poids relatif dans le reste
            for h in heritiers_eligibles_radd:
                poids_relatif = fractions_ajustees[h] / somme_sang
                fractions_ajustees[h] = poids_relatif * reste_a_partager

    return {
        "fractions_finales": fractions_ajustees,
        "somme_initiale": round(somme_actuelle, 4),
        "somme_finale": sum(fractions_ajustees.values()),
        "type_ajustement": ajustement_applique
    }
