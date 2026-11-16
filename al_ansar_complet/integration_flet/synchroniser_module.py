#!/usr/bin/env python3
"""Copie le module Flutter (al_ansar_flutter) dans l'extension Flet.

    python synchroniser_module.py             copie
    python synchroniser_module.py --verifier  contrôle que la copie est à jour (code de sortie 1 sinon)

Seuls lib/, assets/, pubspec.yaml et analysis_options.yaml sont copiés : pas de tests,
pas d'application d'essai. La copie vit dans
hayaati_alnsar/src/flutter/hayaati_alnsar/packages/al_ansar/.
"""
import filecmp
import shutil
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
SOURCE = RACINE.parent / "al_ansar_flutter"
CIBLE = RACINE / "hayaati_alnsar" / "src" / "flutter" / "hayaati_alnsar" / "packages" / "al_ansar"
ELEMENTS = ["lib", "assets", "pubspec.yaml", "analysis_options.yaml"]


def fichiers(base: Path):
    for nom in ELEMENTS:
        p = base / nom
        if p.is_file():
            yield p.relative_to(base)
        elif p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file():
                    yield f.relative_to(base)


def main() -> int:
    if not SOURCE.is_dir():
        print(f"Module introuvable : {SOURCE}")
        return 1
    attendus = list(fichiers(SOURCE))
    if "--verifier" in sys.argv:
        manquants = [f for f in attendus if not (CIBLE / f).is_file() or not filecmp.cmp(SOURCE / f, CIBLE / f, shallow=False)]
        en_trop = [f for f in fichiers(CIBLE) if f not in attendus]
        for f in manquants:
            print("différent ou absent :", f)
        for f in en_trop:
            print("en trop :", f)
        print("Copie à jour." if not (manquants or en_trop) else "Copie obsolète : relancez synchroniser_module.py")
        return 0 if not (manquants or en_trop) else 1
    if CIBLE.exists():
        shutil.rmtree(CIBLE)
    for f in attendus:
        (CIBLE / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE / f, CIBLE / f)
    print(f"{len(attendus)} fichiers copiés vers {CIBLE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
