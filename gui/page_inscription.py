"""
PAGE D'INSCRIPTION DE L'AUDITEUR (GUI/PAGE_INSCRIPTION.PY)
Version 6.2 - Format horizontal condensé, support smartphone défilant et i18n synchrone.
"""
import tkinter as tk
from tkinter import ttk
import uuid
from gui.langues import DICTIONNAIRE_LANGUES

class PageInscription(tk.Frame):
    def __init__(self, parent, app_reference):
        super().__init__(parent, bg="#ffffff")
        self.app = app_reference
        DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_changement_langue)
        self.construire_interface()

    def construire_interface(self):
        self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(0, weight=1)
        self.canevas = tk.Canvas(self, bg="#ffffff", bd=0, highlightthickness=0)
        self.barre_defilement = ttk.Scrollbar(self, orient="vertical", command=self.canevas.yview)
        
        self.c_centre = tk.Frame(self.canevas, bg="#ffffff", padx=20, pady=15)
        self.c_centre.grid_columnconfigure(0, weight=1)
        
        self.id_fenetre = self.canevas.create_window((0, 0), window=self.c_centre, anchor="n")
        self.canevas.configure(yscrollcommand=self.barre_defilement.set)
        self.canevas.pack(side="left", fill="both", expand=True); self.barre_defilement.pack(side="right", fill="y")

        self.lbl_titre = tk.Label(self.c_centre, font=("Helvetica", 13, "bold"), fg="#064e3b", bg="#ffffff")
        self.lbl_titre.pack(pady=(10, 15))

        self.lbl_username = tk.Label(self.c_centre, font=("Helvetica", 9, "bold"), fg="#374151", bg="#ffffff")
        self.lbl_username.pack(anchor="w", pady=(3, 1))
        self.entree_username = tk.Entry(self.c_centre, font=("Arial", 10), bd=1, relief="solid", width=32)
        self.entree_username.pack(pady=(0, 10), fill="x")

        self.lbl_email = tk.Label(self.c_centre, font=("Helvetica", 9, "bold"), fg="#374151", bg="#ffffff")
        self.lbl_email.pack(anchor="w", pady=(3, 1))
        self.entree_email = tk.Entry(self.c_centre, font=("Arial", 10), bd=1, relief="solid", width=32)
        self.entree_email.pack(pady=(0, 10), fill="x")

        self.lbl_password = tk.Label(self.c_centre, font=("Helvetica", 9, "bold"), fg="#374151", bg="#ffffff")
        self.lbl_password.pack(anchor="w", pady=(3, 1))
        self.entree_password = tk.Entry(self.c_centre, font=("Arial", 10), bd=1, relief="solid", width=32, show="*")
        self.entree_password.pack(pady=(0, 15), fill="x")

        self.lbl_verdict = tk.Label(self.c_centre, font=("Helvetica", 9, "italic"), bg="#ffffff", fg="#b91c1c", wrap=280)
        self.lbl_verdict.pack(pady=5)

        self.btn_valider = tk.Button(self.c_centre, font=("Helvetica", 10, "bold"), bg="#064e3b", fg="white", bd=0, padx=15, pady=8, cursor="hand2", command=self.traiter_inscription_physique)
        self.btn_valider.pack(fill="x", pady=5)

        self.btn_retour = tk.Button(self.c_centre, font=("Helvetica", 9, "underline"), fg="#0f766e", bg="#ffffff", bd=0, activebackground="#ffffff", cursor="hand2", command=lambda: self.app.basculer_ecran("CONNEXION"))
        self.btn_retour.pack(pady=10)

        self.c_centre.bind("<Configure>", lambda e: self.canevas.configure(scrollregion=self.canevas.bbox("all")))
        self.bind("<Configure>", self.ajuster_largeur_conteneur)
        self.rafraichir_textes(DICTIONNAIRE_LANGUES.actif)

    def action_changement_langue(self, nouveau_dictionnaire):
        if self.winfo_exists(): self.rafraichir_textes(nouveau_dictionnaire)

    def rafraichir_textes(self, dic_actif):
        txt_auth = dic_actif.get("auth", {})
        self.lbl_titre.config(text=txt_auth.get("titre_inscription", "Inscription"))
        self.lbl_username.config(text=txt_auth.get("username", "Utilisateur :"))
        self.lbl_email.config(text=txt_auth.get("email_lbl", "E-mail :"))
        self.lbl_password.config(text=txt_auth.get("pass_lbl", "Mot de passe :"))
        self.btn_valider.config(text=txt_auth.get("btn_creer", "Créer"))
        self.btn_retour.config(text=txt_auth.get("deja_compte", "Connexion"))

    def ajuster_largeur_conteneur(self, event):
        largeur_fenetre = self.winfo_width()
        if largeur_fenetre <= 1: return
        largeur_cible = min(340, largeur_fenetre - 40)
        self.canevas.itemconfig(self.id_fenetre, width=largeur_cible)
        decalage = max(10, (largeur_fenetre - largeur_cible) // 2)
        self.canevas.coords(self.id_fenetre, decalage, 20)

    def traiter_inscription_physique(self):
        txt_auth = DICTIONNAIRE_LANGUES.actif.get("auth", {})
        username = self.entree_username.get().strip()
        email = self.entree_email.get().strip()
        password = self.entree_password.get().strip()

        if not username or not email or not password:
            self.lbl_verdict.config(text=txt_auth.get("err_champs_vides", "❌ Champs requis."), fg="#b91c1c")
            return

        if len(password) < 4:
            self.lbl_verdict.config(text=txt_auth.get("err_password_court", "❌ Mot de passe court."), fg="#b91c1c")
            return

        if hasattr(self.app, "controleur_auth") and self.app.controleur_auth:
            generateur_user_id = str(uuid.uuid4())[:8].upper()
            succes, message = self.app.controleur_auth.creer_compte_utilisateur(generateur_user_id, username, email, password)
            
            if succes:
                self.entree_username.delete(0, tk.END); self.entree_email.delete(0, tk.END); self.entree_password.delete(0, tk.END)
                self.app.basculer_ecran("CONNEXION")
                ecran_connexion = self.app.layout_central.ecrans.get("CONNEXION")
                if ecran_connexion and hasattr(ecran_connexion, "lbl_status"):
                    ecran_connexion.lbl_status.config(text=txt_auth.get("inscription_ok", "✓ Inscription réussie."), fg="#064e3b")
            else:
                self.lbl_verdict.config(text=f"❌ {message}", fg="#b91c1c")
        else:
            self.lbl_verdict.config(text=txt_auth.get("err_champs_vides", "❌ Erreur."), fg="#b91c1c")

    def changer_langue(self, n_lang): self.rafraichir_textes(DICTIONNAIRE_LANGUES.actif)
    def actualiser_donnees_affichage(self): self.lbl_verdict.config(text="")
