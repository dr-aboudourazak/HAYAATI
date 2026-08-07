"""
MOTEUR DE RÉGULATION ARITHMÉTIQUE SHARIA (CORE/HERITAGE/MATH_ADJUST.PY)
Version 5.3 - Shield Maître Anti-Fuite du Radd Partiel et Protection du Conjoint
"""

def ajuster_proportions_sharia(dictionnaire_fractions_base, doctrine_active="Malikite"):
    """
    Analyse la somme des parts de la session et applique l'Aoul ou le Radd de manière étanche.
    """
    if not dictionnaire_fractions_base:
        return {}

    somme_parts = sum(dictionnaire_fractions_base.values())
    fractions_ajustees = dictionnaire_fractions_base.copy()
    doctrine = str(doctrine_active).strip().capitalize()

    # --- CAS A : L'AOUL (Somme des parts fixes > 1.0) ---
    if somme_parts > 1.0001:
        for heritier in fractions_ajustees.keys():
            fractions_ajustees[heritier] = dictionnaire_fractions_base[heritier] / somme_parts
        return fractions_ajustees

    # --- CAS B : LE RADD (Somme des parts fixes < 1.0) ---
    elif somme_parts < 0.9999:
        if abs(somme_parts - 1.0) < 0.001:
            return fractions_ajustees

        heritiers_de_sang = [h for h in fractions_ajustees.keys() if h not in ["epouse", "epoux", "###"]]
        
        if heritiers_de_sang:
            # 🌟 FIX RADD MALIKITE SANS CONJOINT : Si l'école est Malikite, le surplus ne va pas 
            # aux héritiers de sang, mais il NE DOIT PAS S'ÉVAPORER. On ne fait plus un 'return' immédiat.
            # On laisse le code s'exécuter pour que le bouclier final "###" capture la fuite.
            if doctrine != "Malikite":
                # Écoles Hanafite, Hanbalite, Chafi'ite tardive : Le Radd s'applique normalement
                somme_sang = sum(dictionnaire_fractions_base[h] for h in heritiers_de_sang)
                if somme_sang > 0:
                    part_conjoint = dictionnaire_fractions_base.get("epouse", dictionnaire_fractions_base.get("epoux", 0.0))
                    masse_a_partager_radd = 1.0 - part_conjoint
                    
                    for h in heritiers_de_sang:
                        poids_relatif = dictionnaire_fractions_base[h] / somme_sang
                        fractions_ajustees[h] = poids_relatif * masse_a_partager_radd
                    return fractions_ajustees
                
        elif "epouse" in fractions_ajustees or "epoux" in fractions_ajustees:
            conjoint_cle = "epouse" if "epouse" in fractions_ajustees else "epoux"
            # Blocage absolu du Radd sur le Conjoint (Consensus des 4 Écoles)
            fractions_ajustees[conjoint_cle] = dictionnaire_fractions_base[conjoint_cle]

    # =========================================================================
    # 🌟 LE COUSSIN DE SÉCURITÉ ARITHMÉTIQUE DE SECOURS ("###")
    # =========================================================================
    # Si le budget n'est toujours pas bouclé à 1.0 (cas Malikite sans Radd, ou anomalie),
    # la clé "###" intercepte instantanément l'excédent pour verrouiller la balance à 100%.
    somme_verification_finale = sum(fractions_ajustees.values())
    reliquat_absolu_restant = 1.0 - somme_verification_finale
    
    if reliquat_absolu_restant > 0.0001:
        fractions_ajustees["###"] = fractions_ajustees.get("###", 0.0) + reliquat_absolu_restant

    return fractions_ajustees
