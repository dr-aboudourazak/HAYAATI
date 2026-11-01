"""
ÉCRAN LE CORAN, VERSION NATIVE (GUI/PAGES/PAGE_CORAN_NATIVE.PY) - lot A, 31/10/2026

Héberge le module Flutter « hayaati_coran » (extension hayaati-alnsar, contrôle HayaatiCoran) à la place de
gui/pages/page_coran.py. Ce que fait cette page, et rien de plus :
  • transmettre au module la langue, les textes traduits (section « coran » des fichiers de langue) et l'état de
    lecture enregistré (core/coran_lecture_store.py : réglages, signets, progression) ;
  • enregistrer l'état que le module signale, SANS changer le format du fichier coran_lecture.json : les signets et
    la progression déjà faits par l'utilisateur sont retrouvés tels quels ;
  • rendre le bouton « retour » d'Android cohérent avec la navigation interne du module.
Le texte du Coran (assets/quran/) est embarqué dans le paquet Flutter : il ne passe pas par Flet.

Retour à l'ancien écran Python : mettre CORAN_NATIF = False dans gui/app_layout.py.
"""
from __future__ import annotations

import json

import flet as ft

from gui.langues import DICTIONNAIRE_LANGUES
from core import coran_lecture_store as store

try:
    from hayaati_alnsar import HayaatiCoran
except Exception as _exc:  # extension absente ou trop ancienne : message clair au lieu d'un plantage
    HayaatiCoran = None
    _ERREUR_IMPORT = _exc
else:
    _ERREUR_IMPORT = None


def _code_langue() -> str:
    dic = DICTIONNAIRE_LANGUES.actif or {}
    return str(dic.get("code_langue", "FR")).lower()


class PageCoranNative(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.page_flet = app_reference.page
        self._profondeur = 0
        self._langue = _code_langue()
        self.module = None
        super().__init__(content=self._construire(), expand=True, bgcolor=ft.Colors.WHITE, padding=0)

    # --- Construction -----------------------------------------------------------
    def _construire(self):
        if HayaatiCoran is None:
            return ft.Column(
                [ft.Text("Le Coran natif n'est pas disponible dans cette version de l'application.", size=14),
                 ft.Text(f"Détail : {_ERREUR_IMPORT}", size=11, color="#6b7280")],
                alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        dic = DICTIONNAIRE_LANGUES.actif or {}
        self._langue = _code_langue()
        self._profondeur = 0
        self.module = HayaatiCoran(
            expand=True,
            langue=self._langue,
            on_sauver_etat=self._sauver_etat,
            on_profondeur=self._maj_profondeur,
        )
        self.module.definir_textes(dic.get("coran", {}))
        self.module.definir_etat(store.charger())
        return self.module

    # --- Événements venus du module -----------------------------------------------
    def _maj_profondeur(self, e):
        try:
            self._profondeur = int(float(getattr(e, "data", 0) or 0))
        except (TypeError, ValueError):
            self._profondeur = 0

    def _sauver_etat(self, e):
        """Enregistre l'état de lecture envoyé par le module (nettoyé par le magasin avant écriture)."""
        try:
            brut = json.loads(getattr(e, "data", "") or "{}")
            if isinstance(brut, dict):
                store.remplacer_etat(brut)
        except Exception as exc:
            print(f"[CORAN-NATIF] Enregistrement de l'état de lecture impossible : {exc}")

    # --- Bouton « retour » matériel -------------------------------------------------
    async def gerer_retour(self) -> bool:
        """Vrai si le module a consommé le retour (il revient d'un écran interne)."""
        if self.module is not None and self._profondeur > 0:
            try:
                await self.module.retour()
                return True
            except Exception as exc:
                print(f"[CORAN-NATIF] Retour interne impossible : {exc}")
        return False

    # --- Appels du routeur central ----------------------------------------------------
    def actualiser_donnees_affichage(self):
        """Appelé après chaque arrivée sur l'écran : si la langue a changé, le module est recréé avec les
        nouveaux textes (l'état de lecture est relu du fichier, rien n'est perdu)."""
        if HayaatiCoran is not None and _code_langue() != self._langue:
            self.content = self._construire()
            try:
                self.update()
            except Exception:
                pass

    def actualiser_contexte(self):
        self.actualiser_donnees_affichage()
