#!/usr/bin/env python3
"""Branche Al-Ansâr dans HAYAATI (idempotent : peut être relancé sans danger).

    python appliquer_integration.py F:\\chemin\\vers\\HAYAATI

La racine est le dossier qui contient « gui », « core » et « assets ». Avant toute
modification, chaque fichier est sauvegardé une fois HORS du projet, dans <dossier parent>\\sauvegardes_alansar\\ (jamais dans l'APK).

Modifications :
  1. gui/pages/page_alansar.py et page_hub_simple.py : ajoutés.
  2. gui/app_layout.py : écrans ALANSAR, CALCULS et MON_ESPACE enregistrés ; MADRASSA devient le hub Madrassa en Flutter.
  3. gui/app_visuelle_toolbar.py : barre à 5 boutons (Accueil, Prière, Coran, Calculs ou
     Mon espace, Al-Ansâr) et surbrillance du bouton quand on est dans un de ses sous-écrans.
  4. gui/app_visuelle.py : le bouton « retour » d'Android laisse d'abord Al-Ansâr
     revenir d'un écran interne.
  5. assets/locales/*.json : section « al_ansar » et libellés de menu.
  6. pyproject.toml : épinglage de shared_preferences_android (conflit jni avec Flet 0.86.5).
"""
import json
import re
import shutil
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
MARQUEUR = "ALANSAR"


def lire(p: Path):
    brut = p.read_bytes().decode("utf-8")
    crlf = "\r\n" in brut
    return brut.replace("\r\n", "\n"), crlf


RACINE_PROJET = None  # renseignée par main()


def chemin_sauvegarde(p: Path) -> Path:
    """Les sauvegardes vivent HORS du projet (F:\\sauvegardes_alansar\\<projet>\\...) : dans gui/ ou assets/ elles seraient embarquées dans l'APK."""
    rel = p.resolve().relative_to(RACINE_PROJET)
    return RACINE_PROJET.parent / "sauvegardes_alansar" / RACINE_PROJET.name / (str(rel) + ".avant_alansar")


def sauvegarder(p: Path):
    cible = chemin_sauvegarde(p)
    if not cible.exists() and p.exists():
        cible.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, cible)


def ecrire(p: Path, texte: str, crlf: bool):
    sauvegarder(p)
    if crlf:
        texte = texte.replace("\n", "\r\n")
    p.write_bytes(texte.encode("utf-8"))


def migrer_anciennes_sauvegardes(racine: Path):
    """Déplace hors du projet les fichiers *.avant_alansar laissés par une version précédente du script."""
    deplaces = 0
    for f in list(racine.rglob("*.avant_alansar")):
        if "build" in f.relative_to(racine).parts[:1]:
            continue
        original = f.with_name(f.name[: -len(".avant_alansar")])
        cible = chemin_sauvegarde(original)
        cible.parent.mkdir(parents=True, exist_ok=True)
        if cible.exists():
            f.unlink()
        else:
            shutil.move(str(f), str(cible))
        deplaces += 1
    if deplaces:
        print(f"  ~ {deplaces} ancienne(s) sauvegarde(s) déplacée(s) hors du projet : {racine.parent / 'sauvegardes_alansar' / racine.name}")


def copier_pages(racine: Path):
    for nom in ("page_alansar.py", "page_hub_simple.py"):
        src, dst = ICI / "gui" / "pages" / nom, racine / "gui" / "pages" / nom
        if dst.exists() and dst.read_bytes() == src.read_bytes():
            print(f"  = {nom} déjà à jour")
            continue
        sauvegarder(dst)
        shutil.copy2(src, dst)
        print(f"  + {nom} copié")


def patch_layout(racine: Path):
    p = racine / "gui" / "app_layout.py"
    s, crlf = lire(p)
    if "PageAlAnsar" in s:
        print("  = app_layout.py déjà patché")
        return
    a = "from gui.pages.page_madrassa import PageMadrassa\n"
    b = '            "MADRASSA": PageMadrassa,\n'
    assert s.count(a) == 1 and s.count(b) == 1, "app_layout.py : points d'ancrage introuvables"
    s = s.replace(a, a + "from gui.pages.page_alansar import PageAlAnsar\nfrom gui.pages.page_hub_simple import PageCalculs, PageMonEspace\n")
    s = s.replace(b, b + '            "ALANSAR": PageAlAnsar,\n            "CALCULS": PageCalculs,\n            "MON_ESPACE": PageMonEspace,\n')
    ecrire(p, s, crlf)
    print("  + app_layout.py patché")


def patch_madrassa_native(racine: Path):
    """L'écran « MADRASSA » devient le hub Madrassa du module Flutter (PageMadrassaNative)."""
    p = racine / "gui" / "app_layout.py"
    s, crlf = lire(p)
    if "PageMadrassaNative" in s:
        print("  = app_layout.py : MADRASSA déjà en Flutter")
        return
    ancien_import = "from gui.pages.page_alansar import PageAlAnsar\n"
    ancien_route = '            "MADRASSA": PageMadrassa,\n'
    assert s.count(ancien_import) == 1 and s.count(ancien_route) == 1, "app_layout.py : lignes MADRASSA introuvables"
    s = s.replace(ancien_import, "from gui.pages.page_alansar import PageAlAnsar, PageMadrassaNative\n")
    s = s.replace(ancien_route, '            "MADRASSA": PageMadrassaNative,  # ancien écran Python : gui/pages/page_madrassa.py\n')
    ecrire(p, s, crlf)
    print("  + app_layout.py : MADRASSA -> hub Madrassa en Flutter")


def patch_toolbar(racine: Path):
    p = racine / "gui" / "app_visuelle_toolbar.py"
    s, crlf = lire(p)
    if "_GROUPES_NAVIGATION" in s:
        print("  = app_visuelle_toolbar.py déjà patché")
        return
    # connecté : Devoirs + Inventaire + Madrassa -> Mon espace + Al-Ansâr
    motif_c = re.compile(
        r'(?P<i>[ ]+)\(m_json\.get\("devoirs_hub"[^\n]*"DEVOIRS"\),[ ]*\n'
        r'[ ]+\(m_json\.get\("inventaire_hub"[^\n]*"INVENTAIRE"\),[ ]*\n'
        r'[ ]+\(m_json\.get\("madrassa_hub"[^\n]*"MADRASSA"\),[ ]*\n')
    # visiteur : Zakat + Succession + Madrassa -> Calculs + Al-Ansâr
    motif_v = re.compile(
        r'(?P<i>[ ]+)\(f"\{m_json\.get\(\'zakat\'[^\n]*"ZAKAT_TIERS"\),[ ]*\n'
        r'[ ]+\(f"\{m_json\.get\(\'heritage\'[^\n]*"HERITAGE_TIERS"\),[ ]*\n'
        r'[ ]+\(m_json\.get\("madrassa_hub"[^\n]*"MADRASSA"\),[ ]*\n')
    assert len(motif_c.findall(s)) == 1, "barre connecté : lignes introuvables"
    assert len(motif_v.findall(s)) == 1, "barre visiteur : lignes introuvables"
    s = motif_c.sub(lambda m: (f'{m["i"]}(m_json.get("mon_espace_hub", "👤 Mon espace"), "MON_ESPACE"),\n'
                               f'{m["i"]}(m_json.get("alansar_hub", "🤝 Al-Ansâr"), "ALANSAR"),\n'), s)
    s = motif_v.sub(lambda m: (f'{m["i"]}(m_json.get("calculs_hub", "🧮 Calculs"), "CALCULS"),\n'
                               f'{m["i"]}(m_json.get("alansar_hub", "🤝 Al-Ansâr"), "ALANSAR"),\n'), s)
    # surbrillance : le bouton d'un hub reste actif dans ses sous-écrans
    motif_a = re.compile(r"est_a = \(app\.ecran_courant == cle\)")
    assert len(motif_a.findall(s)) == 2, "surbrillance : lignes introuvables"
    s = motif_a.sub("est_a = (app.ecran_courant in _GROUPES_NAVIGATION.get(cle, (cle,)))", s)
    constante = ('# Un bouton de la barre reste actif dans les écrans qu\'il regroupe.\n'
                 '_GROUPES_NAVIGATION = {\n'
                 '    "MON_ESPACE": ("MON_ESPACE", "DEVOIRS", "INVENTAIRE"),\n'
                 '    "CALCULS": ("CALCULS", "ZAKAT_TIERS", "HERITAGE_TIERS"),\n'
                 '    "ALANSAR": ("ALANSAR", "MADRASSA"),\n'
                 '}\n\n\n')
    i = s.index("def configurer_bandeau_superieur")
    s = s[:i] + constante + s[i:]
    ecrire(p, s, crlf)
    print("  + app_visuelle_toolbar.py patché (5 boutons)")


def patch_retour(racine: Path):
    p = racine / "gui" / "app_visuelle.py"
    s, crlf = lire(p)
    nouveau_if = 'if getattr(self, "ecran_courant", None) in ("ALANSAR", "MADRASSA") and getattr(self, "layout_central", None):'
    if nouveau_if in s:
        print("  = app_visuelle.py : retour Al-Ansâr/Madrassa déjà patché")
        return
    ancien_if = 'if getattr(self, "ecran_courant", None) == "ALANSAR" and getattr(self, "layout_central", None):'
    ancien_get = 'page_alansar = self.layout_central.ecrans_instances.get("ALANSAR")'
    nouveau_get = 'page_alansar = self.layout_central.ecrans_instances.get(self.ecran_courant)'
    if ancien_if in s:  # mise à jour d'une intégration précédente
        s = s.replace(ancien_if, nouveau_if).replace(ancien_get, nouveau_get)
        s = s.replace("# Al-Ansâr : le module Flutter a sa propre navigation interne.", "# Al-Ansâr et Madrassa : le module Flutter a sa propre navigation interne.")
        ecrire(p, s, crlf)
        print("  ~ app_visuelle.py : retour étendu à Madrassa")
        return
    ancre = ('        a_navigue = False\n'
             '        if hasattr(self, "layout_central") and self.layout_central:\n')
    assert s.count(ancre) == 1, "app_visuelle.py : gestion du retour introuvable"
    nouveau = ('        a_navigue = False\n'
               '        # Al-Ansâr et Madrassa : le module Flutter a sa propre navigation interne.\n'
               f'        {nouveau_if}\n'
               '            try:\n'
               f'                {nouveau_get}\n'
               '                if page_alansar is not None and await page_alansar.gerer_retour():\n'
               '                    a_navigue = True\n'
               '            except Exception as exc:\n'
               '                print(f"[NAV] Retour Al-Ansâr : {exc}")\n'
               '        if not a_navigue and hasattr(self, "layout_central") and self.layout_central:\n')
    s = s.replace(ancre, nouveau)
    ecrire(p, s, crlf)
    print("  + app_visuelle.py patché (bouton retour)")


def patch_locales(racine: Path):
    ajouts = json.loads((ICI / "ajouts_locales.json").read_text(encoding="utf-8"))
    for code, contenu in ajouts.items():
        p = racine / "assets" / "locales" / f"{code}.json"
        if not p.exists():
            print(f"  ! {p.name} absent, ignoré")
            continue
        s, crlf = lire(p)
        d = json.loads(s)
        d.setdefault("menu", {}).update(contenu["menu"])
        d["al_ansar"] = contenu["al_ansar"]
        sortie = json.dumps(d, ensure_ascii=False, indent=1) + "\n"
        if sortie.replace("\r\n", "\n") == s:
            print(f"  = {p.name} déjà à jour")
            continue
        ecrire(p, sortie, crlf)
        print(f"  + {p.name} : section al_ansar ({len(contenu['al_ansar'])} textes)")


def patch_pyproject(racine: Path):
    """Épingle shared_preferences_android à 2.3.4, version validée sur le build de HAYAATI :
    2.5.0+ utilise Pigeon JNI et exige jni ^1.1.0, alors que Flet 0.86.5 impose jni 1.0.0.
    Une valeur déjà présente est conservée, sauf l'ancienne « 2.4.29 » proposée par erreur (version introuvable)."""
    cible = '"2.3.4"'
    p = racine / "pyproject.toml"
    if not p.exists():
        print('  ! pyproject.toml introuvable : ajoutez à la main shared_preferences_android = "2.3.4" (voir INSTALLATION.md)')
        return
    s, crlf = lire(p)
    existante = re.search(r'^(shared_preferences_android\s*=\s*)("[^"]*")', s, re.M)
    if existante:
        if existante.group(2) not in ('"2.4.29"', '">=2.4.0 <2.5.0"'):
            print(f"  = pyproject.toml : shared_preferences_android conservé ({existante.group(2)})")
            return
        s = s[: existante.start(2)] + cible + s[existante.end(2):]
        ecrire(p, s, crlf)
        print(f"  ~ pyproject.toml : shared_preferences_android {existante.group(2)} remplacé par {cible}")
        return
    motif = re.compile(r'^(path_provider_android\s*=\s*"[^"]+"[^\n]*)\n', re.M)
    if not motif.search(s):
        print("  ! pyproject.toml : table [tool.flet.flutter.pubspec.dependency_overrides] introuvable.")
        print('    Ajoutez-la avec : shared_preferences_android = "2.3.4" (voir INSTALLATION.md)')
        return
    ajout = ("# Épinglage pour Al-Ansâr : shared_preferences_android 2.5.0+ utilise Pigeon JNI et exige jni ^1.1.0,\n"
             "# alors que Flet 0.86.5 impose jni 1.0.0. 2.3.4 est la version validée sur ce projet (build du 25/10/2026).\n"
             "# À retirer en même temps que l'override ci-dessus, lors d'une montée de version de Flet.\n"
             f"shared_preferences_android = {cible}\n")
    s = motif.sub(lambda m: m.group(1) + "\n" + ajout, s, count=1)
    ecrire(p, s, crlf)
    print(f"  + pyproject.toml : shared_preferences_android = {cible} ajouté")


def verifier_langues(racine: Path):
    """Signale les fichiers de langue de HAYAATI qui n'ont pas de section « al_ansar » complète."""
    ajouts = json.loads((ICI / "ajouts_locales.json").read_text(encoding="utf-8"))
    attendues = set(ajouts["fr"]["al_ansar"])
    manque = []
    for p in sorted((racine / "assets" / "locales").glob("*.json")):
        code = p.stem
        section = json.loads(lire(p)[0]).get("al_ansar", {})
        if not attendues <= set(section):
            manque.append(code)
    if manque:
        print(f"  ! Langues de HAYAATI SANS traduction complète d'Al-Ansâr : {', '.join(manque)}")
        print("    Ajoutez la langue dans al_ansar_flutter/traductions/al_ansar.json (clé _langues) et remplissez sa colonne,")
        print("    puis relancez outils/generer_traductions.py (il refuse tant qu'une traduction manque).")
    else:
        print("  = toutes les langues de HAYAATI ont des textes Al-Ansâr complets")


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    racine = Path(sys.argv[1]).resolve()
    if not (racine / "gui" / "app_layout.py").exists():
        print(f"« {racine} » ne contient pas gui/app_layout.py : indiquez le dossier du projet HAYAATI.")
        return 1
    global RACINE_PROJET
    RACINE_PROJET = racine
    print(f"Intégration d'Al-Ansâr dans {racine}")
    migrer_anciennes_sauvegardes(racine)
    for etape in (copier_pages, patch_layout, patch_madrassa_native, patch_toolbar, patch_retour, patch_locales, patch_pyproject, verifier_langues):
        etape(racine)
    print("Terminé. Installez l'extension hayaati-alnsar (voir INSTALLATION.md), puis reconstruisez l'application.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
