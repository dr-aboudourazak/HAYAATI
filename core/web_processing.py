"""
MOTEUR DE TRAITEMENT CENTRAL POUR L'APPLICATION WEB MOBILE (CORE/WEB_PROCESSING.PY)
"""
from core.zakat.finance import evaluer_zakat_financiere
from core.zakat.commerce import evaluer_zakat_commerciale
from core.zakat.agriculture import evaluer_zakat_agricole, evaluer_zakat_elevage_ovins
from core.heritage.exclusions import appliquer_moteur_exclusions
from core.heritage.fractions import distribuer_parts_completes

def executer_calculs_zakat_web(stocks, pro_cash, dettes, cash, bijoux, cours, madhhab, recolte, elevage):
    """Exécute les trois axes de calculs de la Zakat et centralise les bilans."""
    bilan_com = evaluer_zakat_commerciale(stocks, pro_cash, dettes, 0.0, 0.0, 0.0, 0.0)
    masse_pro = bilan_com["assiette_globale_commerce_contribuee"]
    
    return {
        "financier": evaluer_zakat_financiere(cash + masse_pro, 0.0, bijoux, 0.0, 0.0, cours, madhhab),
        "agricole": evaluer_zakat_agricole(recolte, "naturelle"),
        "elevage": evaluer_zakat_elevage_ovins(elevage)
    }

def executer_partage_heritage_web(config_nombres, famille_brute, exceptions, hors_mariage):
    """Filtre les exclusions et distribue les parts successorales par nombre."""
    if hors_mariage:
        for cpt in ["pere", "grand_pere", "frere_germain", "oncle"]:
            if cpt in famille_brute and cpt not in exceptions:
                exceptions.append(cpt)

    bilan_ex = appliquer_moteur_exclusions(famille_brute, cas_indignite=exceptions)
    bilan_parts = distribuer_parts_completes(bilan_ex["heritiers_valides"], config_nombres)
    
    return {
        "ventilation": bilan_parts["ventilation_fractions"],
        "is_kalalah": bilan_parts["is_kalalah_detected"],
        "exclus_totaux": list(set(bilan_ex["personnes_exclues"] + bilan_ex["indignes_elimines"]))
    }
