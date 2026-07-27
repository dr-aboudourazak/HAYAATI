"""
MOTEUR CENTRAL D'ORCHESTRATION FINANCIÈRE ET ZAKAT
Version 5.5 - Extraction de l'arbitrage du Nisab (Or, Argent, Plus Bas).
"""
import os
import json
from core.zakat.agriculture import evaluer_recolte_agricole

class FinancialEngine:
    def __init__(self, sync_engine_reference=None):
        self.sync = sync_engine_reference
        self.cours_or_par_defaut = 45000.0  
        self.cours_argent_par_defaut = 650.0

    def calculer_nissab_or_dynamique(self, cours_gramme_or):
        val_c = float(cours_gramme_or if cours_gramme_or else self.cours_or_par_defaut)
        return 85.0 * val_c

    def calculer_nissab_argent_dynamique(self, cours_gramme_argent):
        val_c = float(cours_gramme_argent if cours_gramme_argent else self.cours_argent_par_defaut)
        return 595.0 * val_c

    def executer_audit_zakat_complet(self, mode_persistant, user_id, madhhab_actif="Malikite", cours_or_terrain=None, donnees_manuelles_tiers=None):
        doc = str(madhhab_actif).strip().capitalize()
        c_or = float(cours_or_terrain) if cours_or_terrain else self.cours_or_par_defaut
        c_arg = self.cours_argent_par_defaut
        
        or_ref, or_par, arg_ref, arg_par = 0.0, 0.0, 0.0, 0.0
        c_grain, c_ovin, c_bovin = 0.0, 0.0, 0.0
        arbitrage_pref = "PLUS_BAS"

        if mode_persistant and user_id:
            liq, stock, dettes, creances, poids, ovins, bovins = 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0
            if self.sync:
                cf = self.sync.charger_donnees_module(user_id, "FINANCES")
                # 🎯 CORRECTION DE SOURCE : Lecture rigoureuse du module PREFERENCES
                cp = self.sync.charger_donnees_module(user_id, "PREFERENCES")
                
                arbitrage_pref = str(cp.get("arbitrage_nisab", "PLUS_BAS")).upper()
                
                liq = float(cf.get("liq", 0.0)); stock = float(cf.get("stock", 0.0)); dettes = float(cf.get("dettes", 0.0))       
                creances = float(cf.get("creances", 0.0)); poids = float(cf.get("poids", 0.0)); ovins = int(cf.get("ovins", 0)); bovins = int(cf.get("bovins", 0))
                c_or = float(cf.get("or_cours", c_or)); c_arg = float(cf.get("argent_cours", self.cours_argent_par_defaut))
                or_ref = float(cf.get("or_refuge_poids", 0.0)); or_par = float(cf.get("or_parure_poids", 0.0))
                arg_ref = float(cf.get("argent_refuge_poids", 0.0)); arg_par = float(cf.get("argent_parure_poids", 0.0))
                c_grain = float(cf.get("grain_cours", 0.0)); c_ovin = float(cf.get("ovin_cours", 0.0)); c_bovin = float(cf.get("bovin_cours", 0.0))

            return self._calculer_metriques_zakat_atomiq(liq, stock, or_ref, or_par, arg_ref, arg_par, dettes, creances, poids, ovins, bovins, c_or, c_arg, doc, "LIVE_PERSISTANT", c_grain, c_ovin, c_bovin, arbitrage_pref)
        else:
            intrants = donnees_manuelles_tiers if donnees_manuelles_tiers else {}
            # 🎯 CORRECTION DU TIERS : Extraction directe depuis le dictionnaire d'intrants
            arbitrage_pref = str(intrants.get("arbitrage_nisab", "PLUS_BAS")).upper()
            
            liq = float(intrants.get("liq", 0.0)); stock = float(intrants.get("stock", 0.0)); dettes = float(intrants.get("dettes", 0.0)); creances = float(intrants.get("creances", 0.0))  
            poids = float(intrants.get("poids", 0.0)); ovins = int(intrants.get("ovins", 0)); bovins = int(intrants.get("bovins", 0))
            c_or = float(intrants.get("or_cours", c_or)); c_arg = float(intrants.get("argent_cours", self.cours_argent_par_defaut))
            or_ref = float(intrants.get("or_refuge_poids", 0.0)); or_par = float(intrants.get("or_parure_poids", 0.0))
            arg_ref = float(intrants.get("argent_refuge_poids", 0.0)); arg_par = float(intrants.get("argent_parure_poids", 0.0))
            c_grain = float(intrants.get("grain_cours", 0.0)); c_ovin = float(intrants.get("ovin_cours", 0.0)); c_bovin = float(intrants.get("bovin_cours", 0.0))

            return self._calculer_metriques_zakat_atomiq(liq, stock, or_ref, or_par, arg_ref, arg_par, dettes, creances, poids, ovins, bovins, c_or, c_arg, doc, "DIAGNOSTIC_TIERS", c_grain, c_ovin, c_bovin, arbitrage_pref)

    def _calculer_metriques_zakat_atomiq(self, liq, stock, or_ref, or_par, 
                                         arg_ref, arg_par, dettes, creances, 
                                         poids, ovins, bovins, c_or, c_arg, 
                                         doc, contexte_cle,
                                         c_grain=0.0, c_ovin=0.0, c_bovin=0.0,
                                         arbitrage_nisab="PLUS_BAS"):
        c_or = float(c_or or self.cours_or_par_defaut)
        c_arg = float(c_arg or self.cours_argent_par_defaut)
        if c_or <= 0: c_or = self.cours_or_par_defaut
        if c_arg <= 0: c_arg = self.cours_argent_par_defaut

        n_or = self.calculer_nissab_or_dynamique(c_or)
        n_arg = self.calculer_nissab_argent_dynamique(c_arg)
        
        # 🎯 EXÉCUTION DE L'ARBITRAGE SOUVERAIN SUR LE SEUIL DE RÉFÉRENCE (NISAB)
        if arbitrage_nisab == "OR":
            n_app = n_or
            m_ref = "OR (85g)"
        elif arbitrage_nisab == "ARGENT":
            n_app = n_arg
            m_ref = "ARGENT (595g)"
        else:
            # PLUS_BAS : Comportement classique de protection des bénéficiaires
            n_app = min(n_or, n_arg)
            m_ref = "ARGENT (595g)" if n_app == n_arg else "OR (85g)"

        if doc == "Hanafite":
            p_or = float(or_ref or 0.0) + float(or_par or 0.0)
            p_arg = float(arg_ref or 0.0) + float(arg_par or 0.0)
            txt_m = "Inclus (Hanafite : Bijoux portés soumis à Zakat)"
        else:
            p_or = float(or_ref or 0.0)
            p_arg = float(arg_ref or 0.0)
            txt_m = f"Exempté ({doc} : Bijoux de parure personnelle exclus)"

        val_or_z = p_or * c_or
        val_arg_z = p_arg * c_arg

        val_or_b = (float(or_ref or 0.0) + float(or_par or 0.0)) * c_or
        val_arg_b = (float(arg_ref or 0.0) + float(arg_par or 0.0)) * c_arg
        
        # 🎯 CALCUL TRANSPARENT : Valorisation monétaire stricte via les cours de l'utilisateur
        valeur_ovins_monetaire = float(ovins or 0) * float(c_ovin or 0.0)
        valeur_bovins_monetaire = float(bovins or 0) * float(c_bovin or 0.0)
        valeur_grains_monetaire = float(poids or 0.0) * float(c_grain or 0.0)
        total_agro_pastoral_monetaire = valeur_ovins_monetaire + valeur_bovins_monetaire + valeur_grains_monetaire
        
        ass_brute = float(liq or 0.0) + float(stock or 0.0) + val_or_z + val_arg_z + float(creances or 0.0)
        ass_nette = ass_brute - float(dettes or 0.0)
        if ass_nette < 0: ass_nette = 0.0

        if ass_nette >= n_app and n_app > 0:
            zk_due = ass_nette * 0.025
            imp = True
        else:
            zk_due = 0.0
            imp = False

        b_agri = evaluer_recolte_agricole(poids, "pluie")
        
        o_t = "1 brebis due" if 40 <= ovins <= 120 else "2 brebis dues" if 121 <= ovins <= 200 else "Exempté" if ovins < 40 else "3 brebis dues"
        b_t = "1 jeune bovin (Taby)" if 30 <= bovins <= 39 else "1 jeune vache (Musinnah)" if 40 <= bovins <= 59 else "Exempté" if bovins < 30 else "2 Tabys"

        return {
            "contexte_execution": contexte_cle,
            "madhhab_applique": doc,
            "cours_or_applique": c_or,
            "cours_argent_applique": c_arg,
            "nissab_monetaire_calcule": n_app,
            "nissab_or_nominal": n_or,
            "nissab_argent_nominal": n_arg,
            "metal_seuil_reference": m_ref,
            "valeur_or_calculee": val_or_b,               
            "valeur_argent_calculee": val_arg_b,       
            "valeur_or_retenue_zakat": val_or_z,     
            "valeur_argent_retenue_zakat": val_arg_z, 
            "valeur_agro_pastorale_monetaire": total_agro_pastoral_monetaire, # 🎯 VALEUR EXPORTÉE SANS COEFFICIENT CACHÉ
            "assiette_financiere_nette": ass_nette,
            "zakat_monetaire_due": zk_due,
            "est_imposable_monetaire": imp,
            "zakat_agricole_due_kg": b_agri.get("zakat_kg", 0.0),
            "obligation_ovins": o_t,
            "obligation_bovins": b_t,
            "brut_ovins": ovins,
            "brut_bovins": bovins,
            "creances_humaines_incluses": creances,
            "dettes_humaines_deduites": dettes,
            "statut_doctrine_or": txt_m
        }
