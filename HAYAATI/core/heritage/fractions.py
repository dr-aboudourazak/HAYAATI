"""
LOGIQUE ATOMIQUE - QUOTAS ET FRACTIONS DES 21 CATÉGORIES (CORE/HERITAGE/FRACTIONS.PY)
Version 5.9 - Résolution récursive unifiée, purge des clés à 0 et normalisation du Khountha.
"""
from core.heritage.math_adjust import ajuster_proportions_sharia

def determiner_quotas_fixes_de_base(dictionnaire_heritiers, doctrine_active="Malikite"):
    if not dictionnaire_heritiers:
        return {}
        
    quotas = {}
    doc = str(doctrine_active).strip().capitalize()
       
    # 🎯 ALIGNEMENT UNIFIÉ DES MODES : Extraction des métadonnées de contrôle
    cas_khountha = dictionnaire_heritiers.get("cas_khountha_actif", False)
    if str(cas_khountha).lower() in ["true", "1"]: cas_khountha = True
    
    cas_arham = dictionnaire_heritiers.get("cas_zawil_arham_actif", False)
    if str(cas_arham).lower() in ["true", "1"]: cas_arham = True
    
    # --- BLOCK EXTENSION 1 : KHOUNTHA MOSHKIL (RÉSOLUTION RÉCURSIVE UNIFIÉE) ---
    if cas_khountha:
        arbre_sim_m = {k: v for k, v in dictionnaire_heritiers.items() if k not in ["cas_khountha_actif", "cas_zawil_arham_actif", "sexe_defunt"]}
        arbre_sim_f = arbre_sim_m.copy()
        
        arbre_sim_m["fils"] = arbre_sim_m.get("fils", 0) + 1
        arbre_sim_f["fille"] = arbre_sim_f.get("fille", 0) + 1
        
        res_m = determiner_quotas_fixes_de_base(arbre_sim_m, doctrine_active=doc)
        res_f = determiner_quotas_fixes_de_base(arbre_sim_f, doctrine_active=doc)
        
        quotas_fusionnes = {}
        tous_les_heritiers = set(list(res_m.keys()) + list(res_f.keys()))
        
        if doc == "Hanafite":
            part_fille_khountha = res_f.get("fille", 0.0) / arbre_sim_f.get("fille", 1)
            for h in tous_les_heritiers:
                if h == "fille" and dictionnaire_heritiers.get("fille", 0) > 0:
                    quotas_fusionnes["fille"] = res_f.get("fille", 0.0) - part_fille_khountha
                elif h == "fils":
                    quotas_fusionnes["fils"] = res_f.get("fils", 0.0)
                else:
                    quotas_fusionnes[h] = res_f.get(h, 0.0)
            quotas_fusionnes["khountha"] = part_fille_khountha
            quotas = quotas_fusionnes
        else:
            u_kh_m = res_m.get("fils", 0.0) / arbre_sim_m.get("fils", 1)
            u_kh_f = res_f.get("fille", 0.0) / arbre_sim_f.get("fille", 1)
            quotas_fusionnes["khountha"] = (u_kh_m + u_kh_f) / 2.0
            for h in tous_les_heritiers:
                if h == "fils":
                    quotas_fusionnes["fils"] = ((res_m.get("fils", 0.0) - u_kh_m) + res_f.get("fils", 0.0)) / 2.0
                elif h == "fille":
                    quotas_fusionnes["fille"] = (res_m.get("fille", 0.0) + (res_f.get("fille", 0.0) - u_kh_f)) / 2.0
                else:
                    quotas_fusionnes[h] = (res_m.get(h, 0.0) + res_f.get(h, 0.0)) / 2.0
            quotas = quotas_fusionnes

    # --- BLOCK EXTENSION 2 : ZAWIL ARHAM ---
    elif cas_arham:
        quotas_arham = {}
        if doc in ["Hanafite", "Hanbalite"]:
            qte_hommes = int(dictionnaire_heritiers.get("frere_uterin", 0))
            qte_femmes = int(dictionnaire_heritiers.get("soeur_uterine", 0))
            total_parts_arham = (qte_hommes * 2) + qte_femmes
            if total_parts_arham > 0:
                fraction_unitaire = 1.0 / total_parts_arham
                if qte_hommes > 0: quotas_arham["frere_uterin"] = fraction_unitaire * 2 * qte_hommes
                if qte_femmes > 0: quotas_arham["soeur_uterine"] = fraction_unitaire * qte_femmes
                quotas = quotas_arham
        else:
            quotas = {}

    # --- TRAITEMENT STANDARD DES CAS ORDINAIRES ---
    if not cas_khountha and not cas_arham:
        # 🎯 1. DÉTECTION DES COMPOSANTS ET ÉLÉMENTS DE LA FRATRIE
        a_descendants_directs = (dictionnaire_heritiers.get("fils", 0) > 0 or dictionnaire_heritiers.get("fille", 0) > 0)
        a_descendants_totaux = (a_descendants_directs or dictionnaire_heritiers.get("petit_fils", 0) > 0 or dictionnaire_heritiers.get("petite_fille", 0) > 0)
        
        a_pere = dictionnaire_heritiers.get("pere", 0) > 0
        a_mere = dictionnaire_heritiers.get("mere", 0) > 0
        a_grand_pere = dictionnaire_heritiers.get("grand_pere", 0) > 0 and dictionnaire_heritiers.get("pere", 0) == 0
        
        nb_fr_germ = dictionnaire_heritiers.get("frere_germain", 0)
        nb_sr_germ = dictionnaire_heritiers.get("soeur_germaine", 0)
        nb_fr_pat = dictionnaire_heritiers.get("frere_paternel", 0)
        nb_sr_pat = dictionnaire_heritiers.get("soeur_paternelle", 0)
        nb_fr_ut = dictionnaire_heritiers.get("frere_uterin", 0)
        nb_sr_ut = dictionnaire_heritiers.get("soeur_uterine", 0)
        
        nb_fratrie_totale = nb_fr_germ + nb_sr_germ + nb_fr_pat + nb_sr_pat + nb_fr_ut + nb_sr_ut
        a_pere_ou_fils_ou_petit_fils = (a_pere or dictionnaire_heritiers.get("fils", 0) > 0 or dictionnaire_heritiers.get("petit_fils", 0) > 0)

        # =========================================================================
        # 🎯 SHIELD MAÎTRE : CAS DE LA MOUSHTARAKAH
        # =========================================================================
        if "epoux" in dictionnaire_heritiers and a_mere and nb_fr_ut >= 2 and nb_fr_germ > 0 and not a_descendants_totaux:
            if doc in ["Malikite", "Chafi'ite", "Chafiite", "Shafi'ite"]:
                quotas = {"epoux": 0.5, "mere": 0.16666666666666666}
                total_tetes_partage = nb_fr_ut + nb_fr_germ
                part_par_tete = 0.3333333333333333 / total_tetes_partage
                quotas["frere_uterin"] = part_par_tete * nb_fr_ut
                quotas["frere_germain"] = part_par_tete * nb_fr_germ
                return quotas

        # =========================================================================
        # 🎯 SHIELD MAÎTRE : CAS DE L'AKDARIYYAH
        # =========================================================================
        if "epoux" in dictionnaire_heritiers and a_mere and nb_sr_germ == 1 and a_grand_pere and nb_fratrie_totale == 1 and not a_descendants_totaux:
            if doc != "Hanafite":
                return {
                    "epoux": 0.3333333333333333,       # 9/27
                    "mere": 0.2222222222222222,        # 6/27
                    "grand_pere": 0.2962962962962963,  # 8/27
                    "soeur_germaine": 0.14814814814814814 # 4/27
                }
      
        # 🎯 2. CALCUL DES PARTS FIXES DES CONJOINTS
        if "epouse" in dictionnaire_heritiers: quotas["epouse"] = 0.125 if a_descendants_totaux else 0.25  
        if "epoux" in dictionnaire_heritiers: quotas["epoux"] = 0.25 if a_descendants_totaux else 0.50   

        # 🎯 3. ARBITRAGE CRITIQUE DES CAS GHARRAWAYN
        est_cas_gharrawayn_pere = (a_pere and a_mere and not a_descendants_totaux and nb_fratrie_totale <= 1 and ("epoux" in dictionnaire_heritiers or "epouse" in dictionnaire_heritiers))
        est_cas_gharrawayn_gp = (a_grand_pere and a_mere and not a_descendants_totaux and nb_fratrie_totale <= 1 and ("epoux" in dictionnaire_heritiers or "epouse" in dictionnaire_heritiers))

        if est_cas_gharrawayn_pere:
            part_conjoint = quotas.get("epoux", quotas.get("epouse", 0.0))
            reliquat_conjoint = 1.0 - part_conjoint
            quotas["mere"] = reliquat_conjoint / 3.0
            quotas["pere"] = (reliquat_conjoint * 2.0) / 3.0
        elif est_cas_gharrawayn_gp:
            part_conjoint = quotas.get("epoux", quotas.get("epouse", 0.0))
            reliquat_conjoint = 1.0 - part_conjoint
            if doc == "Hanafite":
                quotas["mere"] = reliquat_conjoint / 3.0
                quotas["grand_pere"] = (reliquat_conjoint * 2.0) / 3.0
            else:
                quotas["mere"] = 0.3333333333333333
                residu_gp = reliquat_conjoint - quotas["mere"]
                quotas["grand_pere"] = max(residu_gp, 0.16666666666666666)
        else:
            # 🎯 CAS STANDARDS SORS EXTENSIONS GHARRAWAYN
            if a_mere: 
                quotas["mere"] = 0.16666666666666666 if (a_descendants_totaux or nb_fratrie_totale > 1) else 0.3333333333333333

            # 🎯 INJECTION FIX GRAND-MÈRE UNIVERSELLE CORE HAYAATI
            # L'aïeule est écartée de la répartition par la Mère (a_mere).
            # En école Hanafite, elle est aussi bloquée par le Père s'il s'agit de la lignée paternelle.
            if dictionnaire_heritiers.get("grand_mere", 0) > 0 and not a_mere:
                if doc == "Hanafite" and a_pere:
                    pass
                else:
                    quotas["grand_mere"] = 0.16666666666666666

            if a_pere:
                if dictionnaire_heritiers.get("fils", 0) > 0 or dictionnaire_heritiers.get("petit_fils", 0) > 0 or dictionnaire_heritiers.get("fille", 0) > 0 or dictionnaire_heritiers.get("petite_fille", 0) > 0:
                    quotas["pere"] = 0.16666666666666666
                else: 
                    quotas["pere"] = 0.0  

        # =========================================================================
        # 🎯 4. DISTRIBUTIONS DE LA LIGNÉE DESCENDANTE (FILLES ET PETITES-FILLES FIXÉES)
        # =========================================================================
        nb_fils = dictionnaire_heritiers.get("fils", 0)
        nb_fille = dictionnaire_heritiers.get("fille", 0)
        nb_p_fils = dictionnaire_heritiers.get("petit_fils", 0)
        nb_p_fille = dictionnaire_heritiers.get("petite_fille", 0)
        
        # Cas A : Présence de filles sans fils directs
        if nb_fils == 0 and nb_fille > 0:
            quotas["fille"] = 0.50 if nb_fille == 1 else 0.6666666666666666
            # La petite-fille prend le complément du tiers (1/6) s'il n'y a qu'une seule fille unique
            if nb_fille == 1 and nb_p_fille > 0 and nb_p_fils == 0: 
                quotas["petite_fille"] = 0.16666666666666666
                
        # Cas B : Présence de fils directs (Ta'sib des enfants)
        elif nb_fils > 0:
            somme_deja = sum([v for k, v in quotas.items() if k not in ["cas_khountha_actif", "cas_zawil_arham_actif", "sexe_defunt"]])
            reliquat = 1.0 - somme_deja
            if reliquat > 0:
                parts_totales = (nb_fils * 2) + nb_fille
                part_u = reliquat / parts_totales
                if nb_fille > 0: quotas["fille"] = part_u * nb_fille
                quotas["fils"] = part_u * 2 * nb_fils

        # 🎯 5. FIX CRITIQUE PETITE-FILLE SEULE : Si pas de fils, pas de fille, et pas de petit-fils mâle
        # Elle prend la moitié coranique (1/2) si elle est seule, ou les 2/3 (0.6666) si elles sont plusieurs
        if nb_fils == 0 and nb_fille == 0 and nb_p_fils == 0 and nb_p_fille > 0:
            quotas["petite_fille"] = 0.50 if nb_p_fille == 1 else 0.6666666666666666

        # Cas C : Présence de petits-enfants avec un petit-fils mâle (Ta'sib descendants éloignés)
        elif nb_fils == 0 and nb_fille == 0 and nb_p_fils > 0:
            somme_deja = sum([v for k, v in quotas.items() if k not in ["cas_khountha_actif", "cas_zawil_arham_actif", "sexe_defunt"]])
            reliquat = 1.0 - somme_deja
            if reliquat > 0:
                parts_p = (nb_p_fils * 2) + nb_p_fille
                part_u = reliquat / parts_p
                if nb_p_fille > 0: quotas["petite_fille"] = part_u * nb_p_fille
                quotas["petit_fils"] = part_u * 2 * nb_p_fils


        # 🎯 6. RÈGLE CO-PARTAGE DU GRAND-PÈRE ET DE LA FRATRIE
        if a_grand_pere and doc != "Hanafite":
            if (nb_fr_germ > 0 or nb_sr_germ > 0 or nb_fr_pat > 0 or nb_sr_pat > 0):
                somme_actuelle = sum(quotas.values())
                reliquat_total = 1.0 - somme_actuelle
                option_un_tiers_reliquat = reliquat_total / 3.0
                total_tetes_fratrie = nb_fr_germ + nb_fr_pat + ((nb_sr_germ + nb_sr_pat) * 0.5) + 1.0
                option_partage_egal = reliquat_total / total_tetes_fratrie
                meilleure_part_gp = max(option_un_tiers_reliquat, option_partage_egal, 0.16666666666666666)
                quotas["grand_pere"] = meilleure_part_gp
                reliquat_fratrie = reliquat_total - meilleure_part_gp
                if reliquat_fratrie > 0:
                    tetes_f = ((nb_fr_germ + nb_fr_pat) * 2) + nb_sr_germ + nb_sr_pat
                    if tetes_f > 0:
                        u_f = reliquat_fratrie / tetes_f
                        if nb_fr_germ > 0: quotas["frere_germain"] = u_f * 2 * nb_fr_germ
                        if nb_sr_germ > 0: quotas["soeur_germaine"] = u_f * nb_sr_germ
                        if nb_fr_pat > 0 and nb_fr_germ == 0: quotas["frere_paternel"] = u_f * 2 * nb_fr_pat
                        if nb_sr_pat > 0 and nb_fr_germ == 0: quotas["soeur_paternelle"] = u_f * nb_sr_pat

        # =========================================================================
        # 🎯 7. COLLATÉRAUX ET EXCLUSIONS ABSOLUES DU SANG
        # =========================================================================
        bloque_par_grand_père_hanafite = (doc == "Hanafite" and a_grand_pere)
        if a_pere_ou_fils_ou_petit_fils or bloque_par_grand_père_hanafite:
            quotas.pop("frere_uterin", None); quotas.pop("soeur_uterine", None)
            quotas.pop("soeur_germaine", None); quotas.pop("soeur_paternelle", None)
        else:
            # Répartition coranique des collatéraux utérins (Égalité stricte hommes/femmes)
            nb_uterins = dictionnaire_heritiers.get("frere_uterin", 0) + dictionnaire_heritiers.get("soeur_uterine", 0)
            if nb_uterins > 0:
                part_uterins_globale = 0.16666666666666666 if nb_uterins == 1 else 0.3333333333333333
                if dictionnaire_heritiers.get("frere_uterin", 0) > 0: 
                    quotas["frere_uterin"] = (part_uterins_globale / nb_uterins) * dictionnaire_heritiers["frere_uterin"]
                if dictionnaire_heritiers.get("soeur_uterine", 0) > 0: 
                    quotas["soeur_uterine"] = (part_uterins_globale / nb_uterins) * dictionnaire_heritiers["soeur_uterine"]
            
            # Parts fixes initiales des sœurs SI elles sont seules (Sans frères pour les rendre Asabah)
            if nb_fr_germ == 0 and nb_sr_germ > 0: 
                quotas["soeur_germaine"] = 0.50 if nb_sr_germ == 1 else 0.6666666666666666
            if nb_fr_germ == 0 and nb_fr_pat == 0 and nb_sr_pat > 0: 
                quotas["soeur_paternelle"] = 0.50 if (nb_sr_germ == 0 and nb_sr_pat == 1) else 0.16666666666666666 if nb_sr_germ == 1 else 0.0

    # =========================================================================
    # 🎯 8. LIQUIDATION DES RÉSIDUS AVEC ATTRIBUTION STRICTE AUX ASABÂT (CONSOLIDÉ v1.3.7)
    # =========================================================================
    if not cas_khountha and not cas_arham:
        if a_grand_pere and doc == "Hanafite" and "grand_pere" not in quotas:
            quotas["grand_pere"] = 0.16666666666666666

        somme_intermediaire = sum([v for k, v in quotas.items() if k not in ["cas_khountha_actif", "cas_zawil_arham_actif", "sexe_defunt"]])
        reliquat_patrimonial_global = 1.0 - somme_intermediaire

        # ---------------------------------------------------------------------
        # 👑 SOUS-BLOC A : SHIELD MAÎTRE MUSHTARAKAH (MALÉKITE / CHAFIITE SANCTUARISÉ)
        # ---------------------------------------------------------------------
        nb_ut_tot = dictionnaire_heritiers.get("frere_uterin", 0) + dictionnaire_heritiers.get("soeur_uterine", 0)
        nb_ger_tot = dictionnaire_heritiers.get("frere_germain", 0) + dictionnaire_heritiers.get("soeur_germaine", 0)
        
        if reliquat_patrimonial_global <= 0.0001 and doc in ["Malikite", "Chafiite", "Chafi'ite", "Shafi'ite"]:
            # 🔐 LE VERROU BARRIÈRE IMMUABLE : Pas de Père, pas de Fils, pas de Fille pour ouvrir la Mushtarakah
            if not a_pere and "fils" not in quotas and "fille" not in quotas and "petit_fils" not in quotas and "petite_fille" not in quotas:
                if nb_ut_tot > 0 and nb_ger_tot > 0 and ("epoux" in quotas or "epouse" in quotas) and "mere" in quotas:
                    part_un_tiers_commun = 0.3333333333333333
                    tetes_fusionnees = nb_ut_tot + nb_ger_tot
                    part_par_tete = part_un_tiers_commun / tetes_fusionnees
                    
                    if dictionnaire_heritiers.get("frere_uterin", 0) > 0: quotas["frere_uterin"] = part_par_tete * dictionnaire_heritiers["frere_uterin"]
                    if dictionnaire_heritiers.get("soeur_uterine", 0) > 0: quotas["soeur_uterine"] = part_par_tete * dictionnaire_heritiers["soeur_uterine"]
                    if dictionnaire_heritiers.get("frere_germain", 0) > 0: quotas["frere_germain"] = part_par_tete * dictionnaire_heritiers["frere_germain"]
                    if dictionnaire_heritiers.get("soeur_germaine", 0) > 0: quotas["soeur_germaine"] = part_par_tete * dictionnaire_heritiers["soeur_germaine"]
                    
                    reliquat_patrimonial_global = 0.0

        # ---------------------------------------------------------------------
        # 👑 SOUS-BLOC B : RÉSIDUS POSITIFS AVEC ASABÂT MA'AL GHAYR ET ASCENDANTS
        # ---------------------------------------------------------------------
        if reliquat_patrimonial_global > 0.0001:
            if a_pere and "fils" not in quotas and "petit_fils" not in quotas:
                quotas["pere"] = quotas.get("pere", 0.0) + reliquat_patrimonial_global
                reliquat_patrimonial_global = 0.0
            elif a_grand_pere and "fils" not in quotas and "petit_fils" not in quotas and dictionnaire_heritiers.get("frere_germain", 0) == 0 and dictionnaire_heritiers.get("soeur_germaine", 0) == 0:
                quotas["grand_pere"] = quotas.get("grand_pere", 0.0) + reliquat_patrimonial_global
                reliquat_patrimonial_global = 0.0
            elif a_grand_pere and doc == "Hanafite" and "fils" not in quotas and "petit_fils" not in quotas:
                quotas["grand_pere"] = quotas.get("grand_pere", 0.0) + reliquat_patrimonial_global
                reliquat_patrimonial_global = 0.0
            elif "fille" in quotas and "fils" not in quotas:
                # Règle de prestige : Asabah ma'al Ghayr (Sœurs rendues Asabah par les Filles)
                if dictionnaire_heritiers.get("soeur_germaine", 0) > 0:
                    tetes_g = (nb_fr_germ * 2) + nb_sr_germ if nb_fr_germ > 0 else nb_sr_germ
                    if nb_fr_germ > 0:
                        u_g = reliquat_patrimonial_global / tetes_g
                        quotas["frere_germain"] = quotas.get("frere_germain", 0.0) + (u_g * 2 * nb_fr_germ)
                        quotas["soeur_germaine"] = quotas.get("soeur_germaine", 0.0) + (u_g * nb_sr_germ)
                    else:
                        quotas["soeur_germaine"] = quotas.get("soeur_germaine", 0.0) + reliquat_patrimonial_global
                    reliquat_patrimonial_global = 0.0
                elif dictionnaire_heritiers.get("soeur_paternelle", 0) > 0:
                    tetes_p = (nb_fr_pat * 2) + nb_sr_pat if nb_fr_pat > 0 else nb_sr_pat
                    if nb_fr_pat > 0:
                        u_p = reliquat_patrimonial_global / tetes_p
                        quotas["frere_paternel"] = quotas.get("frere_paternel", 0.0) + (u_p * 2 * nb_fr_pat)
                        quotas["soeur_paternelle"] = quotas.get("soeur_paternelle", 0.0) + (u_p * nb_sr_pat)
                    else:
                        quotas["soeur_paternelle"] = quotas.get("soeur_paternelle", 0.0) + reliquat_patrimonial_global
                    reliquat_patrimonial_global = 0.0

        # ---------------------------------------------------------------------
        # 👑 SOUS-BLOC C : DISTRIBUTION FINALE DES ASABÂT AVEC CO-PARTAGE RATIO 2:1
        # ---------------------------------------------------------------------
        if reliquat_patrimonial_global > 0.0001:
            asabah_prioritaires = ["frere_germain", "frere_paternel", "fils_frere_germain", "fils_frere_paternel", "oncle_germain", "oncle_paternel", "cousin_germain", "cousin_paternel"]
            for h_secours in asabah_prioritaires:
                if dictionnaire_heritiers.get(h_secours, 0) > 0:
                    # ⚖️ Réhabilitation Sœur Germaine (Ta'sib bi-Ghayrihi)
                    if h_secours == "frere_germain" and nb_sr_germ > 0:
                        tetes_g = (int(dictionnaire_heritiers.get("frere_germain", 0)) * 2) + nb_sr_germ
                        u_g = reliquat_patrimonial_global / tetes_g
                        quotas["frere_germain"] = quotas.get("frere_germain", 0.0) + (u_g * 2 * int(dictionnaire_heritiers.get("frere_germain", 0)))
                        quotas["soeur_germaine"] = quotas.get("soeur_germaine", 0.0) + (u_g * nb_sr_germ)
                        reliquat_patrimonial_global = 0.0
                    # ⚖️ Réhabilitation Sœur Paternelle (Ta'sib bi-Ghayrihi)
                    elif h_secours == "frere_paternel" and nb_sr_pat > 0:
                        tetes_p = (int(dictionnaire_heritiers.get("frere_paternel", 0)) * 2) + nb_sr_pat
                        u_p = reliquat_patrimonial_global / tetes_p
                        quotas["frere_paternel"] = quotas.get("frere_paternel", 0.0) + (u_p * 2 * int(dictionnaire_heritiers.get("frere_paternel", 0)))
                        quotas["soeur_paternelle"] = quotas.get("soeur_paternelle", 0.0) + (u_p * nb_sr_pat)
                        reliquat_patrimonial_global = 0.0
                    else:
                        quotas[h_secours] = quotas.get(h_secours, 0.0) + reliquat_patrimonial_global
                        reliquat_patrimonial_global = 0.0
                    break
        elif reliquat_patrimonial_global == 0.0 and len(quotas) == sum(1 for k in quotas if k in ["epoux", "epouse", "mere", "frere_uterin", "soeur_uterine"]):
            pass
        else:
            # 🎯 STRATÉGIE DE TRANSPARENCE UNIFIÉE AJUSTÉE SANS ANGLE MORT
            # L'Asabah ne s'affiche à 0.00 en haut que s'il n'est pas légitimement exclus par le sang (Hajb)
            if not a_pere and "fils" not in quotas and "petit_fils" not in quotas:
                asabah_prioritaires = ["frere_germain", "frere_paternel", "fils_frere_germain", "fils_frere_paternel", "oncle_germain", "oncle_paternel", "cousin_germain", "cousin_paternel"]
                for h_secours in asabah_prioritaires:
                    if dictionnaire_heritiers.get(h_secours, 0) > 0 and h_secours not in quotas:
                        quotas[h_secours] = 0.00000001
                        if h_secours == "frere_germain" and nb_sr_germ > 0 and "soeur_germaine" not in quotas: quotas["soeur_germaine"] = 0.00000001
                        if h_secours == "frere_paternel" and nb_sr_pat > 0 and "soeur_paternelle" not in quotas: quotas["soeur_paternelle"] = 0.00000001
                        break

    # =========================================================================
    # 🎯 SHIELD MAÎTRE KHOUNTHA : PURGE SÉCURISÉE DES CLÉS FANTÔMES À 0.0
    # =========================================================================
    clés_a_purger = [
        k for k, v in quotas.items() 
        if str(k) not in ["cas_khountha_actif", "cas_zawil_arham_actif", "sexe_defunt"] 
        and float(v or 0) <= 0.00001 and float(v or 0) != 0.00000001
    ]
    for cl in clés_a_purger:
        quotas.pop(cl, None)

    # STABILISATION TRANSPARENCE : Fixation à 0.0 net pour l'IHM et ReportLab
    for k_st, v_st in quotas.items():
        if str(v_st) == "1e-08" or float(v_st) == 0.00000001:
            quotas[k_st] = 0.0

    # Nettoyage strict pour l'arbre hanafite
    if doc == "Hanafite" and "khountha" in quotas:
        if int(dictionnaire_heritiers.get("fils", 0)) == 0: quotas.pop("fils", None)
        if int(dictionnaire_heritiers.get("fille", 0)) == 0: quotas.pop("fille", None)

    # Passation à la matrice de correction Sharia (Aoul / Radd) selon la doctrine active
    quotas_ajustes = ajuster_proportions_sharia(quotas, doctrine_active=doc)

    # =========================================================================
    # 🎯 VERROU SÉCURITÉ COMPTABLE DES TOTAUX (Élimine le dépassement Hanafite > 1.0)
    # =========================================================================
    somme_ajustee = sum([float(v) for k, v in quotas_ajustes.items() if k not in ["cas_khountha_actif", "cas_zawil_arham_actif", "sexe_defunt"]])
    if somme_ajustee > 1.0001:
        for k_propr in quotas_ajustes.keys():
            if k_propr not in ["cas_khountha_actif", "cas_zawil_arham_actif", "sexe_defunt"]:
                quotas_ajustes[k_propr] = float(quotas_ajustes[k_propr]) / somme_ajustee

    # =========================================================================
    # 🌟 LE BOUCLIER COMPTABLE UNIVERSEL ABSOLU ANTI-ANGLE MORT ("###" CANONISÉ)
    # =========================================================================
    somme_verrou = sum([float(v) for k, v in quotas_ajustes.items() if k not in ["cas_khountha_actif", "cas_zawil_arham_actif", "sexe_defunt"]])
    reliquat_final_secours = 1.0 - somme_verrou
    
    if reliquat_final_secours > 0.0001:
        # 🎯 RECTIFICATION À LA RACINE : Substitution du jeton technique par l'appellation 
        # canonique sacrée en arabe littéraire dur. Elle s'imposera sur toutes les vues de l'IHM et du PDF.
        quotas_ajustes["بيت مال المسلمين"] = reliquat_final_secours

    # =========================================================================
    # 🎯 RECTIFICATION À LA RACINE : ARABISATION DE LA CLÉ COMMUNE DU KHOUNTHA
    # =========================================================================
    # Si le dictionnaire final contient la clé technique, on la transmute immédiatement
    # pour que TOUS les sous-modules (Live, Tiers, PDF) reçoivent la chaîne sacrée d'origine.
    if "khountha" in quotas_ajustes:
        quotas_ajustes["الخنثى المشكل"] = quotas_ajustes.pop("khountha")

    # On applique la même sécurité sur le dictionnaire brut en amont s'il subsiste
    if "khountha" in quotas:
        quotas["الخنثى المشكل"] = quotas.pop("khountha")

    return quotas_ajustes

