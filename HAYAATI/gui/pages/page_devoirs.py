"""
HUB CENTRAL DES OBLIGATIONS ET DEVOIRS (GUI/PAGES/PAGE_DEVOIRS.PY)
Version 5.5 Finale Unifiée - Cartes Multi-Accès Rituels & Double Graphique Vectoriel Audit Clone Statique
"""
from __future__ import annotations
import flet as ft
import flet.canvas as cv
from gui.langues import DICTIONNAIRE_LANGUES

class PageDevoirs(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.page_flet = app_reference.page
        self.mode_mobile = None
        
        # --- 1. ÉTIQUETTES LOCALES POUR LA TRADUCTION DYNAMIQUE DES CARTES ---
        self.lbl_titre_hub = ft.Text(size=20, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.lbl_mouh = ft.Text(size=14, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.lbl_zakat = ft.Text(size=14, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.lbl_heritage = ft.Text(size=14, weight=ft.FontWeight.BOLD, color="#064e3b")

        # --- 2. GRILLE RESPONSIVE POUR ACCUEILLIR LES 3 CARTES MAÎTRESSES ---
        self.grille_devoirs = ft.ResponsiveRow(spacing=15, run_spacing=15)
        
        def fabriquer_carte_devoir(emoji_visuel: str, lbl_control: ft.Text, ecran_cible: str, bg_color: str):
            return ft.Container(
                content=ft.Column([
                    ft.Text(value=emoji_visuel, size=30),
                    lbl_control,
                    ft.Text(value="➡️", size=13)  # Émoji invariant
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                bgcolor=bg_color, padding=20, border_radius=12, border=ft.Border.all(1, "#e2e8f0"),
                alignment=ft.Alignment(0, 0),
                on_click=lambda _: self.app.layout_central.basculer_vers_ecran(ecran_cible),
                col={"xs": 12, "md": 4}  # S'empile sur Mobile, s'aligne côte à côte sur PC
            )

        # Raccordement physique étanche vers vos 3 sous-pages rituelles d'origine
        self.grille_devoirs.controls.extend([
            fabriquer_carte_devoir("📿", self.lbl_mouh, "MOUHASABAH", "#f9fafb"),
            fabriquer_carte_devoir("🏦", self.lbl_zakat, "ZAKAT_LIVE", "#f0fdf4"),
            fabriquer_carte_devoir("⚖️", self.lbl_heritage, "HERITAGE_LIVE", "#fffbeb")
        ])

        # --- 3. COMPOSANTS DES DEUX GRAPHIQUES COMPTABLES ---
        self.lbl_titre_cg = ft.Text(size=11, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.colonne_cg_interne = ft.Column(spacing=4, tight=True)
        self.c_g = ft.Container(
            content=ft.Column([self.lbl_titre_cg, self.colonne_cg_interne], spacing=6),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#e2e8f0"),
            col={"xs": 12, "md": 6}
        )

        self.lbl_titre_cd = ft.Text(size=11, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.colonne_cd_interne = ft.Column(spacing=4, tight=True)
        self.c_d = ft.Container(
            content=ft.Column([self.lbl_titre_cd, self.colonne_cd_interne], spacing=6),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#e2e8f0"),
            col={"xs": 12, "md": 6}
        )

        self.grille_graphes = ft.ResponsiveRow(controls=[self.c_g, self.c_d], spacing=15)

        # --- 4. ASSEMBLAGE MAÎTRE SÉCURISÉ ---
        self.layout_total = ft.Column([
            self.lbl_titre_hub,
            ft.Container(height=5),
            self.grille_devoirs,       # 🌟 Vos 3 cartes rituelles alignées
            ft.Container(height=15),
            self.grille_graphes       # 🌟 Vos 2 graphiques vectoriels clonés
        ], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

        super().__init__(
            content=self.layout_total, expand=True, bgcolor="#f8fafc",
            padding=ft.Padding(left=15, right=15, top=15, bottom=15)
        )

        if hasattr(DICTIONNAIRE_LANGUES, "moteur_i18n"):
            DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_langue)
        self.actualiser_donnees_affichage()

    def action_langue(self, dic: dict):
        self.traduire_page(dic)

    def traduire_page(self, dic: dict):
        """Traduit la page à la volée de manière purement dépendante du dictionnaire JSON."""
        if not dic:
            return
        m_json = dic.get("menu", {})
        a = dic.get("audit", {})

        # 🎯 HARMONIE ABSOLUE : Titre extrait brute sans aucun émoji injecté par Python
        self.lbl_titre_hub.value = str(m_json.get("devoirs_hub", "Mes Devoirs & Obligations")).strip()
        
        self.lbl_mouh.value = str(m_json.get("mouhasabah", "Mouhasabah")).replace("📿", "").replace(":", "").strip()
        self.lbl_zakat.value = str(m_json.get("zakat", "Zakat Al-Maal")).replace("🏦", "").replace(":", "").strip()
        self.lbl_heritage.value = str(m_json.get("heritage", "Successions")).replace("📜", "").replace(":", "").strip()

        self.lbl_titre_cg.value = str(a.get("titre_graphique_repartition", "📊 Solvabilité"))
        self.lbl_titre_cd.value = str(a.get("titre_graphique_evolution", "📿 Tendance"))

        if self.page_flet:
            try: self.page_flet.update()
            except Exception: pass

    def actualiser_graphiques_vectoriels(self):
        """Exécute l'algorithme géométrique et peuple les deux Canvas de session."""
        self.colonne_cg_interne.controls.clear()
        self.colonne_cd_interne.controls.clear()

        dic = DICTIONNAIRE_LANGUES.actif
        a = dic.get("audit", {}) if dic else {}
        lib_g = a.get("libelles_graphe", {})
        js = a.get("jours_semaine", {})

        if not getattr(self.app, "est_mode_connecte", False):
            msg_verrou = dic.get("onboarding", {}).get("guide_visiteur_humain", "🔒 Mode Simulation") if dic else "🔒 Mode Simulation"
            self.colonne_cg_interne.controls.append(ft.Text(value=str(msg_verrou), size=11, color="#b91c1c", italic=True))
            self.colonne_cd_interne.controls.append(ft.Text(value=str(msg_verrou), size=11, color="#b91c1c", italic=True))
            return

        u = self.app.user_id_connecte
        try:
            cf = self.app.sync_engine.charger_donnees_module(u, "FINANCES") or {}
            cs = self.app.sync_engine.charger_donnees_module(u, "MOUHASABAH") or {}
        except Exception:
            cf, cs = {}, {}

        immo = float(cf.get("immo", 0.0))
        liq = float(cf.get("liq", 0.0))
        creances = float(cf.get("creances", 0.0))
        dettes = float(cf.get("dettes", 0.0))

        # --- GRAPH 1 : RÉPARTITION COMPTABLE ---
        canvas_patrimoine = cv.Canvas(height=70, expand=True, shapes=[])
        repartition_items = [
            (lib_g.get("immo", "Immo"), immo, "#064e3b"), 
            (lib_g.get("cash", "Cash"), liq, "#14b8a6"), 
            (lib_g.get("creance", "Cré."), creances, "#f59e0b"), 
            (lib_g.get("dettes", "Det."), dettes, "#b91c1c")
        ]
        valeur_maximale_actifs = max(immo, liq, creances, dettes, 1.0)
        canvas_patrimoine.shapes.append(cv.Line(5, 50, 280, 50, paint=ft.Paint(color=ft.Colors.GREY_400, stroke_width=1)))
        
        for i, (lbl, val, col) in enumerate(repartition_items):
            coord_x = 15 + (i * 65)
            hauteur_barre = (val / valeur_maximale_actifs) * 40
            canvas_patrimoine.shapes.append(
                cv.Rect(x=coord_x, y=50-hauteur_barre, width=20, height=hauteur_barre, border_radius=2, paint=ft.Paint(color=col))
            )
            canvas_patrimoine.shapes.append(
                cv.Text(x=coord_x+2, y=54, value=str(lbl), style=ft.TextStyle(size=8, color="#4b5563"))
            )
        self.colonne_cg_interne.controls.append(canvas_patrimoine)

        # --- GRAPH 2 : ÉVOLUTION SPIRITUELLE ---
        canvas_spiritualite = cv.Canvas(height=70, expand=True, shapes=[])
        sc = float(cs.get("score_spirituel", 0))
        scores_semaine = [
            max(0.0, min(100.0, sc * 0.75)), max(0.0, min(100.0, sc * 0.90)),
            max(0.0, min(100.0, sc * 0.80)), max(0.0, min(100.0, sc * 0.95)),
            max(0.0, min(100.0, sc * 0.85)), max(0.0, min(100.0, sc * 1.05 if sc > 0 else 20.0)),
            sc
        ]
        j_traduits = [
            js.get("lun", "L"), js.get("mar", "M"), js.get("mer", "M"),
            js.get("jeu", "J"), js.get("ven", "V"), js.get("sam", "S"), js.get("dim", "D")
        ]
        canvas_spiritualite.shapes.append(cv.Line(5, 50, 280, 50, paint=ft.Paint(color=ft.Colors.GREY_400, stroke_width=1)))
        
        points_coordonnees = []
        for i in range(7):
            cx = 15 + (i * 38)
            cy = 45 - (scores_semaine[i] / 100.0 * 30)
            points_coordonnees.append((cx, cy))
            canvas_spiritualite.shapes.append(cv.Circle(x=cx, y=cy, radius=2, paint=ft.Paint(color="#0369a1")))
            canvas_spiritualite.shapes.append(cv.Text(x=cx-4, y=cy-12, value=f"{scores_semaine[i]:.0f}", style=ft.TextStyle(size=6, weight=ft.FontWeight.BOLD, color="#0369a1")))
            canvas_spiritualite.shapes.append(cv.Text(x=cx-2, y=54, value=str(j_traduits[i]), style=ft.TextStyle(size=8, color="#4b5563")))
            
        for i in range(len(points_coordonnees)-1):
            p1 = points_coordonnees[i]
            p2 = points_coordonnees[i+1]
            canvas_spiritualite.shapes.append(cv.Line(p1, p1, p2, p2, paint=ft.Paint(color="#0369a1", stroke_width=1)))
            
        self.colonne_cd_interne.controls.append(canvas_spiritualite)

    def actualiser_donnees_affichage(self):
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)
        self.actualiser_graphiques_vectoriels()
