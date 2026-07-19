"""
MOTEUR D'ANALYSE DE LA MOUHASABAH SPIRITUELLE (CORE/MOUHASABAH_ENGINE.PY)
Version 1.0 - Version condensée sécurisée sans aucun risque de débordement.
"""
from core.db_profil import extraire_historique_mouhasabah

def calculer_bilan_mensuel_spirituel(user_id, jours_mois_lunaire=30):
    """Analyse l'historique récent de pratique pour extraire les indicateurs d'assiduité."""
    historique = extraire_historique_mouhasabah(user_id, limite=jours_mois_lunaire)
    if not historique:
        return {"erreur": "Aucune donnée enregistrée pour ce mois lunaire."}

    total_jours = len(historique)
    prieres_attendues = total_jours * 5
    
    validees_prieres = 0
    total_nawafil = 0
    jours_jeunes = 0
    cumul_sadaqah = 0.0
    pages_coran = 0

    # Consolidation mathématique au fil du mois hégirien
    for jour in historique:
        validees_prieres += jour.get("prieres_obligatoires_validees", 0)
        total_nawafil += jour.get("rakahs_nawafil", 0)
        jours_jeunes += jour.get("jeune_jour_valide", 0)
        cumul_sadaqah += float(jour.get("sadaqah_versee", 0.0))
        pages_coran += jour.get("lecture_coran_pages", 0)

    taux_prieres = (validees_prieres / prieres_attendues) * 100 if prieres_attendues > 0 else 0.0

    return {
        "jours_analyses": total_jours,
        "taux_prieres_pourcentage": taux_prieres,
        "total_prieres": validees_prieres,
        "total_nawafil": total_nawafil,
        "total_jeunes": jours_jeunes,
        "total_coran_pages": pages_coran,
        "total_sadaqah": cumul_sadaqah
    }
