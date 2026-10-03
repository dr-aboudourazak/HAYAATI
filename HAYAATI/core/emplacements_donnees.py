"""
EMPLACEMENTS DE DONNÉES (CORE/EMPLACEMENTS_DONNEES.PY)
Point unique de résolution du dossier de données privées de l'application
(base SQLite, clé maîtresse Fernet, cache de position). Ce dossier est
volontairement HORS de l'arbre du code source (ni core/, ni gui/) :

  1. Un "Add files via upload" ou un commit fait par erreur depuis le
     dossier du projet ne peut plus embarquer des données réelles
     d'utilisateur — elles ne sont physiquement plus dans un dossier
     suivi par Git.
  2. Deuxième ligne de défense derrière le .gitignore (qui doit rester
     en place) : deux protections indépendantes plutôt qu'une seule.

⚠️ Incident du 22/09/2026 : HAYAATI/core/hayaati_private.db (chemin
   relatif "core/hayaati_private.db", donc À L'INTÉRIEUR de l'arbre
   suivi par Git) a été committé et rendu public sur GitHub — compte
   utilisateur en clair (email, date de naissance, hash de mot de
   passe) + modules chiffrés. Cause racine double : aucun .gitignore
   dans le dépôt, ET un chemin par défaut qui pointait dans un dossier
   suivi. Ce module corrige la seconde cause ; le .gitignore ajouté à
   la racine du projet corrige la première.

Le mécanisme (chemin relatif au dossier de travail courant) reste
identique à l'ancien comportement sur PC comme sur Android — seul le
NOM du dossier change, pour ne rien risquer sur le build mobile déjà
fragile par ailleurs.
"""
from __future__ import annotations
import os
import stat

NOM_DOSSIER_DONNEES = "hayaati_donnees_privees"


def dossier_donnees_application() -> str:
    """Retourne (et crée si besoin) le dossier de données privées,
    toujours en dehors de core/ et gui/."""
    dossier = os.path.join(os.getcwd(), NOM_DOSSIER_DONNEES)
    if not os.path.exists(dossier):
        os.makedirs(dossier, exist_ok=True)
    try:
        # Accès restreint au seul propriétaire. Sous Windows, os.chmod
        # ne porte pas le même modèle de permissions : ignoré sans
        # bruit, comme déjà pratiqué pour la clé maîtresse elle-même.
        os.chmod(dossier, stat.S_IRWXU)
    except (OSError, NotImplementedError):
        pass
    return dossier


def chemin_base_privee(nom_fichier: str = "hayaati_private.db") -> str:
    """Chemin de la base SQLite privée (comptes + modules chiffrés).
    Migre automatiquement, une seule fois et par déplacement (pas copie,
    pour ne jamais laisser deux exemplaires divergents), une base et sa
    clé trouvées à l'ancien emplacement (core/, avant la correction du
    23/09/2026) — sans quoi un compte existant perdrait ses données à la
    première mise à jour vers cette version."""
    chemin_cible = os.path.join(dossier_donnees_application(), nom_fichier)
    if not os.path.exists(chemin_cible):
        _migrer_depuis_ancien_emplacement(chemin_cible)
    return chemin_cible


def _migrer_depuis_ancien_emplacement(chemin_cible: str) -> None:
    dossier_ancien = os.path.join(os.getcwd(), "core")
    for nom in ("hayaati_private.db", ".cle_maitresse.key"):
        source = os.path.join(dossier_ancien, nom)
        cible = os.path.join(os.path.dirname(chemin_cible), nom)
        if os.path.exists(source) and not os.path.exists(cible):
            try:
                import shutil
                shutil.move(source, cible)
                print(f"[emplacements_donnees] Migré depuis l'ancien emplacement : {nom}")
            except Exception as exc:
                print(f"[emplacements_donnees] Migration de {nom} a échoué (sans conséquence si {nom} n'existait pas vraiment) : {exc}")


def chemin_cache_position(nom_fichier: str = "derniere_position_connue.json") -> str:
    """Chemin du cache de la dernière position connue (GPS ou IP), pour
    le mode hors-ligne renforcé de core/agenda_engine.py."""
    return os.path.join(dossier_donnees_application(), nom_fichier)
