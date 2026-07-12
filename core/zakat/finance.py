"""
MOTEUR DE CALCUL DE LA ZAKAT FINANCIÈRE (CORE/ZAKAT/FINANCE.PY)
Traduction exhaustive des règles métiers du Knowledge Book.
"""

def evaluer_zakat_financiere(liquidites, or_investissement, bijoux_personnels, crypto_trading, crypto_long_terme, cours_or_gramme, madhhab="maliki"):
    """
    Calcule l'éligibilité et le montant exact de la Zakat sur les avoirs financiers.
    Taux applicable : 2,5% (0.025)
    Seuil (Nissab) : Valeur de 85 grammes d'or pur.
    """
    
    # 1. Détermination du Nissab monétaire actuel (85g d'or pur)
    seuil_nissab = 85.0 * cours_or_gramme
    
    # 2. Consolidation de la masse de calcul de base
    # Le cash, l'or d'investissement et la crypto de trading sont pris en compte à 100%
    patrimoine_imposable = liquidites + or_investissement + crypto_trading
    
    # 3. Application des règles d'écoles (Divergences du Fiqh du Knowledge Book)
    madhhab_selectionne = madhhab.lower()
    
    if madhhab_selectionne == "hanafi":
        # L'école Hanafi inclut obligatoirement l'or personnel peu importe l'intention de parure
        patrimoine_imposable += bijoux_personnels
    else:
        # Écoles Maliki, Shafi'i, Hanbali : Exonération des bijoux de parure licite
        pass
        
    # 4. Traitement des investissements Crypto Long Terme
    # Application d'une assiette forfaitaire prudente de 25% de la valeur totale (représentant la liquidité imposable)
    fraction_taxable_crypto_long = crypto_long_terme * 0.25
    patrimoine_imposable += fraction_taxable_crypto_long
    
    # 5. Vérification du franchissement de seuil (Nissab) et calcul de l'impôt
    if patrimoine_imposable >= seuil_nissab:
        montant_zakat = patrimoine_imposable * 0.025
        return {
            "eligible": True,
            "patrimoine_total_consolide": patrimoine_imposable,
            "seuil_nissab_calculer": seuil_nissab,
            "montant_zakat_du": round(montant_zakat, 2),
            "madhhab_applique": madhhab_selectionne
        }
    
    return {
        "eligible": False,
        "patrimoine_total_consolide": patrimoine_imposable,
        "seuil_nissab_calculer": seuil_nissab,
        "montant_zakat_du": 0.0,
        "madhhab_applique": madhhab_selectionne
    }
