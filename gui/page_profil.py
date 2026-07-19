"""
PANNEAU DE GESTION DE L'IDENTITÉ ET DU PROFIL UTILISATEUR (GUI/PAGE_PROFIL.PY)
Version 6.2 - Sécurisation de la date de naissance par triple Combobox et agencement responsive.
"""
import tkinter as tk
from tkinter import ttk
from gui.langues import DICTIONNAIRE_LANGUES

class PageProfil(tk.Frame):
    def __init__(self, parent, app_reference):
        super().__init__(parent, bg="#ffffff")
        self.app = app_reference
        self.mode_mobile = None
        
        # Liste des clés techniques du formulaire d'identité
        self.cles_champs = [
            "prenom", "nom", "username", "email", 
            "password", "confirm_password", "birth", 
            "tel", "pays", "ville", "profession"
        ]
        self.labels, self.entries = {}, {}
        
        DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_langue)
        self.construire_interface()

    def construire_interface(self):
        # 📂 BLOC STATUS DE SESSION
        self.c_status = tk.LabelFrame(self, font=("Helvetica", 9, "bold"), fg="#064e3b", bg="#ffffff", padx=10, pady=4)
        self.c_status.pack(fill="x", padx=15, pady=2)
        
        self.lbl_info_id = tk.Label(self.c_status, bg="#ffffff", font=("Helvetica", 9), fg="#4b5563")
        self.lbl_info_id.pack(anchor="w")
        self.lbl_info_sec = tk.Label(self.c_status, bg="#ffffff", font=("Helvetica", 9, "bold"), fg="#166534")
        self.lbl_info_sec.pack(anchor="w")

        # 📂 BLOC IDENTITÉ ET SÉCURITÉ NUMÉRIQUE
        self.c_identite = tk.LabelFrame(self, font=("Helvetica", 9, "bold"), fg="#064e3b", bg="#ffffff", padx=10, pady=6)
        self.c_identite.pack(fill="x", padx=15, pady=4)

        # Génération dynamique des zones de saisie
        for c in self.cles_champs:
            self.labels[c] = tk.Label(self.c_identite, bg="#ffffff", font=("Helvetica", 8, "bold"), fg="#4b5563")
            
            if c == "birth":
                # 🎯 SÉCURISATION DU SÉLECTEUR DE DATE : Remplacement de l'Entry par 3 Combobox
                self.c_date_triple = tk.Frame(self.c_identite, bg="#ffffff")
                
                self.cb_jour = ttk.Combobox(self.c_date_triple, values=[f"{i:02d}" for i in range(1, 32)], width=3, state="readonly")
                self.cb_jour.set("01")
                self.cb_jour.pack(side="left", padx=1)
                
                self.cb_mois = ttk.Combobox(self.c_date_triple, values=[f"{i:02d}" for i in range(1, 13)], width=3, state="readonly")
                self.cb_mois.set("01")
                self.cb_mois.pack(side="left", padx=1)
                
                self.cb_annee = ttk.Combobox(self.c_date_triple, values=[str(i) for i in range(1930, 2027)], width=5, state="readonly")
                self.cb_annee.set("2000")
                self.cb_annee.pack(side="left", padx=1)
                
                setattr(self, "en_birth", self.c_date_triple)
            else:
                show_char = "*" if c in ["password", "confirm_password"] else None
                self.entries[c] = tk.Entry(self.c_identite, font=("Arial", 10), bd=1, relief="solid", show=show_char)
                self.entries[c].insert(0, "-")
                setattr(self, f"en_{c}", self.entries[c])

        # Boutons d'actions réactifs
        self.btn_sauver = tk.Button(
            self, font=("Helvetica", 10, "bold"), bg="#064e3b", fg="white", bd=0, pady=6, cursor="hand2", command=self.sauvegarder_profil_disque
        )
        self.btn_sauver.pack(fill="x", padx=15, pady=4)

        self.btn_purger = tk.Button(
            self, font=("Helvetica", 9, "bold"), bg="#b91c1c", fg="white", bd=0, pady=5, cursor="hand2", command=self.purger_donnees_locales
        )
        self.btn_purger.pack(fill="x", padx=15, pady=4)

        # Zone de notification
        self.lbl_status = tk.Label(
            self, text="", font=("Helvetica", 9, "italic"), bg="#f3f4f6", fg="#4b5563", height=2
        )
        self.lbl_status.pack(fill="x", side="bottom")

        self.bind("<Configure>", lambda e: self.ordonner_layout(self.winfo_width() < 550))
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)

    def ordonner_layout(self, is_mobile):
        if is_mobile == self.mode_mobile: return
        self.mode_mobile = is_mobile
        
        for c in self.cles_champs: 
            self.labels[c].grid_forget()
            if c == "birth": self.c_date_triple.grid_forget()
            else: self.entries[c].grid_forget()

        if is_mobile:
            self.c_identite.grid_columnconfigure(0, weight=1)
            for idx, c in enumerate(self.cles_champs):
                self.labels[c].grid(row=idx*2, column=0, sticky="w", pady=(1, 0))
                widget_cible = self.c_date_triple if c == "birth" else self.entries[c]
                widget_cible.grid(row=idx*2+1, column=0, sticky="ew", pady=(0, 3))
        else:
            for idx, c in enumerate(self.cles_champs):
                r, col = divmod(idx, 2)
                self.c_identite.grid_columnconfigure(col*2+1, weight=1)
                self.labels[c].grid(row=r, column=col*2, sticky="w", padx=5, pady=4)
                widget_cible = self.c_date_triple if c == "birth" else self.entries[c]
                widget_cible.grid(row=r, column=col*2+1, sticky="ew", padx=10, pady=4)

    def action_langue(self, dic):
        if self.winfo_exists(): self.traduire_page(dic)

    def traduire_page(self, dic):
        """Met à jour dynamiquement tous les labels du formulaire depuis le JSON."""
        p = dic.get("profil", {})
        
        self.c_status.config(text=p.get("titre_vue", "Profil"))
        self.lbl_info_id.config(text=f"{p.get('lbl_identifiant', 'ID :')} {getattr(self.app, 'user_id_connecte', '-')}")
        self.lbl_info_sec.config(text=f"🛡️ {p.get('statut_connecte', 'Sécurisé')}")
        
        self.c_identite.config(text=p.get("lbl_statut_compte", "Formulaire"))
        self.btn_sauver.config(text=p.get("btn_sauvegarder", "Save"))
        self.btn_purger.config(text=p.get("btn_purger", "Purger"))

        mapping_labels_ihm = {
            "prenom": p.get("lbl_prenom", "Prénom :"),
            "nom": p.get("lbl_nom", "Nom :"),
            "username": p.get("lbl_username", "Utilisateur :"),
            "email": p.get("lbl_email", "Email :"),
            "password": p.get("lbl_password", "Mot de passe :"),
            "confirm_password": p.get("lbl_confirm_password", "Confirmation :"),
            "birth": p.get("lbl_birth", "Naissance :"),
            "tel": p.get("lbl_tel", "Téléphone :"),
            "pays": p.get("lbl_pays", "Pays :"),
            "ville": p.get("lbl_ville", "Ville :"),
            "profession": p.get("lbl_profession", "Profession :")
        }

        for k, text_traduit in mapping_labels_ihm.items():
            if k in self.labels:
                self.labels[k].config(text=text_traduit)

    def sauvegarder_profil_disque(self):
        """Enregistre l'ensemble des données d'identité dans l'espace chiffré et synchronise l'âge."""
        if not getattr(self.app, "est_mode_connecte", False):
            self.lbl_status.config(text="❌ Action impossible hors connexion.", bg="#fee2e2", fg="#991b1b")
            return
            
        try:
            u_id = self.app.user_id_connecte
            p = DICTIONNAIRE_LANGUES.actif.get("profil", {})
            
            # 1. Compilation des champs textes standard
            profil_dict = {c: self.entries[c].get().strip() for c in self.cles_champs if c in self.entries}
            
            # 2. Reconstitution de la date sécurisée depuis les 3 Combobox (Format AAAA-MM-DD)
            date_formatee = f"{self.cb_annee.get()}-{self.cb_mois.get()}-{self.cb_jour.get()}"
            profil_dict["birth"] = date_formatee
            
            # 3. Sauvegarde dans le SyncEngine pour le cache PROFIL
            if hasattr(self.app, "sync_engine") and self.app.sync_engine:
                self.app.sync_engine.executer_sauvegarde_module(u_id, "PROFIL", profil_dict)
            
            # =====================================================================
            # 🎯 4. DEBUT DE L'INSERTION SÉCURISÉE ET PROPRE DU CORRECTIF SQL
            # =====================================================================
            import sqlite3
            conn = sqlite3.connect("core/hayaati_private.db")
            cur = conn.cursor()
            
            # Mise à jour de la colonne native 'date_naissance' lue par l'Onboarding
            cur.execute("""
                UPDATE comptes_utilisateurs 
                SET date_naissance = ? 
                WHERE user_id = ?
            """, (date_formatee, str(u_id)))
            
            conn.commit()
            conn.close()
            # =====================================================================
            # 🎯 FIN DE L'INSERTION DU CORRECTIF SQL
            # =====================================================================
                
            self.lbl_status.config(text=p.get("status_ok_profil", "✓ Profil mis à jour."), bg="#d1fae5", fg="#064e3b")
            
            # Mise à jour des pointeurs de session globaux
            if "ville" in profil_dict: self.app.ville_utilisateur = profil_dict["ville"]
            if "pays" in profil_dict: self.app.pays_utilisateur = profil_dict["pays"]
            if "tel" in profil_dict: self.app.telephone_utilisateur = profil_dict["tel"]
            
            # Force l'application à recharger l'accueil et à recalculer l'âge hégirien immédiatement
            if hasattr(self.app, "declencher_changement_global"):
                self.app.declencher_changement_global()
                
        except Exception as e:
            self.lbl_status.config(text=f"❌ Erreur : {e}", bg="#fee2e2", fg="#991b1b")

    def purger_donnees_locales(self):
        if hasattr(self.app, "executer_deconnexion_session"):
            self.app.executer_deconnexion_session()

    def changer_langue(self, n_lang):
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)

    def actualiser_donnees_affichage(self):
        """Recharge les informations de l'auditeur et synchronise le sélecteur de date."""
        self.lbl_status.config(text="", bg="#f3f4f6", fg="#4b5563")
        if getattr(self.app, "est_mode_connecte", False) and getattr(self.app, "sync_engine", None):
            donnees_profil = self.app.sync_engine.charger_donnees_module(self.app.user_id_connecte, "PROFIL")
            
            # Injection dans les champs textes standard
            for c in self.cles_champs:
                if c != "birth" and c in donnees_profil and c in self.entries:
                    self.entries[c].delete(0, tk.END)
                    self.entries[c].insert(0, str(donnees_profil.get(c, "-")))
            
            # Découpage et réinjection de la date mémorisée dans les Combobox
            date_sauvegardee = donnees_profil.get("birth", "2000-01-01")
            if "-" in date_sauvegardee and len(date_sauvegardee.split("-")) == 3:
                aaaa, mm, jj = date_sauvegardee.split("-")
                if aaaa in self.cb_annee["values"]: self.cb_annee.set(aaaa)
                if mm in self.cb_mois["values"]: self.cb_mois.set(mm)
                if jj in self.cb_jour["values"]: self.cb_jour.set(jj)
                    
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)
