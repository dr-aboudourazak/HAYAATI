#!/usr/bin/env python3
"""Validateur de l'annuaire Al Ansâr (phase 0).

Usage :
    python valider_annuaire.py annuaire_TG.json
    python valider_annuaire.py annuaire_TG.json --production

Contrôle 1 : conformité au schéma JSON (structure, types, formats).
Contrôle 2 : règles métier que le schéma ne sait pas exprimer
             (références, seuils, garde-fous roqya, niveaux de vérification...).

Le mode --production refuse en plus les fiches d'exemple et les fiches publiées
sans vérification suffisante. Code de sortie : 0 si tout est bon, 1 sinon.

Dépendance (poste de développement uniquement) : pip install jsonschema
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

SANTE_SPIRITUELLE = {"roqya", "medecine_prophetique"}


def score_transparence(f):
    """Part des 11 rubriques de la fiche de coûts renseignées, de 0 à 100 (même calcul que l'application)."""
    heb = f.get("hebergement", {})
    criteres = [
        "vol" in f,
        "distance_haram_m" in heb.get("makkah", {}),
        "distance_masjid_m" in heb.get("madina", {}),
        "repas" in f,
        "visa_inclus" in f,
        "transport_inclus" in f,
        "present" in f.get("guide", {}),
        "max" in f.get("taille_groupe", {}),
        "incluse" in f.get("assurance", {}),
        bool(f.get("politique_annulation")),
        "frais_non_inclus" in f,
    ]
    return round(100 * sum(criteres) / len(criteres))
TYPES_VENDEURS = {"librairie", "boutique", "artisan"}


def charger(chemin: Path) -> dict:
    with chemin.open(encoding="utf-8") as f:
        return json.load(f)


def controle_schema(donnees: dict, schema: dict) -> list[str]:
    validateur = Draft202012Validator(schema, format_checker=FormatChecker())
    erreurs = []
    for e in sorted(validateur.iter_errors(donnees), key=lambda x: list(x.absolute_path)):
        chemin = "/".join(str(p) for p in e.absolute_path) or "(racine)"
        erreurs.append(f"[schéma] {chemin} : {e.message}")
    return erreurs


def controle_metier(d: dict, production: bool) -> tuple[list[str], list[str]]:
    erreurs, avertissements = [], []
    aujourd_hui = date.today()
    nature = d.get("nature_fichier", "annuaire")
    if nature == "mosquees":
        for cle in ("cours", "articles", "prestations"):
            if d.get(cle):
                erreurs.append(f"[métier] un fichier « mosquees » ne doit pas contenir de {cle}")

    fiches = {f["id"]: f for f in d.get("fiches", [])}
    villes = {x["id"] for x in d.get("villes", [])}
    tous_ids = [x["id"] for x in d.get("villes", [])] + [f["id"] for f in d.get("fiches", [])]
    for cle in ("cours", "articles", "prestations"):
        tous_ids += [x["id"] for x in d.get(cle, [])]

    # Identifiants uniques sur tout le fichier
    vus = set()
    for i in tous_ids:
        if i in vus:
            erreurs.append(f"[métier] identifiant en double : {i}")
        vus.add(i)

    # Le préfixe de l'identifiant doit être le pays du fichier
    pays = d.get("pays", "").lower()
    for i in tous_ids:
        if not i.startswith(pays + "-"):
            erreurs.append(f"[métier] {i} : l'identifiant doit commencer par « {pays}- »")

    if production and d.get("demonstration"):
        erreurs.append("[production] fichier marqué « demonstration » : interdit en production")

    # Fiches
    for f in fiches.values():
        fid = f["id"]
        est_mosquee = f["type"] == "mosquee"
        if est_mosquee and nature != "mosquees":
            erreurs.append(f"[métier] {fid} : les mosquées vont dans mosquees_XX.json (nature_fichier = « mosquees »)")
        if not est_mosquee and nature == "mosquees":
            erreurs.append(f"[métier] {fid} : seul le type « mosquee » est admis dans un fichier de mosquées")
        if est_mosquee:
            ct = f.get("contacts", {})
            if ("whatsapp" in ct or "telephone" in ct) and "consentement_publication" not in f:
                erreurs.append(f"[vie privée] {fid} : numéro de téléphone publié sans consentement_publication")
        if f.get("source", {}).get("origine") == "openstreetmap" and "OpenStreetMap" not in d.get("attribution", ""):
            erreurs.append(f"[licence] {fid} : source OpenStreetMap sans attribution « © contributeurs OpenStreetMap » (ODbL)")
        if f["lieu"].get("gps", {}).get("verifiee") and niveau < 1:
            erreurs.append(f"[métier] {fid} : position marquée « verifiee » mais fiche de niveau 0")
        if f["lieu"]["ville_id"] not in villes:
            erreurs.append(f"[métier] {fid} : ville_id inconnu ({f['lieu']['ville_id']})")
        for vid in f.get("zone_service", {}).get("villes", []):
            if vid not in villes:
                erreurs.append(f"[métier] {fid} : zone_service référence une ville inconnue ({vid})")
        niveau = f["verification"]["niveau"]
        if niveau == 3 and not f["verification"].get("recommande_par"):
            erreurs.append(f"[métier] {fid} : niveau 3 sans « recommande_par »")
        if f["type"] == "madrassa" and "madrassa" not in f:
            avertissements.append(f"{fid} : fiche madrassa sans bloc « madrassa »")
        if f["type"] == "specialiste" and "specialiste" not in f:
            avertissements.append(f"{fid} : fiche spécialiste sans bloc « specialiste »")
        if f["statut"] == "publie" and not f.get("description"):
            avertissements.append(f"{fid} : fiche publiée sans description")
        if production:
            if f.get("exemple"):
                erreurs.append(f"[production] {fid} : fiche d'exemple interdite")

    # Cours
    for c in d.get("cours", []):
        cid, fid = c["id"], c["fiche_id"]
        fiche = fiches.get(fid)
        if fiche is None:
            erreurs.append(f"[métier] {cid} : fiche_id inconnu ({fid})")
        elif fiche["type"] != "madrassa":
            erreurs.append(f"[métier] {cid} : un cours doit appartenir à une madrassa ({fid} est de type {fiche['type']})")
        if "seuil_min" in c and "capacite_max" in c and c["seuil_min"] > c["capacite_max"]:
            erreurs.append(f"[métier] {cid} : seuil_min ({c['seuil_min']}) supérieur à capacite_max ({c['capacite_max']})")
        if c["horaire"]["fin"] <= c["horaire"]["debut"]:
            erreurs.append(f"[métier] {cid} : l'heure de fin doit suivre l'heure de début")
        limite = date.fromisoformat(c["date_limite"]) if "date_limite" in c else None
        if limite and c["statut"] == "ouvert_preinscriptions" and limite < aujourd_hui:
            erreurs.append(f"[métier] {cid} : date limite dépassée ({c['date_limite']}) pour un cours encore ouvert")
        if limite and "debut_prevu" in c and date.fromisoformat(c["debut_prevu"]) < limite:
            erreurs.append(f"[métier] {cid} : le début prévu précède la date limite de préinscription")
        pre = c.get("preinscrits")
        if pre and "capacite_max" in c and pre["nombre"] > c["capacite_max"]:
            erreurs.append(f"[métier] {cid} : plus de préinscrits ({pre['nombre']}) que de places ({c['capacite_max']})")

    # Agences et forfaits Hadj et Omra : l'argent des pèlerins est en jeu, garde-fous renforcés
    for f in fiches.values():
        if f["type"] != "agence":
            continue
        fid = f["id"]
        agrement = f.get("agence", {}).get("agrement")
        if f["statut"] == "publie":
            if f["verification"]["niveau"] < 2:
                erreurs.append(f"[garde-fou] {fid} : une agence Hadj/Omra ne se publie qu'à partir du niveau 2")
            if not agrement:
                erreurs.append(f"[garde-fou] {fid} : agence publiée sans agrément officiel renseigné")
            elif agrement.get("valide_jusqua") and date.fromisoformat(agrement["valide_jusqua"]) < aujourd_hui:
                erreurs.append(f"[garde-fou] {fid} : agrément expiré le {agrement['valide_jusqua']}")
    for ft in d.get("forfaits_hadj_omra", []):
        tid, fid = ft["id"], ft["fiche_id"]
        fiche = fiches.get(fid)
        if fiche is None:
            erreurs.append(f"[métier] {tid} : fiche_id inconnu ({fid})")
            continue
        if fiche["type"] != "agence":
            erreurs.append(f"[métier] {tid} : un forfait doit appartenir à une agence")
        depart, retour = date.fromisoformat(ft["date_depart"]), date.fromisoformat(ft["date_retour"])
        if retour <= depart:
            erreurs.append(f"[métier] {tid} : le retour doit suivre le départ")
        if ft.get("ville_depart_id") and ft["ville_depart_id"] not in villes:
            erreurs.append(f"[métier] {tid} : ville_depart_id inconnu ({ft['ville_depart_id']})")
        g = ft.get("taille_groupe", {})
        if "min" in g and "max" in g and g["min"] > g["max"]:
            erreurs.append(f"[métier] {tid} : taille de groupe min supérieure à max")
        if "max" in g and ft.get("places_restantes", 0) > g["max"]:
            erreurs.append(f"[métier] {tid} : plus de places restantes que la taille maximale du groupe")
        if "acompte" in ft and ft["acompte"]["montant"] > ft["prix"]["montant"]:
            erreurs.append(f"[métier] {tid} : acompte supérieur au prix")
        if ft["statut"] == "ouvert":
            if depart < aujourd_hui:
                erreurs.append(f"[métier] {tid} : départ déjà passé pour un forfait ouvert")
            limite = ft.get("date_limite_inscription")
            if limite and date.fromisoformat(limite) < aujourd_hui:
                erreurs.append(f"[métier] {tid} : date limite d'inscription dépassée pour un forfait ouvert")
            if fiche["statut"] == "publie" and score_transparence(ft) < 70:
                avertissements.append(f"{tid} : fiche de coûts peu transparente ({score_transparence(ft)} %), à compléter avant mise en avant")

    # Articles
    for a in d.get("articles", []):
        aid, fid = a["id"], a["fiche_id"]
        fiche = fiches.get(fid)
        if fiche is None:
            erreurs.append(f"[métier] {aid} : fiche_id inconnu ({fid})")
        elif fiche["type"] not in TYPES_VENDEURS:
            erreurs.append(f"[métier] {aid} : un article doit appartenir à une librairie, boutique ou artisan")
        if a["categorie"] == "produit_naturel" and not a.get("avertissement_sante"):
            erreurs.append(f"[métier] {aid} : un produit naturel exige « avertissement_sante »: true")

    # Prestations
    for p in d.get("prestations", []):
        pid, fid = p["id"], p["fiche_id"]
        fiche = fiches.get(fid)
        if fiche is None:
            erreurs.append(f"[métier] {pid} : fiche_id inconnu ({fid})")
            continue
        if fiche["type"] != "specialiste":
            erreurs.append(f"[métier] {pid} : une prestation doit appartenir à un spécialiste")
        t = p["tarif"]
        if t["type"] == "fourchette" and t["min"] > t["max"]:
            erreurs.append(f"[métier] {pid} : tarif min supérieur au max")
        if p["besoin"] in SANTE_SPIRITUELLE:
            if "sante_spirituelle" not in d.get("modules_actifs", []):
                avertissements.append(f"{pid} : « sante_spirituelle » n'est pas dans modules_actifs, la prestation restera invisible")
            if fiche["statut"] == "publie":
                if fiche["verification"]["niveau"] < 2:
                    erreurs.append(f"[garde-fou] {pid} : roqya / médecine prophétique visibles seulement à partir du niveau 2")
                if not fiche.get("charte_acceptee_le"):
                    erreurs.append(f"[garde-fou] {pid} : charte de bonne pratique non acceptée par {fid}")

    return erreurs, avertissements


def main() -> int:
    parser = argparse.ArgumentParser(description="Valide un annuaire Al Ansâr")
    parser.add_argument("annuaire", type=Path)
    parser.add_argument("--schema", type=Path, default=Path(__file__).with_name("al_ansar_annuaire.schema.json"))
    parser.add_argument("--production", action="store_true", help="refuse les fiches d'exemple")
    args = parser.parse_args()

    try:
        donnees = charger(args.annuaire)
        schema = charger(args.schema)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Lecture impossible : {e}")
        return 1

    erreurs = controle_schema(donnees, schema)
    avertissements: list[str] = []
    if not erreurs:  # les règles métier supposent une structure correcte
        e2, avertissements = controle_metier(donnees, args.production)
        erreurs += e2

    for a in avertissements:
        print(f"AVERTISSEMENT  {a}")
    for e in erreurs:
        print(f"ERREUR         {e}")

    if erreurs:
        print(f"\nÉchec : {len(erreurs)} erreur(s), {len(avertissements)} avertissement(s).")
        return 1
    n = lambda k: len(donnees.get(k, []))
    print(f"OK : {n('fiches')} fiche(s), {n('cours')} cours, {n('articles')} article(s), "
          f"{n('prestations')} prestation(s), {n('forfaits_hadj_omra')} forfait(s) Hadj/Omra, "
          f"{len(avertissements)} avertissement(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
