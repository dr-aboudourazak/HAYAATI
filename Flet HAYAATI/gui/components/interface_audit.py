"""
CENTRE D'AUDIT ET GRAPHES VECTORIELS (GUI/COMPONENTS/INTERFACE_AUDIT.PY)
Version Finale Intégrale Statique - Totalement compatible Flet 0.86.2, Python 3.14 & APK Android
"""
from __future__ import annotations
import flet as ft
import flet.canvas as cv
from gui.langues import DICTIONNAIRE_LANGUES

class InterfaceAudit(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.page_flet = app_reference.page
        self.mode_mobile = None
        self.categories_doc: list[dict] = []
        
        # --- 1. INSTANCIATION DES COMPOSANTS GRAPHIQUES MATERIAL 3 ---
        # Cadres de diagnostics (Solvabilité et Tendance)
        self.lbl_titre_cg = ft.Text(size=11, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.colonne_cg_interne = ft.Column(spacing=4, tight=True)
        self.c_g = ft.Container(
            content=ft.Column([self.lbl_titre_cg, self.colonne_cg_interne], spacing=6),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#e2e8f0"),
            col={"xs": 12, "md": 6} # 🎯 RESPONSIVE AUTO : Côte à côte sur PC / Empilé sur Mobile
        )

        self.lbl_titre_cd = ft.Text(size=11, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.colonne_cd_interne = ft.Column(spacing=4, tight=True)
        self.c_d = ft.Container(
            content=ft.Column([self.lbl_titre_cd, self.colonne_cd_interne], spacing=6),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#e2e8f0"),
            col={"xs": 12, "md": 6}
        )

        self.grille_graphes = ft.ResponsiveRow(controls=[self.c_g, self.c_d], spacing=15)

        # Secteur Encyclopédie et Recherche législative
        self.lbl_titre_encyclo = ft.Text(size=14, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.lbl_consigne = ft.Text(size=11, italic=True, color="#4b5563")
        
        # 🎯 FIX MASQUAGE TEXTE : Retrait de height=180 fixe, expand=True s'adapte à la hauteur du contenu
        self.liste_modules_view = ft.ListView(spacing=5, expand=True)
        self.cadre_selecteur = ft.Container(
            content=self.liste_modules_view,
            bgcolor=ft.Colors.WHITE, border_radius=6, border=ft.Border.all(1, ft.Colors.GREY_300),
            padding=5, col={"xs": 12, "md": 4}, expand=True
        )

        # 🎯 FIX MASQUAGE TEXTE : expand=True et max_lines=None libèrent la zone de texte pour afficher l'intégralité des preuves
        self.text_preuves = ft.TextField(
            multiline=True, min_lines=8, max_lines=None, text_size=13, read_only=True,
            border_color=ft.Colors.GREY_400, bgcolor="#fcfcfc", col={"xs": 12, "md": 8},
            expand=True
        )

        # Grille responsive configurée pour étirer harmonieusement les deux volets sur l'axe vertical
        self.grille_encyclo_interne = ft.ResponsiveRow(
            controls=[self.cadre_selecteur, self.text_preuves], spacing=15
        )

        # 🎯 ALIGNEMENT GLOBAL : horizontal_alignment=STRETCH force les blocs à s'aligner sur toute la largeur
        self.layout_audit = ft.Column([
            self.grille_graphes,
            ft.Container(height=5),
            self.lbl_titre_encyclo,
            self.lbl_consigne,
            self.grille_encyclo_interne
        ], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

        super().__init__(
            content=self.layout_audit, expand=True, bgcolor="#f8fafc",
            padding=ft.Padding(left=15, right=15, top=15, bottom=15)
        )

        # Liaison i18n
        if hasattr(DICTIONNAIRE_LANGUES, "moteur_i18n"):
            DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_langue)
        self.actualiser_donnees_affichage()

    def action_langue(self, dic: dict):
        """Met à jour l'interface lors d'une modification linguistique globale."""
        self.traduire_page(dic)

    def traduire_page(self, dic: dict):
        """Injecte l'ensemble des traductions d'analyses de la session."""
        if not dic:
            return
        a = dic.get("audit", {})
        enc = dic.get("encyclopedie", {})
        self.categories_doc = enc.get("categories", [])

        self.lbl_titre_cg.value = str(a.get("titre_graphique_repartition", "📊 Solvabilité"))
        self.lbl_titre_cd.value = str(a.get("titre_graphique_evolution", "📿 Tendance"))
        
        self.lbl_titre_encyclo.value = str(enc.get("titre", "Encyclopédie"))
        if "consigne" in enc:
            self.lbl_consigne.value = str(enc["consigne"])
            self.lbl_consigne.visible = True
        else:
            self.lbl_consigne.visible = False

        # Reconstruction de la liste des chapitres encyclopédiques
        self.liste_modules_view.controls.clear()
        for idx, c in enumerate(self.categories_doc):
            titre_chapitre = c.get("titre", f"Module {idx+1}")
            
            def créer_evenement_clic(target_idx=idx):
                return lambda _: self.on_selection_flet(target_idx)

            self.liste_modules_view.controls.append(
                ft.ListTile(
                    title=ft.Text(value=str(titre_chapitre), size=12, weight=ft.FontWeight.W_500),
                    dense=True,
                    on_click=créer_evenement_clic()
                )
            )

        if self.page_flet:
            try: self.update()
            except Exception: pass

    # ============================================================
    # 🎯 PARTIE 2 : HISTORIQUES RECHERCHE ET RENDU VECTORIEL INTERACTIF
    # ============================================================

    def on_selection_flet(self, idx: int):
        """Méthode de rappel invoquée au clic d'une tuile de l'encyclopédie."""
        if not self.categories_doc or idx >= len(self.categories_doc): 
            return
            
        # Extraction et injection propre du contenu de la preuve Sharia correspondante
        self.text_preuves.value = str(self.categories_doc[idx].get("texte", ""))
        if self.page_flet:
            try: self.update()
            except Exception: pass

    def actualiser_graphiques_vectoriels(self):
        """Calcule les indicateurs comptables et dresse les deux graphiques vectoriels natifs."""
        self.colonne_cg_interne.controls.clear()
        self.colonne_cd_interne.controls.clear()

        dic = DICTIONNAIRE_LANGUES.actif
        a = dic.get("audit", {})
        lib_g = a.get("libelles_graphe", {})
        js = a.get("jours_semaine", {})

        # Sécurité d'espace privé déconnecté
        if not getattr(self.app, "est_mode_connecte", False):
            msg_verrou = dic.get("onboarding", {}).get("guide_visiteur_humain", "🔒 Mode Simulation")
            self.colonne_cg_interne.controls.append(ft.Text(value=str(msg_verrou), size=11, color="#b91c1c", italic=True))
            self.colonne_cd_interne.controls.append(ft.Text(value=str(msg_verrou), size=11, color="#b91c1c", italic=True))
            return

        u = self.app.user_id_connecte
        cf = self.app.sync_engine.charger_donnees_module(u, "FINANCES") or {}
        cs = self.app.sync_engine.charger_donnees_module(u, "MOUHASABAH") or {}

        immo = float(cf.get("immo", 0.0))
        liq = float(cf.get("liq", 0.0))
        creances = float(cf.get("creances", 0.0))
        dettes = float(cf.get("dettes", 0.0))

        # --- 📊 GRAPHE 1 VECTORIEL : RÉPARTITION DU PATRIMOINE ---
        canvas_patrimoine = cv.Canvas(height=70, expand=True, shapes=[])
        
        repartition_items = [
            (lib_g.get("immo", "Immo"), immo, "#064e3b"), 
            (lib_g.get("cash", "Cash"), liq, "#14b8a6"), 
            (lib_g.get("creance", "Cré."), creances, "#f59e0b"), 
            (lib_g.get("dettes", "Det."), dettes, "#b91c1c")
        ]
        
        valeur_maximale_actifs = max(immo, liq, creances, dettes, 1.0)
        
        # Tracé vectoriel de la ligne de sol (Baseline)
        canvas_patrimoine.shapes.append(cv.Line(5, 50, 280, 50, paint=ft.Paint(color=ft.Colors.GREY_400, stroke_width=1)))
        
        for i, (lbl, val, col) in enumerate(repartition_items):
            coord_x = 15 + (i * 65)
            hauteur_barre = (val / valeur_maximale_actifs) * 40
            
            # Dessin du rectangle de la barre comptable
            canvas_patrimoine.shapes.append(
                cv.Rect(x=coord_x, y=50-hauteur_barre, width=20, height=hauteur_barre, border_radius=2, paint=ft.Paint(color=col))
            )
            # 🎯 FIX TECHNIQUE : Utilisation de value= au lieu de text=
            canvas_patrimoine.shapes.append(
                cv.Text(x=coord_x+2, y=54, value=str(lbl), style=ft.TextStyle(size=8, color="#4b5563"))
            )
            
        self.colonne_cg_interne.controls.append(canvas_patrimoine)

        # --- 📿 GRAPHE 2 VECTORIEL : ÉVOLUTION DE L'INDICE SPIRITUEL ---
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
        
        # Tracé vectoriel de la ligne de sol (Baseline)
        canvas_spiritualite.shapes.append(cv.Line(5, 50, 280, 50, paint=ft.Paint(color=ft.Colors.GREY_400, stroke_width=1)))
        
        points_coordonnees = []
        for i in range(7):
            cx = 15 + (i * 38)
            cy = 45 - (scores_semaine[i] / 100.0 * 30)
            points_coordonnees.append((cx, cy))
            
            # Dessin de la puce (Ovale/Circle)
            canvas_spiritualite.shapes.append(cv.Circle(x=cx, y=cy, radius=2, paint=ft.Paint(color="#0369a1")))
            # 🎯 FIX TECHNIQUE : Utilisation de value= au lieu de text=
            canvas_spiritualite.shapes.append(cv.Text(x=cx-4, y=cy-12, value=f"{scores_semaine[i]:.0f}", style=ft.TextStyle(size=6, weight=ft.FontWeight.BOLD, color="#0369a1")))
            canvas_spiritualite.shapes.append(cv.Text(x=cx-2, y=54, value=str(j_traduits[i]), style=ft.TextStyle(size=8, color="#4b5563")))
            
        # Tracé des segments reliant les puces rituelles
        for i in range(len(points_coordonnees)-1):
            p1 = points_coordonnees[i]
            p2 = points_coordonnees[i+1]
            # 🎯 FIX TECHNIQUE : Passage des coordonnées directes de positionnement x1, y1, x2, y2
            canvas_spiritualite.shapes.append(
                cv.Line(
                    p1[0], p1[1], p2[0], p2[1],
                    paint=ft.Paint(color="#0369a1", stroke_width=1)
                )
            )
            
        self.colonne_cd_interne.controls.append(canvas_spiritualite)

        if self.page_flet:
            try: self.update()
            except Exception: pass

    def changer_langue(self, n_lang: str): 
        """Méthode invoquée par la propagation descendante du Layout central."""
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)
        self.actualiser_graphiques_vectoriels()
        
    def actualiser_donnees_affichage(self): 
        """Cycle de vie : Force la mise à jour complète à l'ouverture de l'écran."""
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)
        self.actualiser_graphiques_vectoriels()
        
        # Hydratation automatique par défaut sur le premier module de l'encyclopédie
        if self.categories_doc:
            self.on_selection_flet(0)

    def actualiser_contexte(self):
        """Alias pour le routeur central."""
        self.actualiser_donnees_affichage()
