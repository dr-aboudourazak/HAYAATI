"""
MOTEUR DU JEU ÉDUCATIF "LE SENTIER DU SAVOIR" (CORE/JEU_EDUCATIF_ENGINE.PY)
Version 1.0 - Innovation propre à HAYAATI : chaque thème de l'Encyclopédie
devient une étape avec un mini-quiz sourcé (Coran / hadith / fiqh comparé).
Logique pure, sans dépendance à Tkinter, pour rester testable et portable
vers la future interface mobile.

Principe de conception : pas de série à préserver, pas de compte à rebours,
pas de classement comparatif entre utilisateurs. La progression se mesure
à la maîtrise réelle (questions comprises), pas à l'assiduité forcée.
"""

CLE_MODULE_JEU = "JEU_EDUCATIF_PROGRES"

# Paliers de badges, fondés sur le nombre de "Perles de Savoir" (= questions
# maîtrisées de façon unique, sans re-comptage en cas de répétition du quiz).
PALIERS_BADGES = [
    (0, "apprenti", "🌱 Apprenti du Savoir"),
    (5, "eclaire", "🕯️ Éclairé du Savoir"),
    (13, "savant", "📖 Savant HAYAATI"),
    (21, "gardien", "🏅 Gardien du Sentier"),
]


def etat_progres_par_defaut():
    return {"lus": [], "quiz_reussis": {}}


def normaliser_progres(donnees):
    """S'assure que la structure chargée depuis sync_engine est saine,
    même si elle provient d'une ancienne version ou d'un enregistrement partiel."""
    donnees = donnees or {}
    lus = donnees.get("lus", [])
    quiz_reussis_brut = donnees.get("quiz_reussis", {})
    quiz_reussis = {}
    if isinstance(quiz_reussis_brut, dict):
        for cle, valeur in quiz_reussis_brut.items():
            try:
                quiz_reussis[str(int(cle))] = sorted(set(int(v) for v in valeur))
            except (ValueError, TypeError):
                continue
    return {"lus": sorted(set(int(i) for i in lus if str(i).lstrip("-").isdigit())), "quiz_reussis": quiz_reussis}


def compter_perles(progres):
    """Nombre total de questions maîtrisées, tous thèmes confondus."""
    quiz_reussis = progres.get("quiz_reussis", {})
    return sum(len(v) for v in quiz_reussis.values())


def badge_actuel(nb_perles):
    """Renvoie (cle_badge, libelle) correspondant au nombre de perles obtenues."""
    resultat = PALIERS_BADGES[0]
    for seuil, cle, libelle in PALIERS_BADGES:
        if nb_perles >= seuil:
            resultat = (cle, libelle)
    return resultat


def prochain_palier(nb_perles):
    """Renvoie (perles_manquantes, libelle_prochain_badge) ou None si le dernier palier est atteint."""
    for seuil, _cle, libelle in PALIERS_BADGES:
        if nb_perles < seuil:
            return seuil - nb_perles, libelle
    return None


def enregistrer_reponse(progres, index_categorie, index_question, est_correcte):
    """Met à jour la structure de progression après une réponse au quiz.
    Une question déjà maîtrisée ne rapporte pas de nouvelle perle si on la
    retente : ça évite de transformer le jeu en simple générateur de score."""
    progres = normaliser_progres(progres)
    cle = str(index_categorie)
    if est_correcte:
        deja = set(progres["quiz_reussis"].get(cle, []))
        deja.add(index_question)
        progres["quiz_reussis"][cle] = sorted(deja)
    return progres


def questions_maitrisees_categorie(progres, index_categorie):
    return set(progres.get("quiz_reussis", {}).get(str(index_categorie), []))
