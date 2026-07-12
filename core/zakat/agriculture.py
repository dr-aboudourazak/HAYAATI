"""
MOTEUR DE CALCUL DE LA ZAKAT AGRICOLE ET DE L'ÉLEVAGE (CORE/ZAKAT/AGRICULTURE.PY)
Traduction des barèmes spécifiques du Knowledge Book (Seuils de récolte et paliers du bétail).
"""

def evaluer_zakat_agricole(kilos_recolte, type_irrigation):
    """
    Calcule la Zakat sur les récoltes (céréales/fruits stockables).
    Seuil (Nissab) = 5 Awsuq, estimé traditionnellement à environ 653 kg.
    Pas de condition de durée d'un an (Al-Hawl) : payrable le jour de la récolte.
    """
    SEUIL_RECOLTE_KG = 653.0
    
    if kilos_recolte >= SEUIL_RECOLTE_KG:
        # Détermination du taux selon la méthode d'irrigation du Knowledge Book
        if type_irrigation.lower() == "naturelle":
            taux = 0.10  # 10% (Pluie, rivières)
        elif type_irrigation.lower() == "artificielle":
            taux = 0.05  # 5% (Pompes, coûts humains, efforts)
        else:
            taux = 0.075 # 7,5% (Mixte - Prudence jurisprudentielle)
            
        montant_du_kg = kilos_recolte * taux
        return {
            "eligible": True,
            "seuil_kg": SEUIL_RECOLTE_KG,
            "taux_applique": taux,
            "zakat_due_kg": round(montant_du_kg, 2),
            "motif": f"Zakat exigible le jour de la récolte au taux de {taux*100}%."
        }
        
    return {
        "eligible": False,
        "seuil_kg": SEUIL_RECOLTE_KG,
        "taux_applique": 0.0,
        "zakat_due_kg": 0.0,
        "motif": "Récolte inférieure au Nissab (653 kg). Aucune Zakat due."
    }


def evaluer_zakat_elevage_ovins(nombre_tetes):
    """
    Calcule la Zakat sur le bétail (Ovins : Moutons/Chèvres) basé sur les pâturages naturels.
    Application stricte des paliers du Knowledge Book (Sunnah).
    """
    if nombre_tetes < 40:
        return {"eligible": False, "moutons_dus": 0, "motif": "Sous le Nissab (Moins de 40 têtes)."}
    elif 40 <= nombre_tetes <= 120:
        return {"eligible": True, "moutons_dus": 1, "motif": "Palier 40-120 têtes : 1 mouton dû."}
    elif 121 <= nombre_tetes <= 200:
        return {"eligible": True, "moutons_dus": 2, "motif": "Palier 121-200 têtes : 2 moutons dus."}
    elif 201 <= nombre_tetes <= 399:
        return {"eligible": True, "moutons_dus": 3, "motif": "Palier 201-399 têtes : 3 moutons dus."}
    else:
        # À partir de 400, la règle change : 1 mouton par tranche de 100 têtes supplémentaire
        moutons_calculat = nombre_tetes // 100
        return {"eligible": True, "moutons_dus": moutons_calculat, "motif": f"Règle proportionnelle : 1 mouton par tranche de 100 ({moutons_calculat} dus)."}
