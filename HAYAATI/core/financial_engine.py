"""
MOTEUR CENTRAL D'ORCHESTRATION FINANCIÈRE ET ZAKAT
Version 5.6 - Intégration de l'irrigation dynamique et arbitrage des dettes spirituelles.
"""
import os
import json
from core.zakat.agriculture import evaluer_recolte_agricole, normaliser_mode_irrigation, nombre_brebis_dues
import datetime
from core.zakat.elevage import zakat_bovins, zakat_chameaux

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

    def executer_audit_zakat_complet(self, mode_persistant, user_id, madhhab_actif="Malikite", cours_or_terrain=None, donnees_manuelles_tiers=None, cours_par_defaut_autorises=True):
        doc = str(madhhab_actif).strip().capitalize()
        # 04/10/2026 : les cours de repli (45000 / 650) sont des XOF ; hors zone CFA ils sont refuses
        # (cours_par_defaut_autorises=False) et le resultat porte cours_manquants=True.
        self.cours_par_defaut_actif = bool(cours_par_defaut_autorises)
        c_or = float(cours_or_terrain) if cours_or_terrain else (self.cours_or_par_defaut if self.cours_par_defaut_actif else 0.0)
        c_arg = self.cours_argent_par_defaut
        
        or_ref, or_par, arg_ref, arg_par = 0.0, 0.0, 0.0, 0.0
        c_grain, c_ovin, c_bovin = 0.0, 0.0, 0.0
        arbitrage_pref = "PLUS_BAS"
        irrigation_artificielle = False
        dettes_spirituelles = 0.0
        chameaux, dettes_long_terme, date_hawl = 0, 0.0, ""

        if mode_persistant and user_id:
            liq, stock, dettes, creances, poids, ovins, bovins = 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0
            if self.sync:
                cf = self.sync.charger_donnees_module(user_id, "FINANCES")
                cp = self.sync.charger_donnees_module(user_id, "PREFERENCES")
                
                arbitrage_pref = str(cp.get("arbitrage_nisab", "PLUS_BAS")).upper()
                
                liq = float(cf.get("liq", 0.0)); stock = float(cf.get("stock", 0.0)); dettes = float(cf.get("dettes", 0.0))       
                creances = float(cf.get("creances", 0.0)); poids = float(cf.get("poids", 0.0)); ovins = int(cf.get("ovins", 0)); bovins = int(cf.get("bovins", 0))
                chameaux = int(cf.get("chameaux", 0)); dettes_long_terme = float(cf.get("dettes_long_terme", 0.0)); date_hawl = str(cf.get("date_hawl", "") or "")
                c_or = float(cf.get("or_cours", c_or)); c_arg = float(cf.get("argent_cours", self.cours_argent_par_defaut))
                or_ref = float(cf.get("or_refuge_poids", 0.0)); or_par = float(cf.get("or_parure_poids", 0.0))
                arg_ref = float(cf.get("argent_refuge_poids", 0.0)); arg_par = float(cf.get("argent_parure_poids", 0.0))
                c_grain = float(cf.get("grain_cours", 0.0)); c_ovin = float(cf.get("ovin_cours", 0.0)); c_bovin = float(cf.get("bovin_cours", 0.0))
                
                # Extraction étanche du correctif agro-pastoral et du passif rituel
                # irrigation_mode : "pluie" | "artificielle" | "mixte" (ancien booleen conserve en repli)
                irrigation_artificielle = cf.get("irrigation_mode") or ("artificielle" if cf.get("irrigation_artificielle_active") else "pluie")
                dettes_spirituelles = float(cf.get("dettes_spirituelles", 0.0))

            return self._calculer_metriques_zakat_atomiq(liq, stock, or_ref, or_par, arg_ref, arg_par, dettes, creances, poids, ovins, bovins, c_or, c_arg, doc, "LIVE_PERSISTANT", c_grain, c_ovin, c_bovin, arbitrage_pref, irrigation_artificielle, dettes_spirituelles,
                                                   chameaux=chameaux, dettes_long_terme=dettes_long_terme, date_hawl=date_hawl)
        else:
            intrants = donnees_manuelles_tiers if donnees_manuelles_tiers else {}
            arbitrage_pref = str(intrants.get("arbitrage_nisab", "PLUS_BAS")).upper()
            
            liq = float(intrants.get("liq", 0.0)); stock = float(intrants.get("stock", 0.0)); dettes = float(intrants.get("dettes", 0.0)); creances = float(intrants.get("creances", 0.0))  
            poids = float(intrants.get("poids", 0.0)); ovins = int(intrants.get("ovins", 0)); bovins = int(intrants.get("bovins", 0))
            chameaux = int(intrants.get("chameaux", 0)); dettes_long_terme = float(intrants.get("dettes_long_terme", 0.0)); date_hawl = str(intrants.get("date_hawl", "") or "")
            c_or = float(intrants.get("or_cours", c_or)); c_arg = float(intrants.get("argent_cours", self.cours_argent_par_defaut))
            or_ref = float(intrants.get("or_refuge_poids", 0.0)); or_par = float(intrants.get("or_parure_poids", 0.0))
            arg_ref = float(intrants.get("argent_refuge_poids", 0.0)); arg_par = float(intrants.get("argent_parure_poids", 0.0))
            c_grain = float(intrants.get("grain_cours", 0.0)); c_ovin = float(intrants.get("ovin_cours", 0.0)); c_bovin = float(intrants.get("bovin_cours", 0.0))
            
            # Extraction Tiers correspondante
            irrigation_artificielle = intrants.get("irrigation_mode") or ("artificielle" if intrants.get("irrigation_artificielle_active") else "pluie")
            dettes_spirituelles = float(intrants.get("dettes_spirituelles", 0.0))

            return self._calculer_metriques_zakat_atomiq(liq, stock, or_ref, or_par, arg_ref, arg_par, dettes, creances, poids, ovins, bovins, c_or, c_arg, doc, "DIAGNOSTIC_TIERS", c_grain, c_ovin, c_bovin, arbitrage_pref, irrigation_artificielle, dettes_spirituelles,
                                                   chameaux=chameaux, dettes_long_terme=dettes_long_terme, date_hawl=date_hawl)

    DUREE_HAWL_JOURS = 354   # annee lunaire (12 mois de 29,5 jours en moyenne)

    def _evaluer_hawl(self, date_texte):
        """Statut de l'annee lunaire depuis la date ou le nisab a ete atteint (AAAA-MM-JJ ou JJ/MM/AAAA).
        non_precise : date vide (annee supposee accomplie) ; date_invalide : illisible ou future."""
        t = str(date_texte or "").strip()
        if not t:
            return {"statut": "non_precise", "echeance": ""}
        debut = None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                debut = datetime.datetime.strptime(t[:10], fmt).date()
                break
            except ValueError:
                continue
        aujourd_hui = getattr(self, "date_du_jour", None) or datetime.date.today()
        if debut is None or debut > aujourd_hui:
            return {"statut": "date_invalide", "echeance": ""}
        echeance = debut + datetime.timedelta(days=self.DUREE_HAWL_JOURS)
        return {"statut": "accompli" if aujourd_hui >= echeance else "en_cours", "echeance": echeance.isoformat()}

    def _calculer_metriques_zakat_atomiq(self, liq, stock, or_ref, or_par, 
                                         arg_ref, arg_par, dettes, creances, 
                                         poids, ovins, bovins, c_or, c_arg, 
                                         doc, contexte_cle,
                                         c_grain=0.0, c_ovin=0.0, c_bovin=0.0,
                                         arbitrage_nisab="PLUS_BAS",
                                         irrigation_artificielle=False,
                                         dettes_spirituelles=0.0,
                                         chameaux=0, dettes_long_terme=0.0, date_hawl=""):
        cours_manquants = (not c_or or float(c_or) <= 0) or (not c_arg or float(c_arg) <= 0)
        if getattr(self, "cours_par_defaut_actif", True):
            c_or = float(c_or or self.cours_or_par_defaut)
            c_arg = float(c_arg or self.cours_argent_par_defaut)
            if c_or <= 0: c_or = self.cours_or_par_defaut
            if c_arg <= 0: c_arg = self.cours_argent_par_defaut
        else:
            c_or = max(0.0, float(c_or or 0.0))
            c_arg = max(0.0, float(c_arg or 0.0))

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
            n_app = min(n_or, n_arg)
            m_ref = "ARGENT (595g)" if n_app == n_arg else "OR (85g)"

        # 🎯 RECTIFICATION RADICALE : Suppression de toutes les chaînes textuelles en dur 
        # (Exempté, Baromètre, dues, etc.) pour permettre une internationalisation 100% étanche.
        if doc == "Hanafite":
            p_or = float(or_ref or 0.0) + float(or_par or 0.0)
            p_arg = float(arg_ref or 0.0) + float(arg_par or 0.0)
            cle_statut_bijoux = "bijoux_inclus"
        else:
            p_or = float(or_ref or 0.0)
            p_arg = float(arg_ref or 0.0)
            cle_statut_bijoux = "bijoux_exemptes"

        val_or_z = p_or * c_or
        val_arg_z = p_arg * c_arg

        val_or_b = (float(or_ref or 0.0) + float(or_par or 0.0)) * c_or
        val_arg_b = (float(arg_ref or 0.0) + float(arg_par or 0.0)) * c_arg
        
        valeur_ovins_monetaire = float(ovins or 0) * float(c_ovin or 0.0)
        valeur_bovins_monetaire = float(bovins or 0) * float(c_bovin or 0.0)
        valeur_grains_monetaire = float(poids or 0.0) * float(c_grain or 0.0)
        total_agro_pastoral_monetaire = valeur_ovins_monetaire + valeur_bovins_monetaire + valeur_grains_monetaire
        
        ass_brute = float(liq or 0.0) + float(stock or 0.0) + val_or_z + val_arg_z + float(creances or 0.0)
        
        # 05/10/2026 : deduction des dettes selon l'ecole (partie C de l'audit)
        #  - Chafi'ite : aucune deduction ;  - Hanbalite : dettes exigibles dans l'annee + dettes envers Dieu ;
        #  - Hanafite, Malikite : dettes exigibles dans l'annee. Les dettes a long terme saisies sont exclues.
        dettes_courtes = max(0.0, float(dettes or 0.0) - float(dettes_long_terme or 0.0))
        if doc in ("Chafiite", "Chafi'ite", "Shafi'ite"):
            ded_gens, ded_dieu, regime_dettes = 0.0, 0.0, "aucune"
        elif doc == "Hanbalite":
            ded_gens, ded_dieu, regime_dettes = dettes_courtes, float(dettes_spirituelles or 0.0), "gens_et_dieu"
        else:
            ded_gens, ded_dieu, regime_dettes = dettes_courtes, 0.0, "gens"
        dettes_totales_a_deduire = ded_gens + ded_dieu

        ass_nette = ass_brute - dettes_totales_a_deduire
        if ass_nette < 0: ass_nette = 0.0

        if ass_nette >= n_app and n_app > 0:
            zk_due = ass_nette * 0.025
            imp = True
        else:
            zk_due = 0.0
            imp = False

        # Hawl : si l'annee lunaire n'est pas accomplie, la zakat monetaire n'est pas encore exigible.
        hawl = self._evaluer_hawl(date_hawl)
        zakat_a_terme = 0.0
        if imp and hawl["statut"] == "en_cours":
            zakat_a_terme, zk_due = zk_due, 0.0

        mode_irrigation = normaliser_mode_irrigation(irrigation_artificielle)
        b_agri = evaluer_recolte_agricole(poids, mode_irrigation, doc)
        
        # 🎯 RETOUR AUX CODES DE STATUTS : Envoi d'indicateurs numériques propres à l'IHM
        code_ovins = 1 if 40 <= ovins <= 120 else 2 if 121 <= ovins <= 200 else 3 if ovins > 200 else 0
        code_bovins = 1 if 30 <= bovins <= 39 else 2 if 40 <= bovins <= 59 else 3 if bovins >= 60 else 0
        bovins_struct = zakat_bovins(bovins)
        chameaux_struct = zakat_chameaux(chameaux, doc)

        return {
            "contexte_execution": contexte_cle,
            "madhhab_applique": doc,
            "cours_manquants": bool(cours_manquants and not getattr(self, "cours_par_defaut_actif", True)),
            "cours_par_defaut_utilises": bool(cours_manquants and getattr(self, "cours_par_defaut_actif", True)),
            "cours_or_applique": c_or,
            "cours_argent_applique": c_arg,
            "nissab_monetaire_calcule": n_app,
            "nissab_or_nominal": n_or,
            "nissab_argent_nominal": n_arg,
            "metal_seuil_reference": arbitrage_nisab, # 'OR', 'ARGENT', ou 'PLUS_BAS'
            "valeur_or_calculee": val_or_b,               
            "valeur_argent_calculee": val_arg_b,       
            "valeur_or_retenue_zakat": val_or_z,     
            "valeur_argent_retenue_zakat": val_arg_z, 
            "valeur_agro_pastorale_monetaire": total_agro_pastoral_monetaire,
            "assiette_financiere_nette": ass_nette,
            "zakat_monetaire_due": zk_due,
            "est_imposable_monetaire": imp,
            "zakat_agricole_due_kg": b_agri.get("zakat_kg", 0.0),
            "taux_agricole_pct": b_agri.get("taux_pourcentage", 0.0),
            "mode_irrigation": mode_irrigation,
            "ovins_dus": nombre_brebis_dues(ovins),
            "code_obligation_ovins": code_ovins,
            "code_obligation_bovins": code_bovins,
            "brut_ovins": ovins,
            "brut_bovins": bovins,
            "creances_humaines_incluses": creances,
            "dettes_humaines_deduites": ded_gens,
            "dettes_spirituelles_deduites": ded_dieu,
            "dettes_deduites_total": dettes_totales_a_deduire,
            "regime_deduction_dettes": regime_dettes,
            "dettes_saisies": float(dettes or 0.0),
            "dettes_long_terme_exclues": float(dettes_long_terme or 0.0),
            "hawl_statut": hawl["statut"],
            "hawl_echeance": hawl["echeance"],
            "zakat_monetaire_a_terme": zakat_a_terme,
            "madhhab_applique": doc,
            "poids_recolte_kg": poids,
            "nisab_agricole_kg": b_agri.get("nisab_kg", 653.0),
            "bovins_dus": bovins_struct,
            "chameaux_dus": chameaux_struct,
            "brut_chameaux": chameaux,
            "statut_doctrine_or": cle_statut_bijoux
        }
