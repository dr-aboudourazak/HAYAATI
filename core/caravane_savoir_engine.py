"""
MOTEUR DE LA CARAVANE DU SAVOIR (CORE/CARAVANE_SAVOIR_ENGINE.PY)
Version 1.0 - Construit une session de révision personnalisée en piochant
dans les points "à revoir" de TOUS les modules de langue arabe déjà
parcourus (alphabet, vocabulaire, conjugaison, grammaire, lecture).
Ne duplique aucune donnée : reconstruit chaque carte à la volée à partir
du contenu déjà stocké dans le dictionnaire de langue, et renvoie vers la
même clé de progression que le module d'origine — corriger un point ici
met à jour directement le compteur du module concerné.
"""


def _resoudre_alphabet(etape, identifiant):
    try:
        l = etape.get("lettres", [])[int(identifiant)]
    except (ValueError, IndexError):
        return None
    return {"arabe": l.get("lettre", ""), "translitteration": l.get("translitteration", ""), "sens": l.get("nom", ""), "module": "Alphabet"}


def _resoudre_vocabulaire(etape, identifiant):
    try:
        partie_liste, partie_mot = identifiant.split("_mot")
        i_liste = int(partie_liste.replace("liste", ""))
        i_mot = int(partie_mot)
        mot = etape.get("listes", [])[i_liste]["mots"][i_mot]
    except (ValueError, IndexError, KeyError):
        return None
    return {"arabe": mot.get("arabe", ""), "translitteration": mot.get("translitteration", ""), "sens": mot.get("sens", ""), "module": "Vocabulaire"}


def _resoudre_conjugaison(etape, cle_etape, identifiant):
    temps_cle = cle_etape[len("conjugaison_"):]
    for temps in etape.get("temps", []):
        if temps.get("cle") != temps_cle:
            continue
        prefixe = f"{cle_etape}_"
        if not identifiant.startswith(prefixe):
            return None
        try:
            c = temps.get("conjugaisons", [])[int(identifiant[len(prefixe):])]
        except (ValueError, IndexError):
            return None
        return {"arabe": c.get("forme", ""), "translitteration": c.get("translitteration", ""),
                "sens": c.get("sens", ""), "module": f"Conjugaison — {temps.get('titre','')}"}
    return None


def _premier_exemple(lecon):
    exemples = lecon.get("exemples", [])
    return exemples[0] if exemples else {"arabe": "", "translitteration": ""}


def _resoudre_grammaire(etape, cle_etape, identifiant):
    reste = cle_etape[len("grammaire_"):]
    try:
        i = int(identifiant)
    except ValueError:
        return None
    for bab in etape.get("babs", []):
        cle_bab = bab.get("cle", "")
        if reste == cle_bab:
            lecons = bab.get("lecons", [])
            if 0 <= i < len(lecons):
                ex = _premier_exemple(lecons[i])
                return {"arabe": ex.get("arabe") or lecons[i].get("titre", ""), "translitteration": ex.get("translitteration", ""),
                        "sens": lecons[i].get("titre", ""), "module": f"Grammaire — {bab.get('titre','')}"}
        for sr in bab.get("sous_rubriques", []):
            if reste == f"{cle_bab}_{sr.get('cle','')}":
                lecons = sr.get("lecons", [])
                if 0 <= i < len(lecons):
                    ex = _premier_exemple(lecons[i])
                    return {"arabe": ex.get("arabe") or lecons[i].get("titre", ""), "translitteration": ex.get("translitteration", ""),
                            "sens": lecons[i].get("titre", ""), "module": f"Grammaire — {bab.get('titre','')} / {sr.get('titre','')}"}
    return None


def _resoudre_lecture(etape, identifiant):
    try:
        texte = etape.get("textes", [])[int(identifiant)]
    except (ValueError, IndexError):
        return None
    return {"arabe": texte.get("titre", ""), "translitteration": "", "sens": texte.get("niveau", ""), "module": "Lecture"}


def resoudre_item(contenu_langue_arabe, cle_etape, identifiant):
    """Retrouve (arabe/translitteration/sens/module) pour un identifiant de progression donné.
    Renvoie None si le contenu source a changé ou disparu — l'appelant doit ignorer ces cas
    plutôt que planter, le contenu du dictionnaire pouvant évoluer indépendamment."""
    etapes_index = {e.get("cle"): e for e in contenu_langue_arabe.get("etapes", [])}
    try:
        if cle_etape == "alphabet":
            return _resoudre_alphabet(etapes_index.get("alphabet", {}), identifiant)
        if cle_etape == "vocabulaire":
            return _resoudre_vocabulaire(etapes_index.get("vocabulaire", {}), identifiant)
        if cle_etape.startswith("conjugaison_"):
            return _resoudre_conjugaison(etapes_index.get("conjugaison", {}), cle_etape, identifiant)
        if cle_etape.startswith("grammaire_"):
            return _resoudre_grammaire(etapes_index.get("grammaire", {}), cle_etape, identifiant)
        if cle_etape == "lecture":
            return _resoudre_lecture(etapes_index.get("lecture", {}), identifiant)
    except Exception:
        return None
    return None


def construire_session_revision(progres, contenu_langue_arabe, taille_max=10):
    """Priorité aux points marqués "à revoir" dans n'importe quel module ; si la
    session est trop courte (débutant, peu de contenu vu), on complète avec des
    points déjà "connus" pour ne jamais présenter un écran vide."""
    candidats = []
    for cle_etape, donnees in progres.items():
        if cle_etape == "caravane":
            continue
        for identifiant in donnees.get("a_revoir", []):
            item = resoudre_item(contenu_langue_arabe, cle_etape, identifiant)
            if item:
                item.update({"cle_etape": cle_etape, "identifiant": identifiant, "complement": False})
                candidats.append(item)

    if len(candidats) < taille_max:
        for cle_etape, donnees in progres.items():
            if cle_etape == "caravane" or len(candidats) >= taille_max:
                continue
            for identifiant in donnees.get("connues", []):
                if len(candidats) >= taille_max:
                    break
                item = resoudre_item(contenu_langue_arabe, cle_etape, identifiant)
                if item:
                    item.update({"cle_etape": cle_etape, "identifiant": identifiant, "complement": True})
                    candidats.append(item)

    return candidats[:taille_max]


def compter_points_a_revoir(progres):
    return sum(len(d.get("a_revoir", [])) for cle, d in progres.items() if cle != "caravane")
