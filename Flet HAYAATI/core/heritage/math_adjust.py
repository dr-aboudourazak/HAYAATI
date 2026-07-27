"""
MOTEUR DE RÉGULATION ARITHMÉTIQUE SHARIA (CORE/HERITAGE/MATH_ADJUST.PY)
Version 5.0 - Alignement doctrinal sur le Radd et l'Aoul face aux 21 candidats canoniques.
"""

def ajuster_proportions_sharia(dictionnaire_fractions_base, doctrine_active="Malikite"):
    """
    Analyse la somme des parts de la session.
    Applique l'Aoul (si > 1) ou le Radd (si < 1) selon les divergences des écoles.
    """
    if not dictionnaire_fractions_base:
        return {}

    somme_parts = sum(dictionnaire_fractions_base.values())
    fractions_ajustees = dictionnaire_fractions_base.copy()
    doctrine = str(doctrine_active).strip().capitalize()

    # --- CAS A : L'AOUL (Somme des parts fixes > 1.0) ---
    # Consensus absolu (Ijma') des 4 écoles : réduction proportionnelle de tous les ayants droit
    if somme_parts > 1.0001:
        for heritier in fractions_ajustees.keys():
            fractions_ajustees[heritier] = dictionnaire_fractions_base[heritier] / somme_parts
        return fractions_ajustees

    # --- CAS B : LE RADD (Somme des parts fixes < 1.0) ---
    elif somme_parts < 0.9999:
        # Les héritiers universels (Asabah) comme le fils, le frère, etc., ne subissent pas le Radd 
        # car ils ramassent déjà nativement le reliquat dans fractions.py.
        # Le Radd ne s'applique que s'il reste un surplus et qu'il n'y a QUE des héritiers à parts fixes coraniques.
        
        # Identification des héritiers de sang (Fards) admissibles au Radd (Exclusion des conjoints)
        heritiers_de_sang = [h for h in fractions_ajustees.keys() if h not in ["epouse", "epoux"]]
        
        if heritiers_de_sang:
            # 🍏 DIVERGENCE DE L'ÉCOLE MALIKITE : Pas de Radd historique. 
            # Les héritiers de sang gardent leur part fixe coranique stricte, le reliquat revient au Bayt Al-Mal.
            if doctrine == "Malikite":
                return fractions_ajustees
                
            # ⚖️ ÉCOLES HANAFITE, HANBALITE ET FIQH CHAFI'ITE TARDIFA : Application du Radd
            somme_sang = sum(dictionnaire_fractions_base[h] for h in heritiers_de_sang)
            if somme_sang > 0:
                part_conjoint = dictionnaire_fractions_base.get("epouse", dictionnaire_fractions_base.get("epoux", 0.0))
                masse_a_partager_radd = 1.0 - part_conjoint
                
                # Redistribution du reliquat proportionnellement aux parts de sang
                for h in heritiers_de_sang:
                    poids_relatif = dictionnaire_fractions_base[h] / somme_sang
                    fractions_ajustees[h] = poids_relatif * masse_a_partager_radd
                return fractions_ajustees
                
        # DIVERGENCE COMPTABLE CRUCIALE : S'il ne reste absolument QUE le conjoint survivant seul
        elif "epouse" in fractions_ajustees or "epoux" in fractions_ajustees:
            conjoint_cle = "epouse" if "epouse" in fractions_ajustees else "epoux"
            
            # 🛡️ ÉCOLE HANBALITE (et avis hanafite moderne tardif) : 
            # Le conjoint récupère Exceptionnellement le reliquat pour éviter l'expropriation par l'État
            if doctrine in ["Hanbalite", "Hanafite"]:
                fractions_ajustees[conjoint_cle] = 1.0
            else:
                # Chez les Malékites et Chafi'ites classiques, le conjoint est bloqué à sa part fixe coranique,
                # le reliquat est souverainement versé au Trésor Public (Bayt Al-Mal).
                fractions_ajustees[conjoint_cle] = dictionnaire_fractions_base[conjoint_cle]

    return fractions_ajustees
