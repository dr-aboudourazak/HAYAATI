#!/usr/bin/env python3
"""Prépare le dossier à publier pour Al Ansâr (Cloudflare Pages, GitHub Pages ou tout hébergement statique).

    python publier_donnees.py --annuaire annuaire_TG.json --mosquees mosquees_TG.json --sortie publication_cloudflare/site/al-ansar
    python publier_donnees.py ... --production      (refuse les fiches d'exemple et applique tous les garde-fous)

Le script : valide les fichiers, les copie dans le dossier de sortie, calcule taille et empreinte SHA-256,
met à jour manifest.json (les autres pays déjà présents sont conservés) et écrit le fichier _headers
(cache court pour le manifeste, une heure pour les données).
Ensuite il suffit de mettre le dossier « site » en ligne ; l'adresse à reporter dans
gui/pages/page_alansar.py (URL_DONNEES_AL_ANSAR) est affichée à la fin.
"""
import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import valider_annuaire as va  # noqa: E402

# Rectangles approximatifs [lat_min, lon_min, lat_max, lon_max] servant à détecter le pays d'un voyageur.
PAYS = {
    "TG": ("Togo", "Togo", [6.1, -0.15, 11.14, 1.81]),
    "BJ": ("Bénin", "Benin", [6.2, 0.77, 12.42, 3.85]),
    "GH": ("Ghana", "Ghana", [4.7, -3.3, 11.2, 1.2]),
    "BF": ("Burkina Faso", "Burkina Faso", [9.4, -5.5, 15.1, 2.4]),
    "NE": ("Niger", "Niger", [11.7, 0.2, 23.5, 16.0]),
    "NG": ("Nigeria", "Nigeria", [4.2, 2.7, 13.9, 14.7]),
    "CI": ("Côte d'Ivoire", "Ivory Coast", [4.3, -8.6, 10.7, -2.5]),
}


def valider(chemin: Path, production: bool) -> dict:
    schema = json.loads((Path(__file__).with_name("al_ansar_annuaire.schema.json")).read_text(encoding="utf-8"))
    d = json.loads(chemin.read_text(encoding="utf-8"))
    erreurs = va.controle_schema(d, schema)
    if not erreurs:
        e2, _ = va.controle_metier(d, production)
        erreurs += e2
    if erreurs:
        print(f"{chemin.name} : non valide")
        for e in erreurs:
            print("  -", e)
        sys.exit(1)
    return d


def empreinte(chemin: Path):
    octets = chemin.read_bytes()
    return hashlib.sha256(octets).hexdigest(), len(octets)


def main() -> int:
    ap = argparse.ArgumentParser(description="Prépare le dossier de publication d'Al Ansâr")
    ap.add_argument("--annuaire", type=Path, required=True)
    ap.add_argument("--mosquees", type=Path, required=True)
    ap.add_argument("--sortie", type=Path, required=True, help="dossier publié, ex. publication_cloudflare/site/al-ansar")
    ap.add_argument("--base-url", default="", help="adresse publique du dossier (terminée par /), pour information")
    ap.add_argument("--production", action="store_true")
    args = ap.parse_args()

    ann, mos = valider(args.annuaire, args.production), valider(args.mosquees, args.production)
    if ann["pays"] != mos["pays"]:
        print("Les deux fichiers ne concernent pas le même pays.")
        return 1
    pays = ann["pays"]
    if mos.get("nature_fichier") != "mosquees":
        print("Le fichier des mosquées doit avoir nature_fichier = « mosquees ».")
        return 1

    args.sortie.mkdir(parents=True, exist_ok=True)
    fichiers = {"annuaire": (args.annuaire, f"annuaire_{pays}.json", ann), "mosquees": (args.mosquees, f"mosquees_{pays}.json", mos)}
    entree = {}
    for role, (src, nom, d) in fichiers.items():
        dst = args.sortie / nom
        shutil.copy2(src, dst)
        sha, taille = empreinte(dst)
        entree[role] = {"fichier": nom, "version_donnees": d["version_donnees"], "nb_fiches": len(d["fiches"]),
                        "taille_octets": taille, "sha256": sha}

    chemin_manifeste = args.sortie / "manifest.json"
    manifeste = {"version_manifeste": 2, "pays": []}
    if chemin_manifeste.exists():
        manifeste = json.loads(chemin_manifeste.read_text(encoding="utf-8"))
    manifeste["genere_le"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if args.base_url:
        manifeste["base_url"] = args.base_url
    autres = [p for p in manifeste.get("pays", []) if p["code"] != pays]
    fr, en, bbox = PAYS.get(pays, (pays, pays, None))
    nouveau = {"code": pays, "nom": {"fr": fr, "en": en}}
    if bbox:
        nouveau["bbox"] = bbox
    nouveau.update(entree)
    manifeste["pays"] = sorted(autres + [nouveau], key=lambda p: p["code"])
    chemin_manifeste.write_text(json.dumps(manifeste, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Cloudflare Pages lit _headers à la racine du site (dossier parent de « al-ansar »)
    racine_site = args.sortie.parent
    (racine_site / "_headers").write_text(
        "/al-ansar/manifest.json\n  Cache-Control: no-cache\n  Access-Control-Allow-Origin: *\n\n"
        "/al-ansar/*.json\n  Cache-Control: public, max-age=3600\n  Access-Control-Allow-Origin: *\n", encoding="utf-8")

    print(f"Pays {pays} publié : annuaire v{entree['annuaire']['version_donnees']} ({entree['annuaire']['taille_octets']} o), "
          f"mosquées v{entree['mosquees']['version_donnees']} ({entree['mosquees']['taille_octets']} o).")
    print(f"Dossier à mettre en ligne : {racine_site}")
    if args.base_url:
        print(f"URL_DONNEES_AL_ANSAR = \"{args.base_url}\"")
    else:
        print('Une fois en ligne : URL_DONNEES_AL_ANSAR = "https://<votre-site>/al-ansar/" dans gui/pages/page_alansar.py')
    return 0


if __name__ == "__main__":
    sys.exit(main())
