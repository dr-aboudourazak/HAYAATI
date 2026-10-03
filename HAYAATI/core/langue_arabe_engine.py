"""
MOTEUR DU MODULE LANGUE ARABE (CORE/LANGUE_ARABE_ENGINE.PY)
Version 2.0 - Généralisé pour couvrir toutes les étapes (alphabet, vocabulaire,
conjugaison, grammaire, lecture) sous une structure de progression unique par
étape, au lieu d'une structure figée pour l'alphabet seul.
Même principe non punitif partout : une carte reste "connue" jusqu'à ce
qu'on la repasse en revue soi-même, pas de série à préserver.
"""

CLE_MODULE_LANGUE_ARABE = "LANGUE_ARABE_PROGRES"


def etat_progres_par_defaut():
    return {}


def _normaliser_etape(donnees_etape):
    donnees_etape = donnees_etape or {}
    connues = [str(i) for i in donnees_etape.get("connues", [])]
    a_revoir = [str(i) for i in donnees_etape.get("a_revoir", [])]
    return {"connues": sorted(set(connues)), "a_revoir": sorted(set(a_revoir))}


def normaliser_progres(donnees):
    """Structure : {"alphabet": {"connues": [...], "a_revoir": [...]}, "vocabulaire": {...}, ...}
    Tolère une ancienne structure à plat (Version 1.0, alphabet uniquement) en la
    migrant automatiquement sous la clé 'alphabet'."""
    donnees = donnees or {}
    if "lettres_connues" in donnees or "lettres_a_revoir" in donnees:
        donnees = {"alphabet": {"connues": donnees.get("lettres_connues", []), "a_revoir": donnees.get("lettres_a_revoir", [])}}

    resultat = {}
    for cle_etape, valeur in donnees.items():
        if isinstance(valeur, dict):
            resultat[cle_etape] = _normaliser_etape(valeur)
    return resultat


def marquer_item(progres, cle_etape, identifiant_item, connu):
    """Bascule un item (lettre, mot...) entre 'connu' et 'à revoir', exclusivement,
    au sein d'une étape donnée (identifiée par sa clé : 'alphabet', 'vocabulaire'...)."""
    progres = normaliser_progres(progres)
    etape = progres.get(cle_etape, {"connues": [], "a_revoir": []})
    connues = set(etape["connues"])
    a_revoir = set(etape["a_revoir"])
    identifiant_item = str(identifiant_item)
    if connu:
        connues.add(identifiant_item)
        a_revoir.discard(identifiant_item)
    else:
        a_revoir.add(identifiant_item)
        connues.discard(identifiant_item)
    progres[cle_etape] = {"connues": sorted(connues), "a_revoir": sorted(a_revoir)}
    return progres


def etat_item(progres, cle_etape, identifiant_item):
    """Renvoie 'connu', 'a_revoir' ou 'non_vu' pour un item donné."""
    etape = normaliser_progres(progres).get(cle_etape, {"connues": [], "a_revoir": []})
    identifiant_item = str(identifiant_item)
    if identifiant_item in etape["connues"]:
        return "connu"
    if identifiant_item in etape["a_revoir"]:
        return "a_revoir"
    return "non_vu"


def resume_etape(progres, cle_etape, total_items):
    etape = normaliser_progres(progres).get(cle_etape, {"connues": [], "a_revoir": []})
    nb_connues = len(etape["connues"])
    nb_a_revoir = len(etape["a_revoir"])
    nb_non_vues = max(total_items - nb_connues - nb_a_revoir, 0)
    return {"connues": nb_connues, "a_revoir": nb_a_revoir, "non_vues": nb_non_vues, "total": total_items}


# --- Alias de compatibilité avec la Version 1.0 (alphabet uniquement) ---
def marquer_lettre(progres, index_lettre, connue):
    return marquer_item(progres, "alphabet", index_lettre, connue)


def resume_progression(progres, total_lettres):
    return resume_etape(progres, "alphabet", total_lettres)
