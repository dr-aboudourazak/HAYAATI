"""
AFFICHAGE PARTAGÉ DU BILAN SUCCESSORAL (GUI/COMPONENTS/HERITAGE_AFFICHAGE.PY)
Version 1.0 - 04/10/2026

Un seul endroit pour construire les lignes du bilan (écran Live, écran Tiers et PDF),
afin que les montants affichés, imprimés et calculés ne divergent plus.
"""
from __future__ import annotations


def _g(bilan: dict, cle: str) -> float:
    try:
        return float(bilan.get(cle, 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def lignes_bilan(bilan: dict, txt_her: dict, dev: str) -> list[tuple[str, str]]:
    """Lignes ordonnées (libellé, valeur) du bilan. Les lignes sans objet sont omises."""
    t = txt_her or {}
    lignes: list[tuple[str, str]] = []

    lignes.append((t.get("masse_successorale_nette", "Masse successorale nette à distribuer"),
                   f"{_g(bilan, 'masse_successorale_nette'):.2f} {dev}"))
    lignes.append((t.get("creances_actives_incluses", "Créances actives incluses"),
                   f"{_g(bilan, 'creances_actives_incluses'):.2f} {dev}"))

    if _g(bilan, "frais_funeraires_retenus") > 0.004:
        lignes.append((t.get("frais_funeraires_retenus", "Frais funéraires (prélevés en premier)"),
                       f"-{_g(bilan, 'frais_funeraires_retenus'):.2f} {dev}"))

    lignes.append((t.get("dettes_humaines_purgées", "Dettes et passif purgés"),
                   f"-{_g(bilan, 'dettes_humaines_purgées'):.2f} {dev}"))
    if _g(bilan, "dettes_humaines_non_payees") > 0.004:
        lignes.append((t.get("dettes_humaines_non_payees", "Dettes non couvertes par la succession"),
                       f"{_g(bilan, 'dettes_humaines_non_payees'):.2f} {dev}"))

    if _g(bilan, "dettes_spirituelles_demandees") > 0.004:
        lignes.append((t.get("dettes_spirituelles_executees", "Dettes envers Dieu exécutées"),
                       f"-{_g(bilan, 'dettes_spirituelles_executees'):.2f} {dev}"))
        if _g(bilan, "dettes_spirituelles_non_executees") > 0.004:
            lignes.append((t.get("dettes_spirituelles_non_executees", "Dettes envers Dieu non exécutées"),
                           f"{_g(bilan, 'dettes_spirituelles_non_executees'):.2f} {dev}"))

    lignes.append((t.get("wasiyya_retenue", "Legs testamentaires retenus (Max 1/3)"),
                   f"{_g(bilan, 'wasiyya_retenue'):.2f} {dev}"))
    if _g(bilan, "legs_non_retenus") > 0.004:
        lignes.append((t.get("legs_non_retenus", "Legs non retenus (au-delà du tiers)"),
                       f"{_g(bilan, 'legs_non_retenus'):.2f} {dev}"))
    return lignes


def notes_doctrinales(bilan: dict, txt_her: dict) -> list[str]:
    """Rappels d'ordre légal, selon l'école, uniquement quand ils concernent le cas calculé."""
    t = txt_her or {}
    notes: list[str] = []
    if _g(bilan, "frais_funeraires_demandes") > 0.004:
        notes.append(t.get("note_frais_funeraires",
                           "ℹ️ Les frais d'inhumation modérés sont prélevés en premier par les quatre écoles ; "
                           "certaines font passer avant eux une dette garantie par un gage."))
    if _g(bilan, "dettes_spirituelles_demandees") > 0.004:
        if bilan.get("regime_dettes_dieu") == "tiers":
            notes.append(t.get("note_dettes_dieu_tiers",
                               "ℹ️ Selon votre école, les dettes envers Dieu ne sont exécutées que sur le tiers "
                               "disponible, avant les legs volontaires (elles tombent à la mort sauf "
                               "recommandation du défunt)."))
        else:
            notes.append(t.get("note_dettes_dieu_succession",
                               "ℹ️ Selon votre école, les dettes envers Dieu sont prélevées sur l'ensemble de la "
                               "succession, à rang égal avec les dettes des gens (au prorata si l'actif est "
                               "insuffisant ; certains savants font passer les dettes des gens en premier)."))
    return notes
