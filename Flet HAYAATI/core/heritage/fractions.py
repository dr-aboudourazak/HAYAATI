"""
LOGIQUE ATOMIQUE - QUOTAS ET FRACTIONS DES 21 CATÉGORIES (CORE/HERITAGE/FRACTIONS.PY)
Version 5.0 - Intégration exhaustive des 21 candidats canoniques et divergences par Écoles.
"""
from core.heritage.math_adjust import ajuster_proportions_sharia

def determiner_quotas_fixes_de_base(dictionnaire_heritiers, doctrine_active="Malikite"):
    if not dictionnaire_heritiers:
        return {}
        
    quotas = {}
    doc = str(doctrine_active).strip().capitalize()
    
    # 🎯 1. DÉTECTION DES BLOCAGES ET EXCLUSIONS CANONIQUES DE LA SHARIA
    # Descendants directs et en ligne descendante
    a_descendants_directs = (dictionnaire_heritiers.get("fils", 0) > 0 or dictionnaire_heritiers.get("fille", 0) > 0)
    a_descendants_totaux = (a_descendants_directs or dictionnaire_heritiers.get("petit_fils", 0) > 0 or dictionnaire_heritiers.get("petite_fille", 0) > 0)
    
    # Ascendants directs
    a_pere = dictionnaire_heritiers.get("pere", 0) > 0
    a_mere = dictionnaire_heritiers.get("mere", 0) > 0
    a_grand_pere = dictionnaire_heritiers.get("grand_pere", 0) > 0 and not a_pere
    
    # Règle d'or : Le père et le fils bloquent toute la lignée collatérale résiduelle
    a_pere_ou_fils_ou_petit_fils = (a_pere or dictionnaire_heritiers.get("fils", 0) > 0 or dictionnaire_heritiers.get("petit_fils", 0) > 0)

    # 🎯 2. CALCUL DES PARTS FIXES DES CONJOINTS (SÉPARÉS)
    if "epouse" in dictionnaire_heritiers: 
        quotas["epouse"] = 0.125 if a_descendants_totaux else 0.25  
    if "epoux" in dictionnaire_heritiers: 
        quotas["epoux"] = 0.25 if a_descendants_totaux else 0.50   

    # 🎯 3. CALCUL DES PARTS FIXES DES ASCENDANTS DIRECTS
    if a_pere: 
        quotas["pere"] = 0.1666 if a_descendants_totaux else 0.0   
    if a_mere: 
        # La mère prend 1/6 s'il y a des descendants ou une fratrie multiple (>1 frères/sœurs)
        nb_fratrie_totale = sum(dictionnaire_heritiers.get(f, 0) for f in ["frere_germain", "soeur_germaine", "frere_paternel", "soeur_paternelle", "frere_uterin", "soeur_uterine"])
        quotas["mere"] = 0.1666 if (a_descendants_totaux or nb_fratrie_totale > 1) else 0.3333 

    # Grand-mère (Exclue si la mère est vivante)
    if "grand_mere" in dictionnaire_heritiers and not a_mere:
        quotas["grand_mere"] = 0.1666 

    # 🎯 4. BRANCHEMENTS CONDITIONNELS DES EXCLUSIONS PROPRES AUX ÉCOLES (GRAND-PÈRE)
    nb_fr_germ = dictionnaire_heritiers.get("frere_germain", 0)
    nb_sr_germ = dictionnaire_heritiers.get("soeur_germaine", 0)
    nb_fr_pat = dictionnaire_heritiers.get("frere_paternel", 0)
    nb_sr_pat = dictionnaire_heritiers.get("soeur_paternelle", 0)
    
    if a_grand_pere:
        if (nb_fr_germ == 0 and nb_sr_germ == 0 and nb_fr_pat == 0 and nb_sr_pat == 0):
            quotas["grand_pere"] = 0.1666 if a_descendants_totaux else 0.0
        elif doc == "Hanafite":
            # ⚖️ FIQH HANAFITE : Le Grand-père agit comme le Père et exclut totalement la fratrie
            quotas["grand_pere"] = 0.1666 if a_descendants_totaux else 0.0

    # 🎯 5. DISTRIBUTIONS DE LA LIGNÉE DESCENDANTE (FILLES ET PETITES-FILLES)
    nb_fils = dictionnaire_heritiers.get("fils", 0)
    nb_fille = dictionnaire_heritiers.get("fille", 0)
    nb_p_fils = dictionnaire_heritiers.get("petit_fils", 0)
    nb_p_fille = dictionnaire_heritiers.get("petite_fille", 0)
    
    if nb_fils == 0 and nb_fille > 0:
        quotas["fille"] = 0.50 if nb_fille == 1 else 0.6666 
        # Complément du tiers (1/6) pour la petite-fille s'il y a une seule fille unique
        if nb_fille == 1 and nb_p_fille > 0 and nb_p_fils == 0:
            quotas["petite_fille"] = 0.1666
    elif nb_fils > 0:
        # Règle coranique du double ratio (2 pour un fils, 1 pour une fille) s'il y a un reliquat Asabah
        somme_deja = sum(quotas.values())
        reliquat = 1.0 - somme_deja
        if reliquat > 0:
            parts_totales = (nb_fils * 2) + nb_fille
            part_u = reliquat / parts_totales
            if nb_fille > 0: quotas["fille"] = part_u * nb_fille
            quotas["fils"] = part_u * 2 * nb_fils

    # Gestion de secours des petits-enfants si aucun fils direct n'est vivant
    if nb_fils == 0 and nb_fille == 0 and nb_p_fils > 0:
        somme_deja = sum(quotas.values())
        reliquat = 1.0 - somme_deja
        if reliquat > 0:
            parts_p = (nb_p_fils * 2) + nb_p_fille
            part_u = reliquat / parts_p
            if nb_p_fille > 0: quotas["petite_fille"] = part_u * nb_p_fille
            quotas["petit_fils"] = part_u * 2 * nb_p_fils

    # 🎯 6. RÈGLE CO-PARTAGE DU GRAND-PÈRE ET DE LA FRATRIE (ÉCOLES MALIKITE, CHAFI'ITE, HANBALITE)
    if a_grand_pere and doc != "Hanafite":
        if (nb_fr_germ > 0 or nb_sr_germ > 0 or nb_fr_pat > 0 or nb_sr_pat > 0):
            somme_actuelle = sum(quotas.values())
            reliquat_total = 1.0 - somme_actuelle
            
            # Application de l'arbitrage prudent de l'intérêt maximal du grand-père (Avis de Zaïd)
            option_un_tiers_reliquat = reliquat_total / 3.0
            total_tetes_fratrie = nb_fr_germ + nb_fr_pat + ((nb_sr_germ + nb_sr_pat) * 0.5) + 1.0
            option_partage_egal = reliquat_total / total_tetes_fratrie
            
            meilleure_part_gp = max(option_un_tiers_reliquat, option_partage_egal, 0.1666)
            quotas["grand_pere"] = meilleure_part_gp
            
            # Redistribution du reliquat de la fratrie aux collatéraux
            reliquat_fratrie = reliquat_total - meilleure_part_gp
            if reliquat_fratrie > 0:
                tetes_f = ((nb_fr_germ + nb_fr_pat) * 2) + nb_sr_germ + nb_sr_pat
                if tetes_f > 0:
                    u_f = reliquat_fratrie / tetes_f
                    if nb_fr_germ > 0: quotas["frere_germain"] = u_f * 2 * nb_fr_germ
                    if nb_sr_germ > 0: quotas["soeur_germaine"] = u_f * nb_sr_germ
                    if nb_fr_pat > 0 and nb_fr_germ == 0: quotas["frere_paternel"] = u_f * 2 * nb_fr_pat
                    if nb_sr_pat > 0 and nb_fr_germ == 0: quotas["soeur_paternelle"] = u_f * nb_sr_pat

    # 🎯 7. COLLATÉRAUX ET FRATRIE UTÉRINE (EXCLUS SI PÈRE OU DESCENDANTS MÂLES SONT VIVANTS)
    else:
        if not a_pere_ou_fils_ou_petit_fils:
            # Frères et sœurs utérins (Partagent à parts égales d'après le Coran)
            nb_uterins = dictionnaire_heritiers.get("frere_uterin", 0) + dictionnaire_heritiers.get("soeur_uterine", 0)
            if nb_uterins > 0:
                part_uterins_globale = 0.1666 if nb_uterins == 1 else 0.3333
                if dictionnaire_heritiers.get("frere_uterin", 0) > 0: 
                    quotas["frere_uterin"] = (part_uterins_globale / nb_uterins) * dictionnaire_heritiers["frere_uterin"]
                if dictionnaire_heritiers.get("soeur_uterine", 0) > 0: 
                    quotas["soeur_uterine"] = (part_uterins_globale / nb_uterins) * dictionnaire_heritiers["soeur_uterine"]
            
            # Sœurs germaines et paternelles (Parts fixes si aucun frère mâle Asabah n'est vivant)
            if nb_fr_germ == 0 and nb_sr_germ > 0:
                quotas["soeur_germaine"] = 0.50 if nb_sr_germ == 1 else 0.6666
            if nb_fr_germ == 0 and nb_fr_pat == 0 and nb_sr_pat > 0:
                quotas["soeur_paternelle"] = 0.50 if (nb_sr_germ == 0 and nb_sr_pat == 1) else 0.1666 if nb_sr_germ == 1 else 0.0

    # 🎯 8. LIQUIDATION DES HÉRITIERS RÉSIDUELS DE SECOURS (AL-’ASABÂT EXTRA-PROCHES)
    # S'il reste du patrimoine et qu'aucun descendant ou frère n'a épuisé le budget
    somme_intermediaire = sum(quotas.values())
    if interstate_reliquat := (1.0 - somme_intermediaire) > 0:
        asabah_prioritaires = [
            "frere_paternel", "fils_frere_germain", "fils_frere_paternel",
            "oncle_germain", "oncle_paternel", "cousin_germain", "cousin_paternel"
        ]
        for h_secours in asabah_prioritaires:
            if dictionnaire_heritiers.get(h_secours, 0) > 0 and not a_pere_ou_fils_ou_petit_fils:
                # Le premier Asabah vivant dans l'ordre de proximité Sharia rafle le reliquat restant
                quotas[h_secours] = interstate_reliquat
                break

    # Passation à la matrice de correction Sharia (Aoul / Radd) selon la doctrine active
    quotas_ajustes = ajuster_proportions_sharia(quotas, doctrine_active=doc)
    return quotas_ajustes

def _distribuer_parts_completes_compat(dictionnaire_heritiers, configuration_nombres=None, doctrine_active="Malikite"):
    if not dictionnaire_heritiers:
        return {"ventilation_fractions": {}, "distribution_monetaire": {}, "reliquat_patrimoine": 0.0, "statut_calcul": "Aucun héritier"}
    fractions_calculees = determiner_quotas_fixes_de_base(dictionnaire_heritiers, doctrine_active=doctrine_active)
    return {"ventilation_fractions": fractions_calculees, "distribution_monetaire": {}, "reliquat_patrimoine": 0.0, "statut_calcul": "Succès"}

distribuer_parts_completes = _distribuer_parts_completes_compat
