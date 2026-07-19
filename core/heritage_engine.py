"""
MOTEUR DE SUCCESSION SHARIA-COMPLIANT (CORE/HERITAGE_ENGINE.PY)
Version 5.6 - Support exhaustif des 21 candidats canoniques scindés et interconnexion i18n.
"""
from core.financial_engine import FinancialEngine
from core.heritage.exclusions import appliquer_moteur_exclusions
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
        legs_wasiyya = 0.0
        arbre_saisi = {}

        # --- CAS 1 : MODE PERSISTANT CONNECTÉ (LIVE) ---
        if mode_persistant and user_id:
            if self.sync:
                cache_fin = self.sync.charger_donnees_module(user_id, "FINANCES")
                
                immo = float(cache_fin.get("immo", 0.0))
                auto = float(cache_fin.get("auto", 0.0))
                liq = float(cache_fin.get("liq", 0.0))
                
                creances_actives = float(cache_fin.get("creances", 0.0))
                dettes_passives = float(cache_fin.get("dettes", 0.0))
                legs_wasiyya = float(cache_fin.get("wasiyya", 0.0))

                audit_fin = self.moteur_finance.executer_audit_zakat_complet(
                    mode_persistant=True, user_id=user_id, madhhab_actif=madhhab_actif
                )
                
                val_or_totale = float(audit_fin.get("valeur_or_calculee", 0.0))
                val_argent_totale = float(audit_fin.get("valeur_argent_calculee", 0.0))
                val_agro_monetaire = float(audit_fin.get("valeur_agro_pastorale_monetaire", 0.0))

                # Compilation transparente de l'actif net total
                actif_brut_total = immo + auto + liq + val_or_totale + val_argent_totale + val_agro_monetaire

                # Extraction de l'arbre familial mémorisé
                cache_arbre = self.sync.charger_donnees_module(user_id, "ARBRE_FAMILIAL")
                arbre_saisi = {str(k).strip().lower(): int(v) for k, v in cache_arbre.items() if str(v).isdigit()}
        
        # --- CAS 2 : MODE SAISIE MANUELLE (DIAGNOSTIC TIERS) ---
        else:
            intrants = donnees_manuelles_tiers if donnees_manuelles_tiers else {}
            actif_brut_total = float(intrants.get("brut", 0.0))
            creances_actives = float(intrants.get("creances_humains", 0.0))
            dettes_passives = float(intrants.get("dettes_humains", 0.0))
            legs_wasiyya = float(intrants.get("legs", 0.0))
            
            # Normalisation des clés saisies manuellement pour le tiers
            arbre_brut_tiers = intrants.get("arbre_saisi", {})
            arbre_saisi = {str(k).strip().lower(): int(v) for k, v in arbre_brut_tiers.items() if str(v).isdigit()}

        return self._ventiler_faraidh_legal(
            actif_brut_total, creances_actives, dettes_passives, 
            legs_wasiyya, arbre_saisi, doctrine
        )

    def _ventiler_faraidh_legal(self, brut, creances, dettes, 
                                legs, arbre, doctrine):
        """
        Effectue la distribution sur la base des cles techniques 
        unifiees et invariables de l'arbre généalogique.
        """
        brut_total = float(brut or 0.0)
        creances_inc = float(creances or 0.0)
        dettes_purg = float(dettes or 0.0)
        legs_demande = float(legs or 0.0)

        masse_initiale = brut_total + creances_inc
        safe_mass = masse_initiale - dettes_purg
        if safe_mass < 0:
            safe_mass = 0.0

        # Application stricte de la barrière coranique du tiers (1/3 maximum pour les legs)
        tiers_maximal_legal = safe_mass / 3.0
        wasiyya_retenue = min(legs_demande, tiers_maximal_legal)

        m_nette = safe_mass - wasiyya_retenue
        if m_nette < 0:
            m_nette = 0.0

        # 🎯 SÉCURITÉ DOCTRINALE DE NON-CUMUL DES CONJOINTS SUR LE MOTEUR
        if arbre.get("epoux", 0) > 0 and arbre.get("epouse", 0) > 0:
            return {
                "masse_successorale_nette": m_nette,
                "wasiyya_retenue": wasiyya_retenue,
                "creances_actives_incluses": creances_inc,
                "dettes_humaines_purgées": dettes_purg,
                "ventilation_fractions": {},
                "personnes_exclues": list(arbre.keys())
            }

        # 🎯 PASSATION INTERNE ÉTANCHE AUX MODULES ATOMIQUES EXHAUSTIFS DE 21 CATÉGORIES
        # 1. Traitement complet des masquages et exclusions (Hajb)
        resultat_exclusions = _appliquer_moteur_exclusions_compat(arbre, doctrine_active=doctrine)
        heritiers_valides = resultat_exclusions.get("heritiers_valides", {})
        personnes_exclues = resultat_exclusions.get("personnes_exclues", [])

        # 2. Calcul et ajustement mathématique (Aoul / Radd) des quotes-parts d'éligibilité
        fractions_finales = determiner_quotas_fixes_de_base(heritiers_valides, doctrine_active=doctrine)

        return {
            "masse_successorale_nette": m_nette,
            "wasiyya_retenue": wasiyya_retenue,
            "creances_actives_incluses": creances_inc,
            "dettes_humaines_purgées": dettes_purg,
            "ventilation_fractions": fractions_finales,
            "personnes_exclues": personnes_exclues
        }

# Maintien de l'étanchéité de compatibilité avec les anciens modules de filtrage d'exclusions
def _appliquer_moteur_exclusions_compat(arbre_dict, doctrine_active="Malikite"):
    from core.heritage.exclusions import appliquer_moteur_exclusions
    return appliquer_moteur_exclusions(arbre_dict, doctrine_active=doctrine_active)
