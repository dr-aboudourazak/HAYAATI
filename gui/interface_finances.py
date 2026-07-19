"""
INTERFACE MATRICE DU PATRIMOINE GLOBAL LIVE (PARTIE 1)
Version 6.3 - Initialisation, agencement des cadres et grille responsive sécurisée.
"""
import tkinter as tk
from datetime import datetime
from gui.langues import DICTIONNAIRE_LANGUES

class EcranFinances(tk.Frame):
    def __init__(self, parent, app_reference):
        super().__init__(parent, bg="#ffffff")
        self.app = app_reference
        self.mode_mobile = None
        
        # Clés techniques indispensables au moteur de calcul
        self.cles = [
            "immo", "auto", "liq", "creances", "dettes",
            "or_refuge_poids", "or_parure_poids", "or_cours", 
            "argent_refuge_poids", "argent_parure_poids", "argent_cours",
            "poids", "grain_cours", "ovins", "ovin_cours", "bovins", "bovin_cours"
        ]
        self.labels, self.entries = {}, {}
        self.construire_interface()

    def construire_interface(self):
        self.c_principal = tk.Frame(self, bg="#ffffff")
        self.c_principal.pack(fill="x", padx=15, pady=5)

        # 📂 BLOC 1 : LIQUIDITÉS, AVOIRS IMMOBILIERS & DETTES
        self.c_avoirs = tk.LabelFrame(self.c_principal, font=("Helvetica", 9, "bold"), fg="#064e3b", bg="#ffffff", padx=10, pady=4)
        self.c_avoirs.pack(fill="x", pady=4)

        # 📂 BLOC 2 : INVENTAIRE DES MÉTAUX PRÉCIEUX DÉCOUPLÉS
        self.c_metaux = tk.LabelFrame(self.c_principal, font=("Helvetica", 9, "bold"), fg="#064e3b", bg="#ffffff", padx=10, pady=4)
        self.c_metaux.pack(fill="x", pady=4)

        # 📂 BLOC 3 : INVENTAIRE ET COURS AGRO-PASTORAUX
        self.c_agro = tk.LabelFrame(self.c_principal, font=("Helvetica", 9, "bold"), fg="#064e3b", bg="#ffffff", padx=10, pady=4)
        self.c_agro.pack(fill="x", pady=4)

        # Génération dynamique des entrées et étiquettes
        for c in self.cles:
            if "or" in c or "argent" in c:
                p_frame = self.c_metaux
            elif c in ["poids", "grain_cours", "ovins", "ovin_cours", "bovins", "bovin_cours"]:
                p_frame = self.c_agro
            else:
                p_frame = self.c_avoirs

            self.labels[c] = tk.Label(p_frame, bg="#ffffff", font=("Helvetica", 8, "bold"), fg="#4b5563")
            self.entries[c] = tk.Entry(p_frame, font=("Arial", 10), bd=1, relief="solid", width=9)
            self.entries[c].insert(0, "0")
            setattr(self, f"en_{c}", self.entries[c])

        self.btn_sauver = tk.Button(self, font=("Helvetica", 10, "bold"), bg="#064e3b", fg="white", bd=0, pady=6, cursor="hand2", command=self.sauvegarder)
        self.btn_sauver.pack(fill="x", padx=15, pady=4)

        self.cadre_res = tk.LabelFrame(self, font=("Helvetica", 9, "bold"), fg="#064e3b", bg="#ffffff", padx=5, pady=5)
        self.cadre_res.pack(fill="both", expand=True, padx=15, pady=4)
        self.text_hist = tk.Text(self.cadre_res, wrap=tk.WORD, font=("Arial", 9), bg="#f9fafb", bd=1, height=4)
        self.text_hist.pack(fill="both", expand=True)

        self.bind("<Configure>", lambda e: self.ordonner_layout(self.winfo_width() < 550))
        self.traduire(DICTIONNAIRE_LANGUES.actif)

    def ordonner_layout(self, is_mobile):
        if is_mobile == self.mode_mobile: return
        self.mode_mobile = is_mobile
        for c in self.cles: self.labels[c].grid_forget(); self.entries[c].grid_forget()

        if is_mobile:
            self.c_avoirs.grid_columnconfigure(0, weight=1)
            for idx, c in enumerate(["immo", "auto", "liq", "creances", "dettes"]):
                self.labels[c].grid(row=idx*2, column=0, sticky="w", pady=(1, 0))
                self.entries[c].grid(row=idx*2+1, column=0, sticky="ew", pady=(0, 3))
                
            self.c_metaux.grid_columnconfigure(0, weight=1)
            for idx, c in enumerate(["or_refuge_poids", "or_parure_poids", "or_cours", "argent_refuge_poids", "argent_parure_poids", "argent_cours"]):
                self.labels[c].grid(row=idx*2, column=0, sticky="w", pady=(1, 0))
                self.entries[c].grid(row=idx*2+1, column=0, sticky="ew", pady=(0, 3))
                
            self.c_agro.grid_columnconfigure(0, weight=1)
            for idx, c in enumerate(["poids", "grain_cours", "ovins", "ovin_cours", "bovins", "bovin_cours"]):
                self.labels[c].grid(row=idx*2, column=0, sticky="w", pady=(1, 0))
                self.entries[c].grid(row=idx*2+1, column=0, sticky="ew", pady=(0, 3))
        else:
            for idx, c in enumerate(["immo", "auto", "liq", "creances", "dettes"]):
                r, col = divmod(idx, 2)
                self.labels[c].grid(row=r, column=col*2, sticky="w", padx=4, pady=3)
                self.entries[c].grid(row=r, column=col*2+1, sticky="w", padx=10, pady=3)
            
            metaux_ordonnes = [
                ("or_refuge_poids", 0, 0), ("or_parure_poids", 1, 0), ("or_cours", 2, 0),
                ("argent_refuge_poids", 0, 1), ("argent_parure_poids", 1, 1), ("argent_cours", 2, 1)
            ]
            for c, r, col in metaux_ordonnes:
                self.labels[c].grid(row=r, column=col*2, sticky="w", padx=4, pady=3)
                self.entries[c].grid(row=r, column=col*2+1, sticky="w", padx=10, pady=3)
                
            for idx, c in enumerate(["poids", "grain_cours", "ovins", "ovin_cours", "bovins", "bovin_cours"]):
                r, col = divmod(idx, 2)
                self.labels[c].grid(row=r, column=col*2, sticky="w", padx=4, pady=3)
                self.entries[c].grid(row=r, column=col*2+1, sticky="w", padx=10, pady=3)

    def action_langue(self, dic):
        if self.winfo_exists(): self.traduire(dic)

    def traduire(self, dic):
        f, z = dic.get("finances", {}), dic.get("zakat", {})
        self.c_avoirs.config(text=f.get("cadre_liquide", "Patrimoine"))
        self.c_metaux.config(text=f.get("cadre_metaux", "Métaux"))
        self.c_agro.config(text=f.get("cadre_agropastoral", "Élevage"))
        self.btn_sauver.config(text=f.get("btn_sauvegarder", "Enregistrer"))
        self.cadre_res.config(text=dic.get("audit", {}).get("titre_graphique_evolution", "History"))
        
        # 🎯 RECTIFICATION DES CLÉS : Utilisation des VRAIES clés i18n ajoutées au JSON
        dict_labels = {
            "immo": f.get("immo_lbl", "Immobilisations / Terrains :"), 
            "auto": f.get("auto_lbl", "Actifs Mobiliers / Véhicules :"), 
            "liq": f.get("liq_lbl", "Disponibilités Cash / Comptes :"), 
            "creances": f.get("creances_lbl", "Créances Actives Recouvrables :"), 
            "dettes": f.get("dettes_lbl", "Passif Exigible / Dettes :")
        }
        
        # Application directe des libellés financiers i18n (L'écrasement k.upper() a été supprimé)
        for k in ["immo", "auto", "liq", "creances", "dettes"]:
            self.labels[k].config(text=dict_labels[k])
        
        # Alignement réactif sur la matrice des métaux précieux
        self.labels["or_refuge_poids"].config(text=f.get("lbl_or_refuge", "Or Refuge (g) :"))
        self.labels["or_parure_poids"].config(text=f.get("lbl_or_parures", "Or Parure (g) :"))
        self.labels["or_cours"].config(text=z.get("lbl_cours_or", "Cours Or :"))
        self.labels["argent_refuge_poids"].config(text=f.get("lbl_argent_refuge", "Argent Refuge (g) :"))
        self.labels["argent_parure_poids"].config(text=f.get("lbl_argent_parures", "Argent Parure (g) :"))
        self.labels["argent_cours"].config(text=z.get("lbl_cours_argent", "Cours Argent :"))
        
        # Alignement réactif sur le secteur Agro-Pastoral et Élevage
        self.labels["poids"].config(text=f.get("lbl_grain", "Grain (Kg) :"))
        self.labels["grain_cours"].config(text=f.get("valeur_grain", "Cours :"))
        self.labels["ovins"].config(text=f.get("lbl_moutons", "Moutons :"))
        self.labels["ovin_cours"].config(text=f.get("valeur_moutons", "Cours :"))
        self.labels["bovins"].config(text=f.get("lbl_bovins", "Bovins :"))
        self.labels["bovin_cours"].config(text=f.get("valeur_bovins", "Cours :"))

    def sauvegarder(self):
        try:
            v = {c: float(self.entries[c].get() or 0) for c in self.cles}
            v["or_poids"] = v["or_refuge_poids"] + v["or_parure_poids"]
            v["argent_poids"] = v["argent_refuge_poids"] + v["argent_parure_poids"]
            
            val_or = v["or_poids"] * v["or_cours"]
            val_arg = v["argent_poids"] * v["argent_cours"]
            v["or"] = val_or
            
            val_grain = v["poids"] * v["grain_cours"]
            val_ovin = v["ovins"] * v["ovin_cours"]
            val_bovin = v["bovins"] * v["bovin_cours"]
            total_agro = val_grain + val_ovin + val_bovin
            
            brut = v["immo"] + v["auto"] + v["liq"] + val_or + val_arg + v["creances"] + total_agro
            net = brut - v["dettes"]
            dev = getattr(self.app, "devise_active", "XOF")
            
            ligne = f"📅 [{datetime.now().strftime('%d/%m/%Y %H:%M')}] - Net: {net:.2f} {dev}\n"
            self.text_hist.insert("1.0", ligne)

            if getattr(self.app, "est_mode_connecte", False) and getattr(self.app, "sync_engine", None):
                v["historique"] = self.text_hist.get("1.0", tk.END)
                self.app.sync_engine.executer_sauvegarde_module(self.app.user_id_connecte, "FINANCES", v)
                self.app.sync_engine.executer_sauvegarde_module(self.app.user_id_connecte, "ZAKAT", v)
        except Exception: pass

    def injecter_donnees(self, data):
        if not data: return
        for c in self.cles:
            if c in data:
                self.entries[c].delete(0, tk.END)
                self.entries[c].insert(0, str(data.get(c, 0)))
        
        if "or_refuge_poids" in self.entries and float(self.entries["or_refuge_poids"].get() or 0) == 85.0:
            if "or_refuge_poids" not in data:
                self.entries["or_refuge_poids"].delete(0, tk.END)
                self.entries["or_refuge_poids"].insert(0, "0")

        self.text_hist.delete("1.0", tk.END)
        self.text_hist.insert("1.0", data.get("historique", ""))

    def changer_langue(self, n_lang): 
        self.traduire(DICTIONNAIRE_LANGUES.actif)
        
    def actualiser_donnees_affichage(self):
        if getattr(self.app, "est_mode_connecte", False) and getattr(self.app, "sync_engine", None):
            self.injecter_donnees(self.app.sync_engine.charger_donnees_module(self.app.user_id_connecte, "FINANCES"))
