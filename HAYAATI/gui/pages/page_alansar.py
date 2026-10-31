"""
ÉCRANS AL-ANSÂR ET MADRASSA (GUI/PAGES/PAGE_ALANSAR.PY)
Héberge le module Flutter natif de HAYAATI (extension hayaati-alnsar) :
  • PageAlAnsar        : annuaire, cours, mosquées proches, Hadj et Omra, et Madrassa dans le hub ;
  • PageMadrassaNative : le même module, ouvert directement sur le hub Madrassa (écran « MADRASSA »).

Ce que fait cette page, et rien de plus :
  • transmettre au module la langue, les textes traduits (section « al_ansar » des fichiers de langue),
    la dernière position connue de HAYAATI, le contenu pédagogique de la langue active et la
    progression de l'utilisateur connecté ;
  • enregistrer, via le SyncEngine existant, la progression que le module signale ;
  • rendre le bouton « retour » d'Android cohérent avec la navigation interne du module.
Les moteurs (jeu éducatif, langue arabe, Caravane) sont portés en Dart à l'identique et testés
contre ces moteurs Python ; la progression reste stockée par le SyncEngine, aucun format ne change.
"""
from __future__ import annotations

import json

import flet as ft

from gui.langues import DICTIONNAIRE_LANGUES

try:
    from hayaati_alnsar import HayaatiAlAnsar, __version__ as _VERSION_EXTENSION
    print(f"[AL-ANSÂR] extension hayaati-alnsar {_VERSION_EXTENSION} chargée")
except Exception as _exc:  # extension non installée : la page affiche un message clair
    HayaatiAlAnsar = None
    _ERREUR_IMPORT = _exc
else:
    _ERREUR_IMPORT = None

# Adresse où sont publiés manifest.json, annuaire_XX.json et mosquees_XX.json
# (terminée par « / »). Vide : le module n'utilise que les données embarquées.
URL_DONNEES_AL_ANSAR = ""

# Pays d'origine par défaut ; le module bascule seul vers le pays de la position GPS
# quand le manifeste est disponible.
PAYS_PAR_DEFAUT = "TG"

# None : le module suit les données (un fichier marqué « demonstration » affiche ses fiches
# fictives, un fichier réel non). True : affiche aussi les brouillons. False : les masque toujours.
MODE_DEMO_AL_ANSAR = True

# Modules de progression que le module Flutter a le droit d'enregistrer.
CLE_JEU = "JEU_EDUCATIF_PROGRES"
CLE_LANGUE = "LANGUE_ARABE_PROGRES"
CLE_SCIENCES = "SCIENCES_ISLAMIQUES_PROGRES"
MODULES_PROGRES = (CLE_JEU, CLE_LANGUE, CLE_SCIENCES)
SECTIONS_MADRASSA = ("madrassa", "interface_savoir", "encyclopedie", "langue_arabe", "sciences_islamiques")


def _derniere_position():
    """Dernière position réelle connue de HAYAATI (même cache que les heures de prière)."""
    try:
        from core.agenda_engine import _charger_position_persistee
        p = _charger_position_persistee()
        if p and "lat" in p and "lon" in p:
            return float(p["lat"]), float(p["lon"])
    except Exception:
        pass
    return None, None


class PageAlAnsar(ft.Container):
    ECRAN_INITIAL = None  # « madrassa » dans PageMadrassaNative

    def __init__(self, app_reference):
        self.app = app_reference
        self.page_flet = app_reference.page
        self._profondeur = 0
        self.module = None
        self._u_id = getattr(app_reference, "user_id_connecte", None)
        super().__init__(content=self._construire(), expand=True, bgcolor=ft.Colors.WHITE, padding=0)

    # --- Construction -----------------------------------------------------------
    def _construire(self):
        if HayaatiAlAnsar is None:
            return ft.Column(
                [ft.Text("Al-Ansâr n'est pas disponible dans cette version de l'application.", size=14),
                 ft.Text(f"Détail : {_ERREUR_IMPORT}", size=11, color="#6b7280")],
                alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        dic = DICTIONNAIRE_LANGUES.actif or {}
        lat, lon = _derniere_position()
        self._profondeur = 0
        self.module = HayaatiAlAnsar(
            expand=True,
            base_url=URL_DONNEES_AL_ANSAR,
            langue=str(dic.get("code_langue", "FR")).lower(),
            pays=PAYS_PAR_DEFAUT,
            latitude=lat,
            longitude=lon,
            mode_demo=MODE_DEMO_AL_ANSAR,
            ecran_initial=self.ECRAN_INITIAL,
            on_ouvrir_hote=self._ouvrir_ecran_hote,
            on_profondeur=self._maj_profondeur,
            on_sauver_progres=self._sauver_progres,
        )
        self.module.definir_textes(dic.get("al_ansar", {}))
        self.module.definir_raccourcis([])  # Madrassa est désormais dans le module lui-même
        self._preparer_madrassa(dic)
        return self.module

    def _preparer_madrassa(self, dic: dict):
        """Contenu pédagogique de la langue active et progression de l'utilisateur connecté."""
        sections = {cle: dic.get(cle, {}) for cle in SECTIONS_MADRASSA}
        if not any(sections.get(c) for c in ("encyclopedie", "langue_arabe", "sciences_islamiques")):
            return
        self.module.madrassa_json = json.dumps(sections, ensure_ascii=False)
        progres = {}
        if self._u_id:
            for cle in MODULES_PROGRES:
                try:
                    progres[cle] = self.app.sync_engine.charger_donnees_module(self._u_id, cle) or {}
                except Exception as exc:
                    print(f"[MADRASSA] Progression {cle} illisible : {exc}")
        self.module.progres_json = json.dumps(progres, ensure_ascii=False)
        self.module.visiteur = not bool(self._u_id)

    # --- Événements venus du module -----------------------------------------------
    def _ouvrir_ecran_hote(self, e):
        cle = str(getattr(e, "data", "") or "").strip()
        if cle:
            try:
                self.app.basculer_ecran(cle)
            except Exception as exc:
                print(f"[AL-ANSÂR] Ouverture de l'écran {cle} impossible : {exc}")

    def _maj_profondeur(self, e):
        try:
            self._profondeur = int(float(getattr(e, "data", 0) or 0))
        except (TypeError, ValueError):
            self._profondeur = 0

    def _sauver_progres(self, e):
        """Enregistre la progression d'un module (déjà normalisée par le module Dart)."""
        try:
            charge = json.loads(getattr(e, "data", "") or "{}")
            module, donnees = charge.get("module"), charge.get("donnees")
            if module not in MODULES_PROGRES or not isinstance(donnees, dict) or not self._u_id:
                return
            self.app.sync_engine.executer_sauvegarde_module(self._u_id, module, donnees)
        except Exception as exc:
            print(f"[MADRASSA] Enregistrement de la progression impossible : {exc}")

    # --- Bouton « retour » matériel -------------------------------------------------
    async def gerer_retour(self) -> bool:
        """Vrai si le module a consommé le retour (il revient d'un écran interne)."""
        if self.module is not None and self._profondeur > 0:
            try:
                await self.module.retour()
                return True
            except Exception as exc:
                print(f"[AL-ANSÂR] Retour interne impossible : {exc}")
        return False

    def actualiser_donnees_affichage(self):
        """Si l'utilisateur a changé (connexion, déconnexion), le module est recréé avec sa progression."""
        u_id = getattr(self.app, "user_id_connecte", None)
        if u_id != self._u_id and HayaatiAlAnsar is not None:
            self._u_id = u_id
            self.content = self._construire()
            try:
                self.update()
            except Exception:
                pass


class PageMadrassaNative(PageAlAnsar):
    """Écran « MADRASSA » : le module Flutter s'ouvre directement sur le hub Madrassa."""
    ECRAN_INITIAL = "madrassa"
