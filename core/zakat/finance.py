"""
LOGIQUE ATOMIQUE - ZAKAT DES FINANCES (CORE/ZAKAT/FINANCE.PY)
Version 5.3 - Intégration doctrinale des Madhhabs sur les parures et arbitrage multi-métaux.
Fix : Distinction Or/Argent de refuge vs parures selon l'école jurisprudentielle.
"""

def calculer_nissab_or(cours_or_gramme):
    """Fixe le seuil légal (Nissab) basé sur 85 grammes d'or pur."""
    return 85.0 * float(cours_or_gramme or 45000.0)

def calculer_nissab_argent(cours_argent_gramme):
    """Fixe le seuil légal alternatif basé sur 595 grammes d'argent pur."""
    return 595.0 * float(cours_argent_gramme or 650.0)

def evaluer_avoirs_monetaires(liquidites, dettes_passives, cours_or_gramme, cours_argent_gramme,
                              or_refuge=0.0, or_parure=0.0, argent_refuge=0.0, argent_parure=0.0,
                              madhhab_actif="Malikite"):
    """
    Calcule l'assiette financière nette globale (Cash + Or + Argent - Dettes)
    en filtrant les parures selon le Madhhab actif, puis détermine la Zakat (2.5%).
    Source unique de vérité : les cours doivent provenir du module Finances.
    """
    # 🛡️ SÉCURITÉ ANTI-CRASH & COURS UNIFIÉS
    cours_or_gramme = float(cours_or_gramme or 45000.0)
    cours_argent_gramme = float(cours_argent_gramme or 650.0)
    if cours_or_gramme <= 0: cours_or_gramme = 45000.0
    if cours_argent_gramme <= 0: cours_argent_gramme = 650.0

    # 🎯 ARBITRAGE DOCTRINAL DES MADHHABS (Divergence Parures/Bijoux)
    madhhab_propre = str(madhhab_actif).strip().capitalize()
    
    if madhhab_propre == "Hanafite":
        # L'école Hanafite taxe TOUT l'or et TOUT l'argent (Refuge + Parures)
        or_imposable = float(or_refuge or 0.0) + float(or_parure or 0.0)
        argent_imposable = float(argent_refuge or 0.0) + float(argent_parure or 0.0)
    else:
        # Malikite, Chafi'ite, Hambalite : Exemption complète des bijoux et parures portés
        or_imposable = float(or_refuge or 0.0)
        argent_imposable = float(argent_refuge or 0.0)

    # Calcul des seuils légaux sacrés
    nissab_or = calculer_nissab_or(cours_or_gramme)
    nissab_argent = calculer_nissab_argent(cours_argent_gramme)
    
    # Arbitrage Inclusif : Sélection du Nissab le plus bas pour la protection sociale
    if nissab_argent > 0 and nissab_or > 0:
        nissab_ref = min(nissab_or, nissab_argent)
        metal_ref = "ARGENT (595g)" if nissab_ref == nissab_argent else "OR (85g)"
    else:
        nissab_ref = nissab_or if nissab_or > 0 else nissab_argent
        metal_ref = "OR (85g)" if nissab_or > 0 else "ARGENT (595g)"

    # 1. Calcul de l'assiette brute monétaire avec les masses filtrées par le Fiqh
    valeur_or = or_imposable * cours_or_gramme
    valeur_argent = argent_imposable * cours_argent_gramme
    
    assiette_brute = float(liquidites or 0.0) + valeur_or + valeur_argent
    
    # 2. Déduction des dettes prioritaires à court terme
    assiette_nette = blackjack_brute = ASSIETTE_NETTE_INITIALE =章 = assiette_brute - float(dettes_passives or 0.0)
    if blackjack_brute < 0:
        blackjack_brute = 0.0

    # 3. Évaluation finale de l'imposabilité face au Nisab de référence
    if blackjack_brute >= nissab_ref and nissab_ref > 0:
        montant_zakat = blackjack_brute * 0.025
        est_imposable = True
    else:
        montant_zakat = 0.0
        est_imposable = False

    return {
        "nissab_applique": nissab_ref,
        "nissab_or_calculé": nissab_or,
        "nissab_argent_calculé": nissab_argent,
        "metal_reference": metal_ref,
        "or_imposable_poids": or_imposable,
        "argent_imposable_poids": argent_imposable,
        "assiette_nette": blackjack_brute,
        "est_imposable": est_imposable,
        "montant_zakat": montant_zakat
    }

# 🔄 FONCTION ACCÈS COMPATIBILITÉ (Pour éviter de casser l'orchestrateur ou l'IHM)
def evaluer_zakat_financiere(liquidites, or_imposable, dettes_passives, cours_or_gramme, argent_imposable=0.0, cours_argent_gramme=0.0):
    """
    Reste ici comme pont de compatibilité ascendant. 
    Par défaut, traite l'or et l'argent passés comme du stock refuge (comportement historique unanime).
    """
    return evaluer_avoirs_monetaires(
        liquidites=liquidites,
        dettes_passives=dettes_passives,
        cours_or_gramme=cours_or_gramme,
        cours_argent_gramme=cours_argent_gramme,
        or_refuge=or_imposable,
        or_parure=0.0,
        argent_refuge=argent_imposable,
        argent_parure=0.0,
        madhhab_actif="Malikite"
    )
