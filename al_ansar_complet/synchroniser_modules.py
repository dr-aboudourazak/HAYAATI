"""
SYNCHRONISER LES MODULES (synchroniser_modules.py) - lot C, 01/11/2026

Copie les paquets Flutter de l'espace de travail F:\\al_ansar_complet vers l'extension Flet, là où `flet build` les
embarque. L'espace de travail est la SOURCE DE VÉRITÉ (on y modifie et on y teste en Flutter pur) ; les copies de
l'extension sont GÉNÉRÉES : ne jamais les modifier à la main.

    espace de travail (source)                  extension (copie générée)
    al_ansar_complet\\al_ansar_flutter      ->    hayaati_alnsar\\src\\flutter\\hayaati_alnsar\\packages\\al_ansar
    al_ansar_complet\\hayaati_ui            ->    ...\\packages\\hayaati_ui
    al_ansar_complet\\hayaati_coran         ->    ...\\packages\\hayaati_coran

Utilisation, depuis F:\\al_ansar_complet :
    python synchroniser_modules.py --extension "F:\\hayaati_alnsar" --a-blanc      (montre, n'écrit rien)
    python synchroniser_modules.py --extension "F:\\hayaati_alnsar"

Ce qui est copié de chaque paquet : lib\\, assets\\, pubspec.yaml, analysis_options.yaml, LICENSE, README.md.
Ce qui ne l'est JAMAIS : test\\, example\\, .dart_tool\\, build\\, pubspec.lock et autres fichiers générés.
Dans la copie de l'extension, tout fichier qui n'existe pas dans la source est supprimé (la copie est une image fidèle).
Le script refuse d'écrire dans tout chemin qui contient « HAYAATI-main » (ta copie validée).
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
CIBLE_FLUTTER = ("src", "flutter", "hayaati_alnsar", "packages")

# (dossier source dans l'espace de travail, nom du paquet dans l'extension)
MODULES = (
    ("al_ansar_flutter", "al_ansar"),
    ("hayaati_ui", "hayaati_ui"),
    ("hayaati_coran", "hayaati_coran"),
)
ELEMENTS = ("lib", "assets", "pubspec.yaml", "analysis_options.yaml", "LICENSE", "README.md")
DOSSIERS_EXCLUS = {".dart_tool", "build", "__pycache__", ".idea", ".gradle", "test", "example"}
FICHIERS_EXCLUS = {"pubspec.lock", ".flutter-plugins", ".flutter-plugins-dependencies", ".packages", ".gitkeep"}


def fichiers_source(dossier: str) -> dict[str, str]:
    """{chemin relatif avec /, chemin complet} de tout ce qui doit être copié."""
    trouves: dict[str, str] = {}
    for element in ELEMENTS:
        complet = os.path.join(dossier, element)
        if os.path.isfile(complet):
            trouves[element] = complet
        elif os.path.isdir(complet):
            for chemin, sous_dossiers, fichiers in os.walk(complet):
                sous_dossiers[:] = [d for d in sous_dossiers if d not in DOSSIERS_EXCLUS]
                for nom in fichiers:
                    if nom in FICHIERS_EXCLUS:
                        continue
                    f = os.path.join(chemin, nom)
                    trouves[os.path.relpath(f, dossier).replace(os.sep, "/")] = f
    return trouves


def fichiers_cible(dossier: str) -> set[str]:
    trouves: set[str] = set()
    if os.path.isdir(dossier):
        for chemin, _, fichiers in os.walk(dossier):
            for nom in fichiers:
                trouves.add(os.path.relpath(os.path.join(chemin, nom), dossier).replace(os.sep, "/"))
    return trouves


def identiques(a: str, b: str) -> bool:
    if not os.path.isfile(b) or os.path.getsize(a) != os.path.getsize(b):
        return False
    with open(a, "rb") as fa, open(b, "rb") as fb:
        return fa.read() == fb.read()


def refuser_copie_validee(nom: str, chemin: str) -> None:
    if "hayaati-main" in os.path.abspath(chemin).lower().replace("_", "-"):
        print(f"REFUSÉ : {nom} = {chemin}")
        print("Ce dossier contient « HAYAATI-main », ta copie validée. Ce script n'écrit jamais dedans.")
        sys.exit(2)


def main() -> int:
    ap = argparse.ArgumentParser(description="Synchronise les paquets Flutter vers l'extension (copie générée).")
    ap.add_argument("--racine", default=ICI, help="espace de travail (défaut : le dossier de ce script)")
    ap.add_argument("--extension", required=True, help="dossier de l'extension, ex. F:\\hayaati_alnsar")
    ap.add_argument("--a-blanc", action="store_true", help="n'écrit rien, montre ce qui serait fait")
    a = ap.parse_args()
    racine, extension = os.path.abspath(a.racine), os.path.abspath(a.extension)
    refuser_copie_validee("racine", racine)
    refuser_copie_validee("extension", extension)

    paquets = os.path.join(extension, *CIBLE_FLUTTER)
    if not os.path.isfile(os.path.join(extension, "src", "flutter", "hayaati_alnsar", "pubspec.yaml")):
        print(f"ERREUR : {extension} ne ressemble pas au dossier de l'extension (pubspec.yaml de l'extension introuvable).")
        return 2

    plan = []
    erreurs = []
    for source_nom, paquet in MODULES:
        source = os.path.join(racine, source_nom)
        if not (os.path.isfile(os.path.join(source, "pubspec.yaml")) and os.path.isdir(os.path.join(source, "lib"))):
            erreurs.append(f"{source} : pubspec.yaml ou lib\\ introuvable.")
            continue
        cible = os.path.join(paquets, paquet)
        src = fichiers_source(source)
        existants = fichiers_cible(cible)
        a_copier = [r for r, f in sorted(src.items()) if not identiques(f, os.path.join(cible, *r.split("/")))]
        a_supprimer = sorted(existants - set(src))
        plan.append((source_nom, paquet, cible, src, a_copier, a_supprimer))
    if erreurs:
        print("RIEN N'A ÉTÉ ÉCRIT :")
        for e in erreurs:
            print("  -", e)
        return 1

    total_copie = total_supprime = 0
    print(f"Espace de travail : {racine}\nExtension         : {extension}\n")
    for source_nom, paquet, _, src, a_copier, a_supprimer in plan:
        print(f"{source_nom:18} -> packages\\{paquet:14} {len(src):4} fichiers, à copier : {len(a_copier):4}, à supprimer : {len(a_supprimer):4}")
        total_copie += len(a_copier)
        total_supprime += len(a_supprimer)
    if a.a_blanc:
        print("\nMode à blanc : rien n'a été écrit.")
        return 0
    if total_copie == 0 and total_supprime == 0:
        print("\nTout est déjà synchronisé.")
        return 0

    for _, _, cible, src, a_copier, a_supprimer in plan:
        for rel in a_supprimer:
            os.remove(os.path.join(cible, *rel.split("/")))
        for rel in a_copier:
            destination = os.path.join(cible, *rel.split("/"))
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            shutil.copy2(src[rel], destination)
        # dossiers devenus vides
        for chemin, _, _ in sorted(os.walk(cible), key=lambda t: -len(t[0])):
            if chemin != cible and not os.listdir(chemin):
                os.rmdir(chemin)
    print(f"\nSynchronisé : {total_copie} fichiers copiés, {total_supprime} supprimés.")
    print("Pensez à relancer `flutter pub get` dans le dossier de l'extension avant le build.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
