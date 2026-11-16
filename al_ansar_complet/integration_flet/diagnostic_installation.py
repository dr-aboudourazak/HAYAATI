#!/usr/bin/env python3
"""Diagnostique pourquoi Al-Ansâr garde l'ancien comportement après une nouvelle livraison.

    python diagnostic_installation.py F:\\chemin\\vers\\HAYAATI              diagnostic seul
    python diagnostic_installation.py F:\\chemin\\vers\\HAYAATI --nettoyer   vide aussi le cache de flet build
    python diagnostic_installation.py F:\\chemin\\vers\\HAYAATI --corriger   recopie la livraison à l'endroit d'où
                                                                           HAYAATI installe l'extension, puis vide le cache

Deux couches peuvent rester périmées :
  1. L'ENDROIT D'INSTALLATION : pyproject.toml installe l'extension depuis un dossier (ex. file:///F:/hayaati_alnsar).
     Dézipper une livraison ailleurs ne le met pas à jour : il faut recopier l'extension dans ce dossier.
  2. LE CACHE DE FLET BUILD : si les dépendances n'ont pas changé, `flet build` réutilise build/flutter-packages
     du build précédent (code Dart et données de l'extension inclus).
"""
import hashlib
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import unquote

ICI = Path(__file__).resolve().parent
LIVRAISON = ICI / "hayaati_alnsar"                       # racine de l'extension livrée
FLUTTER = Path("src") / "flutter" / "hayaati_alnsar"
FICHIERS_CLES = [
    "pyproject.toml",
    "src/hayaati_alnsar/hayaati_alnsar.py",
    "src/hayaati_alnsar/__init__.py",
    str(FLUTTER / "pubspec.yaml"),
    str(FLUTTER / "lib/src/control.dart"),
    str(FLUTTER / "assets/al_ansar/annuaire_TG.json"),
    str(FLUTTER / "assets/al_ansar/mosquees_TG.json"),
    str(FLUTTER / "packages/al_ansar/lib/src/config.dart"),
    str(FLUTTER / "packages/al_ansar/lib/src/controleur.dart"),
    str(FLUTTER / "packages/al_ansar/lib/src/i18n_donnees.dart"),
    str(FLUTTER / "packages/al_ansar/lib/src/ui/ecrans.dart"),
]


def sha(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def lire_pyproject(projet: Path):
    p = projet / "pyproject.toml"
    if not p.exists():
        return None, ""
    texte = p.read_text(encoding="utf-8")
    try:
        import tomllib
        return tomllib.loads(texte), texte
    except Exception:
        return None, texte


def chemin_installation(cfg, texte: str):
    """Dossier d'où pyproject.toml installe hayaati-alnsar (ligne `hayaati-alnsar @ file:///...`)."""
    lignes = (cfg or {}).get("project", {}).get("dependencies", []) if cfg else re.findall(r'"([^"]*alnsar[^"]*)"', texte)
    for dep in lignes:
        if re.match(r"\s*hayaati[-_]alnsar\b", dep):
            m = re.search(r"@\s*file:/+(.+?)\s*$", dep)
            if not m:
                return None, dep
            brut = unquote(m.group(1))
            return Path(brut if re.match(r"^[A-Za-z]:", brut) else "/" + brut), dep
    return None, None


def differences(source: Path, copie: Path, fichiers):
    return [f for f in fichiers if sha(source / f) != sha(copie / f)]


def vider_cache(build: Path):
    for cible in (build / ".hash" / "package", build / "flutter-packages"):
        if cible.is_dir():
            shutil.rmtree(cible, ignore_errors=True)
            print(f"  supprimé : {cible}")
        elif cible.exists():
            cible.unlink()
            print(f"  supprimé : {cible}")


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        print(__doc__)
        return 1
    projet = Path(args[0]).resolve()
    build = projet / "build"
    corriger, nettoyer = "--corriger" in sys.argv, "--nettoyer" in sys.argv
    problemes = []

    print(f"Projet : {projet}")
    cfg, texte = lire_pyproject(projet)
    if not texte:
        print("  ? pyproject.toml introuvable à la racine du projet")
        return 1

    # 1. endroit d'installation
    installation, dep = chemin_installation(cfg, texte)
    if dep is None:
        print("  KO  hayaati-alnsar n'est pas déclaré dans [project] dependencies")
        problemes.append("declaration")
    elif installation is None:
        print(f"  ?   dépendance non locale ({dep.strip()}) : contrôle de l'endroit d'installation impossible")
    elif not installation.exists():
        print(f"  KO  dossier d'installation introuvable : {installation}")
        problemes.append("installation")
    else:
        diff = differences(LIVRAISON, installation, FICHIERS_CLES)
        if diff:
            problemes.append("installation")
            print(f"  KO  l'extension installée depuis {installation} est DIFFÉRENTE de la livraison ({len(diff)} fichier(s))")
            for f in diff[:6]:
                print(f"        différent ou absent : {f}")
        else:
            print(f"  OK  {installation} contient exactement la livraison")

    # 2. cache de flet build
    copie = build / "flutter-packages" / "hayaati_alnsar"
    if not copie.exists():
        print("  OK  aucune copie en cache de l'extension : le prochain build la crée à neuf")
    else:
        diff = differences(LIVRAISON / FLUTTER, copie, [str(Path(f).relative_to(FLUTTER)) for f in FICHIERS_CLES if f.startswith(str(FLUTTER))])
        if diff:
            problemes.append("cache")
            print(f"  KO  copie en cache de flet build PÉRIMÉE : {copie}")
            for f in diff[:6]:
                print(f"        différent ou absent : {f}")
        else:
            print("  OK  la copie en cache de flet build est identique à la livraison")

    dev = ((cfg or {}).get("tool", {}).get("flet", {}).get("dev_packages", {})) if cfg else {}
    print(f"  --  [tool.flet.dev_packages] : {'contient hayaati-alnsar (réinstallation complète à chaque build)' if 'hayaati-alnsar' in dev else 'absent (normal : voir INSTALLATION.md)'}")

    if corriger and "installation" in problemes and installation is not None:
        for nom in ("src",):
            cible = installation / nom
            if cible.exists():
                shutil.rmtree(cible)
            shutil.copytree(LIVRAISON / nom, cible)
        for nom in ("pyproject.toml", "README.md"):
            if (LIVRAISON / nom).exists():
                shutil.copy2(LIVRAISON / nom, installation / nom)
        print(f"  corrigé : extension recopiée dans {installation}")
        problemes = [p for p in problemes if p != "installation"] + (["cache"] if (build / "flutter-packages").exists() else [])
        nettoyer = True
    if nettoyer or (corriger and "cache" in problemes):
        vider_cache(build)
        print("Cache de flet build vidé : le prochain build réinstalle tout (plus long, une seule fois).")
        problemes = [p for p in problemes if p != "cache"]

    if problemes:
        print("\nRelancez avec --corriger (recopie l'extension et vide le cache), puis reconstruisez.")
        return 2
    print("\nTout est cohérent. Après le build, l'accueil d'Al-Ansâr (mode démo) doit afficher « Module 0.4.0 · données : embarqué v4 · 4 fiches (4 visibles) · 2 forfaits · démo : oui ».")
    return 0


if __name__ == "__main__":
    sys.exit(main())
