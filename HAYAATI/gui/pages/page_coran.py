"""
ÉCRAN DE LECTURE CORANIQUE (GUI/PAGES/PAGE_CORAN.PY)
Version 2.1 — 27/09/2026

Deux vues dans le même Container, sur le même principe que
gui/pages/page_encyclopedie.py (reconstruction complète de l'arbre à
chaque changement de vue via construire_interface() + update(), jamais
de mutation de contrôles déjà affichés) :
  - "liste"  : les 114 sourates (numéro, nom arabe, translittération,
               type de révélation, nombre de versets), avec recherche.
  - "lecture": le texte complet d'une sourate, verset par verset, avec
               recherche de verset.

Structure de la vue "lecture" :
  contenu_racine (Column, non défilante)
    ├─ en-tête FIXE : retour · champ « verset » · suivante ·
    │                 numéro + titre · précédente
    └─ zone_contenu (ListView défilante) : Basmalah, versets, source.
  L'en-tête étant hors de la zone qui défile, on sait à tout instant
  quelle sourate on lit, et le champ de recherche reste toujours
  accessible.

Recherche de verset (v2.1, remplace le "saut" par scroll_to de la v2.0) :
même principe que la recherche de sourate de la vue "liste" — un
FILTRAGE de la base de données (ici : les versets de la sourate
ouverte, plutôt que les 114 sourates), avec reconstruction complète de
la vue affichée. Choisi plutôt que scroll_to() + cache_extent (v2.0) :
ft.ListView (nécessaire pour éviter le gel sur les longues sourates,
voir plus bas) ne construit que les lignes proches de la zone visible
— scroll_to(scroll_key=...) ne peut viser qu'une ligne déjà construite,
et une estimation de position en pixels n'était pas fiable (verset 55
tombait sur le 90, les versets variant trop en longueur pour une
hauteur moyenne). Filtrer, comme la recherche de sourate, évite le
problème à la racine : on ne cherche jamais à faire défiler vers une
ligne non construite, on reconstruit directement la vue avec la bonne
ligne dedans — exactement le mécanisme déjà fiable pour les sourates.

Ordre des flèches — sens de lecture arabe (de droite à gauche) : un livre
arabe s'ouvre de droite à gauche, donc « avancer » (sourate suivante)
est à GAUCHE du titre, et « reculer » (sourate précédente, vers le
début du livre) est à DROITE.

Texte arabe : voir assets/quran/LICENCE_SOURCE.md — source Tanzil.net,
copie verbatim (non modifiée), attribution affichée dans les deux vues.

Police : NotoSansArabic (déjà enregistrée dans page.fonts, main.py).
"""
from __future__ import annotations
import asyncio
import flet as ft

from gui.langues import DICTIONNAIRE_LANGUES
from gui.palette_hayaati import (
    VERT_PROFOND, VERT_CLAIR, OCRE, OCRE_CLAIR, SABLE, BLANC, GRIS_TEXTE, GRIS_CLAIR, TEXTE_FONCE, ROUGE_ERREUR,
)
from core.quran_engine import charger_index_sourates, charger_sourate, SIGNE_SAJDA
from core.hayaati_task_registry import HayaatiTaskRegistry

FONT_ARABE = "NotoSansArabic"

CANAL_FILTRE_SOURATE = "coran.filtre_sourate_debounce"
CANAL_FILTRE_VERSET = "coran.filtre_verset_debounce"
DELAI_ANTI_REBOND_S = 0.35


class EcranCoran(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.page_flet = app_reference.page

        self.vue = "liste"          # "liste" | "lecture"
        self.sourate_active = None  # numéro (1-114) pendant la vue "lecture"
        self.filtre_sourate = ""    # recherche par nom/numéro (vue liste)
        self.filtre_verset = ""     # recherche par numéro de verset (vue lecture)
        self.nb_versets_sourate_active = 0
        self.champ_verset = None

        # contenu_racine (Column non défilante) porte, selon la vue, soit
        # une seule ListView (liste), soit un en-tête fixe + une ListView
        # (lecture). zone_contenu désigne toujours la ListView défilante
        # de la vue courante.
        self.contenu_racine = ft.Column(spacing=0, expand=True)
        self.zone_contenu = ft.ListView(spacing=6, expand=True)
        self.construire_interface()

        super().__init__(content=self.contenu_racine, expand=True, bgcolor=BLANC, padding=ft.Padding(15, 15, 15, 15))

    def actualiser_contexte(self):
        """Alias pour le routeur central (OrganisateurLayout)."""
        self._rafraichir()

    # ------------------------------------------------------------------
    # ORCHESTRATION
    # ------------------------------------------------------------------
    def construire_interface(self):
        self.contenu_racine.controls.clear()
        txt = DICTIONNAIRE_LANGUES.actif.get("coran", {}) if hasattr(DICTIONNAIRE_LANGUES, "actif") else {}

        if self.vue == "lecture" and self.sourate_active is not None:
            self._construire_vue_lecture(txt, self.sourate_active)
        else:
            self.vue = "liste"
            self._construire_vue_liste(txt)

    def _nouvelle_zone_defilante(self) -> ft.ListView:
        # ft.ListView plutôt que ft.Column : construit ses enfants à la
        # demande (build_controls_on_demand=True par défaut) — une Column
        # construit TOUS ses enfants d'un coup, coûteux pour Al-Baqara
        # (286 versets en police arabe dédiée).
        zone = ft.ListView(spacing=6, expand=True)
        self.zone_contenu = zone
        self.contenu_racine.controls.append(zone)
        return zone

    # ------------------------------------------------------------------
    # VUE 1 : LISTE DES 114 SOURATES
    # ------------------------------------------------------------------
    def _construire_vue_liste(self, txt):
        zone = self._nouvelle_zone_defilante()

        btn_retour = ft.IconButton(
            icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED, icon_color=VERT_PROFOND, icon_size=16,
            tooltip="↩️", on_click=self._retour_ecran_precedent,
        )
        zone.controls.append(btn_retour)
        zone.controls.append(
            ft.Text(txt.get("titre", "📖 Le Coran"), size=20, weight=ft.FontWeight.BOLD, color=VERT_PROFOND)
        )
        zone.controls.append(
            ft.Text(txt.get("consigne", "Sélectionnez une sourate pour la lire."), size=11, italic=True, color=GRIS_TEXTE)
        )
        zone.controls.append(
            ft.Text(txt.get("source_attribution", "Source : Tanzil.net"), size=9, color=GRIS_TEXTE)
        )
        zone.controls.append(ft.Container(height=8))

        zone.controls.append(
            ft.TextField(
                value=self.filtre_sourate,
                hint_text=txt.get("filtre_placeholder", "🔎 Rechercher une sourate (nom ou numéro)"),
                dense=True, height=42, text_size=13, autofocus=bool(self.filtre_sourate),
                border_radius=8, border_color=OCRE,
                on_change=self._filtrer_sourate,
            )
        )
        zone.controls.append(ft.Container(height=6))

        index = charger_index_sourates()
        if not index:
            zone.controls.append(
                ft.Text("⚠️ Texte coranique indisponible (fichiers manquants).", size=12, color=ROUGE_ERREUR)
            )
            return

        index_filtre = self._appliquer_filtre_sourates(index)
        if not index_filtre:
            zone.controls.append(
                ft.Text(txt.get("aucun_resultat", "Aucune sourate ne correspond à cette recherche."),
                        size=12, italic=True, color=GRIS_TEXTE)
            )
            return

        for entree in index_filtre:
            zone.controls.append(self._construire_ligne_sourate(entree, txt))

    def _appliquer_filtre_sourates(self, index: list) -> list:
        requete = self.filtre_sourate.strip().lower()
        if not requete:
            return index
        resultats = []
        for entree in index:
            if requete == str(entree["numero"]):
                resultats.append(entree)
                continue
            champs = (entree.get("translitteration", ""), entree.get("nom_anglais", ""), entree.get("nom_arabe", ""))
            if any(requete in str(c).lower() for c in champs):
                resultats.append(entree)
        return resultats

    def _filtrer_sourate(self, e):
        """Même anti-rebond que la recherche de verset ci-dessous — voir
        son commentaire pour le détail du mécanisme."""
        self.filtre_sourate = e.control.value or ""
        if self.page_flet:
            HayaatiTaskRegistry.lancer(self.page_flet, CANAL_FILTRE_SOURATE, self._filtrer_sourate_differe)
        else:
            self._rafraichir()

    async def _filtrer_sourate_differe(self, generation):
        await asyncio.sleep(DELAI_ANTI_REBOND_S)
        if HayaatiTaskRegistry.generation_active(CANAL_FILTRE_SOURATE, generation):
            self._rafraichir()

    def _construire_ligne_sourate(self, entree: dict, txt: dict) -> ft.Container:
        numero = entree["numero"]
        mot_versets = txt.get("mot_versets", "versets")
        cle_revelation = "revelation_meccane" if entree.get("revelation") == "meccane" else "revelation_medinoise"
        revelation_affichee = txt.get(cle_revelation, "Meccane" if cle_revelation.endswith("meccane") else "Médinoise")
        sous_titre = f"{entree.get('translitteration', '')} · {revelation_affichee} · {entree.get('nb_versets', '?')} {mot_versets}"
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text(str(numero), size=12, weight=ft.FontWeight.BOLD, color=VERT_PROFOND),
                    width=32, height=32, bgcolor=OCRE_CLAIR, border_radius=16, alignment=ft.Alignment.CENTER,
                ),
                ft.Column([
                    ft.Text(entree.get("nom_arabe", ""), size=16, font_family=FONT_ARABE, color=TEXTE_FONCE,
                            text_align=ft.TextAlign.RIGHT),
                    ft.Text(sous_titre, size=10, color=GRIS_TEXTE),
                ], spacing=0, expand=True),
                ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, size=12, color=GRIS_TEXTE),
            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=SABLE, padding=ft.Padding(10, 8, 10, 8), border_radius=8, margin=ft.Margin(0, 0, 0, 4),
            on_click=lambda _, n=numero: self._ouvrir_sourate(n),
            ink=True,
        )

    def _retour_ecran_precedent(self, _e=None):
        """Le Coran est accessible directement depuis la barre d'outils
        (visiteur comme connecté) et depuis le hub Madrassa : on revient à
        l'écran d'où l'on vient réellement, et on ne retombe sur MADRASSA
        que si l'historique de navigation n'est pas disponible."""
        layout = getattr(self.app, "layout_central", None)
        if layout and hasattr(layout, "revenir_ecran_precedent"):
            if layout.revenir_ecran_precedent():
                return
        if layout:
            layout.basculer_vers_ecran("MADRASSA")

    def _ouvrir_sourate(self, numero: int):
        HayaatiTaskRegistry.arreter(CANAL_FILTRE_VERSET)
        self.sourate_active = numero
        self.vue = "lecture"
        self.filtre_verset = ""
        self._rafraichir()

    # ------------------------------------------------------------------
    # VUE 2 : LECTURE D'UNE SOURATE
    # ------------------------------------------------------------------
    def _construire_vue_lecture(self, txt, numero: int):
        donnees = charger_sourate(numero)
        versets = donnees.get("versets", []) if donnees else []
        self.nb_versets_sourate_active = len(versets)

        # En-tête FIXE (hors de la zone qui défile), puis la zone défilante.
        self.contenu_racine.controls.append(self._construire_entete_lecture(txt, numero, donnees))
        zone = self._nouvelle_zone_defilante()

        if not donnees:
            zone.controls.append(
                ft.Text("⚠️ Texte de cette sourate indisponible.", size=12, color=ROUGE_ERREUR)
            )
            return

        versets_filtres = self._appliquer_filtre_versets(versets)
        filtre_actif = bool(self.filtre_verset.strip())

        zone.controls.append(ft.Container(height=6))
        # La Basmalah n'a pas de numéro de verset propre — l'afficher
        # pendant une recherche filtrée n'aurait pas de sens (elle ne
        # correspond à aucun numéro tapé) : seulement quand rien n'est
        # filtré, comme avant.
        if not filtre_actif and donnees.get("basmalah"):
            zone.controls.append(
                ft.Text(donnees["basmalah"], size=17, font_family=FONT_ARABE, color=VERT_PROFOND,
                        text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.BOLD)
            )
            zone.controls.append(ft.Container(height=6))

        if filtre_actif and not versets_filtres:
            zone.controls.append(
                ft.Text(txt.get("aucun_verset", "Aucun verset ne correspond à ce numéro."),
                        size=12, italic=True, color=GRIS_TEXTE)
            )
        else:
            for verset in versets_filtres:
                zone.controls.append(self._construire_ligne_verset(verset))

        zone.controls.append(ft.Container(height=12))
        zone.controls.append(
            ft.Text(txt.get("source_attribution", "Source : Tanzil.net"), size=9, color=GRIS_TEXTE,
                    text_align=ft.TextAlign.CENTER)
        )

    def _appliquer_filtre_versets(self, versets: list) -> list:
        """Même principe que _appliquer_filtre_sourates, appliqué aux
        versets de la sourate ouverte plutôt qu'aux 114 sourates —
        correspondance exacte sur le numéro (un numéro de verset n'a pas
        d'équivalent textuel à chercher, contrairement au nom d'une
        sourate)."""
        requete = self.filtre_verset.strip()
        if not requete:
            return versets
        if not requete.isdigit():
            return []
        numero_cherche = int(requete)
        return [v for v in versets if v["numero"] == numero_cherche]

    def _construire_entete_lecture(self, txt, numero: int, donnees) -> ft.Container:
        nom_arabe = donnees.get("nom_arabe", "") if donnees else "?"

        self.champ_verset = ft.TextField(
            value=self.filtre_verset,
            hint_text=txt.get("verset_court", "Verset"),
            tooltip=txt.get("aller_au_verset", "Rechercher un verset par numéro"),
            dense=True, height=36, width=88, text_size=12, text_align=ft.TextAlign.CENTER,
            content_padding=ft.Padding(4, 0, 4, 0),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=8, border_color=OCRE,
            on_change=self._filtrer_verset,
        )

        def _bouton(icone, tooltip, on_click, disabled=False, taille=20):
            return ft.IconButton(
                icon=icone, icon_color=VERT_PROFOND, icon_size=taille, tooltip=tooltip,
                width=36, height=36, padding=0, disabled=disabled, on_click=on_click,
            )

        btn_retour = _bouton(ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED, "↩️", self._retour_liste, taille=16)

        # ⬅ ORDRE RTL : « suivante » (avancer dans le livre) à GAUCHE du
        # titre, « précédente » (vers le début du livre) à DROITE — sens
        # de progression d'un livre arabe, qui s'ouvre de droite à gauche.
        btn_suivante = _bouton(
            ft.Icons.CHEVRON_LEFT_ROUNDED, txt.get("sourate_suivante", "Sourate suivante"),
            lambda _: self._ouvrir_sourate(numero + 1), disabled=(numero >= 114), taille=24,
        )
        btn_precedente = _bouton(
            ft.Icons.CHEVRON_RIGHT_ROUNDED, txt.get("sourate_precedente", "Sourate précédente"),
            lambda _: self._ouvrir_sourate(numero - 1), disabled=(numero <= 1), taille=24,
        )

        titre = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text(str(numero), size=11, weight=ft.FontWeight.BOLD, color=VERT_PROFOND),
                    width=26, height=26, bgcolor=OCRE_CLAIR, border_radius=13, alignment=ft.Alignment.CENTER,
                ),
                ft.Text(nom_arabe, size=18, weight=ft.FontWeight.BOLD, color=VERT_PROFOND,
                        font_family=FONT_ARABE, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
            ], spacing=6, alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True, alignment=ft.Alignment.CENTER,
        )

        return ft.Container(
            content=ft.Row(
                [btn_retour, self.champ_verset, btn_suivante, titre, btn_precedente],
                spacing=2, vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=BLANC, padding=ft.Padding(0, 0, 0, 6),
            border=ft.Border(bottom=ft.BorderSide(1, GRIS_CLAIR)),
        )

    def _construire_ligne_verset(self, verset: dict) -> ft.Container:
        # 🆕 29/09/2026 : couleur verte alternée, pairs plus foncés que
        # impairs — contraste visuel entre versets consécutifs, pour
        # mieux suivre sa lecture sur un long texte ininterrompu.
        couleur_texte = VERT_PROFOND if verset["numero"] % 2 == 0 else VERT_CLAIR

        # Signe de prosternation (۩) — séparé du texte du verset lui-même
        # (pas dans le même Text sélectionnable) : c'est une annotation
        # éditoriale, pas une partie du texte coranique verbatim.
        #
        # 🆕 29/09/2026 (correction) : apparaissait au DÉBUT du verset au
        # lieu de la fin. Cause : ft.Row est LTR par défaut — son second
        # enfant (le signe) se retrouvait donc physiquement à DROITE,
        # côté où la lecture arabe COMMENCE (elle se lit de droite à
        # gauche), pas à la fin. `rtl=True` sur cette Row fait que ses
        # enfants sont disposés en respectant l'ordre de lecture arabe :
        # le texte d'abord (à droite), le signe ensuite (vers la gauche,
        # là où le verset se termine réellement) — et `alignment=START`
        # (pas END) pour que le bloc reste bien collé à droite, le sens
        # de "début" en RTL.
        elements_texte = [
            ft.Text(
                verset["texte"], size=18, font_family=FONT_ARABE, color=couleur_texte,
                text_align=ft.TextAlign.RIGHT, selectable=True,
            ),
        ]
        if verset.get("sajda"):
            elements_texte.append(
                ft.Text(SIGNE_SAJDA, size=20, font_family=FONT_ARABE, color=OCRE, weight=ft.FontWeight.BOLD,
                        tooltip="۩ Verset de prosternation (sajdah)")
            )
        return ft.Container(
            key=f"verset_{verset['numero']}",
            content=ft.Row([
                ft.Container(
                    content=ft.Text(str(verset["numero"]), size=10, color=GRIS_TEXTE),
                    width=24, height=24, bgcolor=GRIS_CLAIR, border_radius=12, alignment=ft.Alignment.CENTER,
                ),
                ft.Row(elements_texte, rtl=True, wrap=True, alignment=ft.MainAxisAlignment.START,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=6, expand=True),
            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.START),
            padding=ft.Padding(4, 8, 4, 8),
            border=ft.Border(bottom=ft.BorderSide(1, GRIS_CLAIR)),
        )

    def _filtrer_verset(self, e):
        """🆕 27/09/2026 : remplace le « saut » scroll_to()/cache_extent
        de la v2.0 (peu fiable : ListView ne construit que les lignes
        proches de la zone visible, et une estimation de position en
        pixels ne tombait pas toujours juste — « 55 tombait sur le 90 »).
        Même mécanisme, déjà fiable, que la recherche de sourate : on
        FILTRE la base (ici les versets de la sourate ouverte) et on
        reconstruit — jamais de scroll vers une ligne non construite.
        Anti-rebond ~350ms comme la recherche de sourate, via
        HayaatiTaskRegistry."""
        self.filtre_verset = e.control.value or ""
        if self.page_flet:
            HayaatiTaskRegistry.lancer(self.page_flet, CANAL_FILTRE_VERSET, self._filtrer_verset_differe)
        else:
            self._rafraichir()

    async def _filtrer_verset_differe(self, generation):
        await asyncio.sleep(DELAI_ANTI_REBOND_S)
        if HayaatiTaskRegistry.generation_active(CANAL_FILTRE_VERSET, generation):
            self._rafraichir()

    # ------------------------------------------------------------------
    def _retour_liste(self, _e=None):
        HayaatiTaskRegistry.arreter(CANAL_FILTRE_VERSET)
        self.sourate_active = None
        self.vue = "liste"
        self._rafraichir()

    def _rafraichir(self):
        self.construire_interface()
        if self.page_flet:
            try:
                self.update()
            except Exception:
                pass

    def _action_langue(self, *_args):
        """Rafraîchissement lors d'un changement de langue (chrome
        français/anglais/etc. — le texte arabe lui-même ne change pas)."""
        self._rafraichir()
