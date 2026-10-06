"""
MOTEUR DE SUCCESSION : ORDRE LEGAL, DETTES ET TESTAMENT (CORE/WASIYYA_ENGINE.PY)
Version 4.0 - 04/10/2026 : source unique de l'ordre de prelevement sur la succession.
(Avant, la regle du tiers etait dupliquee dans heritage_engine.py.)

Ordre applique :
  1. Frais d'inhumation moderes (tajhiz) : premier prelevement, dans les quatre ecoles
  2. Dettes envers les gens
  3. Dettes envers Dieu (zakat impayee, kaffara, hajj, fidya...)
  4. Legs volontaires, dans la limite du tiers de ce qui reste
  5. Le reste est partage entre les heritiers

Dettes envers Dieu, selon l'ecole :
  - Hanafite et Malikite : elles tombent a la mort sauf recommandation du defunt ; saisies dans
    le testament, elles sont executees depuis le TIERS, avant les legs volontaires.
  - Chafi'ite et Hanbalite : ce sont des dettes ; elles sont prelevees sur l'ensemble de la
    succession, a rang egal avec les dettes des gens (au prorata si l'actif est insuffisant).
    Divergence : certains font passer les dettes des gens avant.

Les dettes garanties par un gage (rahn) passent avant les frais d'inhumation chez certaines ecoles :
non modelisees (aucune saisie correspondante dans l'application).
"""
from __future__ import annotations

ECOLES_DETTES_DANS_LE_TIERS = ("Hanafite", "Malikite")
_EPSILON = 0.005


def repartir_succession(actifs, dettes_humaines=0.0, dettes_spirituelles=0.0,
                        legs_demandes=0.0, frais_funeraires=0.0, doctrine="Malikite"):
    """
    actifs : total de l'actif de la succession (creances incluses), AVANT tout prelevement.
    Retourne un dictionnaire complet (voir les cles en fin de fonction).
    """
    actifs = max(0.0, float(actifs or 0.0))
    h = max(0.0, float(dettes_humaines or 0.0))
    s = max(0.0, float(dettes_spirituelles or 0.0))
    legs = max(0.0, float(legs_demandes or 0.0))
    f = max(0.0, float(frais_funeraires or 0.0))
    dans_le_tiers = str(doctrine) in ECOLES_DETTES_DANS_LE_TIERS

    # 1. Frais d'inhumation
    frais_pris = min(f, actifs)
    reste = actifs - frais_pris

    if dans_le_tiers:
        # 2. Dettes des gens d'abord
        h_payees = min(h, reste)
        reste -= h_payees
        # 3 et 4. Obligations puis legs volontaires, ensemble limites au tiers du reste
        tiers = reste / 3.0
        s_exec = min(s, tiers)
        legs_ret = min(legs, tiers - s_exec)
        reste -= (s_exec + legs_ret)
        regime = "tiers"
    else:
        # 2 et 3. Dettes des gens et dettes envers Dieu : rang egal, au prorata si insuffisant
        total_dettes = h + s
        if total_dettes <= reste or total_dettes <= 0:
            h_payees, s_exec = h, s
        else:
            h_payees = reste * h / total_dettes
            s_exec = reste * s / total_dettes
        reste -= (h_payees + s_exec)
        # 4. Legs volontaires : tiers de ce qui reste
        legs_ret = min(legs, reste / 3.0)
        reste -= legs_ret
        regime = "succession"

    return {
        "masse_partageable": max(0.0, reste),
        "regime_dettes_dieu": regime,
        "actifs_totaux": actifs,
        "frais_funeraires_demandes": f,
        "frais_funeraires_retenus": frais_pris,
        "dettes_humaines_demandees": h,
        "dettes_humaines_payees": h_payees,
        "dettes_humaines_non_payees": max(0.0, h - h_payees),
        "dettes_spirituelles_demandees": s,
        "dettes_spirituelles_executees": s_exec,
        "dettes_spirituelles_non_executees": max(0.0, s - s_exec),
        "legs_demandes": legs,
        "legs_retenus": legs_ret,
        "legs_non_retenus": max(0.0, legs - legs_ret),
    }


class WasiyyaEngine:
    """Conserve l'interface historique (analyse de conformite d'un legs) ; la regle du tiers vient de repartir_succession."""

    def evaluer_conformite_legs(self, masse_brute, dettes_passives, montant_legs_demande):
        bilan = repartir_succession(masse_brute, dettes_humaines=dettes_passives,
                                    legs_demandes=montant_legs_demande, doctrine="Chafi'ite")
        masse_avant_legs = max(0.0, float(masse_brute or 0.0) - float(dettes_passives or 0.0))
        plafond = masse_avant_legs / 3.0
        est_conforme = bilan["legs_non_retenus"] < _EPSILON
        return {
            "est_conforme_sharia": est_conforme,
            "statut_verdict": ("Entièrement conforme et exécutable" if est_conforme
                               else "Plafonné au tiers légal (Dépassement détecté)"),
            "plafond_autorise_un_tiers": plafond,
            "montant_testament_retenu": bilan["legs_retenus"],
            "masse_residuelle_heritiers": bilan["masse_partageable"],
        }
