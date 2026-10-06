"""
MOTEUR DE SUCCESSION SHARIA-COMPLIANT (CORE/HERITAGE_ENGINE.PY)
Version 7.0 - 04/10/2026
L'ordre de prélèvement (frais d'inhumation, dettes des gens, dettes envers Dieu, legs au tiers)
vient désormais d'une source unique : core/wasiyya_engine.repartir_succession().
"""
from __future__ import annotations
import flet as ft
from core.financial_engine import FinancialEngine
from core.heritage.fractions import determiner_quotas_fixes_de_base
from core.wasiyya_engine import repartir_succession

_META = ("cas_khountha_actif", "cas_zawil_arham_actif", "sexe_defunt")


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

        actifs_totaux = 0.0       # actif de la succession AVANT tout prélèvement (créances incluses)
        creances_actives = 0.0
        dettes_passives = 0.0
        dettes_spirituelles = 0.0
        legs_wasiyya = 0.0
        frais_funeraires = 0.0
        arbre_saisi = {}

        # --- CAS 1 : MODE PERSISTANT CONNECTÉ (LIVE) ---
        if mode_persistant and user_id:
            if self.sync:
                cache_fin = self.sync.charger_donnees_module(user_id, "FINANCES") or {}
                creances_actives = float(cache_fin.get("creances", 0.0))
                dettes_passives = float(cache_fin.get("dettes", 0.0))
                # Patrimoine net deja calcule par l'ecran Finances = actifs + creances - dettes humaines.
                # L'actif de depart est donc net + dettes : le moteur applique lui-meme l'ordre legal.
                if "net" in cache_fin:
                    actifs_totaux = max(0.0, float(cache_fin.get("net", 0.0)) + dettes_passives)
                else:
                    immo = float(cache_fin.get("immo", 0.0))
                    auto = float(cache_fin.get("auto", 0.0))
                    liq = float(cache_fin.get("liq", 0.0))
                    stock = float(cache_fin.get("stock", 0.0))
                    actifs_totaux = max(0.0, immo + auto + liq + stock + creances_actives)

                dettes_spirituelles = float(cache_fin.get("dettes_spirituelles", 0.0))
                legs_wasiyya = float(cache_fin.get("wasiyya", 0.0))
                # Mode Live : aucun montant de frais funeraires (les volontes sont saisies sans somme).

                cache_arbre = self.sync.charger_donnees_module(user_id, "ARBRE_FAMILIAL") or {}
                for k, v in cache_arbre.items():
                    if k not in _META and str(v).isdigit():
                        arbre_saisi[str(k).strip().lower()] = int(v)

                arbre_saisi["sexe_defunt"] = cache_arbre.get("sexe_defunt", "HOMME")
                arbre_saisi["cas_khountha_actif"] = cache_arbre.get("cas_khountha_actif", False)
                arbre_saisi["cas_zawil_arham_actif"] = cache_arbre.get("cas_zawil_arham_actif", False)

        # --- CAS 2 : MODE SAISIE MANUELLE (DIAGNOSTIC TIERS) ---
        else:
            intrants = donnees_manuelles_tiers if donnees_manuelles_tiers else {}
            creances_actives = float(intrants.get("creances_humains", 0.0))
            dettes_passives = float(intrants.get("dettes_humains", 0.0))
            actifs_totaux = max(0.0, float(intrants.get("brut", 0.0)) + creances_actives)
            dettes_spirituelles = float(intrants.get("dettes_spirituelles", 0.0))
            legs_wasiyya = float(intrants.get("legs", 0.0))
            frais_funeraires = float(intrants.get("frais_funeraires", 0.0))

            for k, v in intrants.get("arbre_saisi", {}).items():
                if k not in _META and str(v).isdigit():
                    arbre_saisi[str(k).strip().lower()] = int(v)

            arbre_saisi["sexe_defunt"] = intrants.get("sexe_defunt", "HOMME")
            arbre_saisi["cas_khountha_actif"] = intrants.get("cas_khountha_actif", False)
            arbre_saisi["cas_zawil_arham_actif"] = intrants.get("cas_zawil_arham_actif", False)

        return self._ventiler_faraidh_legal(
            actifs_totaux, creances_actives, dettes_passives, dettes_spirituelles,
            legs_wasiyya, frais_funeraires, arbre_saisi, doctrine
        )

    def _ventiler_faraidh_legal(self, actifs, creances, dettes, dettes_s,
                                legs, frais, arbre, doctrine):
        """
        Applique l'ordre légal des prélèvements puis distribue la masse partageable sur la base
        des clés techniques unifiées de l'arbre généalogique.
        """
        bilan = repartir_succession(
            actifs, dettes_humaines=dettes, dettes_spirituelles=dettes_s,
            legs_demandes=legs, frais_funeraires=frais, doctrine=doctrine
        )
        m_nette = bilan["masse_partageable"]

        entete = {
            "masse_successorale_nette": m_nette,
            "wasiyya_retenue": bilan["legs_retenus"],
            "creances_actives_incluses": float(creances or 0.0),
            # Montants EXECUTES (et non plus seulement demandes) ; les demandes restent disponibles.
            "dettes_humaines_purgées": bilan["dettes_humaines_payees"],
            "dettes_spirituelles_purgées": bilan["dettes_spirituelles_executees"],
        }
        entete.update({k: v for k, v in bilan.items() if k != "masse_partageable"})

        # 🎯 SÉCURITÉ DOCTRINALE DE NON-CUMUL DES CONJOINTS SUR LE MOTEUR
        if arbre.get("epoux", 0) > 0 and arbre.get("epouse", 0) > 0:
            return dict(entete, **{
                "ventilation_fractions": {},
                "personnes_exclues": list(arbre.keys()),
                "composition_arbre": {k: v for k, v in arbre.items() if k not in _META and int(v) > 0},
            })

        # 🎯 PASSATION INTERNE ÉTANCHE AUX MODULES ATOMIQUES EXHAUSTIFS
        resultat_exclusions = _appliquer_moteur_exclusions_compat(arbre, doctrine_active=doctrine)
        personnes_exclues = resultat_exclusions.get("personnes_exclues", [])

        # Seuls les heritiers presents (compteur > 0) sont transmis : une cle a 0 ne doit pas compter comme "presente".
        arbre_utile = {k: v for k, v in arbre.items() if k in _META or (str(v).isdigit() and int(v) > 0)}
        fractions_finales = determiner_quotas_fixes_de_base(arbre_utile, doctrine_active=doctrine)

        # Extraction de l'arbre brut sans interférence des métadonnées
        arbre_complet_effectifs = {}
        for k, v in arbre.items():
            if k not in _META:
                try:
                    if int(v) > 0:
                        arbre_complet_effectifs[str(k).strip()] = int(v)
                except Exception:
                    pass

        # 🌟 INJECTION DIRECTE DANS LE TABLEAU VERT DU PDF
        if arbre.get("cas_khountha_actif", False):
            arbre_complet_effectifs["مسألة الخنثى المشكل"] = 1

        if arbre.get("cas_zawil_arham_actif", False):
            arbre_complet_effectifs["مسألة ذوي الأرحام"] = 1

        return dict(entete, **{
            "ventilation_fractions": fractions_finales,
            "personnes_exclues": personnes_exclues,
            "composition_arbre": arbre_complet_effectifs,
        })


def _appliquer_moteur_exclusions_compat(arbre_dict, doctrine_active="Malikite"):
    from core.heritage.exclusions import appliquer_moteur_exclusions
    arbre_propre = {k: v for k, v in arbre_dict.items() if k not in _META}
    return appliquer_moteur_exclusions(arbre_propre, doctrine_active=doctrine_active)
