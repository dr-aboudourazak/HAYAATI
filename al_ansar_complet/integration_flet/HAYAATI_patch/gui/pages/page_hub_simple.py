"""
HUBS DE LA BARRE DE NAVIGATION À 5 BOUTONS (GUI/PAGES/PAGE_HUB_SIMPLE.PY)
  • PageCalculs   (visiteur)  : Zakat et Succession en mode simulation.
  • PageMonEspace (connecté)  : Mes Devoirs et Mon Inventaire.
Deux cartes chacune, dans la palette HAYAATI. Les écrans ciblés existent déjà.
"""
from __future__ import annotations

import flet as ft

from gui.langues import DICTIONNAIRE_LANGUES
from gui.palette_hayaati import BLANC, GRIS_TEXTE, SABLE, TEXTE_FONCE, VERT_PROFOND

BORDURE = "#e5e7eb"


class _PageHubSimple(ft.Container):
    TITRE_CLE = ""
    TITRE_DEFAUT = ""
    # (emoji, clé du menu, libellé par défaut, écran cible)
    CARTES: tuple = ()

    def __init__(self, app_reference):
        self.app = app_reference
        self.page_flet = app_reference.page
        self.zone = ft.Column(spacing=12, scroll=ft.ScrollMode.AUTO, expand=True,
                              horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
        super().__init__(content=self.zone, expand=True, bgcolor=SABLE,
                         padding=ft.Padding(left=15, right=15, top=15, bottom=15))
        self.actualiser_donnees_affichage()

    def _carte(self, emoji: str, titre: str, ecran: str) -> ft.Container:
        return ft.Container(
            content=ft.Row([
                ft.Text(emoji, size=28),
                ft.Text(titre, size=16, weight=ft.FontWeight.BOLD, color=TEXTE_FONCE, expand=True),
                ft.Text("➡️", size=14, color=GRIS_TEXTE),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=14),
            bgcolor=BLANC, padding=20, border_radius=12, border=ft.Border.all(1, BORDURE),
            on_click=lambda _, e=ecran: self.app.basculer_ecran(e),
        )

    def actualiser_donnees_affichage(self):
        menu = (DICTIONNAIRE_LANGUES.actif or {}).get("menu", {})
        titre = menu.get(self.TITRE_CLE, self.TITRE_DEFAUT)
        self.zone.controls = [ft.Text(titre, size=20, weight=ft.FontWeight.BOLD, color=VERT_PROFOND)]
        for emoji, cle, defaut, ecran in self.CARTES:
            libelle = menu.get(cle, defaut)
            # Le libellé du menu commence souvent par son emoji : on ne le répète pas.
            nu = libelle.split(" ", 1)[1] if " " in libelle and not libelle.split(" ", 1)[0].isalnum() else libelle
            self.zone.controls.append(self._carte(emoji, nu, ecran))
        try:
            self.update()
        except Exception:
            pass


class PageCalculs(_PageHubSimple):
    TITRE_CLE = "calculs_hub"
    TITRE_DEFAUT = "🧮 Calculs"
    CARTES = (
        ("🏦", "zakat", "🏦 Zakat", "ZAKAT_TIERS"),
        ("📜", "heritage", "📜 Succession", "HERITAGE_TIERS"),
    )


class PageMonEspace(_PageHubSimple):
    TITRE_CLE = "mon_espace_hub"
    TITRE_DEFAUT = "👤 Mon espace"
    CARTES = (
        ("⚖️", "devoirs_hub", "⚖️ Mes Devoirs", "DEVOIRS"),
        ("📦", "inventaire_hub", "📦 Mon Inventaire", "INVENTAIRE"),
    )
