"""
MOTEUR DE TESTAMENT ET LEGS (CORE/WASIYYA_ENGINE.PY)
Version 3.0 - Analyse de conformité du legs (Plafond 1/3) pour les modes Live et Tiers.
"""

class WasiyyaEngine:
    def __init__(self):
        pass

    def evaluer_conformite_legs(self, masse_brute, dettes_passives, montant_legs_demande):
        """
        Calcule le plafond du tiers net (1/3) après déduction des dettes.
        Détermine le montant exécutable retenu et le reliquat pour la succession.
        """
        # 1. Calcul de la masse nette de base avant testament
        masse_nette_avant_legs = masse_brute - dettes_passives
        if masse_nette_avant_legs < 0:
            masse_nette_avant_legs = 0.0

        # 2. Fixation du plafond légal de la Sharia (1/3 du net)
        plafond_maximum = masse_nette_avant_legs / 3.0

        # 3. Arbitrage doctrinal
        if montant_legs_demande > plafond_maximum:
            montant_executable = plafond_maximum
            est_conforme = False
            statut_cle = "Plafonné au tiers légal (Dépassement détecté)"
        else:
            montant_executable = montant_legs_demande
            est_conforme = True
            statut_cle = "Entièrement conforme et exécutable"

        # 4. Masse résiduelle finale destinée au partage des héritiers légitimes
        masse_partageable_finale = masse_nette_avant_legs - montant_executable

        return {
            "est_conforme_sharia": est_conforme,
            "statut_verdict": statut_cle,
            "plafond_autorise_un_tiers": plafond_maximum,
            "montant_testament_retenu": montant_executable,
            "masse_residuelle_heritiers": masse_partageable_finale
        }
