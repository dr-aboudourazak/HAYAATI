"""
HUB CENTRAL ENSEIGNEMENT - MADRASSA (GUI/PAGES/PAGE_MADRASSA.PY)
Version 1.9 - Raccordement sécurisé final des 3 sous-pages (Arabe, Sciences, Encyclopédie).
Modèle rigoureusement aligné sur le cycle de vie de PageDevoirs.
Totalement compatible Flet 0.86.2, Python 3.10+ & APK Android.
"""
from __future__ import annotations
import flet as ft
from gui.langues import DICTIONNAIRE_LANGUES

class PageMadrassa(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.page_flet = app_reference.page
        self.mode_mobile = None
        
        # --- 1. ÉTIQUETTES LOCALES POUR LA TRADUCTION DYNAMIQUE ---
        self.lbl_titre_hub = ft.Text(size=20, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.lbl_arabe = ft.Text(size=14, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.lbl_sciences = ft.Text(size=14, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.lbl_encyclopedie = ft.Text(size=14, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.lbl_statut = ft.Text(size=12, color="#4b5563")

        # --- 2. GRILLE RESPONSIVE POUR ACCUEILLIR LES 3 CARTES VALIDEES ---
        self.grille_madrassa = ft.ResponsiveRow(spacing=15, run_spacing=15)
        
        def fabriquer_carte_madrassa(emoji_visuel: str, lbl_control: ft.Text, ecran_cible: str, bg_color: str):
            return ft.Container(
                content=ft.Column([
                    ft.Text(value=emoji_visuel, size=30),
                    lbl_control,
                    ft.Text(value="➡️", size=13)
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                bgcolor=bg_color, padding=20, border_radius=12, border=ft.Border.all(1, "#e2e8f0"),
                alignment=ft.Alignment(0, 0),
                on_click=lambda _: self.app.layout_central.basculer_vers_ecran(ecran_cible),
                col={"xs": 12, "md": 4} # S'empile sur Mobile, s'aligne côte à côte sur PC
            )

        # Raccordement physique étanche des trois sous-pages d'origine d'HAYAATI
        self.grille_madrassa.controls.extend([
            fabriquer_carte_madrassa("📚", self.lbl_encyclopedie, "ENCYCLOPEDIE", "#f9fafb"),
            fabriquer_carte_madrassa("🔤", self.lbl_arabe, "LANGUE_ARABE", "#f0fdf4"),
            fabriquer_carte_madrassa("🕌", self.lbl_sciences, "SCIENCES_ISLAMIQUES", "#fffbeb")
        ])

        # --- 3. ASSEMBLAGE MAÎTRE SÉCURISÉ ---
        self.layout_total = ft.Column([
            self.lbl_titre_hub,
            ft.Container(height=5),
            self.lbl_statut,
            ft.Container(height=10),
            self.grille_madrassa
        ], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

        super().__init__(
            content=self.layout_total, expand=True, bgcolor="#f8fafc",
            padding=ft.Padding(left=15, right=15, top=15, bottom=15)
        )

        if hasattr(DICTIONNAIRE_LANGUES, "moteur_i18n"):
            try:
                DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_langue)
            except Exception:
                pass
                
        self.actualiser_donnees_affichage()

    def action_langue(self, dic: dict):
        self.traduire_page(dic)

    def traduire_page(self, dic: dict):
        """Traduit la page à la volée de manière purement dépendante du dictionnaire JSON."""
        if not dic:
            return
        m_json = dic.get("menu", {})
        m_hub = dic.get("madrassa", {})

        # Raccordement dynamique i18n
        self.lbl_titre_hub.value = str(m_hub.get("titre_hub", "🏫 Madrassa")).strip()
        self.lbl_encyclopedie.value = str(m_json.get("encyclopedie", "Encyclopédie")).replace("📚", "").replace(":", "").strip()
        self.lbl_arabe.value = str(m_json.get("langue_arabe", "Langue arabe")).replace("🔤", "").replace(":", "").strip()
        self.lbl_sciences.value = str(m_json.get("sciences_islamiques", "Sciences islamiques")).replace("🕌", "").replace(":", "").strip()
        self.lbl_statut.value = str(m_hub.get("soustitre_hub", "Espace d'études et d'audits doctrinaux"))

        if self.page_flet:
            try: 
                self.page_flet.update()
            except Exception: 
                pass

    def actualiser_donnees_affichage(self):
        """Recharge les libellés au focus de l'écran depuis le dictionnaire actif."""
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)
