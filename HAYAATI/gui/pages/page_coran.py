"""
ÉCRAN DE LECTURE CORANIQUE (GUI/PAGES/PAGE_CORAN.PY)
Version 4.0 - 09/10/2026

Deux vues dans le même Container (reconstruction de l'arbre à chaque changement de vue via
construire_interface(), comme gui/pages/page_encyclopedie.py) :
  - "liste"   : les 114 sourates, « Reprendre la lecture », progression, signets, recherche.
  - "lecture" : une sourate, en deux modes au choix (mémorisé) :
        mode "page"  - FEUILLETAGE LATÉRAL comme un mushaf : un écran = une page de Médine (604),
                       glissement du doigt de gauche à droite pour avancer (sens de lecture arabe),
                       cadre ornemental, en-tête (juz, sourate), numéro de page en pied. Les pages
                       s'enchaînent d'une sourate à l'autre, exactement comme dans le livre.
        mode "liste" - prose continue défilant vers le bas (limitée à la sourate ouverte), blocs
                       chargés au fur et à mesure du défilement.

Performance (téléphone d'entrée de gamme) :
  - Mode page : le ft.PageView porte 604 conteneurs VIDES ; seules la page courante et ses deux
    voisines (±1) sont remplies, les autres sont vidées dès qu'on s'en éloigne. Un feuilletage ne
    construit donc qu'une page (~200 spans) au lieu de toute la sourate.
  - Mode liste : 4 pages au départ, 3 de plus quand le défilement approche de la fin.
  - Taille du texte (A- / A+) : la propriété size des textes DÉJÀ construits est modifiée sur place
    (aucun span n'est reconstruit). Les versions précédentes reconstruisaient toute la sourate.
  - Recherche de verset : mise à jour sur place (la saisie garde le focus).

Cadre ornemental : 100 % widgets Flet (deux bordures + quatre rosettes « ۞ » aux angles), aucune
image, aucun fichier : n'alourdit ni l'APK ni la mémoire.

Persistance : réglages, signets, dernière page et progression dans core/coran_lecture_store.py
(petit JSON local, indépendant des comptes). Une page compte comme « lue » après 8 s d'affichage.

Ordre des flèches - sens de lecture arabe : « avancer » est à GAUCHE, « reculer » à DROITE.

Texte arabe : voir assets/quran/LICENCE_SOURCE.md (Tanzil 1.1, copie verbatim). Polices : AmiriQuran
(texte coranique), NotoSansArabic (interface), enregistrées dans page.fonts (main.py).
"""
from __future__ import annotations
import asyncio
import time
import flet as ft

from gui.langues import DICTIONNAIRE_LANGUES
from gui.palette_hayaati import (
    VERT_PROFOND, VERT_CLAIR, OCRE, OCRE_CLAIR, SABLE, BLANC, GRIS_TEXTE, GRIS_CLAIR, TEXTE_FONCE, ROUGE_ERREUR,
)
from core.quran_engine import (
    charger_index_sourates, charger_sourate, juz_de_page, versets_de_page, page_de_verset,
    premiere_page_sourate, pages_de_sourate, sourate_de_page, preparer_texte_affichage,
    segments_verset, chiffres_arabes, marqueur_verset, NB_PAGES,
)
from core.quran_tajweed import couleur_famille
from core import coran_lecture_store as store
from core.hayaati_task_registry import HayaatiTaskRegistry

FONT_ARABE = "NotoSansArabic"      # interface (noms de sourates, titres)
FONT_CORAN = "AmiriQuran"          # texte coranique (police conçue pour le texte Tanzil, licence OFL)

CANAL_FILTRE_SOURATE = "coran.filtre_sourate_debounce"
CANAL_FILTRE_VERSET = "coran.filtre_verset_debounce"
DELAI_ANTI_REBOND_S = 0.35

TAILLES_TEXTE = store.TAILLES_VALIDES
HAUTEUR_LIGNE = 1.9      # interligne généreux : les signes au-dessus et au-dessous des lettres
                         # ne doivent pas se toucher d'une ligne à l'autre
DELAI_PAGE_LUE_S = 8.0   # une page est comptée comme lue après ce temps d'affichage
LISTE_BLOCS_INITIAUX = 4
LISTE_BLOCS_PAR_LOT = 3
LISTE_SEUIL_CHARGEMENT_PX = 900


class EcranCoran(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.page_flet = app_reference.page

        self.vue = "liste"          # "liste" | "lecture"
        self.sourate_active = None  # numéro (1-114) pendant la vue "lecture"
        self.page_active = None     # page de mushaf (1-604) affichée
        self.filtre_sourate = ""    # recherche par nom/numéro (vue liste)
        self.filtre_verset = ""     # recherche par numéro de verset (vue lecture)
        self.surligne = None        # (sourate, verset) surligné après une recherche
        self.confirmer_reinit = False

        # Réglages mémorisés
        self.mode = store.lire("mode")
        self.taille_texte = store.lire("taille")
        self.tajweed_actif = store.lire("tajweed")

        # Références des contrôles de la vue "lecture" (mises à jour sur place)
        self.champ_verset = None
        self.page_view = None
        self._contenants = []
        self._pages_remplies = set()
        self._textes = {}           # page -> [ft.Text] (pour changer la taille sans reconstruire)
        self._titre_num = None
        self._titre_nom = None
        self._btn_signet = None
        self._btn_sourate_suiv = None
        self._btn_sourate_prec = None
        self._btn_moins = None
        self._btn_plus = None
        self._info_page = None
        self._msg_recherche = None
        self._page_depuis = None    # (page, instant d'arrivée) pour le suivi de lecture
        self._liste_pages = []
        self._liste_prochain = 0
        self._liste_debut = 0
        self._liste_fin = False

        # contenu_racine (Column non défilante) : selon la vue, une ListView (liste de sourates),
        # ou en-tête + barre d'outils fixes + corps (PageView ou ListView).
        self.contenu_racine = ft.Column(spacing=0, expand=True)
        self.zone_contenu = ft.ListView(spacing=6, expand=True)
        self.construire_interface()

        super().__init__(content=self.contenu_racine, expand=True, bgcolor=BLANC, padding=ft.Padding(15, 15, 15, 15))

    def actualiser_contexte(self):
        """Alias pour le routeur central (OrganisateurLayout)."""
        self._rafraichir()

    # ------------------------------------------------------------------
    # OUTILS
    # ------------------------------------------------------------------
    def _txt(self) -> dict:
        return DICTIONNAIRE_LANGUES.actif.get("coran", {}) if hasattr(DICTIONNAIRE_LANGUES, "actif") else {}

    def _maj(self, *controles):
        """Mise à jour ciblée ; sans effet (et sans erreur) si le contrôle n'est pas encore sur la page."""
        for c in controles:
            if c is None:
                continue
            try:
                c.update()
            except Exception:
                pass

    def _message(self, texte: str):
        if not self.page_flet:
            return
        try:
            snack = ft.SnackBar(content=ft.Text(texte, size=13), bgcolor="#064e3b", duration=2500,
                                behavior=ft.SnackBarBehavior.FLOATING)
            self.page_flet.overlay.append(snack)
            snack.open = True
            self.page_flet.update()
        except Exception as exc:
            print(f"[CORAN] Message non affiché : {exc}")

    def _nom_sourate(self, numero) -> str:
        for entree in charger_index_sourates():
            if entree.get("numero") == numero:
                return entree.get("nom_arabe", "")
        return ""

    # ------------------------------------------------------------------
    # ORCHESTRATION
    # ------------------------------------------------------------------
    def construire_interface(self):
        self.contenu_racine.controls.clear()
        txt = self._txt()
        if self.vue == "lecture" and self.sourate_active is not None and self.page_active is not None:
            self._construire_vue_lecture(txt)
        else:
            self.vue = "liste"
            self._construire_vue_liste(txt)

    def _nouvelle_zone_defilante(self, **kwargs) -> ft.ListView:
        # ft.ListView plutôt que ft.Column : construit ses enfants à la demande.
        zone = ft.ListView(spacing=6, expand=True, **kwargs)
        self.zone_contenu = zone
        self.contenu_racine.controls.append(zone)
        return zone

    # ------------------------------------------------------------------
    # VUE 1 : LISTE DES 114 SOURATES (+ reprise, progression, signets)
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
        zone.controls.append(ft.Container(height=6))

        reprise = self._construire_carte_reprise(txt)
        if reprise is not None:
            zone.controls.append(reprise)
        zone.controls.append(self._construire_progression(txt))
        signets = self._construire_signets(txt)
        if signets:
            zone.controls.extend(signets)
        zone.controls.append(ft.Container(height=6))

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
        for entree in index_filtre:
            zone.controls.append(self._construire_ligne_sourate(entree, txt))

        zone.controls.append(ft.Container(height=10))
        zone.controls.append(
            ft.Text(txt.get("source_attribution", "Source : Tanzil.net"), size=9, color=GRIS_TEXTE,
                    text_align=ft.TextAlign.CENTER)
        )
        zone.controls.append(
            ft.Text(txt.get("source_tajweed", "Tajweed : annotations cpfair/quran-tajweed (CC BY 4.0)"),
                    size=9, color=GRIS_TEXTE, text_align=ft.TextAlign.CENTER)
        )

    def _construire_carte_reprise(self, txt):
        page = store.lire("derniere_page")
        if not page:
            return None
        sourate = sourate_de_page(page)
        if not sourate:
            return None
        titre = txt.get("reprendre_lecture", "Reprendre la lecture")
        detail = f"{self._nom_sourate(sourate)} · {txt.get('mot_page', 'Page')} {page}"
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.AUTO_STORIES_ROUNDED, color=VERT_PROFOND, size=22),
                ft.Column([
                    ft.Text(titre, size=13, weight=ft.FontWeight.BOLD, color=VERT_PROFOND),
                    ft.Text(detail, size=12, color=TEXTE_FONCE, font_family=FONT_ARABE),
                ], spacing=0, expand=True),
                ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, size=12, color=GRIS_TEXTE),
            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=OCRE_CLAIR, padding=ft.Padding(12, 10, 12, 10), border_radius=10,
            margin=ft.Margin(0, 0, 0, 6),
            on_click=lambda _, p=page, s=sourate: self._ouvrir_lecture(s, p),
            ink=True,
        )

    def _construire_progression(self, txt) -> ft.Control:
        lues, total = store.progression()
        modele = txt.get("progression_pages", "{n} / {total} pages lues")
        ligne = ft.Row([
            ft.Text(modele.replace("{n}", str(lues)).replace("{total}", str(total)), size=11, color=GRIS_TEXTE),
            ft.TextButton(
                content=ft.Text(
                    txt.get("confirmer_reinitialiser", "Confirmer la remise à zéro") if self.confirmer_reinit
                    else txt.get("reinitialiser_progression", "Remettre à zéro"),
                    size=11, color=ROUGE_ERREUR if self.confirmer_reinit else GRIS_TEXTE),
                on_click=self._reinitialiser_progression,
            ) if lues else ft.Container(),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        return ft.Column([
            ft.ProgressBar(value=(lues / total) if total else 0, color=VERT_PROFOND, bgcolor=GRIS_CLAIR, height=5),
            ligne,
        ], spacing=2)

    def _reinitialiser_progression(self, _e=None):
        """Deux temps : un premier appui demande confirmation, le second remet à zéro."""
        if not self.confirmer_reinit:
            self.confirmer_reinit = True
        else:
            store.reinitialiser_progression()
            self.confirmer_reinit = False
        self._rafraichir()

    def _construire_signets(self, txt) -> list:
        pages = store.signets()
        if not pages:
            return []
        lignes = [ft.Text(txt.get("signets_titre", "Signets"), size=12, weight=ft.FontWeight.BOLD, color=VERT_PROFOND)]
        for page in pages:
            sourate = sourate_de_page(page) or 0
            lignes.append(ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.BOOKMARK, color=OCRE, size=18),
                    ft.Text(f"{txt.get('mot_page', 'Page')} {page} · {self._nom_sourate(sourate)}",
                            size=12, color=TEXTE_FONCE, font_family=FONT_ARABE, expand=True),
                    ft.IconButton(icon=ft.Icons.DELETE_OUTLINE_ROUNDED, icon_size=18, icon_color=GRIS_TEXTE,
                                  width=32, height=32, padding=0,
                                  on_click=lambda _, p=page: self._retirer_signet_liste(p)),
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=SABLE, padding=ft.Padding(10, 2, 4, 2), border_radius=8, margin=ft.Margin(0, 0, 0, 3),
                on_click=lambda _, p=page, s=sourate: self._ouvrir_lecture(s, p),
                ink=True,
            ))
        return lignes

    def _retirer_signet_liste(self, page: int):
        store.basculer_signet(page)
        self._rafraichir()

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
        """Même anti-rebond que la recherche de verset ci-dessous."""
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
        """Le Coran est accessible directement depuis la barre d'outils (visiteur comme
        connecté) et depuis le hub Madrassa : on revient à l'écran d'où l'on vient réellement,
        et on ne retombe sur MADRASSA que si l'historique de navigation n'est pas disponible."""
        layout = getattr(self.app, "layout_central", None)
        if layout and hasattr(layout, "revenir_ecran_precedent"):
            if layout.revenir_ecran_precedent():
                return
        if layout:
            layout.basculer_vers_ecran("MADRASSA")

    # ------------------------------------------------------------------
    # OUVERTURE D'UNE SOURATE / D'UNE PAGE
    # ------------------------------------------------------------------
    def _ouvrir_sourate(self, numero: int):
        page = premiere_page_sourate(numero)
        if page:
            self._ouvrir_lecture(numero, page)

    def _ouvrir_lecture(self, sourate: int, page: int):
        HayaatiTaskRegistry.arreter(CANAL_FILTRE_VERSET)
        self._valider_page_lue()
        self.sourate_active = sourate
        self.page_active = page
        self.filtre_verset = ""
        self.surligne = None
        self.vue = "lecture"
        self._page_depuis = (page, time.monotonic())
        store.definir("derniere_page", page)
        self._rafraichir()

    # ------------------------------------------------------------------
    # SUIVI DE LECTURE
    # ------------------------------------------------------------------
    def _valider_page_lue(self):
        """Compte la page quittée comme lue si elle est restée affichée assez longtemps."""
        if self._page_depuis:
            page, depuis = self._page_depuis
            if time.monotonic() - depuis >= DELAI_PAGE_LUE_S:
                store.marquer_page_lue(page)
        self._page_depuis = None

    def _changer_page_active(self, page: int):
        """Point unique de changement de page (feuilletage, défilement, recherche) : suivi de
        lecture, mémorisation, titre et icône de signet."""
        if page == self.page_active:
            return
        self._valider_page_lue()
        self.page_active = page
        self._page_depuis = (page, time.monotonic())
        store.definir("derniere_page", page)

    # ------------------------------------------------------------------
    # VUE 2 : LECTURE
    # ------------------------------------------------------------------
    def _construire_vue_lecture(self, txt):
        self._textes = {}
        self.contenu_racine.controls.append(self._construire_entete_lecture(txt))
        self.contenu_racine.controls.append(self._construire_barre_outils(txt))
        self._msg_recherche = ft.Text("", size=11, italic=True, color=GRIS_TEXTE, visible=False,
                                      text_align=ft.TextAlign.CENTER)
        self.contenu_racine.controls.append(self._msg_recherche)
        if self.mode == "page":
            self._construire_corps_page(txt)
        else:
            self._construire_corps_liste(txt)

    # ----- En-tête et barre d'outils (fixes) -----------------------------------------------
    def _construire_entete_lecture(self, txt) -> ft.Container:
        sourate = self.sourate_active
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

        def _bouton(icone, tooltip, on_click, disabled=False, taille=20, couleur=VERT_PROFOND):
            return ft.IconButton(
                icon=icone, icon_color=couleur, icon_size=taille, tooltip=tooltip,
                width=36, height=36, padding=0, disabled=disabled, on_click=on_click,
            )

        btn_retour = _bouton(ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED, "↩️", self._retour_liste, taille=16)

        # ORDRE RTL : « suivante » (avancer dans le livre) à GAUCHE du titre, « précédente » à DROITE.
        self._btn_sourate_suiv = _bouton(
            ft.Icons.CHEVRON_LEFT_ROUNDED, txt.get("sourate_suivante", "Sourate suivante"),
            lambda _: self._ouvrir_sourate(self.sourate_active + 1), disabled=(sourate >= 114), taille=24,
        )
        self._btn_sourate_prec = _bouton(
            ft.Icons.CHEVRON_RIGHT_ROUNDED, txt.get("sourate_precedente", "Sourate précédente"),
            lambda _: self._ouvrir_sourate(self.sourate_active - 1), disabled=(sourate <= 1), taille=24,
        )

        self._titre_num = ft.Text(str(sourate), size=11, weight=ft.FontWeight.BOLD, color=VERT_PROFOND)
        self._titre_nom = ft.Text(self._nom_sourate(sourate), size=18, weight=ft.FontWeight.BOLD, color=VERT_PROFOND,
                                  font_family=FONT_ARABE, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
        titre = ft.Container(
            content=ft.Row([
                ft.Container(content=self._titre_num, width=26, height=26, bgcolor=OCRE_CLAIR, border_radius=13,
                             alignment=ft.Alignment.CENTER),
                self._titre_nom,
            ], spacing=6, alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True, alignment=ft.Alignment.CENTER,
        )

        self._btn_signet = _bouton(
            ft.Icons.BOOKMARK if store.est_signet(self.page_active) else ft.Icons.BOOKMARK_BORDER_ROUNDED,
            txt.get("signet_bascule", "Signet"), self._basculer_signet, couleur=OCRE,
        )

        return ft.Container(
            content=ft.Row(
                [btn_retour, self.champ_verset, self._btn_sourate_suiv, titre, self._btn_sourate_prec, self._btn_signet],
                spacing=2, vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=BLANC, padding=ft.Padding(0, 0, 0, 6),
        )

    def _construire_barre_outils(self, txt) -> ft.Container:
        interrupteur = ft.Switch(
            label=txt.get("tajweed", "Tajweed"), value=self.tajweed_actif,
            active_color=VERT_PROFOND, on_change=self._basculer_tajweed,
        )
        index_taille = TAILLES_TEXTE.index(self.taille_texte) if self.taille_texte in TAILLES_TEXTE else 0
        self._btn_moins = ft.IconButton(
            icon=ft.Icons.TEXT_DECREASE_ROUNDED, icon_color=VERT_PROFOND, icon_size=20,
            tooltip=txt.get("texte_plus_petit", "Texte plus petit"),
            width=36, height=36, padding=0, disabled=(index_taille <= 0),
            on_click=lambda _: self._changer_taille(-1),
        )
        self._btn_plus = ft.IconButton(
            icon=ft.Icons.TEXT_INCREASE_ROUNDED, icon_color=VERT_PROFOND, icon_size=20,
            tooltip=txt.get("texte_plus_grand", "Texte plus grand"),
            width=36, height=36, padding=0, disabled=(index_taille >= len(TAILLES_TEXTE) - 1),
            on_click=lambda _: self._changer_taille(+1),
        )

        def _mode(icone, mode, tooltip):
            actif = (self.mode == mode)
            return ft.IconButton(
                icon=icone, icon_size=20, width=36, height=36, padding=0, tooltip=tooltip,
                icon_color=BLANC if actif else VERT_PROFOND,
                bgcolor=VERT_PROFOND if actif else None,
                on_click=lambda _, m=mode: self._changer_mode(m),
            )

        bouton_page = _mode(ft.Icons.AUTO_STORIES_ROUNDED, "page", txt.get("mode_page", "Mode page"))
        bouton_liste = _mode(ft.Icons.VIEW_AGENDA_OUTLINED, "liste", txt.get("mode_liste", "Mode liste"))

        return ft.Container(
            content=ft.Row(
                [interrupteur, ft.Row([self._btn_moins, self._btn_plus, ft.Container(width=6), bouton_page, bouton_liste],
                                      spacing=0)],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding(0, 0, 0, 2),
            border=ft.Border(bottom=ft.BorderSide(1, GRIS_CLAIR)),
        )

    def _maj_entete(self):
        """Titre, flèches de sourate et signet, mis à jour sur place après un changement de page."""
        sourate = self.sourate_active
        if self._titre_num is not None:
            self._titre_num.value = str(sourate)
            self._titre_nom.value = self._nom_sourate(sourate)
            self._btn_sourate_suiv.disabled = sourate >= 114
            self._btn_sourate_prec.disabled = sourate <= 1
            self._btn_signet.icon = ft.Icons.BOOKMARK if store.est_signet(self.page_active) else ft.Icons.BOOKMARK_BORDER_ROUNDED
            self._maj(self._titre_num, self._titre_nom, self._btn_sourate_suiv, self._btn_sourate_prec, self._btn_signet)
        if self._info_page is not None:
            self._info_page.value = f"{chiffres_arabes(self.page_active)} / {chiffres_arabes(NB_PAGES)}  ·  Tanzil.net"
            self._maj(self._info_page)

    def _basculer_signet(self, _e=None):
        txt = self._txt()
        ajoute = store.basculer_signet(self.page_active)
        modele = txt.get("signet_ajoute", "Signet ajouté : page {page}") if ajoute else txt.get(
            "signet_retire", "Signet retiré : page {page}")
        self._maj_entete()
        self._message(modele.replace("{page}", str(self.page_active)))

    # ----- Réglages ---------------------------------------------------------------------------
    def _basculer_tajweed(self, e):
        self.tajweed_actif = bool(e.control.value)
        store.definir("tajweed", self.tajweed_actif)
        if self.mode == "page":
            self._reconstruire_fenetre_pages()
            self._maj(self.page_view)
        else:
            self._rafraichir()

    def _changer_taille(self, delta: int):
        """Change la taille SUR PLACE : on ne touche qu'à la propriété size des textes déjà construits."""
        index = TAILLES_TEXTE.index(self.taille_texte) if self.taille_texte in TAILLES_TEXTE else 0
        index = max(0, min(len(TAILLES_TEXTE) - 1, index + delta))
        self.taille_texte = TAILLES_TEXTE[index]
        store.definir("taille", self.taille_texte)
        for textes in self._textes.values():
            for t, rapport in textes:
                t.size = self.taille_texte * rapport
        self._btn_moins.disabled = index <= 0
        self._btn_plus.disabled = index >= len(TAILLES_TEXTE) - 1
        self._maj(self._btn_moins, self._btn_plus)
        self._maj(self.page_view if self.mode == "page" else self.zone_contenu)

    def _changer_mode(self, mode: str):
        if mode == self.mode:
            return
        self._valider_page_lue()
        self._page_depuis = (self.page_active, time.monotonic())
        self.mode = mode
        store.definir("mode", mode)
        self._rafraichir()

    # ----- Recherche de verset ---------------------------------------------------------------
    def _filtrer_verset(self, e):
        """Recherche d'un verset de la sourate affichée. Mise à jour SUR PLACE (la saisie garde le
        focus) avec anti-rebond ~350 ms via HayaatiTaskRegistry."""
        self.filtre_verset = e.control.value or ""
        if self.page_flet:
            HayaatiTaskRegistry.lancer(self.page_flet, CANAL_FILTRE_VERSET, self._filtrer_verset_differe)
        else:
            self._appliquer_recherche_verset()

    async def _filtrer_verset_differe(self, generation):
        await asyncio.sleep(DELAI_ANTI_REBOND_S)
        if HayaatiTaskRegistry.generation_active(CANAL_FILTRE_VERSET, generation):
            self._appliquer_recherche_verset()

    def _afficher_message_recherche(self, texte: str):
        if self._msg_recherche is not None:
            self._msg_recherche.value = texte
            self._msg_recherche.visible = bool(texte)
            self._maj(self._msg_recherche)

    def _appliquer_recherche_verset(self):
        txt = self._txt()
        requete = self.filtre_verset.strip()
        ancien = self.surligne
        if not requete:
            self.surligne = None
            self._afficher_message_recherche("")
            if ancien is not None:
                self._reconstruire_apres_recherche()
            return
        page = None
        if requete.isdigit():
            page = page_de_verset(self.sourate_active, int(requete))
        if page is None:
            self.surligne = None
            self._afficher_message_recherche(txt.get("aucun_verset", "Aucun verset ne correspond à ce numéro."))
            if ancien is not None:
                self._reconstruire_apres_recherche()
            return
        self.surligne = (self.sourate_active, int(requete))
        modele = txt.get("verset_trouve_page", "Verset {verset} - page {page} du mushaf")
        self._afficher_message_recherche(modele.replace("{verset}", requete).replace("{page}", str(page)))
        self._changer_page_active(page)
        self._reconstruire_apres_recherche(saut=True)

    def _reconstruire_apres_recherche(self, saut: bool = False):
        """Mode page : on saute à la page trouvée et on peut CONTINUER À FEUILLETER à partir d'elle.
        Mode liste : la lecture reprend à partir de la page trouvée."""
        if self.mode == "page":
            self._reconstruire_fenetre_pages()
            if saut and self.page_view is not None:
                self.page_view.selected_index = self.page_active - 1
            self._maj(self.page_view)
            self._maj_entete()
        else:
            self._reconstruire_corps_liste()

    # ------------------------------------------------------------------
    # CONSTRUCTION DU TEXTE D'UNE PAGE (commune aux deux modes)
    # ------------------------------------------------------------------
    def _spans_segments(self, texte: str, annotations, couleur_base, bgcolor) -> list:
        """Spans Flet d'un texte : tajweed (si actif) par segments de couleur, sinon un seul span."""
        texte = preparer_texte_affichage(texte)
        spans = []
        for segment, famille in segments_verset(texte, annotations, self.tajweed_actif):
            couleur = couleur_famille(famille) or couleur_base
            spans.append(ft.TextSpan(segment, style=ft.TextStyle(color=couleur, bgcolor=bgcolor)))
        return spans

    def _spans_versets(self, sourate: int, versets: list) -> list:
        spans = []
        for verset in versets:
            # Vert alterné (pairs plus foncés) quand le tajweed est éteint ; texte foncé uni quand il
            # est allumé, pour que les couleurs du tajweed ressortent.
            if self.tajweed_actif:
                couleur_base = TEXTE_FONCE
            else:
                couleur_base = VERT_PROFOND if verset["numero"] % 2 == 0 else VERT_CLAIR
            fond = OCRE_CLAIR if self.surligne == (sourate, verset["numero"]) else None
            spans.extend(self._spans_segments(verset["texte"], verset.get("tajweed"), couleur_base, fond))
            spans.append(ft.TextSpan(marqueur_verset(verset["numero"]), style=ft.TextStyle(color=OCRE, bgcolor=fond)))
        return spans

    def _texte_coranique(self, page: int, spans: list, alignement, rapport: float = 1.0) -> ft.Text:
        """Texte coranique ; (texte, rapport) est mémorisé pour changer la taille sans reconstruire."""
        t = ft.Text(
            spans=spans, size=self.taille_texte * rapport, font_family=FONT_CORAN,
            text_align=alignement, rtl=True, style=ft.TextStyle(height=HAUTEUR_LIGNE),
        )
        self._textes.setdefault(page, []).append((t, rapport))
        return t

    def _basmalah(self, page: int, bloc: dict) -> ft.Container:
        spans = self._spans_segments(bloc["basmalah"], bloc.get("basmalah_tajweed"), VERT_PROFOND, None)
        return ft.Container(
            content=self._texte_coranique(page, spans, ft.TextAlign.CENTER),
            padding=ft.Padding(0, 2, 0, 6), alignment=ft.Alignment.CENTER,
        )

    def _banniere_sourate(self, page: int, nom: str) -> ft.Container:
        titre = ft.Text(f"سورة {nom}", size=self.taille_texte * 0.9, font_family=FONT_CORAN,
                        color=VERT_PROFOND, weight=ft.FontWeight.BOLD)
        self._textes.setdefault(page, []).append((titre, 0.9))
        rosette = ft.Text("۞", size=16, color=OCRE, font_family=FONT_CORAN)
        return ft.Container(
            content=ft.Row([rosette, titre, ft.Text("۞", size=16, color=OCRE, font_family=FONT_CORAN)],
                           alignment=ft.MainAxisAlignment.CENTER, spacing=10,
                           vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=OCRE_CLAIR, border=ft.Border.all(1, OCRE), border_radius=6,
            padding=ft.Padding(6, 2, 6, 2), margin=ft.Margin(0, 4, 0, 6),
        )

    # ------------------------------------------------------------------
    # MODE PAGE : FEUILLETAGE LATÉRAL
    # ------------------------------------------------------------------
    def _construire_corps_page(self, txt):
        self._contenants = [ft.Container(expand=True) for _ in range(NB_PAGES)]
        self._pages_remplies = set()
        self._remplir_fenetre(self.page_active)
        # reverse=True : la page 1 est à DROITE, on avance en glissant le doigt de gauche à droite,
        # comme dans un livre arabe.
        self.page_view = ft.PageView(
            controls=self._contenants, selected_index=self.page_active - 1, reverse=True,
            expand=True, on_change=self._on_page_change,
        )
        self._info_page = ft.Text("", size=11, color=GRIS_TEXTE, text_align=ft.TextAlign.CENTER, expand=True)
        self._info_page.value = f"{chiffres_arabes(self.page_active)} / {chiffres_arabes(NB_PAGES)}  ·  Tanzil.net"

        def _fleche(icone, tooltip, gestionnaire):
            return ft.IconButton(icon=icone, icon_color=VERT_PROFOND, icon_size=26, tooltip=tooltip,
                                 width=44, height=36, padding=0, on_click=gestionnaire)

        # Sens de lecture arabe : « page suivante » à GAUCHE, « page précédente » à DROITE.
        barre = ft.Row([
            _fleche(ft.Icons.CHEVRON_LEFT_ROUNDED, txt.get("page_suivante", "Page suivante"), self._page_suivante),
            self._info_page,
            _fleche(ft.Icons.CHEVRON_RIGHT_ROUNDED, txt.get("page_precedente", "Page précédente"), self._page_precedente),
        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        self.contenu_racine.controls.append(self.page_view)
        self.contenu_racine.controls.append(barre)

    async def _page_suivante(self, _e=None):
        await self._aller_page(+1)

    async def _page_precedente(self, _e=None):
        await self._aller_page(-1)

    async def _aller_page(self, delta: int):
        cible = (self.page_active or 1) + delta
        if 1 <= cible <= NB_PAGES and self.page_view is not None:
            try:
                await self.page_view.go_to_page(cible - 1, animation_duration=250)
            except Exception as exc:
                print(f"[CORAN] Changement de page impossible : {exc}")

    def _on_page_change(self, e):
        """Le lecteur a feuilleté : on remplit la nouvelle page et ses voisines, on vide les autres."""
        try:
            index = int(e.data)
        except (TypeError, ValueError):
            index = getattr(e.control, "selected_index", None)
        if index is None or not (0 <= index < NB_PAGES):
            return
        page = index + 1
        if page == self.page_active:
            return
        self._changer_page_active(page)
        self.page_view.selected_index = index     # reste cohérent avec l'état côté Flutter
        self._remplir_fenetre(page)
        sourate = sourate_de_page(page)
        if sourate:
            self.sourate_active = sourate
        self._maj(self.page_view)
        self._maj_entete()

    def _remplir_fenetre(self, page: int):
        """Remplit la page, la précédente et la suivante ; vide les autres (mémoire et temps de
        mise à jour bornés quel que soit le nombre de pages feuilletées)."""
        voulues = {p for p in (page - 1, page, page + 1) if 1 <= p <= NB_PAGES}
        for p in self._pages_remplies - voulues:
            self._contenants[p - 1].content = None
            self._textes.pop(p, None)
        for p in voulues - self._pages_remplies:
            self._contenants[p - 1].content = self._construire_page_mushaf(p)
        self._pages_remplies = voulues

    def _reconstruire_fenetre_pages(self):
        """Reconstruit les pages visibles (tajweed, surlignage, saut à une page lointaine). Les pages
        précédemment remplies sont VIDÉES d'abord : après un saut, les anciennes ne doivent pas rester
        en mémoire."""
        for p in self._pages_remplies:
            self._contenants[p - 1].content = None
            self._textes.pop(p, None)
        self._pages_remplies = set()
        self._remplir_fenetre(self.page_active)

    def _rosette_angle(self, **position) -> ft.Container:
        return ft.Container(
            content=ft.Text("۞", size=15, color=OCRE, font_family=FONT_CORAN),
            width=24, height=24, bgcolor=BLANC, border=ft.Border.all(1.5, OCRE), border_radius=12,
            alignment=ft.Alignment.CENTER, **position,
        )

    def _construire_page_mushaf(self, page: int) -> ft.Control:
        txt = self._txt()
        blocs = versets_de_page(page)
        if not blocs:
            return ft.Container(
                content=ft.Text("⚠️ Texte de cette page indisponible.", size=12, color=ROUGE_ERREUR),
                alignment=ft.Alignment.CENTER, expand=True,
            )
        corps = []
        for bloc in blocs:
            if bloc["debut"]:
                corps.append(self._banniere_sourate(page, bloc["nom_arabe"]))
                if bloc["basmalah"]:
                    corps.append(self._basmalah(page, bloc))
            spans = self._spans_versets(bloc["sourate"], bloc["versets"])
            corps.append(self._texte_coranique(page, spans, ft.TextAlign.JUSTIFY))

        juz = juz_de_page(page)
        mot_juz = txt.get("mot_juz", "Juz")
        entete = ft.Row([
            ft.Text(f"{mot_juz} {chiffres_arabes(juz)}" if juz else "", size=11, color=GRIS_TEXTE, font_family=FONT_ARABE),
            ft.Text(blocs[0]["nom_arabe"], size=12, color=VERT_PROFOND, font_family=FONT_ARABE,
                    weight=ft.FontWeight.BOLD),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        pied = ft.Container(
            content=ft.Text(chiffres_arabes(page), size=12, color=VERT_PROFOND, font_family=FONT_CORAN,
                            weight=ft.FontWeight.BOLD),
            alignment=ft.Alignment.CENTER, padding=ft.Padding(0, 2, 0, 0),
        )

        # Cadre ornemental : double bordure (verte, puis ocre) et quatre rosettes aux angles.
        interieur = ft.Container(
            expand=True, border=ft.Border.all(1, OCRE), border_radius=6, padding=ft.Padding(10, 10, 10, 4),
            content=ft.Column([
                entete,
                ft.Divider(height=6, color=OCRE),
                ft.Container(expand=True, content=ft.Column(corps, scroll=ft.ScrollMode.AUTO, spacing=4)),
                pied,
            ], spacing=2, expand=True),
        )
        exterieur = ft.Container(
            expand=True, border=ft.Border.all(3, VERT_PROFOND), border_radius=10, padding=3, bgcolor=SABLE,
            content=interieur,
        )
        return ft.Container(
            expand=True, padding=ft.Padding(4, 8, 4, 4),
            content=ft.Stack([
                exterieur,
                self._rosette_angle(left=-2, top=-2), self._rosette_angle(right=-2, top=-2),
                self._rosette_angle(left=-2, bottom=-2), self._rosette_angle(right=-2, bottom=-2),
            ], expand=True, clip_behavior=ft.ClipBehavior.NONE),
        )

    # ------------------------------------------------------------------
    # MODE LISTE : DÉFILEMENT CONTINU, CHARGEMENT PAR LOTS
    # ------------------------------------------------------------------
    def _construire_corps_liste(self, txt):
        pages = pages_de_sourate(self.sourate_active)
        zone = self._nouvelle_zone_defilante(on_scroll=self._on_scroll_liste, scroll_interval=150)
        if not pages:
            zone.controls.append(ft.Text("⚠️ Texte de cette sourate indisponible.", size=12, color=ROUGE_ERREUR))
            return
        self._liste_pages = pages
        debut = pages.index(self.page_active) if self.page_active in pages else 0
        self._liste_debut = debut
        self._liste_prochain = debut
        self._liste_fin = False

        zone.controls.append(ft.Container(height=4))
        if debut > 0:
            zone.controls.append(ft.TextButton(
                content=ft.Text(txt.get("debut_sourate", "↑ Début de la sourate"), size=12, color=VERT_PROFOND),
                on_click=lambda _: self._ouvrir_lecture(self.sourate_active, pages[0]),
            ))
        else:
            donnees = charger_sourate(self.sourate_active)
            if donnees and donnees.get("basmalah"):
                zone.controls.append(self._basmalah(pages[0], {
                    "basmalah": donnees["basmalah"], "basmalah_tajweed": donnees.get("basmalah_tajweed")}))
        self._charger_blocs_liste(zone, LISTE_BLOCS_INITIAUX)

    def _reconstruire_corps_liste(self):
        """Mode liste : reconstruit la liste à partir de la page active (recherche de verset)."""
        self._textes = {}
        if self.zone_contenu in self.contenu_racine.controls:
            self.contenu_racine.controls.remove(self.zone_contenu)
        self._construire_corps_liste(self._txt())
        self._maj_entete()
        self._maj(self.contenu_racine)

    def _bloc_liste(self, page: int, txt) -> ft.Container:
        spans = []
        for bloc in versets_de_page(page):
            if bloc["sourate"] != self.sourate_active:
                continue          # une page peut contenir la fin d'une autre sourate : hors vue "liste"
            spans.extend(self._spans_versets(bloc["sourate"], bloc["versets"]))
        juz = juz_de_page(page)
        pied = f"{txt.get('mot_page', 'Page')} {chiffres_arabes(page)}"
        if juz:
            pied += f"  ·  {txt.get('mot_juz', 'Juz')} {chiffres_arabes(juz)}"
        return ft.Container(
            content=ft.Column([
                self._texte_coranique(page, spans, ft.TextAlign.JUSTIFY),
                ft.Text(pied, size=10, color=GRIS_TEXTE, text_align=ft.TextAlign.CENTER),
            ], spacing=6, horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
            padding=ft.Padding(8, 10, 8, 8),
            border=ft.Border(bottom=ft.BorderSide(1, GRIS_CLAIR)),
        )

    def _charger_blocs_liste(self, zone: ft.ListView, nombre: int):
        txt = self._txt()
        for _ in range(nombre):
            if self._liste_prochain >= len(self._liste_pages):
                break
            zone.controls.append(self._bloc_liste(self._liste_pages[self._liste_prochain], txt))
            self._liste_prochain += 1
        if self._liste_prochain >= len(self._liste_pages) and not self._liste_fin:
            self._liste_fin = True
            zone.controls.append(ft.Container(height=12))
            zone.controls.append(
                ft.Text(txt.get("source_attribution", "Source : Tanzil.net"), size=9, color=GRIS_TEXTE,
                        text_align=ft.TextAlign.CENTER))

    def _on_scroll_liste(self, e):
        """Charge les pages suivantes à l'approche de la fin et suit la page lue (estimation à partir
        de la position de défilement parmi les pages déjà chargées)."""
        if self._liste_prochain < len(self._liste_pages) and \
                (e.max_scroll_extent - e.pixels) < LISTE_SEUIL_CHARGEMENT_PX:
            self._charger_blocs_liste(self.zone_contenu, LISTE_BLOCS_PAR_LOT)
            self._maj(self.zone_contenu)
        chargees = self._liste_prochain - self._liste_debut
        if chargees > 0 and e.max_scroll_extent > 0:
            fraction = min(0.999, max(0.0, e.pixels / e.max_scroll_extent))
            page = self._liste_pages[self._liste_debut + int(fraction * chargees)]
            if page != self.page_active:
                self._changer_page_active(page)
                self._maj_entete()

    # ------------------------------------------------------------------
    def _retour_liste(self, _e=None):
        HayaatiTaskRegistry.arreter(CANAL_FILTRE_VERSET)
        self._valider_page_lue()
        self.sourate_active = None
        self.page_active = None
        self.surligne = None
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
        """Rafraîchissement lors d'un changement de langue (chrome uniquement - le texte arabe
        lui-même ne change pas)."""
        self._rafraichir()
