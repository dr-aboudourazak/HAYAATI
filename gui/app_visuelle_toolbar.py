"""
BARRE D'OUTILS ET CONFIGURATEUR DE NAVIGATION (GUI/APP_VISUELLE_TOOLBAR.PY)
Version 3.3 - Alignement i18n complet, suppression des mentions '(Tiers)' codées en dur.
"""
import tkinter as tk
from tkinter import ttk
from gui import ressources_visuelles

def configurer_bandeau_superieur(app):
    """Dessine et gère les liaisons d'écouteurs de la barre supérieure i18n."""
    for w in app.barre_outils.winfo_children(): 
        w.destroy()

    barre_json = app.txt_global.get("barre_outils", {})
    is_m = app.mode_smartphone_actif if hasattr(app, 'mode_smartphone_actif') else False
    
    # 1. En-tête : Icône (le logo porte déjà le nom HAYAATI, inutile de le redoubler en texte)
    icone_img = ressources_visuelles.icone(taille=22 if is_m else 26)
    if icone_img:
        lbl_icone = tk.Label(app.barre_outils, image=icone_img, bg="#064e3b")
        lbl_icone.image = icone_img  # référence conservée, sinon Tkinter la ramasse et l'icône disparaît
        lbl_icone.pack(side="left", padx=(8, 5))
    else:
        titre_app = barre_json.get("titre_app", "🕌 HAYAATI")
        tk.Label(app.barre_outils, text=titre_app[:12] if is_m else titre_app, font=("Helvetica", 10 if is_m else 12, "bold"), fg="#ffffff", bg="#064e3b").pack(side="left", padx=5)

    statut_txt = f"👤 {app.nom_utilisateur_connecte}" if app.est_mode_connecte else barre_json.get("visiteur", "👤 Visiteur")
    tk.Label(app.barre_outils, text=statut_txt[:12] if is_m else statut_txt, font=("Helvetica", 8 if is_m else 9, "italic"), fg="#e5e7eb", bg="#064e3b").pack(side="left", padx=5)

    # 2. Bouton d'action unique de mode (Commutateur Live / Tiers sécurisé)
    if app.est_mode_connecte:
        txt_m = barre_json.get("mode_live", "🟢 Live") if app.mode_persistant_actif else barre_json.get("mode_tiers", "🟡 Tiers")
        bg_m = "#0f766e" if app.mode_persistant_actif else "#d97706"
        
        def on_bascule_bouton():
            if app.mode_persistant_actif:
                app.executer_deconnexion_session()
                return

            app.basculer_ecran("CONNEXION")
            if app.mode_persistant_actif:
                try:
                    import sqlite3
                    conn = sqlite3.connect("core/hayaati_private.db")
                    curseur = conn.cursor()
                    curseur.execute("SELECT devise_defaut, langue_defaut, fiqh_defaut FROM comptes_utilisateurs WHERE user_id = ?", (str(app.user_id_connecte),))
                    res = curseur.fetchone()
                    conn.close()
                    if res: 
                        app.devise_active, app.langue_actuelle, app.madhhab_actif = res[0], res[1], res[2]
                except Exception: 
                    pass
                app.ecran_courant = "ONBOARDING"
                app.changer_langue_globale(app.langue_actuelle)

        tk.Button(app.barre_outils, text=txt_m, font=("Helvetica", 8 if is_m else 9, "bold"), bg=bg_m, fg="white", bd=0, padx=4 if is_m else 10, pady=2, cursor="hand2", command=on_bascule_bouton).pack(side="left", padx=2)

    # 3. Zone des Préférences Doctrinales Déroulantes (À droite)
    cadre_combos = tk.Frame(app.barre_outils, bg="#064e3b")
    cadre_combos.pack(side="right", padx=5)

    # Passe en readonly si déconnecté, bloqué en disabled si connecté Live
    etat_menu = "disabled" if (app.est_mode_connecte and app.mode_persistant_actif) else "readonly"

    # Devise
    app.combo_devise = ttk.Combobox(cadre_combos, values=["XOF", "FCFA", "EUR", "SAR", "USD"], width=4, state=etat_menu)
    app.combo_devise.set(app.devise_active)
    app.combo_devise.pack(side="right", padx=1)
    app.combo_devise.bind("<<ComboboxSelected>>", lambda e: [setattr(app, "devise_active", app.combo_devise.get()), hasattr(app, 'declencher_changement_global') and app.declencher_changement_global()])

    # Langue
    app.combo_langue = ttk.Combobox(cadre_combos, values=["FR", "EN", "HA", "AR", "ES", "ZH"], width=3, state=etat_menu)
    app.combo_langue.set(app.langue_actuelle)
    app.combo_langue.pack(side="right", padx=1)
    app.combo_langue.bind("<<ComboboxSelected>>", lambda e: app.changer_langue_globale(app.combo_langue.get()))

    # Fiqh / Madhhab
    if not is_m:
        # Liste des clés de Fiqh inchangées pour le moteur de calcul
        options_fiqh_techniques = ["Malikite", "Hanafite", "Chafi'ite", "Hanbalite"]
        
        # 🎯 MAP DYNAMIQUE MULTILINGUE : On génère les labels affichés à partir du sous-bloc 'ecoles'
        ecoles_trad_json = barre_json.get("ecoles", {})
        map_cle_vers_trad_fiqh = {c: ecoles_trad_json.get(c, c) for c in options_fiqh_techniques}
        map_trad_vers_cle_fiqh = {v: k for k, v in map_cle_vers_trad_fiqh.items()}
        
        app.combo_fiqh = ttk.Combobox(cadre_combos, values=list(map_cle_vers_trad_fiqh.values()), width=10, state=etat_menu)
        
        # Affichage de l'école active traduit
        fiqh_pur = getattr(app, "madhhab_actif", "Malikite")
        app.combo_fiqh.set(map_cle_vers_trad_fiqh.get(fiqh_pur, fiqh_pur))
        app.combo_fiqh.pack(side="right", padx=1)
        
        def on_selection_fiqh(event):
            trad_choisie = app.combo_fiqh.get()
            cle_technique_brute = map_trad_vers_cle_fiqh.get(trad_choisie, "Malikite")
            setattr(app, "madhhab_actif", cle_technique_brute)
            if hasattr(app, 'declencher_changement_global'):
                app.declencher_changement_global()
                
        app.combo_fiqh.bind("<<ComboboxSelected>>", on_selection_fiqh)

def dessiner_boutons_navigation(app):
    """Génère l'affichage des menus de navigation latérale (PC) ou basse (Smartphone)."""
    for w in app.barre_navigation.winfo_children(): 
        w.destroy()
        
    menu_json = app.txt_global.get("menu", {})
    barre_json = app.txt_global.get("barre_outils", {})

    if app.mode_persistant_actif:
        # 🎯 RECTIFICATION : Réintégration de l'écran REGLAGES dans la Sidebar connectée
        boutons = [
            (menu_json.get("onboarding", "🏠 Accueil"), "ONBOARDING"), 
            (menu_json.get("finances", "💰 Patrimoine"), "FINANCES"),
            (menu_json.get("zakat", "🏦 Zakat"), "ZAKAT_LIVE"), 
            (menu_json.get("arbre", "👥 Famille"), "ARBRE"),
            (menu_json.get("heritage", "📜 Succession"), "HERITAGE_LIVE"), 
            (menu_json.get("testament", "📝 Testament"), "TESTAMENT"),
            (menu_json.get("mouhasabah", "📿 Mouhasabah"), "MOUHASABAH"), 
            (menu_json.get("audit", "📖 Audit"), "AUDIT"),
            (menu_json.get("encyclopedie", "📚 Encyclopédie"), "ENCYCLOPEDIE"),
            (menu_json.get("langue_arabe", "🔤 Langue arabe"), "LANGUE_ARABE"),
            (menu_json.get("profil", "👤 Profil"), "PROFIL"),
            (menu_json.get("reglages", "⚙️ Réglages"), "REGLAGES")
        ]
    else:
        lbl_zakat_tiers = f"{menu_json.get('zakat', '🏦 Zakat')} - {barre_json.get('mode_tiers', 'Simulation')}"
        lbl_heritage_tiers = f"{menu_json.get('heritage', '📜 Succession')} - {barre_json.get('mode_tiers', 'Simulation')}"
        
        boutons = [
            (menu_json.get("onboarding", "🏠 Accueil"), "ONBOARDING"),
            (lbl_zakat_tiers, "ZAKAT_TIERS"), 
            (lbl_heritage_tiers, "HERITAGE_TIERS"),
            (menu_json.get("encyclopedie", "📚 Encyclopédie"), "ENCYCLOPEDIE"),
            (menu_json.get("langue_arabe", "🔤 Langue arabe"), "LANGUE_ARABE")
        ]

    # --- FORMAT SMARTPHONE (BOTTOM NAV) ---
    if app.mode_smartphone_actif:
        defilement_h = tk.Canvas(app.barre_navigation, bg="#f3f4f6", height=50, bd=0, highlightthickness=0)
        barre_h = tk.Scrollbar(app.barre_navigation, orient="horizontal", command=defilement_h.xview)
        cadre_i = tk.Frame(defilement_h, bg="#f3f4f6")
        
        defilement_h.create_window((0, 0), window=cadre_i, anchor="nw")
        defilement_h.configure(xscrollcommand=barre_h.set)
        
        defilement_h.pack(fill="x", side="top")
        if len(boutons) > 4: 
            barre_h.pack(fill="x", side="bottom")

        for libelle, cle in boutons:
            lib_c = libelle.split(" ")[-1] if " " in libelle else libelle
            em = libelle.split(" ") if " " in libelle else "•"
            
            btn = tk.Button(cadre_i, text=f"{em}\n{lib_c}", font=("Helvetica", 8), fg="#1f2937", bg="#f3f4f6", bd=0, padx=4, pady=2, cursor="hand2", command=lambda c=cle: app.basculer_ecran(c))
            if app.ecran_courant == cle: 
                btn.config(bg="#e5e7eb", font=("Helvetica", 8, "bold"))
            btn.pack(side="left", fill="both", expand=True)

        cadre_i.bind("<Configure>", lambda e: defilement_h.configure(scrollregion=defilement_h.bbox("all")))
            
    # --- FORMAT PC DE BUREAU (SIDEBAR) ---
    else:
        tk.Frame(app.barre_navigation, bg="#f3f4f6", height=10).pack(fill="x")
        for libelle, cle in boutons:
            btn = tk.Button(app.barre_navigation, text=libelle, font=("Helvetica", 9), fg="#1f2937", bg="#f3f4f6", bd=0, anchor="w", padx=15, pady=5, activebackground="#e5e7eb", cursor="hand2", command=lambda c=cle: app.basculer_ecran(c))
            if app.ecran_courant == cle: 
                btn.config(bg="#d1d5db", font=("Helvetica", 9, "bold"))
            btn.pack(fill="x", pady=1)
