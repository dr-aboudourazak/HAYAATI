"""
PAGE DE RÉGLAGES ET CONFIGURATION DE SESSION
Version 6.7 - Alignement total des guides textuels absents et éradication complète des chaînes figées.
"""
import tkinter as tk
from tkinter import ttk
import sqlite3
from gui.langues import DICTIONNAIRE_LANGUES

class PageReglages(tk.Frame):
    def __init__(self, parent, app_reference):
        super().__init__(parent, bg="#ffffff")
        self.app = app_reference
        self.mode_mobile = None
        self.map_nisab_trad_vers_cle = {}
        self.map_nisab_cle_vers_trad = {}
        DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_changement_langue)
        self.construire_interface()

    def construire_interface(self):
        self.c_pref = tk.LabelFrame(self, bg="#ffffff", padx=10, pady=4)
        self.c_pref.pack(fill="x", padx=15, pady=2)

        # 🎯 AJOUT DES LIBELLÉS DE GUIDAGE EXPLICITES INTERNES EXIGÉS PAR L'AUDIT
        self.lbl_guide_devise = tk.Label(self.c_pref, bg="#ffffff", font=("Helvetica", 9))
        self.cb_devise = ttk.Combobox(self.c_pref, values=["XOF", "FCFA", "EUR", "SAR", "USD"], width=8, state="readonly")
        
        self.lbl_guide_langue = tk.Label(self.c_pref, bg="#ffffff", font=("Helvetica", 9))
        m_index = DICTIONNAIRE_LANGUES.moteur_i18n.langues_disponibles_index
        self.cb_langue = ttk.Combobox(self.c_pref, values=list(m_index.keys()), width=8, state="readonly")
        
        self.lbl_guide_fiqh = tk.Label(self.c_pref, bg="#ffffff", font=("Helvetica", 9))
        self.cb_fiqh = ttk.Combobox(self.c_pref, width=12, state="readonly")
        
        self.lbl_guide_nisab = tk.Label(self.c_pref, bg="#ffffff", font=("Helvetica", 9))
        self.cb_nisab = ttk.Combobox(self.c_pref, width=16, state="readonly")
        
        # 🌐 Récupération des valeurs d'initialisation stables de l'application
        self.cb_devise.set(self.app.devise_active)
        self.cb_langue.set(self.app.langue_actuelle)

        # 🎯 CURSEUR EXPLICITE GRADUÉ (-2, -1, 0, 1, 2)
        self.c_lunaire = tk.Frame(self.c_pref, bg="#ffffff")
        self.lbl_ajust = tk.Label(self.c_lunaire, bg="#ffffff", font=("Helvetica", 9, "bold"), fg="#d97706")
        self.sc_ajustement = tk.Scale(self.c_lunaire, from_=-2, to=2, orient="horizontal", tickinterval=1, resolution=1, showvalue=True, bg="#ffffff", bd=0, highlightthickness=0, font=("Arial", 9), troughcolor="#f3f4f6", activebackground="#064e3b")

        ajust_pref = 0; nisab_pref = "PLUS_BAS"
        if hasattr(self.app, "sync_engine") and self.app.sync_engine:
            c_p = self.app.sync_engine.charger_donnees_module(getattr(self.app, "user_id_connecte", None), "PREFERENCES")
            ajust_pref = int(c_p.get("ajustement_hegiri", 0))
            nisab_pref = str(c_p.get("arbitrage_nisab", "PLUS_BAS")).upper()
        self.sc_ajustement.set(ajust_pref)

        self.btn_sauver_pref = tk.Button(self.c_pref, font=("Helvetica", 9, "bold"), bg="#064e3b", fg="white", bd=0, pady=5, command=self.sauvegarder_preferences_disque)

        self.c_feed = tk.LabelFrame(self, bg="#ffffff", padx=10, pady=4)
        self.c_feed.pack(fill="x", padx=15, pady=2); self.c_feed.grid_columnconfigure(0, weight=1)

        self.lbl_note = tk.Label(self.c_feed, bg="#ffffff", font=("Helvetica", 9))
        self.combo_etoiles = ttk.Combobox(self.c_feed, values=["5 ★", "4 ★", "3 ★", "2 ★", "1 ★"], width=6, state="readonly")
        self.combo_etoiles.set("5 ★")
        
        self.lbl_suggestions = tk.Label(self.c_feed, bg="#ffffff", font=("Helvetica", 9))
        self.txt_commentaire = tk.Text(self.c_feed, font=("Arial", 9), bd=1, relief="solid", wrap=tk.WORD, height=2, width=20)
        self.btn_send_feed = tk.Button(self.c_feed, font=("Helvetica", 9, "bold"), bg="#0f766e", fg="white", bd=0, pady=4, command=self.traiter_envoi_feedback)

        self.c_deconnexion = tk.Frame(self, bg="#ffffff")
        self.c_deconnexion.pack(fill="x", padx=15, pady=2)
        self.btn_deconnexion = tk.Button(self.c_deconnexion, font=("Helvetica", 9, "bold"), bg="#b91c1c", fg="white", bd=0, pady=5, cursor="hand2", command=self.app.executer_deconnexion_session)

        self.lbl_status = tk.Label(self, text="", font=("Helvetica", 9, "italic"), bg="#f3f4f6", fg="#4b5563", height=2)
        self.lbl_status.pack(fill="x", side="bottom")

        self.cle_nisab_active_memoire = nisab_pref
        self.bind("<Configure>", lambda e: self.ordonner_layout(self.winfo_width() < 500))
        
        # 🔄 Traduction et application instantanée des dictionnaires
        self.traduire_page(getattr(self.app, "langue_active", DICTIONNAIRE_LANGUES.actif))

    def ordonner_layout(self, is_mobile):
        if is_mobile == self.mode_mobile: return
        self.mode_mobile = is_mobile
        for w in self.c_pref.winfo_children() + self.c_feed.winfo_children() + self.c_deconnexion.winfo_children(): w.grid_forget()
        self.btn_deconnexion.pack_forget(); is_connecte = getattr(self.app, "est_mode_connecte", False)

        if is_mobile:
            self.c_pref.grid_columnconfigure(0, weight=1)
            self.lbl_guide_devise.grid(row=0, column=0, sticky="w")
            self.cb_devise.grid(row=1, column=0, sticky="ew", pady=(0,4))
            self.lbl_guide_langue.grid(row=2, column=0, sticky="w")
            self.cb_langue.grid(row=3, column=0, sticky="ew", pady=(0,4))
            self.lbl_guide_fiqh.grid(row=4, column=0, sticky="w")
            self.cb_fiqh.grid(row=5, column=0, sticky="ew", pady=(0,4))
            self.lbl_guide_nisab.grid(row=6, column=0, sticky="w")
            self.cb_nisab.grid(row=7, column=0, sticky="ew", pady=(0,4))
            self.c_lunaire.grid(row=8, column=0, sticky="ew", pady=2); self.lbl_ajust.pack(anchor="w"); self.sc_ajustement.pack(fill="x", pady=1)
            self.btn_sauver_pref.grid(row=9, column=0, sticky="ew", pady=4)
            
            self.lbl_note.grid(row=0, column=0, sticky="w")
            self.combo_etoiles.grid(row=1, column=0, sticky="w", pady=(0,4))
            self.lbl_suggestions.grid(row=2, column=0, sticky="w")
            self.txt_commentaire.grid(row=3, column=0, sticky="ew", pady=(0,4))
            self.btn_send_feed.grid(row=4, column=0, sticky="ew", pady=4)
            if is_connecte: self.btn_deconnexion.pack(fill="x", pady=5)
        else:
            self.c_pref.grid_columnconfigure(0, weight=1)
            self.lbl_guide_devise.grid(row=0, column=0, sticky="w", padx=5)
            self.cb_devise.grid(row=1, column=0, padx=5, pady=(0,4), sticky="ew")
            self.lbl_guide_langue.grid(row=0, column=1, sticky="w", padx=5)
            self.cb_langue.grid(row=1, column=1, padx=5, pady=(0,4), sticky="ew")
            self.lbl_guide_fiqh.grid(row=0, column=2, sticky="w", padx=5)
            self.cb_fiqh.grid(row=1, column=2, padx=5, pady=(0,4), sticky="ew")
            self.lbl_guide_nisab.grid(row=0, column=3, sticky="w", padx=5)
            self.cb_nisab.grid(row=1, column=3, padx=5, pady=(0,4), sticky="ew")
            self.c_lunaire.grid(row=2, column=0, columnspan=4, sticky="ew", padx=5, pady=4); self.lbl_ajust.pack(side="left", padx=5); self.sc_ajustement.pack(side="left", fill="x", expand=True, padx=5)
            self.btn_sauver_pref.grid(row=3, column=0, columnspan=4, sticky="ew", pady=5)
            
            self.lbl_note.grid(row=0, column=0, sticky="w", padx=5)
            self.combo_etoiles.grid(row=0, column=1, sticky="w", padx=5, pady=4)
            self.lbl_suggestions.grid(row=1, column=0, sticky="w", padx=5)
            self.txt_commentaire.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=4)
            self.btn_send_feed.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=4)
            if is_connecte: self.btn_deconnexion.pack(side="right", padx=5, pady=5)

    def action_changement_langue(self, nuevo_dic):
        if self.winfo_exists(): self.traduire_page(nuevo_dic)

    def traduire_page(self, dic):
        r, b_j = dic.get("reglages", {}), dic.get("barre_outils", {})
        self.c_pref.config(text=r.get("cadre_pref", "Preferences"))
        self.lbl_ajust.config(text=r.get("lunaire_lbl", "Ajustement Lune (Jours) :"))
        self.btn_sauver_pref.config(text=r.get("btn_sauver_pref", "Save"))
        self.btn_deconnexion.config(text=b_j.get("btn_deconnexion", "🚪 Déconnexion"))
        self.c_feed.config(text=r.get("cadre_feed", "Feedback"))
        self.btn_send_feed.config(text=r.get("btn_soumettre", "Submit"))
        
        # Injection dynamique des guides textuels pour l'IHM
        self.lbl_guide_devise.config(text=r.get("lbl_guide_devise", "Devise :"))
        self.lbl_guide_langue.config(text=r.get("lbl_guide_langue", "Langue :"))
        self.lbl_guide_fiqh.config(text=r.get("lbl_guide_fiqh", "Fiqh :"))
        self.lbl_guide_nisab.config(text=r.get("lbl_guide_nisab", "Nisab :"))
        self.lbl_note.config(text=r.get("note_lbl", "Note :"))
        self.lbl_suggestions.config(text=r.get("lbl_commentaires", "Suggestions :"))

        # 🎯 ALIGNEMENT I18N FIQH SANS CHAÎNE BRUTE CORROMPUE
        ecoles_trad_json = b_j.get("ecoles", {})
        options_fiqh_techniques = ["Malikite", "Hanafite", "Chafiite", "Hanbalite"]
        
        map_cle_vers_trad_fiqh = {c: ecoles_trad_json.get(c, c) for c in options_fiqh_techniques}
        self.map_fiqh_trad_vers_cle = {str(v).strip().upper(): k for k, v in map_cle_vers_trad_fiqh.items()}
        
        self.cb_fiqh.config(values=list(map_cle_vers_trad_fiqh.values()))
        
        # On force l'affichage du libellé traduit de la nouvelle langue cible
        fiqh_pur = getattr(self.app, "madhhab_actif", "Malikite")
        if fiqh_pur == "Chafi'ite": fiqh_pur = "Chafiite"
        
        self.cb_fiqh.set(map_cle_vers_trad_fiqh.get(fiqh_pur, fiqh_pur))

        # 🎯 RECTIFICATION NISAB
        self.map_nisab_trad_vers_cle.clear()
        self.map_nisab_cle_vers_trad.clear()
        options_cles = ["PLUS_BAS", "OR", "ARGENT"]
        
        opt_nisab = dic.get("zakat", {}).get("options_nisab", {})
        if not opt_nisab: opt_nisab = r.get("options_nisab", {}) # Sécurité double compartiment JSON
        
        trads = {
            "PLUS_BAS": opt_nisab.get("nisab_plus_bas", opt_nisab.get("PLUS_BAS", "Baromètre Prudent (Plus Bas)")),
            "OR": opt_nisab.get("nisab_or", opt_nisab.get("OR", "Seuil de l'Or (85g)")),
            "ARGENT": opt_nisab.get("nisab_argent", opt_nisab.get("ARGENT", "Seuil de l'Argent (595g)"))
        }
        
        liste_valeurs_traduites = []
        for c in options_cles:
            txt_t = trads[c]
            self.map_nisab_trad_vers_cle[str(txt_t).strip().upper()] = c
            self.map_nisab_cle_vers_trad[c] = txt_t
            liste_valeurs_traduites.append(txt_t)
            
        self.cb_nisab.config(values=liste_valeurs_traduites)
        
        # 🎯 VERROU DE TRADUCTION À LA VOLÉE : Lecture unifiée sur l'application racine
        cle_pure = getattr(self.app, "cle_nisab_active_memoire", getattr(self, "cle_nisab_active_memoire", "PLUS_BAS"))
        label_a_remettre = self.map_nisab_cle_vers_trad.get(cle_pure, liste_valeurs_traduites[0])
        self.cb_nisab.set(label_a_remettre)

    def sauvegarder_preferences_disque(self):
        if not getattr(self.app, "est_mode_connecte", False): return
        u = self.app.user_id_connecte
        d = self.cb_devise.get()
        l = self.cb_langue.get()
        
        # 🎯 SÉCURITÉ FIQH SÉCURISÉE PAR MAP LOCAL
        trad_fiqh_choisie = str(self.cb_fiqh.get()).strip().upper()
        f = getattr(self, "map_fiqh_trad_vers_cle", {}).get(trad_fiqh_choisie)
        
        if not f:
            cles_techniques_possibles = ["MALIKITE", "HANAFITE", "CHAFIITE", "HANBALITE"]
            if trad_fiqh_choisie in cles_techniques_possibles:
                f = trad_fiqh_choisie.capitalize()
            else:
                dictionnaires_a_tester = [getattr(self.app, "langue_active", {}), DICTIONNAIRE_LANGUES.actif]
                if hasattr(DICTIONNAIRE_LANGUES, "dictionnaires"): 
                    dictionnaires_a_tester.extend(DICTIONNAIRE_LANGUES.dictionnaires.values())
                
                for dict_langue in dictionnaires_a_tester:
                    if not isinstance(dict_langue, dict): continue
                    ecoles = dict_langue.get("barre_outils", {}).get("ecoles", {})
                    for cle_tech, nom_traduit in ecoles.items():
                        if str(nom_traduit).strip().upper() == trad_fiqh_choisie:
                            f = cle_tech
                            break
                    if f: break

        if not f: f = getattr(self.app, "madhhab_actif", "Malikite")
        if f == "Chafi'ite": f = "Chafiite"
        
        # 🎯 SÉCURISATION INTER-MODULES : Extraction et affectation à la racine de self.app
        trad_nisab_choisi = str(self.cb_nisab.get()).strip().upper()
        cle_nisab = getattr(self, "map_nisab_trad_vers_cle", {}).get(trad_nisab_choisi, "PLUS_BAS")
        
        # Double verrouillage d'affectation pour qu'interface_zakat.py lise la vraie clé
        self.cle_nisab_active_memoire = cle_nisab
        self.app.cle_nisab_active_memoire = cle_nisab

        # 🎯 SÉCURITÉ NISAB SECURISEE PAR MAP LOCAL
        trad_nisab_choisi = str(self.cb_nisab.get()).strip().upper()
        cle_nisab = getattr(self, "map_nisab_trad_vers_cle", {}).get(trad_nisab_choisi)
        
        if not cle_nisab:
            if trad_nisab_choisi in ["PLUS_BAS", "OR", "ARGENT"]:
                cle_nisab = trad_nisab_choisi
            else:
                for dict_langue in [getattr(self.app, "langue_active", {}), DICTIONNAIRE_LANGUES.actif]:
                    if not isinstance(dict_langue, dict): continue
                    opt_n = dict_langue.get("zakat", {}).get("options_nisab", dict_langue.get("reglages", {}).get("options_nisab", {}))
                    for cle_n, nom_n_traduit in opt_n.items():
                        if str(nom_n_traduit).strip().upper() == trad_nisab_choisi:
                            cle_nisab = cle_n
                            break
                    if cle_nisab: break
                
        if not cle_nisab: cle_nisab = "PLUS_BAS"
        
        # 🎯 VERROU INTER-MODULES : Double affectation sur l'instance locale et l'application racine
        self.cle_nisab_active_memoire = cle_nisab
        self.app.cle_nisab_active_memoire = cle_nisab

        if hasattr(self.app, "sync_engine") and self.app.sync_engine:
            pref = self.app.sync_engine.charger_donnees_module(u, "PREFERENCES")
            if not isinstance(pref, dict): pref = {}
            pref["ajustement_hegiri"] = int(self.sc_ajustement.get())
            pref["arbitrage_nisab"] = cle_nisab
            self.app.sync_engine.executer_sauvegarde_module(u, "PREFERENCES", pref)

        if hasattr(self.app, "controleur_auth") and self.app.controleur_auth:
            dt_naiss = "2000-01-01"
            try:
                conn = sqlite3.connect("core/hayaati_private.db"); cur = conn.cursor()
                cur.execute("SELECT date_naissance FROM comptes_utilisateurs WHERE user_id = ?", (str(u),))
                row = cur.fetchone(); conn.close()
                if row and row[0]: dt_naiss = row[0]
            except Exception: pass
            
            # Envoi de la clé technique pure validée
            succes, _ = self.app.controleur_auth.sauvegarder_preferences_reglages(u, dt_naiss, d, l, f)
            if succes:
                self.app.devise_active, self.app.langue_actuelle, self.app.madhhab_actif = d, l, f
                
                # Application du changement de langue global
                if hasattr(self.app, "changer_langue_globale"):
                    self.app.changer_langue_globale(l)
                else:
                    DICTIONNAIRE_LANGUES.moteur_i18n.charger_dictionnaire_langue(l)
                    if hasattr(self.app, "declencher_changement_global"): self.app.declencher_changement_global()
                
                # 🌐 Récupération immédiate du dictionnaire i18n nouvellement chargé
                nouvelle_langue = getattr(self.app, "langue_active", DICTIONNAIRE_LANGUES.actif)
                
                # 🔄 Déclenchement de la traduction complète de la page (Fiqh, Nisab et composants d'IHM)
                self.traduire_page(nouvelle_langue)

                # 🔄 Notification immédiate des en-têtes de rapports connectés
                if hasattr(self.app, "interface_zakat") and self.app.interface_zakat:
                    try: self.app.interface_zakat.actualiser_contexte()
                    except Exception: pass
                    
                if hasattr(self.app, "interface_heritage") and self.app.interface_heritage:
                    try: self.app.interface_heritage.actualiser_contexte()
                    except Exception: pass
                
                if hasattr(self, "actualiser_langue_interface"):
                    try: self.actualiser_langue_interface()
                    except Exception: pass
                
                r_t = DICTIONNAIRE_LANGUES.actif.get("reglages", {})
                self.lbl_status.config(text=r_t.get("status_ok_pref", "✓ Paramètres sauvegardés."), bg="#d1fae5", fg="#064e3b")

    def traiter_envoi_feedback(self):
        if not getattr(self.app, "est_mode_connecte", False): return
        com = self.txt_commentaire.get("1.0", tk.END).strip(); r = DICTIONNAIRE_LANGUES.actif.get("reglages", {})
        if not com:
            self.lbl_status.config(text=r.get("err_feed_vide", "❌ Les commentaires ne peuvent pas être vides."), bg="#fee2e2", fg="#991b1b"); return
        if hasattr(self.app, "controleur_auth") and self.app.controleur_auth:
            note_entiere = int(self.combo_etoiles.get()[0])
            succes, _ = self.app.controleur_auth.enregistrer_feedback_utilisateur(self.app.user_id_connecte, note_entiere, com)
            if succes:
                self.lbl_status.config(text=r.get("status_ok_feed", "✓ Avis enregistré."), bg="#d1fae5", fg="#064e3b")
                self.txt_commentaire.delete("1.0", tk.END)

    def changer_langue(self, n_lang): 
        langue_cible = getattr(self.app, "langue_active", DICTIONNAIRE_LANGUES.actif)
        self.traduire_page(langue_cible)

    def actualiser_donnees_affichage(self):
        self.cb_devise.set(self.app.devise_active)
        self.cb_langue.set(self.app.langue_actuelle)
        
        if hasattr(self.app, "sync_engine") and self.app.sync_engine:
            c_p = self.app.sync_engine.charger_donnees_module(getattr(self.app, "user_id_connecte", None), "PREFERENCES")
            self.sc_ajustement.set(int(c_p.get("ajustement_hegiri", 0)))
            
            # 🎯 SECURISATION DU CHARGEMENT : Alimentation simultanée lors du chargement des préférences
            cle_chargee = str(c_p.get("arbitrage_nisab", "PLUS_BAS")).upper()
            self.cle_nisab_active_memoire = cle_chargee
            self.app.cle_nisab_active_memoire = cle_chargee
        
        # 🔄 Reconfiguration multilingue de la ComboBox
        langue_cible = getattr(self.app, "langue_active", DICTIONNAIRE_LANGUES.actif)
        self.traduire_page(langue_cible)
        
        self.mode_mobile = None
        self.ordonner_layout(self.winfo_width() < 500)
