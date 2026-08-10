"""
HUB CENTRAL ENSEIGNEMENT - MADRASSA (GUI/PAGES/PAGE_MADRASSA.PY)
Version 2.0 — Le hub reprend l'identité verte historique (logo / PDF), qui
n'est PAS remplacée : seules Encyclopédie, Langue arabe et Sciences
islamiques utilisent la palette Sahélienne terracotta/ocre. Le hub, lui,
gagne trois choses concrètes : les titres/descriptions dédiés déjà rédigés
dans dic["madrassa"] (jusqu'ici ignorés), une pastille de progression réelle
par carte, et un raccourci direct vers la Caravane du Savoir.
Totalement compatible Flet 0.86.2, Python 3.10+ & APK Android.
"""
from __future__ import annotations
import flet as ft
from gui.langues import DICTIONNAIRE_LANGUES
from core.jeu_educatif_engine import CLE_MODULE_JEU, normaliser_progres as normaliser_progres_jeu, compter_perles
from core.langue_arabe_engine import CLE_MODULE_LANGUE_ARABE, normaliser_progres as normaliser_progres_langue

# Même clé que dans page_langue_arabe.py / page_sciences_islamiques.py — les
# trois fichiers doivent impérativement s'accorder sur ce nom de clé.
CLE_MODULE_SCIENCES_ISLAMIQUES = "SCIENCES_ISLAMIQUES_PROGRES"

VERT_FONCE = "#064e3b"
GRIS_TEXTE = "#4b5563"
BORDURE = "#e2e8f0"
FOND_PAGE = "#f8fafc"


def _compter_points_module(donnees_brutes):
    """Additionne connues/à revoir sur toutes les étapes d'un module au format
    {cle_etape: {"connues": [...], "a_revoir": [...]}}."""
    progres = normaliser_progres_langue(donnees_brutes)
    connues = sum(len(v.get("connues", [])) for v in progres.values())
    a_revoir = sum(len(v.get("a_revoir", [])) for v in progres.values())
    return connues, a_revoir


class PageMadrassa(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.page_flet = app_reference.page

        self.zone_contenu = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True,
                                       horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
        super().__init__(
            content=self.zone_contenu, expand=True, bgcolor=FOND_PAGE,
            padding=ft.Padding(left=15, right=15, top=15, bottom=15),
        )

        if hasattr(DICTIONNAIRE_LANGUES, "moteur_i18n"):
            try:
                DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self._action_langue)
            except Exception:
                pass

        self.actualiser_donnees_affichage()

    def _action_langue(self, dic: dict):
        self.construire_interface()
        if self.page_flet:
            try:
                self.page_flet.update()
            except Exception:
                pass

    def actualiser_donnees_affichage(self):
        """Reconstruit entièrement la page à chaque retour sur le hub, pour que
        les pastilles de progression restent fidèles à ce que l'utilisateur
        vient de faire dans les sous-modules."""
        self.construire_interface()

    # --- Lecture de la progression réelle de chaque module ------------------
    def _progres_encyclopedie(self):
        u_id = getattr(self.app, "user_id_connecte", None)
        if not u_id or not hasattr(self.app, "sync_engine"):
            return None
        donnees = self.app.sync_engine.charger_donnees_module(u_id, CLE_MODULE_JEU)
        perles = compter_perles(normaliser_progres_jeu(donnees))
        return f"✨ {perles} perle(s)" if perles else "Pas encore commencé"

    def _progres_module_langue(self, cle_module, libelle_unite):
        u_id = getattr(self.app, "user_id_connecte", None)
        if not u_id or not hasattr(self.app, "sync_engine"):
            return None
        donnees = self.app.sync_engine.charger_donnees_module(u_id, cle_module)
        connues, a_revoir = _compter_points_module(donnees)
        if not connues and not a_revoir:
            return "Pas encore commencé"
        libelle = f"✓ {connues} {libelle_unite}"
        if a_revoir:
            libelle += f"  ·  ❓❓ {a_revoir}"
        return libelle

    def _points_a_revoir_total(self):
        u_id = getattr(self.app, "user_id_connecte", None)
        if not u_id or not hasattr(self.app, "sync_engine"):
            return 0
        d_langue = normaliser_progres_langue(self.app.sync_engine.charger_donnees_module(u_id, CLE_MODULE_LANGUE_ARABE))
        d_sciences = normaliser_progres_langue(self.app.sync_engine.charger_donnees_module(u_id, CLE_MODULE_SCIENCES_ISLAMIQUES))
        total = 0
        for progres in (d_langue, d_sciences):
            total += sum(len(v.get("a_revoir", [])) for v in progres.values())
        return total

    # --- Construction de l'interface -----------------------------------------
    def _carte_module(self, emoji, titre, description, badge_progres, ecran_cible, bg_color, on_click=None):
        elements = [
            ft.Text(emoji, size=30),
            ft.Text(titre, size=14, weight=ft.FontWeight.BOLD, color=VERT_FONCE, text_align=ft.TextAlign.CENTER),
        ]
        if description:
            elements.append(ft.Text(description, size=11, color=GRIS_TEXTE, text_align=ft.TextAlign.CENTER))
        if badge_progres:
            elements.append(ft.Container(
                content=ft.Text(badge_progres, size=10, weight=ft.FontWeight.BOLD, color=VERT_FONCE),
                bgcolor="white", border_radius=20, padding=ft.Padding(left=10, right=10, top=4, bottom=4),
                margin=ft.Margin(left=0, top=2, right=0, bottom=0),
            ))
        elements.append(ft.Text("➡️", size=13))

        return ft.Container(
            content=ft.Column(elements, alignment=ft.MainAxisAlignment.CENTER,
                               horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
            bgcolor=bg_color, padding=20, border_radius=12, border=ft.Border.all(1, BORDURE),
            alignment=ft.Alignment(0, 0),
            on_click=on_click or (lambda _: self.app.layout_central.basculer_vers_ecran(ecran_cible)),
            col={"xs": 12, "md": 4},
        )

    def _ouvrir_caravane(self, _e):
        # Le drapeau est lu et consommé par PageLangueArabe.actualiser_donnees_affichage.
        self.app.demande_ouverture_caravane = True
        self.app.layout_central.basculer_vers_ecran("LANGUE_ARABE")

    def construire_interface(self):
        self.zone_contenu.controls.clear()
        dic = DICTIONNAIRE_LANGUES.actif or {}
        m_hub = dic.get("madrassa", {})

        titre_hub = ft.Text(str(m_hub.get("titre_hub", "🏫 Madrassa")).strip(),
                             size=20, weight=ft.FontWeight.BOLD, color=VERT_FONCE)
        sous_titre = ft.Text(str(m_hub.get("soustitre_hub", "Espace d'études et d'audits doctrinaux")),
                              size=12, color=GRIS_TEXTE)

        grille = ft.ResponsiveRow(spacing=15, run_spacing=15)
        grille.controls.extend([
            self._carte_module("📚", m_hub.get("titre_encyclopedie", "Encyclopédie"),
                                m_hub.get("desc_encyclopedie", ""), self._progres_encyclopedie(),
                                "ENCYCLOPEDIE", "#f9fafb"),
            self._carte_module("🔤", m_hub.get("titre_langue_arabe", "Langue Arabe"),
                                m_hub.get("desc_langue_arabe", ""),
                                self._progres_module_langue(CLE_MODULE_LANGUE_ARABE, "acquis"),
                                "LANGUE_ARABE", "#f0fdf4"),
            self._carte_module("🕌", m_hub.get("titre_sciences_islamiques", "Sciences Islamiques"),
                                m_hub.get("desc_sciences_islamiques", ""),
                                self._progres_module_langue(CLE_MODULE_SCIENCES_ISLAMIQUES, "acquis"),
                                "SCIENCES_ISLAMIQUES", "#fffbeb"),
        ])

        nb_a_revoir = self._points_a_revoir_total()
        badge_caravane = f"❓❓ {nb_a_revoir}" if nb_a_revoir else "🌱"
        grille.controls.append(self._carte_module(
            "🗺️", "Caravane du Savoir",
            "Révision groupée : Langue arabe + Sciences islamiques",
            badge_caravane, None, "#eef2ff", on_click=self._ouvrir_caravane,
        ))

        self.zone_contenu.controls.extend([
            titre_hub,
            ft.Container(height=5),
            sous_titre,
            ft.Container(height=10),
            grille,
        ])

        if not getattr(self.app, "user_id_connecte", None):
            self.zone_contenu.controls.append(ft.Container(
                content=ft.Text("👤 Mode Visiteur : la progression n'est pas conservée d'une session à l'autre.",
                                 size=11, italic=True, color=GRIS_TEXTE),
                bgcolor="#f1f5f9", padding=10, border_radius=6, margin=ft.Margin(left=0, top=8, right=0, bottom=0),
            ))
