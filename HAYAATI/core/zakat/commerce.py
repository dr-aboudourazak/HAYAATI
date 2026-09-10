"""
LOGIQUE ATOMIQUE - ZAKAT DU COMMERCE ET COMPARAISON MULTI-MÉTAUX (CORE/ZAKAT/COMMERCE.PY)
Version 5.3 - Évaluation des stocks marchands, intégration des Nissabs Or (85g) et Argent (595g).
Fix : Unification stricte des cours et sécurité anti-crash (Valeurs de repli si à zéro).
"""

def evaluer_biens_commerciaux(valeur_stock_marchand, liquidites_caisse, creances_recouvrables, or_cours, argent_cours):
    """
    Calcule l'assiette commerciale soumise aux règles de la Zakat et détermine
    les Nissabs de référence Or (85g) et Argent (595g).
    Sécurité : Si l'utilisateur n'a encore rien saisi, des valeurs de repli
    standards sont appliquées pour éviter un crash ou un Nisab nul.
    """
    # 🛡️ SÉCURITÉ ANTI-CRASH : Conversion et valeurs de secours si la base est vide (0 ou None)
    or_cours = float(or_cours or 45000.0)
    argent_cours = float(argent_cours or 650.0)
    
    if or_cours <= 0:
        or_cours = 45000.0
    if argent_cours <= 0:
        argent_cours = 650.0

    # Cumul des actifs du commerce (Valeur marchande des biens + Caisse + Créances sûres)
    total_actif_commercial = float(valeur_stock_marchand or 0.0) + float(liquidites_caisse or 0.0) + float(creances_recouvrables or 0.0)
    
    if total_actif_commercial < 0:
        total_actif_commercial = 0.0

    # Calcul des deux seuils sacrés (Nissabs Nominaux) basés sur les cours validés
    nissab_or_monnaie = 85.0 * or_cours
    nissab_argent_monnaie = 595.0 * argent_cours

    # Arbitrage Doctrinal : Choix du Nisab le plus bas (Inclusivité et protection des pauvres)
    if nissab_argent_monnaie > 0 and nissab_or_monnaie > 0:
        nissab_reference = min(nissab_or_monnaie, nissab_argent_monnaie)
        metal_reference = "ARGENT (595g)" if nissab_reference == nissab_argent_monnaie else "OR (85g)"
    else:
        nissab_reference = nissab_or_monnaie if nissab_or_monnaie > 0 else nissab_argent_monnaie
        metal_reference = "OR (85g)" if nissab_or_monnaie > 0 else "ARGENT (595g)"

    # Évaluation de l'éligibilité commerciale face au Nisab de référence
    eligibilite = total_actif_commercial >= nissab_reference if nissab_reference > 0 else False
    zakat_due = (total_actif_commercial * 0.025) if eligibilite else 0.0

    return {
        "total_actif_commercial": total_actif_commercial,
        "nissab_or_monnaie": nissab_or_monnaie,
        "nissab_argent_monnaie": nissab_argent_monnaie,
        "nissab_reference": nissab_reference,
        "metal_reference": metal_reference,
        "eligibilite_commerciale": eligibilite,
        "zakat_commerciale_due": zakat_due
    }

# Alias de compatibilité ascendant impératif pour votre interface graphique existante
evaluer_zakat_commerciale = evaluer_biens_commerciaux
