"""
SÉLECTEUR AVEC SUGGESTIONS PENDANT LA SAISIE (GUI/COMPONENTS/SELECTEUR_RECHERCHE.PY) - 15/10/2026

Champ de saisie + liste de suggestions filtrée à chaque frappe, pour choisir parmi une très longue liste
(les ~250 pays du monde, ~150 devises) sans la dérouler. Utilisé par la page Profil (pays) et la page
Réglages (devise).

Le sélecteur est un contrôle Flet (ft.Column) qui garde l'interface d'un menu déroulant :
  .value            code choisi (ex. "TG"), ou None tant que rien de valide n'est sélectionné
  .definir(code)    choisit un code par programme
  .actualiser_langue()  réécrit le libellé affiché (changement de langue de l'application)

Les listes viennent de fonctions fournies par l'appelant :
  rechercher(requete) -> [codes]   libelle_de(code) -> texte affiché   exact(texte) -> code | None

Les suggestions ne sont masquées qu'avec un court délai à la perte du focus : sur téléphone, toucher une
suggestion fait d'abord perdre le focus au champ, et masquer tout de suite ferait perdre le toucher.
"""
from __future__ import annotations
import asyncio
import flet as ft

COULEUR_BORDURE = "#064e3b"
DELAI_MASQUAGE_S = 0.4


class SelecteurRecherche(ft.Column):
    def __init__(self, rechercher, libelle_de, exact=None, hint="", on_select=None, rtl=False,
                 max_suggestions=8, hauteur=44):
        self._rechercher = rechercher
        self._libelle_de = libelle_de
        self._exact = exact
        self._on_select = on_select
        self._max = max_suggestions
        self._code = None
        self._derniere_suggestions = []

        self.champ = ft.TextField(
            hint_text=hint, dense=True, height=hauteur, text_size=13, border_radius=8,
            border_color=COULEUR_BORDURE, content_padding=ft.Padding(10, 6, 10, 6), rtl=rtl,
            on_change=self._saisie, on_blur=self._fin_saisie, on_submit=self._valider,
        )
        self.liste = ft.Column(spacing=0, visible=False)
        self._cadre = ft.Container(
            content=self.liste, visible=False, bgcolor=ft.Colors.WHITE, border_radius=8,
            border=ft.Border.all(1, COULEUR_BORDURE), margin=ft.Margin(0, 0, 0, 4),
        )
        super().__init__([self.champ, self._cadre], spacing=2, tight=True)

    # --------------------------------------------------------------- interface « menu déroulant »
    @property
    def value(self):
        return self._code

    @value.setter
    def value(self, code):
        self.definir(code)

    def definir(self, code, notifier: bool = False):
        self._code = code or None
        self.champ.value = self._libelle_de(code) if code else ""
        self._masquer()
        self._maj(self.champ, self._cadre)
        if notifier and code and self._on_select:
            self._on_select(code)

    def definir_texte_libre(self, texte: str):
        """Ancien texte saisi à la main : reconnu s'il correspond à un élément, sinon simplement affiché."""
        code = self._exact(texte) if (self._exact and texte) else None
        if code:
            self.definir(code)
        else:
            self._code = None
            self.champ.value = str(texte or "")
            self._masquer()

    def actualiser_langue(self, hint=None, rtl=None):
        if hint is not None:
            self.champ.hint_text = hint
        if rtl is not None:
            self.champ.rtl = rtl
        if self._code:
            self.champ.value = self._libelle_de(self._code)
        self._masquer()
        self._maj(self.champ, self._cadre)

    # --------------------------------------------------------------- saisie
    def _maj(self, *controles):
        for c in controles:
            try:
                c.update()
            except Exception:
                pass

    def _masquer(self):
        self.liste.controls.clear()
        self.liste.visible = False
        self._cadre.visible = False

    def _saisie(self, e):
        texte = (self.champ.value or "").strip()
        if self._code and texte != self._libelle_de(self._code):
            self._code = None                      # le texte a été modifié : l'ancien choix n'est plus valable
        if not texte:
            self._masquer()
            self._maj(self._cadre)
            return
        self._afficher(self._rechercher(texte)[: self._max])

    def _afficher(self, codes):
        self._derniere_suggestions = list(codes)
        self.liste.controls.clear()
        for code in codes:
            self.liste.controls.append(ft.Container(
                content=ft.Text(self._libelle_de(code), size=13, color="#1f2937"),
                padding=ft.Padding(12, 9, 12, 9), ink=True,
                on_click=lambda _, c=code: self._choisir(c),
            ))
        visible = bool(codes)
        self.liste.visible = visible
        self._cadre.visible = visible
        self._maj(self._cadre)

    def _choisir(self, code):
        self.definir(code, notifier=True)

    def _valider(self, e):
        """Validation au clavier : un nom exact est pris ; sinon la première suggestion."""
        texte = (self.champ.value or "").strip()
        code = self._exact(texte) if (self._exact and texte) else None
        if not code and self._derniere_suggestions:
            code = self._derniere_suggestions[0]
        if code:
            self._choisir(code)

    async def _fin_saisie(self, e):
        await asyncio.sleep(DELAI_MASQUAGE_S)
        texte = (self.champ.value or "").strip()
        if self._code is None and texte and self._exact:
            code = self._exact(texte)
            if code:
                self._choisir(code)
                return
        if self._code is not None:
            self.champ.value = self._libelle_de(self._code)    # remet le libellé propre
            self._maj(self.champ)
        self._masquer()
        self._maj(self._cadre)
