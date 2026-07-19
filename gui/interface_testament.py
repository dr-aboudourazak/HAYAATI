"""
PANNEAU DE RÉDACTION ET DISPOSITIONS TESTAMENTAIRES (GUI/INTERFACE_TESTAMENT.PY)
Version 6.0 - Architecture structurelle et routage i18n synchrone.
"""
import tkinter as tk
from tkinter import ttk
from gui.langues import DICTIONNAIRE_LANGUES

class EcranTestament(tk.Frame):
    def __init__(self, parent, app_reference):
        super().__init__(parent, bg="#ffffff")
        self.app = app_reference
        self.mode_mobile = None
        
        # Abonnement étanche au moteur i18n pour le multilingue à la volée
        DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_langue)
        self.construire_interface()

    def construire_interface(self):
        # 📂 BLOC DE RÉDACTION LEGS
        self.cadre_redaction = tk.LabelFrame(
            self, font=("Helvetica", 9, "bold"), fg="#064e3b", bg="#ffffff", padx=15, pady=10
        )
        self.cadre_redaction.pack(fill="x", padx=15, pady=4)

        # Rappel canonique souverain sur le plafond du tiers (1/3)
        self.lbl_rappel_loi = tk.Label(
            self.cadre_redaction, font=("Helvetica", 9, "italic"), fg="#b91c1c", 
            bg="#fee2e2", padx=8, pady=6, justify="left", wrap=450
        )
        self.lbl_rappel_loi.pack(fill="x", pady=(0, 15))

        # Champ Bénéficiaire
        self.lbl_beneficiaire = tk.Label(self.cadre_redaction, bg="#ffffff", font=("Helvetica", 9, "bold"), fg="#4b5563")
        self.lbl_beneficiaire.pack(anchor="w", pady=(2, 0))
        self.en_beneficiaire = tk.Entry(self.cadre_redaction, font=("Arial", 10), bd=1, relief="solid")
        self.en_beneficiaire.insert(0, "Association Dar es Salaam")
        self.en_beneficiaire.pack(fill="x", pady=(0, 10))

        # Champ Valeur financière du legs
        self.lbl_valeur = tk.Label(self.cadre_redaction, bg="#ffffff", font=("Helvetica", 9, "bold"), fg="#4b5563")
        self.lbl_valeur.pack(anchor="w", pady=(2, 0))
        
        # Cadre d'alignement monétaire
        c_val = tk.Frame(self.cadre_redaction, bg="#ffffff")
        c_val.pack(fill="x", pady=(0, 15))
        
        self.en_valeur_legs = tk.Entry(c_val, font=("Arial", 10), bd=1, relief="solid", width=15)
        self.en_valeur_legs.insert(0, "0")
        self.en_valeur_legs.pack(side="left")
        
        self.lbl_devise_symbole = tk.Label(c_val, font=("Helvetica", 10, "bold"), fg="#064e3b", bg="#ffffff")
        self.lbl_devise_symbole.pack(side="left", padx=5)

        # Bouton de validation
        self.btn_valider = tk.Button(
            self, font=("Helvetica", 10, "bold"), bg="#064e3b", fg="white", bd=0, pady=6, cursor="hand2", command=self.enregistrer_testament_db
        )
        self.btn_valider.pack(fill="x", padx=15, pady=4)

        # Statut inférieur de confirmation
        self.lbl_status = tk.Label(
            self, text="", font=("Helvetica", 9, "italic"), bg="#f3f4f6", fg="#4b5563", height=2
        )
        self.lbl_status.pack(fill="x", side="bottom")

        self.bind("<Configure>", self.on_redimensionnement)
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)

    def action_langue(self, dic):
        if self.winfo_exists(): self.traduire_page(dic)

    def on_redimensionnement(self, event):
        largeur = self.winfo_width()
        if largeur <= 1: return
        # Ajustement responsive automatique du wrapping du rappel de la Sharia
        self.lbl_rappel_loi.config(wraplength=max(200, largeur - 60))

    def traduire_page(self, dic):
        """Met à jour dynamiquement l'intégralité des textes du module de testament."""
        t = dic.get("testament", {})
        dev = getattr(self.app, "devise_active", "XOF")
        
        self.cadre_redaction.config(text=t.get("cadre_redaction", "Dispositions"))
        self.lbl_rappel_loi.config(text=t.get("limite_legale", "Rappel : Limite du tiers (1/3)."))
        self.lbl_beneficiaire.config(text=t.get("lbl_beneficiaire", "Bénéficiaire :"))
        self.lbl_valeur.config(text=t.get("lbl_valeur", "Montant du Legs :"))
        self.btn_valider.config(text=t.get("btn_enregistrer", "Valider"))
        self.lbl_devise_symbole.config(text=dev)

    def enregistrer_testament_db(self):
        """Sauvegarde les dispositions testamentaires dans l'espace chiffré."""
        if not getattr(self.app, "est_mode_connecte", False):
            self.lbl_status.config(text="❌ Espace privé déconnecté.", bg="#fee2e2", fg="#991b1b")
            return
            
        try:
            beneficiaire = self.en_beneficiaire.get().strip()
            valeur_legs = float(self.en_valeur_legs.get().strip() or 0.0)
            if valeur_legs < 0: raise ValueError

            if hasattr(self.app, "sync_engine") and self.app.sync_engine:
                u_id = self.app.user_id_connecte
                
                # 🎯 ALIGNEMENT DU MOTEUR : Sauvegarde synchrone pour le calcul de l'héritage live
                cache_fin = self.app.sync_engine.charger_donnees_module(u_id, "FINANCES")
                if not isinstance(cache_fin, dict): cache_fin = {}
                cache_fin["wasiyya"] = valeur_legs
                self.app.sync_engine.executer_sauvegarde_module(u_id, "FINANCES", cache_fin)
                
                # Sauvegarde du document textuel spécifique du testament
                doc_testament = {"beneficiaire": beneficiaire, "valeur": valeur_legs}
                self.app.sync_engine.executer_sauvegarde_module(u_id, "TESTAMENT", doc_testament)
                
            self.lbl_status.config(text="✓ Intentions testamentaires enregistrées avec succès.", bg="#d1fae5", fg="#064e3b")
            
            if hasattr(self.app, "declencher_changement_global"):
                self.app.declencher_changement_global()
                
        except ValueError:
            self.lbl_status.config(text="❌ Erreur : Montant numérique positif requis.", bg="#fee2e2", fg="#991b1b")

    def injecter_donnees(self, data):
        """Réinjecte la sauvegarde SQLite du legs au sein de l'interface."""
        if not data: return
        self.en_beneficiaire.delete(0, tk.END)
        self.en_beneficiaire.insert(0, str(data.get("beneficiaire", "Association Dar es Salaam")))
        self.en_valeur_legs.delete(0, tk.END)
        self.en_valeur_legs.insert(0, f"{data.get('valeur', 0.0):.2f}")

    def changer_langue(self, n_lang):
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)

    def actualiser_donnees_affichage(self):
        """Recharge les dispositions à l'apparition de l'écran."""
        self.lbl_status.config(text="", bg="#f3f4f6", fg="#4b5563")
        if getattr(self.app, "est_mode_connecte", False) and getattr(self.app, "sync_engine", None):
            testament_sauvegarde = self.app.sync_engine.charger_donnees_module(
                self.app.user_id_connecte, "TESTAMENT"
            )
            self.injecter_donnees(testament_sauvegarde)
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)
