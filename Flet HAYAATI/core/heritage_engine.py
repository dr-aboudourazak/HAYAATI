"""
MOTEUR DE SUCCESSION SHARIA-COMPLIANT (CORE/HERITAGE_ENGINE.PY)
Version 6.1 Stable - Intégration des Dettes Spirituelles et Arbitrage des Passifs du Fiqh.
"""
from __future__ import annotations
import flet as ft
from core.financial_engine import FinancialEngine
from core.heritage.fractions import determiner_quotas_fixes_de_base

class HeritageEngine:
    def __init__(self, sync_engine_reference=None):
        self.sync = sync_engine_reference
        self.moteur_finance = FinancialEngine(sync_engine_reference=sync_engine_reference)

    def executer_audit_successoral_complet(self, mode_persistant, user_id, 
                                            madhhab_actif="Malikite", 
                                            donnees_manuelles_tiers=None):
        """
        Calcule la masse successorale nette réelle et applique les barèmes 
        du Fiqh en mode connecté (SQLite) ou diagnostic à blanc (Tiers).
        """
        doctrine = str(madhhab_actif).strip().capitalize()
        
        actif_brut_total = 0.0
        creances_actives = 0.0
        dettes_passives = 0.0
        dettes_spirituelles = 0.0
        legs_wasiyya = 0.0
        arbre_saisi = {}

        # --- CAS 1 : MODE PERSISTANT CONNECTÉ (LIVE) ---
        if mode_persistant and user_id:
            if self.sync:
                cache_fin = self.sync.charger_donnees_module(user_id, "FINANCES") or {}
                fortune_nette_comptable = float(cache_fin.get("net", 0.0))
                
                if fortune_nette_comptable > 0:
                    actif_brut_total = fortune_nette_comptable
                else:
                    immo = float(cache_fin.get("immo", 0.0))
                    auto = float(cache_fin.get("auto", 0.0))
                    liq = float(cache_fin.get("liq", 0.0))
                    stock = float(cache_fin.get("stock", 0.0))
                    actif_brut_total = immo + auto + liq + stock

                creances_actives = float(cache_fin.get("creances", 0.0))
                dettes_passives = float(cache_fin.get("dettes", 0.0))
                dettes_spirituelles = float(cache_fin.get("dettes_spirituelles", 0.0))
                legs_wasiyya = float(cache_fin.get("wasiyya", 0.0))

                cache_arbre = self.sync.charger_donnees_module(user_id, "ARBRE_FAMILIAL") or {}
                
                for k, v in cache_arbre.items():
                    if k not in ["cas_khountha_actif", "cas_zawil_arham_actif", "sexe_defunt"]:
                        if str(v).isdigit():
                            arbre_saisi[str(k).strip().lower()] = int(v)
                
                arbre_saisi["sexe_defunt"] = cache_arbre.get("sexe_defunt", "HOMME")
                arbre_saisi["cas_khountha_actif"] = cache_arbre.get("cas_khountha_actif", False)
                arbre_saisi["cas_zawil_arham_actif"] = cache_arbre.get("cas_zawil_arham_actif", False)
        
        # --- CAS 2 : MODE SAISIE MANUELLE (DIAGNOSTIC TIERS) ---
        else:
            intrants = donnees_manuelles_tiers if donnees_manuelles_tiers else {}
            actif_brut_total = float(intrants.get("brut", 0.0))
            creances_actives = float(intrants.get("creances_humains", 0.0))
            dettes_passives = float(intrants.get("dettes_humains", 0.0))
            dettes_spirituelles = float(intrants.get("dettes_spirituelles", 0.0))
            legs_wasiyya = float(intrants.get("legs", 0.0))
            
            arbre_brut_tiers = intrants.get("arbre_saisi", {})
            for k, v in arbre_brut_tiers.items():
                if k not in ["cas_khountha_actif", "cas_zawil_arham_actif", "sexe_defunt"]:
                    if str(v).isdigit():
                        arbre_saisi[str(k).strip().lower()] = int(v)
            
            arbre_saisi["sexe_defunt"] = intrants.get("sexe_defunt", "HOMME")
            arbre_saisi["cas_khountha_actif"] = intrants.get("cas_khountha_actif", False)
            arbre_saisi["cas_zawil_arham_actif"] = intrants.get("cas_zawil_arham_actif", False)

        return self._ventiler_faraidh_legal(
            actif_brut_total, creances_actives, dettes_passives, dettes_spirituelles, 
            legs_wasiyya, arbre_saisi, doctrine
        )

    def _ventiler_faraidh_legal(self, brut, creances, dettes, dettes_s, 
                                legs, arbre, doctrine):
        """
        Effectue la distribution sur la base des cles techniques 
        unifiees et invariables de l'arbre généalogique.
        """
        brut_total = float(brut or 0.0)
        creances_inc = float(creances or 0.0)
        dettes_purg = float(dettes or 0.0)
        dettes_spirituelles = float(dettes_s or 0.0)
        legs_demande = float(legs or 0.0)

        # 🎯 RECTIFICATION DIRECTE CONFORMÉMENT À VOTRE ARCHITECTURE :
        # brut_total est déjà purgé des dettes humaines et contient les créances.
        # On applique le passif rituel (Diyoun Allah) directement sur cette base saine.
        if doctrine in ["Hanafite", "Malikite"]:
            # Les dettes rituelles s'imputent sur le tiers de legs s'il y a un testament
            safe_mass = brut_total
            total_legs_sollicite = legs_demande + dettes_spirituelles
            wasiyya_retenue = min(total_legs_sollicite, safe_mass / 3.0)
            m_nette = safe_mass - wasiyya_retenue
            
        else: # Chafiite et Hanbalite
            # Ces deux écoles purgent de plein droit le passif de Dieu sur la masse active
            safe_mass = max(0.0, brut_total - dettes_spirituelles)
            wasiyya_retenue = min(legs_demande, safe_mass / 3.0)
            m_nette = safe_mass - wasiyya_retenue

        # 🎯 SÉCURITÉ DOCTRINALE DE NON-CUMUL DES CONJOINTS SUR LE MOTEUR
        if arbre.get("epoux", 0) > 0 and arbre.get("epouse", 0) > 0:
            return {
                "masse_successorale_nette": m_nette,
                "wasiyya_retenue": wasiyya_retenue,
                "creances_actives_incluses": creances_inc,
                "dettes_humaines_purgées": dettes_purg,
                "dettes_spirituelles_purgées": dettes_spirituelles,
                "ventilation_fractions": {},
                "personnes_exclues": list(arbre.keys()),
                "composition_arbre": {k: v for k, v in arbre.items() if k not in ["cas_khountha_actif", "cas_zawil_arham_actif", "sexe_defunt"] and int(v) > 0} 
            }

        # 🎯 PASSATION INTERNE ÉTANCHE AUX MODULES ATOMIQUES EXHAUSTIFS
        resultat_exclusions = _appliquer_moteur_exclusions_compat(arbre, doctrine_active=doctrine)
        heritiers_valides = resultat_exclusions.get("heritiers_valides", {})
        personnes_exclues = resultat_exclusions.get("personnes_exclues", [])

        # Calcul et ajustement mathématique des quotes-parts
        fractions_finales = determiner_quotas_fixes_de_base(arbre, doctrine_active=doctrine)

        # Extraction de l'arbre brut sans interférence des métadonnées
        arbre_complet_effectifs = {}
        for k, v in arbre.items():
            if k not in ["cas_khountha_actif", "cas_zawil_arham_actif", "sexe_defunt"]:
                try:
                    if int(v) > 0: arbre_complet_effectifs[str(k).strip()] = int(v)
                except Exception: pass

        # 🌟 INJECTION DIRECTE DANS LE TABLEAU VERT DU PDF
        if arbre.get("cas_khountha_actif", False):
            arbre_complet_effectifs["مسألة الخنثى المشكل"] = 1
            
        if arbre.get("cas_zawil_arham_actif", False):
            arbre_complet_effectifs["مسألة ذوي الأرحام"] = 1

        return {
            "masse_successorale_nette": m_nette,
            "wasiyya_retenue": wasiyya_retenue,
            "creances_actives_incluses": creances_inc,
            "dettes_humaines_purgées": dettes_purg,
            "dettes_spirituelles_purgées": dettes_spirituelles,
            "ventilation_fractions": fractions_finales,
            "personnes_exclues": personnes_exclues,
            "composition_arbre": arbre_complet_effectifs
        }

def _appliquer_moteur_exclusions_compat(arbre_dict, doctrine_active="Malikite"):
    from core.heritage.exclusions import appliquer_moteur_exclusions
    arbre_propre = {k: v for k, v in arbre_dict.items() if k not in ["cas_khountha_actif", "cas_zawil_arham_actif", "sexe_defunt"]}
    return appliquer_moteur_exclusions(arbre_propre, doctrine_active=doctrine_active)
