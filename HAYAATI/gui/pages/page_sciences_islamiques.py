"""
PAGE SCIENCES ISLAMIQUES EN FLET (GUI/PAGES/PAGE_SCIENCES_ISLAMIQUES.PY)
Version 2.0 — Adapté pour routage via app_layout.py
"""
from __future__ import annotations
import json
import os
import flet as ft
from core.langue_arabe_engine import normaliser_progres, marquer_item, resume_etape
from gui.langues import DICTIONNAIRE_LANGUES

CHEMIN_FR_JSON = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "locales", "fr.json")
# Même clé que côté PageLangueArabe (qui combine les deux progrès pour la
# Caravane du Savoir) : les deux fichiers doivent impérativement s'accorder
# sur ce nom de clé pour lire/écrire la même ligne dans le coffre chiffré.
CLE_MODULE_SCIENCES_ISLAMIQUES = "SCIENCES_ISLAMIQUES_PROGRES"

TERRACOTTA = "#C1502E"
TERRACOTTA_CLAIR = "#F4E4DC"
OCRE = "#D9A441"
OCRE_CLAIR = "#FBF0DA"
VERT_SUCCES = "#27500A"
AMBRE_ATTENTE = "#d97706"
TEXTE_FONCE = "#2b1607"
GRIS_CLAIR = "#f3f4f6"
GRIS_TEXTE_CLAIR = "#6b7280"


def bordure_uniforme(couleur, largeur=1):
    cote = ft.BorderSide(width=largeur, color=couleur)
    return ft.Border(top=cote, right=cote, bottom=cote, left=cote)


def charger_sciences_islamiques():
    with open(CHEMIN_FR_JSON, encoding="utf-8") as f:
        d = json.load(f)
    return d.get("sciences_islamiques", {})


class EtatApplication:
    def __init__(self):
        self.progres = normaliser_progres(None)
        self.etape_active = 0
        self.index_lecon = 0
        self.onglet_sous_rubrique = 0


class PageSciencesIslamiques(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.etat = EtatApplication()
        # Conservé uniquement comme filet de secours si txt_global n'est pas
        # encore disponible (ex. accès direct hors du routeur principal).
        self._contenu_secours = charger_sciences_islamiques()

        self.zone_contenu = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=0, expand=True)
        super().__init__(
            content=self.zone_contenu, expand=True,
            bgcolor="white", padding=ft.Padding(20, 20, 20, 20)
        )
        self._charger_progres_persistant()
        if hasattr(DICTIONNAIRE_LANGUES, "moteur_i18n"):
            try:
                DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self._action_langue)
            except Exception:
                pass
        self.construire_page()

    def _action_langue(self, dic: dict):
        """Appelé par le routeur i18n dès qu'une nouvelle langue est chargée,
        même si l'utilisateur est déjà sur cet écran."""
        self._rafraichir()

    @property
    def contenu(self):
        """DICTIONNAIRE_LANGUES (gui.langues) est le routeur i18n réel et
        éprouvé de l'application (utilisé par PageMadrassa). self.app.txt_global
        reste consulté en second, pour compatibilité, avant le repli local figé."""
        dic_actif = DICTIONNAIRE_LANGUES.actif or {}
        return (dic_actif.get("sciences_islamiques")
                or (self.app.txt_global.get("sciences_islamiques", {}) if hasattr(self.app, "txt_global") else None)
                or self._contenu_secours)

    @property
    def txt_ui(self):
        dic_actif = DICTIONNAIRE_LANGUES.actif or {}
        return (dic_actif.get("interface_savoir")
                or (self.app.txt_global.get("interface_savoir", {}) if hasattr(self.app, "txt_global") else None)
                or {})

    def actualiser_donnees_affichage(self):
        self.construire_page()

    def _rafraichir(self):
        self.construire_page()
        self.update()

    # --- Persistance sécurisée (même raccordement que PageLangueArabe) -----
    def _charger_progres_persistant(self):
        u_id = getattr(self.app, "user_id_connecte", None)
        if not u_id or not hasattr(self.app, "sync_engine"):
            return
        donnees = self.app.sync_engine.charger_donnees_module(u_id, CLE_MODULE_SCIENCES_ISLAMIQUES)
        self.etat.progres = normaliser_progres(donnees)

    def _sauvegarder_progres(self):
        u_id = getattr(self.app, "user_id_connecte", None)
        if not u_id or not hasattr(self.app, "sync_engine"):
            return
        self.app.sync_engine.executer_sauvegarde_module(u_id, CLE_MODULE_SCIENCES_ISLAMIQUES, self.etat.progres)

    def _construire_chronologie(self, chronologie):
        lignes = []
        for i, etape_chrono in enumerate(chronologie):
            puce = ft.Container(
                content=ft.Text(str(i + 1), color="white", size=11, weight=ft.FontWeight.BOLD),
                width=26, height=26, border_radius=13, bgcolor=TERRACOTTA,
                alignment=ft.Alignment(0, 0),
            )
            contenu = ft.Column([
                ft.Text(etape_chrono["date"], size=12, weight=ft.FontWeight.BOLD, color=TERRACOTTA),
                ft.Text(etape_chrono["evenement"], size=11, color=TEXTE_FONCE),
            ], spacing=1, tight=True)
            lignes.append(ft.Row([puce, contenu], spacing=10, vertical_alignment=ft.CrossAxisAlignment.START))
            if i < len(chronologie) - 1:
                lignes.append(ft.Container(width=2, height=14, bgcolor=OCRE, margin=ft.Margin(left=12)))
        return ft.Column(lignes, spacing=4, tight=True)

    def _construire_bloc_exemples(self, exemples):
        return [
            ft.Container(
                content=ft.Column([
                    ft.Text(ex.get("arabe", ""), size=17, weight=ft.FontWeight.BOLD, color=TEXTE_FONCE),
                    ft.Text(f"{ex.get('translitteration','')} — {ex.get('sens','')}", size=10, color=TEXTE_FONCE),
                ], spacing=2, tight=True),
                border=bordure_uniforme(OCRE), border_radius=6, padding=10, margin=ft.Margin(bottom=6),
            )
            for ex in exemples
        ]

    def construire_page(self):
        self.zone_contenu.controls.clear()
        contenu = self.contenu
        etat = self.etat

        # 🎯 BOUTON RETOUR SOUVERAIN VERS LE HUB MADRASSA
        btn_retour_madrassa = ft.IconButton(
            icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
            icon_color=TERRACOTTA,
            icon_size=16,
            tooltip="↩️",
            on_click=lambda _: self.app.layout_central.basculer_vers_ecran("MADRASSA")
        )
        self.zone_contenu.controls.append(btn_retour_madrassa)

        self.zone_contenu.controls.append(
            ft.Text(contenu.get("titre", "🕌 Sciences islamiques"), size=20, weight=ft.FontWeight.BOLD, color=TERRACOTTA)
        )
        self.zone_contenu.controls.append(
            ft.Text(contenu.get("sous_titre", ""), size=11, italic=True, color=TEXTE_FONCE)
        )
        self.zone_contenu.controls.append(ft.Container(height=10))

        etapes = contenu.get("etapes", [])
        if not etapes:
            self.zone_contenu.controls.append(ft.Text(self.txt_ui.get("contenu_indisponible", "Contenu non disponible."), color=TEXTE_FONCE))
            return

        etape_courante = etapes[min(etat.etape_active, len(etapes) - 1)]

        # Sentier horizontal
        segments = []
        for i, e in enumerate(etapes):
            actif = (i == etat.etape_active)
            dispo = e.get("disponible", False)
            segments.append(
                ft.Container(
                    content=ft.Text(e.get("titre", "").split(" - ")[0], size=11,
                        weight=ft.FontWeight.BOLD if actif else ft.FontWeight.NORMAL,
                        color="white" if actif else (TEXTE_FONCE if dispo else GRIS_TEXTE_CLAIR)),
                    bgcolor=TERRACOTTA if actif else (OCRE_CLAIR if dispo else GRIS_CLAIR),
                    padding=8, border_radius=6,
                    on_click=(lambda e2, idx=i: self._choisir_etape(idx)) if dispo else None,
                )
            )
        self.zone_contenu.controls.append(ft.Row(segments, wrap=True, spacing=4))

        if not etape_courante.get("disponible", False):
            self.zone_contenu.controls.append(ft.Container(
                content=ft.Text(f"⏳ {etape_courante.get('titre','')} — {self.txt_ui.get('etape_bientot_disponible', 'bientôt disponible.')}", color=OCRE),
                bgcolor=OCRE_CLAIR, padding=14, border_radius=6, margin=ft.Margin(top=10),
            ))
            return

        lecons = etape_courante.get("lecons", [])
        cle_progres = f"sciences_{etape_courante.get('cle', etat.etape_active)}"

        # Certaines étapes (comme Tawhid) proposent plusieurs onglets internes
        # — deux parcours parallèles plutôt qu'une seule liste de leçons.
        sous_rubriques = etape_courante.get("sous_rubriques")
        if sous_rubriques:
            etat.onglet_sous_rubrique = min(etat.onglet_sous_rubrique, len(sous_rubriques) - 1)
            onglets = []
            for i, sr in enumerate(sous_rubriques):
                actif_sr = (i == etat.onglet_sous_rubrique)
                onglets.append(ft.Container(
                    content=ft.Text(sr.get("titre", ""), size=11,
                        weight=ft.FontWeight.BOLD if actif_sr else ft.FontWeight.NORMAL,
                        color="white" if actif_sr else TEXTE_FONCE),
                    bgcolor=OCRE if actif_sr else OCRE_CLAIR, padding=8, border_radius=6,
                    on_click=(lambda e2, idx=i: self._choisir_sous_rubrique(idx)),
                ))
            self.zone_contenu.controls.append(ft.Row(onglets, wrap=True, spacing=4))
            sr_active = sous_rubriques[etat.onglet_sous_rubrique]
            if sr_active.get("description"):
                self.zone_contenu.controls.append(ft.Container(
                    content=ft.Text(sr_active["description"], size=10, italic=True, color=TEXTE_FONCE),
                    margin=ft.Margin(top=6, bottom=0, left=2, right=0),
                ))
            lecons = sr_active.get("lecons", [])
            cle_progres = f"{cle_progres}_{sr_active.get('cle', etat.onglet_sous_rubrique)}"

        etat.index_lecon = min(etat.index_lecon, len(lecons) - 1) if lecons else 0

        resume = resume_etape(etat.progres, cle_progres, len(lecons))
        bandeau = ft.Container(
            content=ft.Text(f"✓ {resume['connues']} {self.txt_ui.get('resume_compris', 'compris(es)')}   ·   "
                            f"🔁 {resume['a_revoir']} {self.txt_ui.get('resume_a_revoir', 'à revoir')}   ·   "
                            f"⚪ {resume['non_vues']} {self.txt_ui.get('resume_non_vues', 'pas encore vu(e)s')}",
                             size=12, weight=ft.FontWeight.BOLD, color=TEXTE_FONCE),
            bgcolor=OCRE_CLAIR, padding=10, border_radius=6, margin=ft.Margin(top=10, bottom=10),
        )
        self.zone_contenu.controls.append(bandeau)

        if not lecons:
            self.zone_contenu.controls.append(ft.Text(self.txt_ui.get("aucune_lecon", "Aucune leçon."), color=TEXTE_FONCE))
            return

        lecon = lecons[etat.index_lecon]
        identifiant = str(etat.index_lecon)

        corps_lecon = [
            ft.Text(lecon.get("titre", ""), size=15, weight=ft.FontWeight.BOLD, color=TERRACOTTA),
            ft.Text(lecon.get("explication", ""), size=12, color=TEXTE_FONCE),
        ]
        if lecon.get("type_visuel") == "chronologie":
            corps_lecon.append(ft.Container(content=self._construire_chronologie(lecon.get("chronologie", [])), margin=ft.Margin(top=8, bottom=8)))
        corps_lecon.extend(self._construire_bloc_exemples(lecon.get("exemples", [])))

        def marquer(e, connu):
            etat.progres = marquer_item(etat.progres, cle_progres, identifiant, connu)
            self._sauvegarder_progres()
            if etat.index_lecon < len(lecons) - 1:
                etat.index_lecon += 1
            self._rafraichir()

        pied = ft.Row([
            ft.ElevatedButton("✅", bgcolor=VERT_SUCCES, color="white", height=36, width=52,
                              style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
                              tooltip=self.txt_ui.get("tooltip_jai_compris", "J'ai compris"), on_click=lambda _: marquer(None, True)),
            ft.ElevatedButton("❓❓", bgcolor=AMBRE_ATTENTE, color="white", height=36, width=52,
                              style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
                              tooltip=self.txt_ui.get("tooltip_a_revoir", "À revoir"), on_click=lambda _: marquer(None, False)),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)

        def naviguer(delta):
            etat.index_lecon += delta
            self._rafraichir()

        barre_pagination = ft.Row([
            ft.ElevatedButton("◀", on_click=lambda e: naviguer(-1), disabled=(etat.index_lecon == 0), width=44,
                              style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6))),
            ft.Text(f"{etat.index_lecon + 1} / {len(lecons)}", size=12, weight=ft.FontWeight.BOLD, color=TEXTE_FONCE),
            ft.ElevatedButton("▶", on_click=lambda e: naviguer(1), disabled=(etat.index_lecon >= len(lecons) - 1), width=44,
                              style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6))),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        carte = ft.Container(
            content=ft.Column(corps_lecon + [ft.Container(height=8), pied], spacing=6, tight=True),
            bgcolor=GRIS_CLAIR, border=bordure_uniforme(TERRACOTTA), border_radius=8, padding=16,
        )

        self.zone_contenu.controls.append(carte)
        self.zone_contenu.controls.append(ft.Container(height=10))
        self.zone_contenu.controls.append(barre_pagination)

    def _choisir_etape(self, index):
        self.etat.etape_active = index
        self.etat.index_lecon = 0
        self.etat.onglet_sous_rubrique = 0
        self._rafraichir()

    def _choisir_sous_rubrique(self, index):
        self.etat.onglet_sous_rubrique = index
        self.etat.index_lecon = 0
        self._rafraichir()
