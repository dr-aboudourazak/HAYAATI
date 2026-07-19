"""
PAGE DE CONNEXION ET CERTIFICATION DOCTRINALE CINKASSÉ
Version 6.1 - Traduction à la volée et éradication complète des statuts figés.
"""
import tkinter as tk
from tkinter import ttk
from gui.langues import DICTIONNAIRE_LANGUES

class PageConnexion(tk.Frame):
    def __init__(self, parent, app_reference):
        super().__init__(parent, bg="#ffffff")
        self.app = app_reference
        
        # 🎯 ABONNEMENT DIRECT AU MOTEUR I18N POUR LA TRADUCTION À LA VOLÉE
        DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_changement_langue)
        self.construire_interface()

    def construire_interface(self):
        self.c_conteneur = tk.Frame(self, bg="#ffffff", padx=30, pady=15)
        self.c_conteneur.place(relx=0.5, rely=0.5, anchor="center")

        self.lbl_titre = tk.Label(self.c_conteneur, font=("Helvetica", 14, "bold"), fg="#064e3b", bg="#ffffff")
        self.lbl_titre.pack(pady=(0, 10))

        # 🎯 LE PANNEAU DE BIENVENUE ANNONÇANT LA VALIDATION DE CINKASSÉ AU TOGO
        self.c_annonce_officielle = tk.LabelFrame(self.c_conteneur, bg="#f9fafb", padx=10, pady=8, fg="#d97706", font=("Helvetica", 8, "bold"))
        self.c_annonce_officielle.pack(fill="x", pady=(0, 15))
        
        self.lbl_bienvenue_conseil = tk.Label(self.c_annonce_officielle, font=("Helvetica", 9), bg="#f9fafb", fg="#374151", justify="center", wrap=340)
        self.lbl_bienvenue_conseil.pack(fill="x")

        # Formulaire de saisie standard de session
        self.lbl_user = tk.Label(self.c_conteneur, font=("Helvetica", 9, "bold"), bg="#ffffff", fg="#4b5563")
        self.lbl_user.pack(anchor="w", pady=(4, 0))
        self.en_login = tk.Entry(self.c_conteneur, font=("Arial", 10), bd=1, relief="solid", width=26)
        self.en_login.pack(pady=(0, 8))

        self.lbl_pass = tk.Label(self.c_conteneur, font=("Helvetica", 9, "bold"), bg="#ffffff", fg="#4b5563")
        self.lbl_pass.pack(anchor="w", pady=(4, 0))
        self.en_password = tk.Entry(self.c_conteneur, font=("Arial", 10), bd=1, relief="solid", show="*", width=26)
        self.en_password.pack(pady=(0, 15))

        self.btn_valider = tk.Button(self.c_conteneur, font=("Helvetica", 10, "bold"), bg="#064e3b", fg="white", bd=0, pady=6, command=self.traiter_tentative_connexion)
        self.btn_valider.pack(fill="x", pady=4)

        self.btn_bascule = tk.Button(self.c_conteneur, font=("Helvetica", 8, "underline"), bg="#ffffff", fg="#0f766e", bd=0, command=lambda: self.app.basculer_ecran("INSCRIPTION"))
        self.btn_bascule.pack(pady=4)

        self.lbl_status = tk.Label(self.c_conteneur, text="", font=("Helvetica", 9, "italic"), bg="#ffffff", fg="#b91c1c")
        self.lbl_status.pack(fill="x", pady=4)

        self.traduire_page(DICTIONNAIRE_LANGUES.actif)

    def action_changement_langue(self, nuevo_dic):
        if self.winfo_exists(): self.traduire_page(nuevo_dic)

    def traduire_page(self, dic):
        txt_auth = dic.get("auth", {})
        self.c_annonce_officielle.config(text=txt_auth.get("cadre_legal", "📜 Homologation & Conseils"))
        self.lbl_titre.config(text=txt_auth.get("titre_connexion", "Connexion"))
        self.lbl_user.config(text=txt_auth.get("user_lbl", "Identifiant :"))
        self.lbl_pass.config(text=txt_auth.get("pass_lbl", "Mot de passe :"))
        self.btn_valider.config(text=txt_auth.get("btn_soumettre", "Se connecter"))
        self.btn_bascule.config(text=txt_auth.get("pas_compte", "S'inscrire"))

        # 🎯 CAPTURE MULTILINGUE DYNAMIQUE SANS TEXTE EN DUR
        self.lbl_bienvenue_conseil.config(text=txt_auth.get("message_bienvenue_doctrinal", ""))

    def traiter_tentative_connexion(self):
        txt_auth = DICTIONNAIRE_LANGUES.actif.get("auth", {})
        login = self.en_login.get().strip()
        password = self.en_password.get().strip()
        
        # 🎯 LIEN DYNAMIQUE DES ALERTES DE SÉCURITÉ DE SAISIE
        if not login or not password:
            self.lbl_status.config(text=txt_auth.get("err_champs_vides", "❌ Champs vides."))
            return
            
        if hasattr(self.app, "controleur_auth") and self.app.controleur_auth:
            succes, user_id, email = self.app.controleur_auth.verifier_connexion_utilisateur(login, password)
            if succes:
                self.en_login.delete(0, tk.END); self.en_password.delete(0, tk.END); self.lbl_status.config(text="")
                self.app.executer_connexion_session(user_id, login, email)
            else:
                self.lbl_status.config(text=txt_auth.get("err_connexion", "❌ Identifiants incorrects."))
