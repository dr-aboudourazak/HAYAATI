"""
INTERFACE DIAGNOSTIC ZAKAT TIERS
Version 6.4 - Alignement i18n total du Nisab, du bétail, et mémorisation harmonisée de l'inventaire Live.
"""
import tkinter as tk
from tkinter import ttk
from gui.langues import DICTIONNAIRE_LANGUES
from core.certificate_engine import generer_certificat_pdf
from core.financial_engine import FinancialEngine

class EcranZakatTiers(tk.Frame):
    def __init__(self, parent, app_reference):
        super().__init__(parent, bg="#ffffff")
        self.app = app_reference
        self.mode_mobile = None
        self.moteur_zakat = FinancialEngine()
        self.intrants_mem, self.lignes_mem = {}, []
        self.map_nisab_trad_vers_cle = {}
        self.map_nisab_cle_vers_trad = {}
        
        # 🎯 HARMONISATION SECTIONS : Conteneurs mémoires calqués sur Zakat Live
        self.fortune_calculee = {"liq": 0.0, "or": 0.0, "argent": 0.0, "due": 0.0, "creances": 0.0, "dettes": 0.0}
        self.agri_calcule = {"poids": 0.0, "due": 0.0}
        self.pastoral_calcule = {"o": "0", "b": "0", "ovins": 0, "bovins": 0}

        self.cles_champs = [
            "liq", "stock", "creances", "dettes",
            "or_refuge_poids", "or_parure_poids", "or_cours",
            "argent_refuge_poids", "argent_parure_poids", "argent_cours",
            "poids", "ovins", "bovins"
        ]
        self.labels, self.entries = {}, {}
        m_i18n = DICTIONNAIRE_LANGUES.moteur_i18n
        m_i18n.abonner_au_changement_langue(self.action_langue)
        self.construire_interface()

    def construire_interface(self):
        self.c_principal = tk.Frame(self, bg="#ffffff")
        self.c_principal.pack(fill="x", padx=15, pady=4)

        # Zone d'identité enrichie avec le choix de Nisab autonome à l'écran
        self.c_nom = tk.Frame(self.c_principal, bg="#ffffff")
        self.c_nom.pack(fill="x", pady=2)
        
        self.lbl_nom = tk.Label(self.c_nom, bg="#ffffff", font=("Helvetica", 9, "bold"), fg="#d97706")
        self.lbl_nom.pack(side="left")
        
        self.en_nom_tiers = tk.Entry(self.c_nom, font=("Arial", 9), bd=1, relief="solid", width=14)
        self.en_nom_tiers.insert(0, "Fatoumata ")
        self.en_nom_tiers.pack(side="left", padx=4)

        self.cb_nisab_tiers = ttk.Combobox(self.c_nom, width=20, state="readonly")
        self.cb_nisab_tiers.pack(side="left", padx=10)

        # LabelFrames d'agencements structurels i18n
        self.c_f = tk.LabelFrame(self.c_principal, bg="#ffffff", padx=10, pady=4, fg="#d97706", font=("Helvetica", 9, "bold"))
        self.c_f.pack(fill="x", pady=3)
        self.c_m = tk.LabelFrame(self.c_principal, bg="#ffffff", padx=10, pady=4, fg="#d97706", font=("Helvetica", 9, "bold"))
        self.c_m.pack(fill="x", pady=3)
        self.c_a = tk.LabelFrame(self.c_principal, bg="#ffffff", padx=10, pady=4, fg="#d97706", font=("Helvetica", 9, "bold"))
        self.c_a.pack(fill="x", pady=3)

        for c in self.cles_champs:
            p_frame = self.c_m if ("or" in c or "argent" in c) else self.c_a if c in ["poids", "ovins", "bovins"] else self.c_f
            self.labels[c] = tk.Label(p_frame, bg="#ffffff", font=("Helvetica", 8, "bold"), fg="#4b5563")
            self.entries[c] = tk.Entry(p_frame, font=("Arial", 9), bd=1, relief="solid", width=8)
            self.entries[c].insert(0, "0")
            setattr(self, f"en_{c}", self.entries[c])

        self.en_or_cours.delete(0, tk.END); self.en_or_cours.insert(0, "45000")
        self.en_argent_cours.delete(0, tk.END); self.en_argent_cours.insert(0, "650")

        self.btn_calculer = tk.Button(self, font=("Helvetica", 10, "bold"), bg="#064e3b", fg="white", bd=0, pady=6, command=self.executer_calcul_tiers)
        self.btn_calculer.pack(fill="x", padx=15, pady=4)

        self.btn_pdf = tk.Button(self, font=("Helvetica", 10, "bold"), bg="#0f766e", fg="white", bd=0, pady=6, command=self.imprimer_pdf_tiers)
        self.btn_pdf.pack(fill="x", padx=15, pady=4)

        self.c_res = tk.LabelFrame(self, font=("Helvetica", 10, "bold"), fg="#064e3b", bg="#ffffff", padx=10, pady=6)
        self.c_res.pack(fill="both", expand=True, padx=15, pady=6)

        self.scr_txt = tk.Scrollbar(self.c_res)
        self.scr_txt.pack(side="right", fill="y")
        self.text_rapport = tk.Text(self.c_res, font=("Courier New", 10), bg="#f9fafb", bd=1, relief="solid", wrap=tk.WORD, height=8, yscrollcommand=self.scr_txt.set)
        self.text_rapport.pack(fill="both", expand=True); self.scr_txt.config(command=self.text_rapport.yview)

        self.bind("<Configure>", lambda e: self.ordonner_layout(self.winfo_width() < 550))
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)

    def ordonner_layout(self, is_mobile):
        if is_mobile == self.mode_mobile: return
        self.mode_mobile = is_mobile
        for c in self.cles_champs: self.labels[c].grid_forget(); self.entries[c].grid_forget()

        if is_mobile:
            for idx, c in enumerate(["liq", "stock", "creances", "dettes"]):
                self.c_f.grid_columnconfigure(0, weight=1)
                self.labels[c].grid(row=idx*2, column=0, sticky="w"); self.entries[c].grid(row=idx*2+1, column=0, sticky="ew")
            for idx, c in enumerate(["or_refuge_poids", "or_parure_poids", "or_cours", "argent_refuge_poids", "argent_parure_poids", "argent_cours"]):
                self.c_m.grid_columnconfigure(0, weight=1)
                self.labels[c].grid(row=idx*2, column=0, sticky="w"); self.entries[c].grid(row=idx*2+1, column=0, sticky="ew")
            for idx, c in enumerate(["poids", "ovins", "bovins"]):
                self.c_a.grid_columnconfigure(0, weight=1)
                self.labels[c].grid(row=idx*2, column=0, sticky="w"); self.entries[c].grid(row=idx*2+1, column=0, sticky="ew")
        else:
            for idx, c in enumerate(["liq", "stock", "creances", "dettes"]):
                r, col = divmod(idx, 2)
                self.labels[c].grid(row=r, column=col*2, sticky="w", padx=4, pady=3); self.entries[c].grid(row=r, column=col*2+1, padx=8, pady=3)
            
            metaux_ordonnes = [
                ("or_refuge_poids", 0, 0), ("or_parure_poids", 1, 0), ("or_cours", 2, 0),
                ("argent_refuge_poids", 0, 1), ("argent_parure_poids", 1, 1), ("argent_cours", 2, 1)
            ]
            for c, r, col in metaux_ordonnes:
                self.labels[c].grid(row=r, column=col*2, sticky="w", padx=4, pady=3); self.entries[c].grid(row=r, column=col*2+1, padx=8, pady=3)
                
            for idx, c in enumerate(["poids", "ovins", "bovins"]):
                r, col = divmod(idx, 2)
                self.labels[c].grid(row=r, column=col*2, sticky="w", padx=4, pady=3); self.entries[c].grid(row=r, column=col*2+1, padx=8, pady=3)

    def action_langue(self, dic):
        if self.winfo_exists(): self.traduire_page(dic)

    def traduire_page(self, dic):
        zk, p, fin, r = dic.get("zakat", {}), dic.get("pdf", {}), dic.get("finances", {}), dic.get("reglages", {})
        self.c_f.config(text=fin.get("cadre_liquide", "Finances"))
        self.c_m.config(text=fin.get("cadre_metaux", "Métaux"))
        self.c_a.config(text=fin.get("cadre_agropastoral", "Agro-Pastoral"))
        self.lbl_nom.config(text=p.get("tableau_part", "Bénéficiaire :"))
        self.btn_calculer.config(text=zk.get("btn_calculer", "Calculer"))
        self.btn_pdf.config(text=zk.get("btn_imprimer", "Générer PDF"))
        self.c_res.config(text=zk.get("cadre_analyse", "Verdict"))

        # Traduction réactive des avoirs financiers du tiers
        dict_labels_tiers = {
            "liq": fin.get("liq_lbl", "Liquidités :"),
            "stock": fin.get("auto_lbl", "Stocks :"),
            "creances": fin.get("creances_lbl", "Créances :"),
            "dettes": fin.get("dettes_lbl", "Dettes :")
        }
        for k in ["liq", "stock", "creances", "dettes"]:
            if k in self.labels: 
                self.labels[k].config(text=dict_labels_tiers[k])

        # 🎯 RECTIFICATION : Remplacement de l'anglais/français figé par les vraies variables du dictionnaire finances (fin)
        self.labels["or_refuge_poids"].config(text=fin.get("lbl_or_refuge", "Or Refuge (g) :"))
        self.labels["or_parure_poids"].config(text=fin.get("lbl_or_parures", "Or Parure (g) :"))
        self.labels["or_cours"].config(text=zk.get("lbl_cours_or", "Cours Or :"))
        self.labels["argent_refuge_poids"].config(text=fin.get("lbl_argent_refuge", "Argent Refuge (g) :"))
        self.labels["argent_parure_poids"].config(text=fin.get("lbl_argent_parures", "Argent Parure (g) :"))
        self.labels["argent_cours"].config(text=zk.get("lbl_cours_argent", "Cours Argent :"))
        self.labels["poids"].config(text=fin.get("lbl_grain", "Grains (kg) :"))
        self.labels["ovins"].config(text=fin.get("lbl_moutons", "Moutons :"))
        self.labels["bovins"].config(text=fin.get("lbl_bovins", "Bovins :"))

        memoire_nisab_local = self.cb_nisab_tiers.get()
        cle_technique_restauration = self.map_nisab_trad_vers_cle.get(memoire_nisab_local, "PLUS_BAS")
        self.map_nisab_trad_vers_cle.clear()
        options_cles = ["PLUS_BAS", "OR", "ARGENT"]
        
        # 🎯 RECTIFICATION DE L'INDEXATION : Lecture directe depuis le sous-bloc zk ("zakat") du JSON
        opt_nisab = zk.get("options_nisab", {})
        trads = {
            "PLUS_BAS": opt_nisab.get("nisab_plus_bas", "Baromètre Prudent"), 
            "OR": opt_nisab.get("nisab_or", "Seuil de l'Or (85g)"), 
            "ARGENT": opt_nisab.get("nisab_argent", "Seuil de l'Argent (595g)")
        }
        
        liste_valeurs_traduites = []
        for c in options_cles:
            txt_t = trads[c]
            self.map_nisab_trad_vers_cle[txt_t] = c
            liste_valeurs_traduites.append(txt_t)
            
        self.cb_nisab_tiers.config(values=liste_valeurs_traduites)
        self.cb_nisab_tiers.set(trads.get(cle_technique_restauration, liste_valeurs_traduites[0] if liste_valeurs_traduites else ""))

    def executer_calcul_tiers(self):
        try:
            dev = getattr(self.app, "devise_active", "XOF")
            doc = getattr(self.app, "madhhab_actif", "Malikite")
            
            langue_active = getattr(self.app, "langue_active", DICTIONNAIRE_LANGUES.actif)
            txt_zk = langue_active.get("zakat", {})
            txt_pdf = langue_active.get("pdf", {})
            txt_fin = langue_active.get("patrimoine", {})

            intrants = {c: float(self.entries[c].get().strip() or 0) for c in self.cles_champs}
            intrants["ovins"] = int(intrants["ovins"]); intrants["bovins"] = int(intrants["bovins"])
            intrants["arbitrage_nisab"] = self.map_nisab_trad_vers_cle.get(self.cb_nisab_tiers.get(), "PLUS_BAS")

            res = self.moteur_zakat.executer_audit_zakat_complet(
                mode_persistant=False, user_id=None, madhhab_actif=doc, cours_or_terrain=intrants["or_cours"], donnees_manuelles_tiers=intrants
            )

            # 🎯 STOCKAGE MÉMOIRE INTERNE POUR L'HARMONISATION DES SECTIONS
            self.fortune_calculee = {
                "liq": res.get("assiette_financiere_nette", 0.0),
                "or": res.get("valeur_or_retenue_zakat", 0.0),
                "argent": res.get("valeur_argent_retenue_zakat", 0.0),
                "due": res.get("zakat_monetaire_due", 0.0),
                "creances": intrants["creances"],
                "dettes": intrants["dettes"]
            }
            self.agri_calcule = {
                "poids": intrants["poids"],
                "due": res.get("zakat_agricole_due_kg", 0.0)
            }
            self.pastoral_calcule = {
                "o": res.get("obligation_ovins", "0"),
                "b": res.get("obligation_bovins", "0"),
                "ovins": res.get("brut_ovins", 0),
                "bovins": res.get("brut_bovins", 0)
            }

            # 🎯 APPLICATION DU FORMAT STRICT DE LA SECTION 1 DE ZAKAT LIVE
            # Les clés en majuscules techniques seront mappées par le dictionnaire du CertificatEngine
            p_or_poids = res.get("or_imposable_poids", 0.0)
            p_ag_poids = res.get("argent_imposable_poids", 0.0)
            
            self.intrants_mem = {
                "LIQUIDE": f"{self.fortune_calculee['liq']:.2f} {dev}",
                "OR": f"{self.fortune_calculee['or']:.2f} {dev} ({p_or_poids:.1f}g)",
                "ARGENT": f"{self.fortune_calculee['argent']:.2f} {dev} ({p_ag_poids:.1f}g)",
                "DETTES": f"-{self.fortune_calculee['dettes']:.2f} {dev}",
                "CREANCES": f"{self.fortune_calculee['creances']:.2f} {dev}",
                "AGRO": f"{self.agri_calcule['poids']:.1f} kg"
            }

            # 🎯 ALIGNEMENT DU RAPPORT ÉCRAN MULTILINGUE ET FIQH TRADUIT
            b_v = txt_zk.get("statut_eligible", "🟢 ÉLIGIBLE") if res["est_imposable_monetaire"] else txt_zk.get("statut_non_eligible", "🔴 EXEMPTÉ")
            titre_traduit = txt_zk.get("rapport_titre", "RAPPORT DE ZAKAT")
            
            lbl_m_ref = res['metal_seuil_reference']
            if "OR" in str(lbl_m_ref).upper():
                lbl_m_ref = txt_zk.get("options_nisab", {}).get("nisab_or", "Or")
            elif "ARGENT" in str(lbl_m_ref).upper():
                lbl_m_ref = txt_zk.get("options_nisab", {}).get("nisab_argent", "Argent")

            b_outils = langue_active.get("barre_outils", {})
            ecole_traduite = b_outils.get("ecoles", {}).get(doc, doc)

            # Remplissage du tableau de verdict vert épuré (Section 2 validée)
            self.lignes_mem = [
                [f"{txt_zk.get('assiette_imposable', 'Assiette')} : {self.fortune_calculee['liq']:.2f} {dev}"],
                [f"{txt_zk.get('montant_du', 'Zakat monétaire due')} (2.5%) : {self.fortune_calculee['due']:.2f} {dev}"],
                [f"{txt_zk.get('zakat_grain', 'Zakat Agricole')} : {self.agri_calcule['due']:.2f} kg"],
                [f"{txt_zk.get('zakat_moutons', 'Zakat Ovins')} : {self.pastoral_calcule['o']}"],
                [f"{txt_zk.get('zakat_bovins', 'Zakat Bovins')} : {self.pastoral_calcule['b']}"]
            ]
            
            # Format d'affichage visuel pour la zone de texte de l'écran principal
            lignes_visuelles_ecran = [
                f" 🕋 {titre_traduit} ({ecole_traduite.upper()}) :",
                f" ==================================================",
                f"   • {txt_zk.get('cadre_analyse', 'VERDICT').strip()} : {b_v}",
                f"   • {txt_zk.get('nisab_applique', 'NISAB')}   : {lbl_m_ref} ({res['nissab_monetaire_calcule']:.2f} {dev})",
                f"   • {self.lignes_mem[0][0]}",
                f"   • {self.lignes_mem[1][0]}",
                f"   • {self.lignes_mem[2][0]}",
                f"   • {self.lignes_mem[3][0]}",
                f"   • {self.lignes_mem[4][0]}",
            ]
            
            self.text_rapport.config(state=tk.NORMAL); self.text_rapport.delete("1.0", tk.END)
            self.text_rapport.insert("1.0", "\n".join(lignes_visuelles_ecran)); self.text_rapport.config(state=tk.DISABLED)
        except Exception as e:
            self.text_rapport.config(state=tk.NORMAL); self.text_rapport.delete("1.0", tk.END)
            self.text_rapport.insert("1.0", f"❌ : {e}"); self.text_rapport.config(state=tk.DISABLED)

    def imprimer_pdf_tiers(self):
        if not self.lignes_mem: return
        
        # 🌐 Reconstruction de la structure d'identité manuelle pour le tiers audité
        id_t = {"nom": self.en_nom_tiers.get().strip() or "Tiers", "prenom": "", "ville": "Saisie Manuelle", "pays": "Diagnostic", "telephone": "-"}
        
        # 🎯 SÉCURITÉ NISAB TIERS : Extraction du libellé exact affiché à l'écran (Ex: "Seuil de l'Or (85g)" ou sa traduction)
        nisab_choisi_texte = self.cb_nisab_tiers.get()
        
        # Transmission de l'inventaire Live, des lignes épurées vertes de Tiers et du baromètre extrait
        generer_certificat_pdf(
            id_t, 
            "ZAKAT", 
            getattr(self.app, "madhhab_actif", "Malikite"), 
            getattr(self.app, "devise_active", "XOF"), 
            self.intrants_mem, 
            self.lignes_mem,
            nisab_label=nisab_choisi_texte
        )

    def action_langue(self, dic):
        if self.winfo_exists(): self.traduire_page(dic)
        
    def changer_langue(self, n_lang): 
        self.traduire_page(getattr(self.app, "langue_active", DICTIONNAIRE_LANGUES.actif))
        
    def actualiser_donnees_affichage(self): 
        self.en_nom_tiers.delete(0, tk.END); self.en_nom_tiers.insert(0, "")
        for c in self.cles_champs:
            self.entries[c].delete(0, tk.END)
            self.entries[c].insert(0, "45000" if c=="or_cours" else "650" if c=="argent_cours" else "0")
        self.text_rapport.config(state=tk.NORMAL); self.text_rapport.delete("1.0", tk.END); self.text_rapport.config(state=tk.DISABLED)
        
    def actualiser_contexte(self): self.actualiser_donnees_affichage()
