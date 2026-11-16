#!/usr/bin/env python3
"""Traite une proposition envoyée depuis l'application (nouvelle mosquée ou correction de position).

Le responsable colle le message WhatsApp reçu dans un fichier texte (par exemple proposition.txt).
Le script y retrouve la ligne « AL-ANSAR-JSON {...} », vérifie la proposition et la compare à
l'annuaire, puis, sur demande, met à jour le fichier des mosquées.

Usage :
    python traiter_proposition.py mosquees_TG.json proposition.txt
        -> analyse seulement : rien n'est modifié
    python traiter_proposition.py mosquees_TG.json proposition.txt --appliquer
        -> nouvelle mosquée ajoutée en brouillon, ou position corrigée (non confirmée)
    python traiter_proposition.py mosquees_TG.json proposition.txt --appliquer --publier
        -> la nouvelle mosquée est publiée tout de suite
    python traiter_proposition.py mosquees_TG.json proposition.txt --appliquer --confirmer --par pf-dapaong-01
        -> correction de position confirmée par le responsable pf-dapaong-01

Une sauvegarde « .bak » est créée avant toute écriture, puis le fichier est revalidé.
Dépendance : pip install jsonschema (poste du responsable uniquement).
"""
import argparse
import json
import math
import re
import shutil
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import valider_annuaire as va  # noqa: E402
from jsonschema import Draft202012Validator, FormatChecker  # noqa: E402

PREFIXE = "AL-ANSAR-JSON "
SEUIL_DOUBLON_M = 75        # une autre mosquée à moins de 75 m : doublon probable
SEUIL_PRECISION_M = 50      # au-delà, le relevé GPS est jugé peu fiable
SEUIL_VILLE_M = 30_000      # position à plus de 30 km du centre de la ville annoncée
MOTS_VIDES = {"mosquee", "masjid", "grande", "centrale", "de", "du", "la", "le", "des", "d", "l"}


def distance_m(lat1, lon1, lat2, lon2):
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def normaliser(nom):
    sans_accents = "".join(c for c in unicodedata.normalize("NFKD", nom) if not unicodedata.combining(c))
    mots = re.sub(r"[^a-z0-9]+", " ", sans_accents.lower()).split()
    return " ".join(m for m in mots if m not in MOTS_VIDES)


def lire_proposition(chemin):
    texte = Path(chemin).read_text(encoding="utf-8")
    for ligne in texte.splitlines():
        i = ligne.find(PREFIXE)
        if i >= 0:
            return json.loads(ligne[i + len(PREFIXE):].strip())
    return json.loads(texte)  # fichier JSON brut


def horodatage():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def analyser(d, p):
    """Renvoie (infos, alertes, fiche_concernee)."""
    infos, alertes = [], []
    pos = p["position"]
    fiche = None

    villes = {v["id"]: v for v in d.get("villes", [])}
    ville = villes.get(p.get("ville_id"))
    if p.get("ville_id") and ville is None:
        alertes.append(f"ville_id inconnu : {p['ville_id']}")
    elif ville and ville.get("gps"):
        ecart = distance_m(pos["lat"], pos["lon"], ville["gps"]["lat"], ville["gps"]["lon"])
        infos.append(f"distance au centre de la ville : {ecart / 1000:.1f} km")
        if ecart > SEUIL_VILLE_M:
            alertes.append(f"position à {ecart / 1000:.0f} km du centre de la ville annoncée")

    precision = pos.get("precision_m")
    if precision is None:
        alertes.append("précision GPS absente")
    elif precision > SEUIL_PRECISION_M:
        alertes.append(f"précision GPS faible (±{precision:.0f} m)")

    mosquees = [f for f in d["fiches"] if f["type"] == "mosquee"]
    if p["type"] == "correction_position":
        fiche = next((f for f in mosquees if f["id"] == p["fiche_id"]), None)
        if fiche is None:
            alertes.append(f"fiche introuvable : {p['fiche_id']}")
        else:
            ancien = fiche["lieu"]["gps"]
            ecart = distance_m(ancien["lat"], ancien["lon"], pos["lat"], pos["lon"])
            infos.append(f"écart avec la position actuelle : {ecart:.0f} m")
    else:
        nom_n = normaliser(p["nom"])
        for f in mosquees:
            g = f["lieu"]["gps"]
            dd = distance_m(g["lat"], g["lon"], pos["lat"], pos["lon"])
            if dd < SEUIL_DOUBLON_M:
                alertes.append(f"doublon probable : « {f['nom']} » ({f['id']}) à {dd:.0f} m")
            elif nom_n and normaliser(f["nom"]) == nom_n:
                alertes.append(f"même nom que « {f['nom']} » ({f['id']}), à {dd / 1000:.1f} km")
    return infos, alertes, fiche


def appliquer(d, p, fiche, publier, confirmer, par):
    maintenant = horodatage()
    pos = p["position"]
    bloc_gps = {"lat": pos["lat"], "lon": pos["lon"], "source": "releve_sur_place", "verifiee": bool(confirmer)}
    if "precision_m" in pos:
        bloc_gps["precision_m"] = pos["precision_m"]

    if p["type"] == "correction_position":
        fiche["lieu"]["gps"] = bloc_gps
        fiche["maj_le"] = maintenant
        cible = fiche
    else:
        ville_id = p["ville_id"]
        numeros = [int(m.group(1)) for f in d["fiches"]
                   if (m := re.fullmatch(re.escape(ville_id) + r"-msq-(\d+)", f["id"]))]
        cible = {
            "id": f"{ville_id}-msq-{max(numeros, default=0) + 1:03d}",
            "type": "mosquee",
            "nature": "personne_morale",
            "nom": p["nom"],
            "lieu": {"ville_id": ville_id, "precision_adresse": "exacte", "gps": bloc_gps},
            "verification": {"niveau": 0},
            "statut": "publie" if publier else "brouillon",
            "mosquee": {"jumua": "inconnu", "femmes": "inconnu", "ablutions": "inconnu"},
            "source": {"origine": "communaute", "importe_le": maintenant[:10]},
            "maj_le": maintenant,
        }
        d["fiches"].append(cible)

    if confirmer:
        v = cible["verification"]
        v["niveau"] = max(v.get("niveau", 0), 1)
        v["verifie_par"] = par
        v["date"] = maintenant[:10]
        details = set(v.get("details", [])) | {"existence_controlee"}
        v["details"] = sorted(details)

    d["version_donnees"] += 1
    d["genere_le"] = maintenant
    return cible


def main():
    ap = argparse.ArgumentParser(description="Traite une proposition de mosquée (nouvelle ou correction).")
    ap.add_argument("mosquees", type=Path, help="fichier mosquees_XX.json")
    ap.add_argument("proposition", type=Path, help="message WhatsApp collé dans un fichier, ou JSON brut")
    ap.add_argument("--appliquer", action="store_true", help="écrit la modification (sinon simple analyse)")
    ap.add_argument("--publier", action="store_true", help="nouvelle mosquée publiée au lieu d'être en brouillon")
    ap.add_argument("--confirmer", action="store_true", help="marque la position comme vérifiée (exige --par)")
    ap.add_argument("--par", help="code du responsable qui confirme, ex. pf-dapaong-01")
    args = ap.parse_args()

    if args.confirmer and not args.par:
        ap.error("--confirmer exige --par CODE_RESPONSABLE")

    try:
        d = json.loads(args.mosquees.read_text(encoding="utf-8"))
        p = lire_proposition(args.proposition)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Lecture impossible : {e}")
        return 1

    schema_p = json.loads((Path(__file__).with_name("al_ansar_proposition.schema.json")).read_text(encoding="utf-8"))
    erreurs = [f"{'/'.join(map(str, e.absolute_path)) or '(racine)'} : {e.message}"
               for e in Draft202012Validator(schema_p, format_checker=FormatChecker()).iter_errors(p)]
    if erreurs:
        print("Proposition invalide :")
        for e in erreurs:
            print("  -", e)
        return 1
    if p["pays"] != d.get("pays"):
        print(f"Pays différent : proposition {p['pays']}, fichier {d.get('pays')}")
        return 1

    infos, alertes, fiche = analyser(d, p)
    print(f"Type : {p['type']}   Nom : {p['nom']}")
    print(f"Position : {p['position']['lat']}, {p['position']['lon']}"
          + (f" (±{p['position']['precision_m']} m)" if 'precision_m' in p['position'] else ""))
    print(f"Carte : https://www.openstreetmap.org/?mlat={p['position']['lat']}&mlon={p['position']['lon']}#map=19/{p['position']['lat']}/{p['position']['lon']}")
    for i in infos:
        print("  info    ", i)
    for a in alertes:
        print("  ALERTE  ", a)

    if p["type"] == "correction_position" and fiche is None:
        return 1
    if not args.appliquer:
        print("\nAnalyse seulement : rien n'a été modifié. Ajoutez --appliquer pour écrire.")
        return 0

    shutil.copy2(args.mosquees, args.mosquees.with_suffix(args.mosquees.suffix + ".bak"))
    cible = appliquer(d, p, fiche, args.publier, args.confirmer, args.par)
    args.mosquees.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nFiche {cible['id']} mise à jour ({cible['statut']}), version_donnees = {d['version_donnees']}.")

    schema = json.loads(Path(__file__).with_name("al_ansar_annuaire.schema.json").read_text(encoding="utf-8"))
    problemes = va.controle_schema(d, schema)
    if not problemes:
        e2, _ = va.controle_metier(d, production=False)
        problemes += e2
    if problemes:
        print("Le fichier modifié ne passe pas la validation :")
        for e in problemes:
            print("  -", e)
        print(f"Restaurez la sauvegarde : {args.mosquees}.bak")
        return 1
    print("Validation OK. Republiez le fichier et mettez à jour le manifeste (version et empreinte SHA-256).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
