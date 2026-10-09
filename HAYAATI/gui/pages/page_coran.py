"""
ÉCRAN DE LECTURE CORANIQUE (GUI/PAGES/PAGE_CORAN.PY)
Version 3.0 - 08/10/2026

Deux vues dans le même Container (reconstruction complète de l'arbre à chaque changement
de vue via construire_interface() + update(), comme gui/pages/page_encyclopedie.py) :
  - "liste"  : les 114 sourates, avec recherche.
  - "lecture": le texte d'une sourate EN PROSE CONTINUE, comme un mushaf imprimé.

v3.0 - lecture en prose :
  - Les versets se suivent à la file dans un texte justifié de droite à gauche, séparés par
    leur numéro entre parenthèses ornées (plus de ligne par verset, donc plus de signe de
    prosternation isolé sur une ligne).
  - Le texte est découpé PAR PAGE DE MUSHAF (604 pages de Médine) : un bloc par page, numéro
    de page et de juz en pied. Un ft.ListView ne construit que les blocs proches de la zone
    visible (Al-Baqara : 48 pages au lieu de 286 versets).
  - Anti-orphelins, à l'affichage seulement : l'espace avant un signe de pause ou du signe de
    prosternation, et après le signe de hizb, devient insécable
    (core.quran_engine.preparer_texte_affichage). Le texte stocké reste verbatim.
  - Tajweed optionnel (interrupteur) : 5 familles de couleurs + légende, annotations
    automatiques (cpfair/quran-tajweed, CC BY 4.0) présentées comme une aide à la lecture.
  - Taille du texte réglable (A- / A+).
  - Recherche de verset : affiche la PAGE de mushaf qui contient le verset, avec le verset
    surligné (même principe de filtrage que la recherche de sourate : on reconstruit la vue,
    on ne fait jamais défiler vers une ligne non construite).

Structure de la vue "lecture" :
  contenu_racine (Column, non défilante)
    - en-tête FIXE : retour, champ « verset », suivante, numéro + titre, précédente
    - barre d'outils FIXE : tajweed, taille du texte
    - zone_contenu (ListView défilante) : légende, basmala, pages, source.

Ordre des flèches - sens de lecture arabe (de droite à gauche) : « avancer » (sourate
suivante) est à GAUCHE du titre, « reculer » (sourate précédente) à DROITE.

Texte arabe : voir assets/quran/LICENCE_SOURCE.md - source Tanzil.net (version 1.1), copie
verbatim, attribution affichée dans les deux vues.

Polices : AmiriQuran pour le texte coranique, NotoSansArabic pour l'interface (toutes deux
enregistrées dans page.fonts, main.py).
"""
from __future__ import annotations
import asyncio
import flet as ft

from gui.langues import DICTIONNAIRE_LANGUES
from gui.palette_hayaati import (
    VERT_PROFOND, VERT_CLAIR, OCRE, OCRE_CLAIR, SABLE, BLANC, GRIS_TEXTE, GRIS_CLAIR, TEXTE_FONCE, ROUGE_ERREUR,
)
from core.quran_engine import (
    charger_index_sourates, charger_sourate, regrouper_par_page, juz_de_page,
    preparer_texte_affichage, segments_verset, chiffres_arabes, marqueur_verset,
)
from core.quran_tajweed import FAMILLES, couleur_famille
from core.hayaati_task_registry import HayaatiTaskRegistry

FONT_ARABE = "NotoSansArabic"      # interface (noms de sourates, titres)
FONT_CORAN = "AmiriQuran"          # texte coranique (police conçue pour le texte Tanzil, licence OFL)

CANAL_FILTRE_SOURATE = "coran.filtre_sourate_debounce"
CANAL_FILTRE_VERSET = "coran.filtre_verset_debounce"
DELAI_ANTI_REBOND_S = 0.35

TAILLES_TEXTE = (18, 20, 22, 24, 28, 32)
TAILLE_TEXTE_DEFAUT = 24
HAUTEUR_LIGNE = 2.0     # interligne généreux : les signes au-dessus et au-dessous des lettres
                        # ne doivent pas se toucher d'une ligne à l'autre


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
        self.tajweed_actif = False
        self.taille_texte = TAILLE_TEXTE_DEFAUT

        # contenu_racine (Column non défilante) porte, selon la vue, soit une seule ListView
        # (liste), soit en-tête + barre d'outils fixes + une ListView (lecture). zone_contenu
        # désigne toujours la ListView défilante de la vue courante.
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
        # ft.ListView plutôt que ft.Column : construit ses enfants à la demande — une Column
        # construit TOUS ses enfants d'un coup, coûteux pour Al-Baqara.
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

    def _ouvrir_sourate(self, numero: int):
        HayaatiTaskRegistry.arreter(CANAL_FILTRE_VERSET)
        self.sourate_active = numero
        self.vue = "lecture"
        self.filtre_verset = ""
        self._rafraichir()

    # ------------------------------------------------------------------
    # VUE 2 : LECTURE D'UNE SOURATE (PROSE PAR PAGE DE MUSHAF)
    # ------------------------------------------------------------------
    def _construire_vue_lecture(self, txt, numero: int):
        donnees = charger_sourate(numero)
        versets = donnees.get("versets", []) if donnees else []
        self.nb_versets_sourate_active = len(versets)

        # En-tête et barre d'outils FIXES (hors de la zone qui défile), puis la zone défilante.
        self.contenu_racine.controls.append(self._construire_entete_lecture(txt, numero, donnees))
        self.contenu_racine.controls.append(self._construire_barre_outils(txt))
        zone = self._nouvelle_zone_defilante()

        if not donnees:
            zone.controls.append(
                ft.Text("⚠️ Texte de cette sourate indisponible.", size=12, color=ROUGE_ERREUR)
            )
            return

        requete = self.filtre_verset.strip()
        filtre_actif = bool(requete)
        verset_cherche = None
        if filtre_actif and requete.isdigit():
            verset_cherche = next((v for v in versets if v["numero"] == int(requete)), None)

        zone.controls.append(ft.Container(height=4))
        if self.tajweed_actif:
            zone.controls.append(self._construire_legende_tajweed(txt))

        if filtre_actif and verset_cherche is None:
            zone.controls.append(
                ft.Text(txt.get("aucun_verset", "Aucun verset ne correspond à ce numéro."),
                        size=12, italic=True, color=GRIS_TEXTE)
            )
        elif verset_cherche is not None:
            # Recherche : la page de mushaf qui contient le verset, avec le verset surligné.
            page = verset_cherche.get("page")
            versets_page = [v for v in versets if v.get("page") == page]
            modele = txt.get("verset_trouve_page", "Verset {verset} - page {page} du mushaf")
            zone.controls.append(
                ft.Text(modele.replace("{verset}", str(verset_cherche["numero"])).replace("{page}", str(page)),
                        size=11, italic=True, color=GRIS_TEXTE, text_align=ft.TextAlign.CENTER)
            )
            zone.controls.append(
                self._construire_bloc_page(page, versets_page, txt, surligne=verset_cherche["numero"])
            )
        else:
            # La basmala n'a pas de numéro de verset propre : affichée seulement hors recherche.
            if donnees.get("basmalah"):
                zone.controls.append(self._construire_basmalah(donnees))
            for page, versets_page in regrouper_par_page(versets):
                zone.controls.append(self._construire_bloc_page(page, versets_page, txt))

        zone.controls.append(ft.Container(height=12))
        zone.controls.append(
            ft.Text(txt.get("source_attribution", "Source : Tanzil.net"), size=9, color=GRIS_TEXTE,
                    text_align=ft.TextAlign.CENTER)
        )
        zone.controls.append(
            ft.Text(txt.get("source_tajweed", "Tajweed : annotations cpfair/quran-tajweed (CC BY 4.0)"),
                    size=9, color=GRIS_TEXTE, text_align=ft.TextAlign.CENTER)
        )

    def _construire_basmalah(self, donnees: dict) -> ft.Container:
        spans = self._spans_segments(
            donnees["basmalah"], donnees.get("basmalah_tajweed"), VERT_PROFOND, None,
        )
        return ft.Container(
            content=ft.Text(
                spans=spans, size=self.taille_texte, font_family=FONT_CORAN,
                text_align=ft.TextAlign.CENTER, rtl=True, style=ft.TextStyle(height=HAUTEUR_LIGNE),
            ),
            padding=ft.Padding(0, 4, 0, 8), alignment=ft.Alignment.CENTER,
        )

    def _spans_segments(self, texte: str, annotations, couleur_base, bgcolor) -> list:
        """Spans Flet d'un texte : tajweed (si actif) par segments de couleur, sinon un seul span."""
        texte = preparer_texte_affichage(texte)
        spans = []
        for segment, famille in segments_verset(texte, annotations, self.tajweed_actif):
            couleur = couleur_famille(famille) or couleur_base
            spans.append(ft.TextSpan(segment, style=ft.TextStyle(color=couleur, bgcolor=bgcolor)))
        return spans

    def _construire_bloc_page(self, page, versets_page: list, txt, surligne=None) -> ft.Container:
        """Un bloc = une page de mushaf (la portion de la sourate ouverte qu'elle contient)."""
        spans = []
        for verset in versets_page:
            # Couleur verte alternée (pairs plus foncés) quand le tajweed est éteint, comme avant ;
            # texte foncé uni quand il est allumé, pour que les couleurs du tajweed ressortent.
            if self.tajweed_actif:
                couleur_base = TEXTE_FONCE
            else:
                couleur_base = VERT_PROFOND if verset["numero"] % 2 == 0 else VERT_CLAIR
            fond = OCRE_CLAIR if verset["numero"] == surligne else None
            spans.extend(self._spans_segments(verset["texte"], verset.get("tajweed"), couleur_base, fond))
            # Numéro du verset entre parenthèses ornées (core.quran_engine.marqueur_verset).
            spans.append(ft.TextSpan(marqueur_verset(verset["numero"]), style=ft.TextStyle(color=OCRE, bgcolor=fond)))

        mot_page = txt.get("mot_page", "Page")
        mot_juz = txt.get("mot_juz", "Juz")
        juz = juz_de_page(page) if page else None
        pied = f"{mot_page} {chiffres_arabes(page)}" if page else ""
        if juz:
            pied += f"  ·  {mot_juz} {chiffres_arabes(juz)}"

        return ft.Container(
            key=f"page_{page}",
            content=ft.Column([
                ft.Text(
                    spans=spans, size=self.taille_texte, font_family=FONT_CORAN,
                    text_align=ft.TextAlign.JUSTIFY, rtl=True, selectable=True,
                    style=ft.TextStyle(height=HAUTEUR_LIGNE),
                ),
                ft.Text(pied, size=10, color=GRIS_TEXTE, text_align=ft.TextAlign.CENTER),
            ], spacing=6, horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
            padding=ft.Padding(8, 10, 8, 8),
            border=ft.Border(bottom=ft.BorderSide(1, GRIS_CLAIR)),
        )

    def _construire_legende_tajweed(self, txt) -> ft.Container:
        puces = []
        for _cle, couleur, cle_libelle in FAMILLES:
            puces.append(ft.Row([
                ft.Container(width=12, height=12, bgcolor=couleur, border_radius=6),
                ft.Text(txt.get(cle_libelle, cle_libelle), size=11, color=TEXTE_FONCE),
            ], spacing=4, tight=True))
        return ft.Container(
            content=ft.Column([
                ft.Text(txt.get("tajweed_legende_titre", "Légende du tajweed"), size=12,
                        weight=ft.FontWeight.BOLD, color=VERT_PROFOND),
                ft.Row(puces, wrap=True, spacing=12, run_spacing=4),
                ft.Text(txt.get("tajweed_avertissement",
                                "Annotations automatiques, à titre d'aide à la lecture : elles ne remplacent "
                                "pas l'apprentissage auprès d'un enseignant qualifié."),
                        size=10, italic=True, color=GRIS_TEXTE),
            ], spacing=4),
            bgcolor=SABLE, padding=ft.Padding(10, 8, 10, 8), border_radius=8,
            margin=ft.Margin(0, 0, 0, 6),
        )

    def _construire_barre_outils(self, txt) -> ft.Container:
        interrupteur = ft.Switch(
            label=txt.get("tajweed", "Tajweed"), value=self.tajweed_actif,
            active_color=VERT_PROFOND, on_change=self._basculer_tajweed,
        )
        index_taille = TAILLES_TEXTE.index(self.taille_texte) if self.taille_texte in TAILLES_TEXTE else 0
        btn_moins = ft.IconButton(
            icon=ft.Icons.TEXT_DECREASE_ROUNDED, icon_color=VERT_PROFOND, icon_size=20,
            tooltip=txt.get("texte_plus_petit", "Texte plus petit"),
            width=36, height=36, padding=0, disabled=(index_taille <= 0),
            on_click=lambda _: self._changer_taille(-1),
        )
        btn_plus = ft.IconButton(
            icon=ft.Icons.TEXT_INCREASE_ROUNDED, icon_color=VERT_PROFOND, icon_size=20,
            tooltip=txt.get("texte_plus_grand", "Texte plus grand"),
            width=36, height=36, padding=0, disabled=(index_taille >= len(TAILLES_TEXTE) - 1),
            on_click=lambda _: self._changer_taille(+1),
        )
        return ft.Container(
            content=ft.Row([interrupteur, ft.Row([btn_moins, btn_plus], spacing=0)],
                           alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                           vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding(0, 0, 0, 2),
            border=ft.Border(bottom=ft.BorderSide(1, GRIS_CLAIR)),
        )

    def _basculer_tajweed(self, e):
        self.tajweed_actif = bool(e.control.value)
        self._rafraichir()

    def _changer_taille(self, delta: int):
        index = TAILLES_TEXTE.index(self.taille_texte) if self.taille_texte in TAILLES_TEXTE else 0
        index = max(0, min(len(TAILLES_TEXTE) - 1, index + delta))
        self.taille_texte = TAILLES_TEXTE[index]
        self._rafraichir()

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

        # ORDRE RTL : « suivante » (avancer dans le livre) à GAUCHE du titre, « précédente » à DROITE.
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
        )

    def _filtrer_verset(self, e):
        """Recherche de verset : FILTRE la sourate ouverte (affiche la page de mushaf qui contient
        le verset, surligné) et reconstruit la vue - jamais de scroll vers une ligne non construite.
        Anti-rebond ~350ms comme la recherche de sourate, via HayaatiTaskRegistry."""
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
        """Rafraîchissement lors d'un changement de langue (chrome uniquement - le texte arabe
        lui-même ne change pas)."""
        self._rafraichir()
