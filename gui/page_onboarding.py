"""
PANNEAU D'ACCUEIL INTERACTIF CONNECTÉ (GUI/PAGE_ONBOARDING.PY)
Version 8.4 - Aimation géométrique en arrière-plan, cartes à effet de profondeur et i18n synchrone.
"""
import tkinter as tk
from tkinter import ttk
from gui.page_onboarding_alerts import compiler_alertes_espace_prive
from gui.langues import DICTIONNAIRE_LANGUES
from gui import ressources_visuelles

class PageOnboarding(tk.Frame):
    def __init__(self, parent, app_reference):
        # Fond blanc pur de base
        super().__init__(parent, bg="#ffffff")
        self.app = app_reference
        self.mode_smartphone_interne = None
        
        # Initialisation du Canevas d'Arrière-plan pour l'animation et le filigrane géométrique
        self.canevas_fond = tk.Canvas(self, bg="#ffffff", bd=0, highlightthickness=0)
        self.canevas_fond.pack(fill="both", expand=True)
        
        # Zone dynamique flottante superposée au canevas
        self.zone_dynamique = tk.Frame(self.canevas_fond, bg="#ffffff")
        self.id_zone = self.canevas_fond.create_window((0, 0), window=self.zone_dynamique, anchor="nw")
        
        DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_changement_langue)
        self.bind("<Configure>", self.on_redimensionnement_fenetre)
        self.actualiser_contexte()

    def action_changement_langue(self, nouveau_dictionnaire):
        if self.winfo_exists(): self.actualiser_contexte()

    def actualiser_contexte(self):
        for w in self.zone_dynamique.winfo_children(): w.destroy()
        if getattr(self.app, "est_mode_connecte", False): self.rendre_tableau_de_bord_connecte()
        else: self.rendre_page_vitrine_visiteur()

    def rendre_tableau_de_bord_connecte(self):
        u_id = self.app.user_id_connecte
        dev = getattr(self.app, "devise_active", "XOF")
        fiqh = getattr(self.app, "madhhab_actif", "Malikite")
        
        txt_onb = DICTIONNAIRE_LANGUES.actif.get("onboarding", {})
        txt_zk = DICTIONNAIRE_LANGUES.actif.get("zakat", {})

        c_fin = self.app.sync_engine.charger_donnees_module(u_id, "FINANCES")
        c_sp = self.app.sync_engine.charger_donnees_module(u_id, "MOUHASABAH")
        c_arb = self.app.sync_engine.charger_donnees_module(u_id, "PROFIL")
        c_pref = self.app.sync_engine.charger_donnees_module(u_id, "PREFERENCES")

        ajust_hegiri = int(c_pref.get("ajustement_hegiri", 0))

        # Évaluation patrimoniale
        val_grain = float(c_fin.get("poids", 0.0)) * float(c_fin.get("grain_cours", 0.0))
        val_ovin = float(c_fin.get("ovins", 0)) * float(c_fin.get("ovin_cours", 0.0))
        val_bovin = float(c_fin.get("bovins", 0)) * float(c_fin.get("bovin_cours", 0.0))
        total_agro = val_grain + val_ovin + val_bovin

        brut = float(c_fin.get("immo", 0)) + float(c_fin.get("auto", 0)) + float(c_fin.get("liq", 0)) + float(c_fin.get("creances", 0)) + total_agro
        net = brut - float(c_fin.get("dettes", 0))
        score = c_sp.get("score_spirituel", 0)

        nom_c = f"{c_arb.get('prenom', '')} {c_arb.get('nom', '')}".strip()
        if not nom_c or nom_c == "- -": nom_c = self.app.nom_utilisateur_connecte

        bienvenue_fmt = txt_onb.get("bienvenue", "Assalâmou Alaykoum, {} 🌟").format(nom_c.upper())
        sous_titre_fmt = txt_onb.get("sous_titre", "Rapport de vigilance doctrinale — École {}").format(fiqh)

        # En-tête aérée et premium
        tk.Label(self.zone_dynamique, text=bienvenue_fmt, font=("Helvetica", 14, "bold"), fg="#064e3b", bg="#ffffff").pack(anchor="w", padx=20, pady=(15, 2))
        tk.Label(self.zone_dynamique, text=sous_titre_fmt, font=("Helvetica", 9, "italic"), fg="#4b5563", bg="#ffffff").pack(anchor="w", padx=20, pady=(0, 10))

        self.c_grid = tk.Frame(self.zone_dynamique, bg="#ffffff")
        self.c_grid.pack(fill="x", padx=15, pady=2)

        # 🎯 RACCOURCISSEMENT ET ÉTANCHÉITÉ COMPLÈTE : Lecture des deux mots maximum depuis le dictionnaire JSON
        cours_or_db = float(c_fin.get("or_cours", 45000.0))
        nisab_or_calcul_sec = 85.0 * cours_or_db
        if net >= nisab_or_calcul_sec:
            statut_zakat_traduit = txt_zk.get('statut_eligible', '🔴 IMPOSABLE')
            couleur_statut_zakat = "#b91c1c"
        else:
            statut_zakat_traduit = txt_zk.get('statut_non_eligible', '🟢 EXEMPTÉ')
            couleur_statut_zakat = "#166534"

        # Métriques structurées
        self.metrics_data = [
            (txt_onb.get("titre_fortune", " 💰 Fortune Nette "), f"{net:.2f} {dev}", "#f0fdf4", "#166534"),
            (txt_onb.get("titre_zakat", " 🏦 Statut Zakat "), statut_zakat_traduit, "#fffbeb", couleur_statut_zakat),
            (txt_onb.get("titre_mouhasabah", " 📿 Indice Spirituel "), f"{score}%", "#f0f9ff", "#0369a1")
        ]
        
        self.mode_smartphone_interne = None
        self.ordonner_grille_metrics()
        self.poursuivre_construction_alertes(c_fin, c_sp, net, dev, fiqh, u_id, ajust_hegiri, txt_onb)

    def poursuivre_construction_alertes(self, c_fin, c_sp, net, dev, fiqh, u_id, ajust_hegiri, txt_onb):
        """Construit les volets d'alertes avec une typographie aérée à interligne élargi."""
        txt_pr, txt_cal, color_bg, color_fg = compiler_alertes_espace_prive(
            c_fin, c_sp, net, dev, fiqh, user_id=u_id, ajustement_lune=ajust_hegiri
        )

        prefixe_date = txt_onb.get("date_prefixe", "Date : ")
        txt_cal_complet = f"{prefixe_date}{txt_cal}"

        # --- BLOC PRIÈRES : Cadre et Zone de texte à interligne aéré ---
        self.c_prieres = tk.LabelFrame(
            self.zone_dynamique, text=txt_onb.get("cadre_prieres", " 🕋 Prières Échues "), 
            font=("Helvetica", 9, "bold"), fg="#b91c1c", bg="#ffffff", padx=12, pady=8
        )
        self.c_prieres.pack(fill="x", padx=20, pady=6)
        
        # Utilisation de tk.Text pour contrôler l'interligne de façon premium
        self.txt_view_prieres = tk.Text(
            self.c_prieres, font=("Helvetica", 10), bg=color_bg, fg=color_fg, 
            bd=0, highlightthickness=0, wrap=tk.WORD, height=3, padx=8, pady=6,
            spacing3=8  # 🎯 COHÉRENCE ET CONFORT : Ajoute de l'espace généreux après chaque ligne
        )
        self.txt_view_prieres.insert("1.0", txt_pr)
        self.txt_view_prieres.config(state=tk.DISABLED)
        self.txt_view_prieres.pack(fill="x")

        # --- BLOC CALENDRIER : Cadre et Zone de texte à interligne aéré ---
        self.c_calendrier = tk.LabelFrame(
            self.zone_dynamique, text=txt_onb.get("cadre_calendrier", " 🌙 Chronologie Sacrée "), 
            font=("Helvetica", 9, "bold"), fg="#d97706", bg="#ffffff", padx=12, pady=8
        )
        self.c_calendrier.pack(fill="both", expand=True, padx=20, pady=6)
        
        self.txt_view_calendrier = tk.Text(
            self.c_calendrier, font=("Helvetica", 10), bg="#fdfbf7", fg="#1f2937", 
            bd=0, highlightthickness=0, wrap=tk.WORD, height=10, padx=8, pady=6,
            spacing3=8  # 🎯 INTERLIGNE ÉLARGIE : Lecture claire des recommandations de Fiqh
        )
        self.txt_view_calendrier.insert("1.0", txt_cal_complet)
        self.txt_view_calendrier.config(state=tk.DISABLED)
        self.txt_view_calendrier.pack(fill="both", expand=True)

        self.update_idletasks()
        self.on_redimensionnement_fenetre(None)

    def ordonner_grille_metrics(self):
        """Ordonne l'affichage des 3 indicateurs de fortune à effet de profondeur."""
        for w in self.c_grid.winfo_children(): w.destroy()
        largeur_actuelle = self.winfo_width()
        is_small = largeur_actuelle < 600 if largeur_actuelle > 1 else False

        if is_small:
            self.c_grid.columnconfigure(0, weight=1)
            for idx, (titre, val, bg_c, fg_c) in enumerate(self.metrics_data):
                card = tk.LabelFrame(self.c_grid, text=f" {titre} ", font=("Helvetica", 9, "bold"), fg="#064e3b", bg=bg_c, padx=6, pady=5, bd=1, relief="solid")
                card.grid(row=idx, column=0, padx=4, pady=3, sticky="ew")
                tk.Label(card, text=val, font=("Arial", 11, "bold"), fg=fg_c, bg=bg_c).pack()
        else:
            for idx, (titre, val, bg_c, fg_c) in enumerate(self.metrics_data):
                self.c_grid.columnconfigure(idx, weight=1)
                card = tk.LabelFrame(self.c_grid, text=f" {titre} ", font=("Helvetica", 9, "bold"), fg="#064e3b", bg=bg_c, padx=6, pady=6, bd=1, relief="solid")
                card.grid(row=0, column=idx, padx=5, pady=0, sticky="ew")
                tk.Label(card, text=val, font=("Arial", 12, "bold"), fg=fg_c, bg=bg_c).pack()

    def rendre_page_vitrine_visiteur(self):
        """Affiche le volet d'accueil premium pour les utilisateurs anonymes."""
        txt_auth = DICTIONNAIRE_LANGUES.actif.get("auth", {})
        txt_onb = DICTIONNAIRE_LANGUES.actif.get("onboarding", {})
        
        c_onb = tk.Frame(self.zone_dynamique, bg="#ffffff", padx=40, pady=25)
        c_onb.place(relx=0.5, rely=0.5, anchor="center")
        
        logo_img = ressources_visuelles.logo(taille=110)
        if logo_img:
            lbl_logo = tk.Label(c_onb, image=logo_img, bg="#ffffff")
            lbl_logo.image = logo_img  # référence conservée, sinon Tkinter la ramasse et le logo disparaît
            lbl_logo.pack(pady=(0, 8))
        else:
            tk.Label(c_onb, text=DICTIONNAIRE_LANGUES.actif.get("barre_outils", {}).get("titre_app", "Hayaati"), font=("Helvetica", 18, "bold"), fg="#064e3b", bg="#ffffff").pack()
        
        desc_humaine = txt_onb.get("guide_visiteur_humain", "Mode Simulation Tiers.")
        self.lbl_vitrine_desc = tk.Label(c_onb, text=desc_humaine, font=("Helvetica", 10), bg="#ffffff", fg="#374151", justify="center")
        self.lbl_vitrine_desc.pack(pady=12)

        c_buttons = tk.Frame(c_onb, bg="#ffffff")
        c_buttons.pack()
        tk.Button(c_buttons, text=txt_auth.get("deja_compte", " Se connecter"), font=("Helvetica", 10, "bold"), bg="#064e3b", fg="white", bd=0, padx=12, pady=6, cursor="hand2", command=lambda: self.app.basculer_ecran("CONNEXION")).pack(side="left", padx=6)
        tk.Button(c_buttons, text=txt_auth.get("pas_compte", " S'inscrire"), font=("Helvetica", 10, "bold"), bg="#0f766e", fg="white", bd=0, padx=12, pady=6, cursor="hand2", command=lambda: self.app.basculer_ecran("INSCRIPTION")).pack(side="left", padx=6)

    def on_redimensionnement_fenetre(self, event):
        """Recalcule la zone fluide et anime le filigrane géométrique d'arrière-plan."""
        largeur = self.winfo_width()
        hauteur = self.winfo_height()
        if largeur <= 1 or hauteur <= 1: return
        
        # Redimensionnement de la fenêtre interne flottante
        self.canevas_fond.itemconfig(self.id_zone, width=largeur, height=hauteur)
        
        # 🎨 CRÉATIVITÉ : Tracé dynamique d'un filigrane d'art arabo-andalou en arrière-plan
        self.canevas_fond.delete("filigrane")
        
        # Lignes géométriques fines en vert émeraude très estompé (translucide)
        color_filigrane = "#f3fdfa" 
        pas = max(40, largeur // 8)
        
        # Dessin de mailles losanges croisées en arrière-plan
        for i in range(0, largeur + pas, pas):
            self.canevas_fond.create_line(i, 0, i - hauteur, hauteur, fill=color_filigrane, width=1, tags="filigrane")
            self.canevas_fond.create_line(i, 0, i + hauteur, hauteur, fill=color_filigrane, width=1, tags="filigrane")
            
        # Re-superposition de la zone d'IHM au-dessus du tracé vectoriel
        self.canevas_fond.tag_raise(self.id_zone)
            
        nouveau_statut = largeur < 600
        if nouveau_statut != self.mode_smartphone_interne and getattr(self.app, "est_mode_connecte", False):
            self.mode_smartphone_interne = nouveau_statut
            self.ordonner_grille_metrics()

    def actualiser_donnees_affichage(self): 
        self.actualiser_contexte()
