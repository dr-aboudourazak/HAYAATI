"""
CENTRE D'AUDIT ET GRAPHES VECTORIELS (GUI/INTERFACE_AUDIT.PY)
Version 15.7 - Architecture structurelle fixe et routage i18n étanche.
"""
import tkinter as tk
from tkinter import ttk
from gui.langues import DICTIONNAIRE_LANGUES

class InterfaceAudit(ttk.Frame):
    def __init__(self, parent, app_reference):
        super().__init__(parent)
        self.app = app_reference
        self.mode_mobile = None
        self.categories_doc = []
        
        # Structure des composants graphiques persistants
        self.c_g = None
        self.c_d = None
        self.tree_modules = None
        self.text_preuves = None
        
        DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_langue)
        self.bind("<Configure>", self.ordonner_layout)

    def ordonner_layout(self, event=None):
        if event is not None and hasattr(event, "widget") and event.widget != self: return
        
        largeur_fenetre = self.winfo_width()
        if largeur_fenetre <= 1: return
        
        is_m = largeur_fenetre < 600
        if is_m == self.mode_mobile and len(self.winfo_children()) > 0: return
        self.mode_mobile = is_m
        
        # Nettoyage et reconstruction propre de la vue
        for w in self.winfo_children(): w.destroy()
        
        dic = DICTIONNAIRE_LANGUES.actif
        a, enc = dic.get("audit", {}), dic.get("encyclopedie", {})
        self.categories_doc = enc.get("categories", [])

        # 1. EN-TÊTE : ZONE DES COMPOSANTS GRAPHES GRAPHISMES
        cadre_s = tk.Frame(self, bg="#ffffff")
        cadre_s.pack(fill="x", padx=10, pady=2)
        
        self.c_g = tk.LabelFrame(cadre_s, text=a.get("titre_graphique_repartition", "📊 Solvabilité"), font=("Helvetica", 8, "bold"), fg="#064e3b", bg="#ffffff", padx=5)
        self.c_d = tk.LabelFrame(cadre_s, text=a.get("titre_graphique_evolution", "📿 Tendance"), font=("Helvetica", 8, "bold"), fg="#064e3b", bg="#ffffff", padx=5)

        if is_m:
            self.c_g.pack(fill="x", pady=1); self.c_d.pack(fill="x", pady=1)
        else:
            self.c_g.pack(side="left", fill="both", expand=True, padx=2)
            self.c_d.pack(side="right", fill="both", expand=True, padx=2)

        # 2. SECTEUR ENCYCLOPÉDIE ET RECHERCHE
        w_t = max(200, largeur_fenetre - 20)
        tk.Label(self, text=enc.get("titre", "Encyclopédie"), font=("Helvetica", 9, "bold"), bg="#ffffff", fg="#064e3b", wraplength=w_t).pack(pady=2, anchor="w", padx=10)
        
        if "consigne" in enc:
            tk.Label(self, text=enc["consigne"], font=("Helvetica", 8, "italic"), bg="#ffffff", fg="#4b5563", wraplength=w_t).pack(pady=(0, 2), anchor="w", padx=10)
            
        c_enc = tk.Frame(self, bg="#ffffff")
        c_enc.pack(fill="both", expand=True, padx=10, pady=2)

        hauteur_grille = 6 if is_m else 10
        largeur_colonne = max(180, largeur_fenetre - 40) if is_m else 320

        cadre_selecteur = tk.Frame(c_enc, bg="#ffffff")
        if not is_m: cadre_selecteur.config(width=largeur_colonne)

        style_tree = ttk.Style()
        style_tree.configure("Audit.Treeview", font=("Helvetica", 9), rowheight=22)
        style_tree.layout("Audit.Treeview", [('Audit.Treeview.treearea', {'sticky': 'nswe'})])

        self.tree_modules = ttk.Treeview(cadre_selecteur, columns=("titre"), show="tree", style="Audit.Treeview", height=hauteur_grille)
        self.tree_modules.column("#0", width=largeur_colonne, minwidth=150, stretch=True)
        
        scroll_l = ttk.Scrollbar(cadre_selecteur, orient="vertical", command=self.tree_modules.yview)
        self.tree_modules.configure(yscrollcommand=scroll_l.set)
        
        self.tree_modules.pack(fill="both", expand=True, side="left")
        scroll_l.pack(side="right", fill="y")

        self.text_preuves = tk.Text(c_enc, wrap=tk.WORD, font=("Helvetica", 9), bg="#fcfcfc", bd=1, relief="solid", height=5)
        scroll_t = ttk.Scrollbar(c_enc, orient="vertical", command=self.text_preuves.yview)
        self.text_preuves.configure(yscrollcommand=scroll_t.set)

        if is_m:
            cadre_selecteur.pack(fill="x", side="top", pady=(0, 6))
            self.text_preuves.pack(fill="both", expand=True, side="bottom")
        else:
            cadre_selecteur.pack(fill="y", side="left")
            cadre_selecteur.pack_propagate(False)
            scroll_l.pack(side="left", fill="y", padx=(0, 4))
            self.text_preuves.pack(fill="both", expand=True, side="left")
            scroll_t.pack(side="right", fill="y")

        self.tree_modules.bind("<<TreeviewSelect>>", self.on_selection)
        
        for i, c in enumerate(self.categories_doc): 
            self.tree_modules.insert("", tk.END, iid=str(i), text=c.get("titre", f"Module {i+1}"))
            
        if self.categories_doc: 
            self.tree_modules.selection_set("0")
            self.on_selection(None)
            
        # Appel déguisé de la seconde partie isolée
        self.actualiser_graphiques_vectoriels()

    def on_selection(self, event):
        if not self.categories_doc or not self.tree_modules: return
        sel = self.tree_modules.selection()
        idx = int(sel[0]) if sel else 0
        
        if idx < len(self.categories_doc) and self.text_preuves:
            self.text_preuves.configure(state=tk.NORMAL)
            self.text_preuves.delete("1.0", tk.END)
            self.text_preuves.insert(tk.END, self.categories_doc[idx].get("texte", ""))
            self.text_preuves.configure(state=tk.DISABLED)

    def actualiser_graphiques_vectoriels(self):
        """Calcule les indicateurs comptables et trace les graphiques vectoriels multilingues."""
        if not hasattr(self, "c_g") or self.c_g is None or not self.c_g.winfo_exists(): return
        for w in self.c_g.winfo_children() + self.c_d.winfo_children(): w.destroy()
        
        w_can = max(240, (self.winfo_width() // 2) - 20 if not self.mode_mobile else self.winfo_width() - 40)

        # Extraction sécurisée des sous-blocs i18n
        dic = DICTIONNAIRE_LANGUES.actif
        a = dic.get("audit", {})
        lib_g = a.get("libelles_graphe", {})
        js = a.get("jours_semaine", {})

        if not getattr(self.app, "est_mode_connecte", False):
            w = dic.get("onboarding", {}).get("guide_visiteur_humain", "🔒 Anonyme")
            for c in [self.c_g, self.c_d]: 
                tk.Label(c, text=w, font=("Arial", 8), bg="#ffffff", fg="#b91c1c").pack(pady=5)
            return

        u = self.app.user_id_connecte
        cf = self.app.sync_engine.charger_donnees_module(u, "FINANCES")
        cs = self.app.sync_engine.charger_donnees_module(u, "MOUHASABAH")

        immo = float(cf.get("immo", 0.0))
        liq = float(cf.get("liq", 0.0))
        creances = float(cf.get("creances", 0.0))
        dettes = float(cf.get("dettes", 0.0))

        # --- GRAPHE 1 : RÉPARTITION DU PATRIMOINE ---
        can_p = tk.Canvas(self.c_g, width=w_can, height=65, bg="#f9fafb", highlightthickness=0)
        can_p.pack(anchor="center")
        
        ct = [
            (lib_g.get("immo", "Immo"), immo, "#064e3b"), 
            (lib_g.get("cash", "Cash"), liq, "#14b8a6"), 
            (lib_g.get("creance", "Cré."), creances, "#f59e0b"), 
            (lib_g.get("dettes", "Det."), dettes, "#b91c1c")
        ]
        m_v = max(immo, liq, creances, dettes, 1.0)
        for i, (lbl, val, col) in enumerate(ct):
            x = 10 + (i * (w_can // 4))
            h = (val / m_v) * 40
            can_p.create_rectangle(x, 45-h, x+18, 45, fill=col, width=0)
            can_p.create_text(x+9, 55, text=lbl, font=("Arial", 7), fill="#4b5563")
        can_p.create_line(5, 45, w_can-5, 45, fill="#9ca3af")

        # --- GRAPHE 2 : ÉVOLUTION DE L'INDICE SPIRITUEL ---
        can_s = tk.Canvas(self.c_d, width=w_can, height=65, bg="#f9fafb", highlightthickness=0)
        can_s.pack(anchor="center")
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
        
        pts = []
        for i in range(7):
            cx = 15 + (i * (w_can // 7))
            cy = 40 - (scores_semaine[i] / 100.0 * 32)
            pts.append((cx, cy))
            
            can_s.create_oval(cx-1.5, cy-1, cx+1.5, cy+1, fill="#0369a1")
            can_s.create_text(cx, cy - 6, text=f"{scores_semaine[i]:.0f}", font=("Arial", 6, "bold"), fill="#0369a1")
            can_s.create_text(cx, 55, text=j_traduits[i], font=("Arial", 7), fill="#4b5563")
            
        for i in range(len(pts)-1): can_s.create_line(pts[i], pts[i+1], fill="#0369a1", width=1)
        can_s.create_line(5, 45, w_can-5, 45, fill="#9ca3af")

    def action_langue(self, dic):
        if self.winfo_exists(): 
            self.mode_mobile = None
            self.ordonner_layout()
            
    def changer_langue(self, n_lang): 
        self.action_langue(DICTIONNAIRE_LANGUES.actif)
        
    def actualiser_donnees_affichage(self): 
        self.mode_mobile = None
        self.ordonner_layout()
