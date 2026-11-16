#!/usr/bin/env python3
"""Génère les textes d'Al Ansâr à partir de la source unique traductions/al_ansar.json.

    python outils/generer_traductions.py            génère et contrôle
    python outils/generer_traductions.py --controle contrôle seulement

Sorties :
  lib/src/i18n_donnees.dart                          textes intégrés au module (toutes les langues)
  ../integration_flet/HAYAATI_patch/ajouts_locales.json  section « al_ansar » des fichiers de langue de HAYAATI

Règle « zéro dette de traduction » : chaque clé doit avoir un texte non vide dans CHAQUE langue de `_langues`,
avec les mêmes marqueurs {nom}. Sinon le script s'arrête sans rien écrire. Pour ajouter une langue,
ajoutez-la dans `_langues` et remplissez sa colonne : le script liste tout ce qui manque.
Le contrôle vérifie aussi que chaque t('clé') du code Dart existe dans la source.
"""
import json
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SOURCE = RACINE / "traductions" / "al_ansar.json"
DART = RACINE / "lib" / "src" / "i18n_donnees.dart"
LOCALES = RACINE.parent / "integration_flet" / "HAYAATI_patch" / "ajouts_locales.json"

MENU = {
    "fr": {"alansar_hub": "🤝 Al-Ansâr", "calculs_hub": "🧮 Calculs", "mon_espace_hub": "👤 Mon espace"},
    "en": {"alansar_hub": "🤝 Al-Ansâr", "calculs_hub": "🧮 Calculations", "mon_espace_hub": "👤 My space"},
    "ar": {"alansar_hub": "🤝 الأنصار", "calculs_hub": "🧮 الحسابات", "mon_espace_hub": "👤 مساحتي"},
    "ha": {"alansar_hub": "🤝 Al-Ansâr", "calculs_hub": "🧮 Lissafi", "mon_espace_hub": "👤 Wurina"},
}
CLES_DYNAMIQUES = re.compile(r"^(repas_|cap_)")  # clés construites dans le code : t('repas_$r'), t('cap_$c')


def dart_chaine(s: str) -> str:
    s = s.replace("\\", "\\\\").replace("'", "\\'").replace("$", "\\$").replace("\n", "\\n")
    return f"'{s}'"


def controler(src: dict) -> list:
    erreurs = []
    langues = src["_langues"]
    for cle, textes in src["cles"].items():
        marqueurs_fr = set(re.findall(r"\{\w+\}", textes.get("fr", "")))
        for lg in langues:
            t = textes.get(lg, "")
            if not t.strip():
                erreurs.append(f"manque : {cle} [{lg}]")
            elif set(re.findall(r"\{\w+\}", t)) != marqueurs_fr:
                erreurs.append(f"marqueurs différents du français : {cle} [{lg}]")
    for lg in langues:
        if lg not in MENU:
            erreurs.append(f"libellés de menu absents pour la langue {lg} (voir MENU dans ce script)")
    utilisees = set()
    for f in (RACINE / "lib").rglob("*.dart"):
        if f.name == "i18n_donnees.dart":
            continue
        utilisees |= set(re.findall(r"\bt\('([a-zA-Z_]+)'\)", f.read_text(encoding="utf-8")))
    for cle in sorted(utilisees - set(src["cles"])):
        if not CLES_DYNAMIQUES.match(cle):
            erreurs.append(f"clé utilisée dans le code mais absente de la source : {cle}")
    return erreurs


def main() -> int:
    src = json.loads(SOURCE.read_text(encoding="utf-8"))
    erreurs = controler(src)
    if erreurs:
        print(f"{len(erreurs)} problème(s) de traduction :")
        for e in erreurs:
            print("  -", e)
        return 1
    langues = src["_langues"]
    print(f"{len(src['cles'])} clés complètes dans {len(langues)} langues : {', '.join(langues)}")
    for lg, statut in src.get("_statut", {}).items():
        if lg != "fr":
            print(f"  {lg} : {statut}")
    if "--controle" in sys.argv:
        return 0
    lignes = ["// FICHIER GÉNÉRÉ par outils/generer_traductions.py depuis traductions/al_ansar.json : ne pas modifier à la main.",
              "const Map<String, Map<String, String>> chainesGenerees = <String, Map<String, String>>{"]
    for lg in langues:
        lignes.append(f"  '{lg}': <String, String>{{")
        for cle, textes in src["cles"].items():
            lignes.append(f"    '{cle}': {dart_chaine(textes[lg])},")
        lignes.append("  },")
    lignes.append("};")
    DART.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    sortie = {lg: {"menu": MENU[lg], "al_ansar": {k: t[lg] for k, t in src["cles"].items()}} for lg in langues}
    LOCALES.parent.mkdir(parents=True, exist_ok=True)
    LOCALES.write_text(json.dumps(sortie, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"écrit : {DART.relative_to(RACINE)} et {LOCALES.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
