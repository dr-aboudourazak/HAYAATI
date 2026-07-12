"""
MOTEUR DE CALCUL DE LA ZAKAT COMMERCIALE ET IMMOBILIÈRE (CORE/ZAKAT/COMMERCE.PY)
Traduction des règles d'évaluation des actifs marchands et investissements modernes.
"""

def evaluer_zakat_commerciale(valeur_marchandises_gros, liquidites_entreprise, dettes_fournisseurs_court_terme, actions_speculation, actions_long_terme, immo_revente, loyers_accumules):
    """
    Calcule l'assiette imposable des investissements, commerces et biens immobiliers.
    Les règles du Knowledge Book stipulent que seuls les actifs circulants/liquides sont taxés.
    Les actifs immobilisés (murs du magasin, étagères, outils de production) sont exclus.
    """
    
    assiette_commerce = 0.0
    
    # 1. ÉVALUATION DU FONDS DE COMMERCE
    # Base imposable = (Marchandises estimées au prix de gros actuel + Cash en caisse/compte pro) - Dettes à court terme
    actif_circulant_boutique = valeur_marchandises_gros + liquidites_entreprise
    passif_deductible = dettes_fournisseurs_court_terme
    
    net_commercial = actif_circulant_boutique - passif_deductible
    if net_commercial > 0:
        assiette_commerce += net_commercial

    # 2. TRAITEMENT DES ACTIONS BOURSIÈRES (RÈGLE MODERNE DU KB)
    # Court terme (Trading) : Taxé sur la valeur totale du marché (100%)
    assiette_commerce += actions_speculation
    
    # Long terme (Rendement) : Taxé uniquement sur la part liquide de l'entreprise (Forfait prudentiel à 25%)
    assiette_commerce += (actions_long_terme * 0.25)

    # 3. TRAITEMENT DE L'IMMOBILIER
    # Biens destinés à la revente (Promotion/Achat-revente) : Estimés à la valeur marchande (100%)
    assiette_commerce += immo_revente
    
    # Biens locatifs : La structure physique est exonérée, seuls les loyers perçus et épargnés sont inclus
    assiette_commerce += loyers_accumules

    return {
        "assiette_commerciale_pure": max(0.0, net_commercial),
        "assiette_investissements_modernes": actions_speculation + (actions_long_terme * 0.25),
        "assiette_immobiliere": immo_revente + loyers_accumules,
        "assiette_globale_commerce_contribuee": max(0.0, assiette_commerce)
    }
