"""
ROUTEUR CENTRAL DES LANGUES (GUI/LANGUES.PY)
Centralise et distribue les dictionnaires de traduction de la plateforme Hayaati.
"""
from gui.dictionnaires.fr import DATA_FR
from gui.dictionnaires.en import DATA_EN
from gui.dictionnaires.ar import DATA_AR
from gui.dictionnaires.ha import DATA_HA
from gui.dictionnaires.es import DATA_ES
from gui.dictionnaires.zh import DATA_ZH

# Injection dynamique de l'étiquette du sélecteur de Fiqh pour l'accueil de manière sécurisée
DATA_FR["selection_fiqh"] = "Fiqh / Madhhab :"
DATA_EN["selection_fiqh"] = "Fiqh / Madhhab:"
DATA_AR["selection_fiqh"] = "الفقه / المذهب:"
DATA_HA["selection_fiqh"] = "Fiqh / Madhhab:"
DATA_ES["selection_fiqh"] = "Fiqh / Madhhab:"
DATA_ZH["selection_fiqh"] = "法学派别 / 麦兹海布："

# Base de données d'internationalisation (i18n) maîtresse de l'application
DICTIONNAIRE_LANGUES = {
    "FR": DATA_FR,
    "EN": DATA_EN,
    "AR": DATA_AR,
    "HA": DATA_HA,
    "ES": DATA_ES,
    "ZH": DATA_ZH
}
