"""
PANNEAU DE CONFIGURATION DE L'ARBRE GÉNÉALOGIQUE SUCCESSORAL INTERACTIF
Version 7.0 - endu horizontal par compteurs (Spinbox) synchronisés.
"""
import tkinter as tk
from tkinter import ttk
from gui.langues import DICTIONNAIRE_LANGUES

class EcranArbre(tk.Frame):
    def __init__(self, parent, app_reference):
        super().__init__(parent, bg="#ffffff")
        self.app = app_reference
        self.mode_mobile = None
        
        # 🎯 EXHAUSTIVITÉ ET SÉPARATION CANONIQUE STRICTE DES CONJOINTS
        self.candidats = [
            "epoux", "epouse", "fils", "fille", "pere", "mere", "grand_pere", "grand_mere",
            "petit_fils", "petite_fille", "frere_germain", "soeur_germaine", "frere_paternel",
            "soeur_paternelle", "frere_uterin", "soeur_uterine", "fils_frere_germain",
            "fils_frere_paternel", "oncle_germain", "oncle_paternel", "cousin_germain", "cousin_paternel"
        ]
        self.labels, self.entries = {}, {}
        
        DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_langue)
        self.construire_interface()

    def construire_interface(self):
        # 📂 BLOC DE CONFIGURATION : Tableau horizontal à compteurs
        self.cadre_form = tk.LabelFrame(
            self, font=("Helvetica", 9, "bold"), fg="#064e3b", bg="#ffffff", padx=10, pady=8
        )
        self.cadre_form.pack(fill="x", padx=15, pady=4)

        # Instanciation des Widgets de décompte Sharia
        for c in self.candidats:
            self.labels[c] = tk.Label(self.cadre_form, bg="#ffffff", font=("Helvetica", 8, "bold"), fg="#4b5563")
            
            # Application des plafonds doctrinaux par catégorie technique
            max_limite = 1 if c in ["epoux", "pere", "mere", "grand_pere", "grand_mere"] else 4 if c == "epouse" else 20
            self.entries[c] = tk.Spinbox(self.cadre_form, from_=0, to=max_limite, width=3, font=("Arial", 9), bd=1, relief="solid")
            self.entries[c].delete(0, tk.END)
            self.entries[c].insert(0, "0")
            setattr(self, f"sb_{c}", self.entries[c])

        self.btn_sauver = tk.Button(
            self, font=("Helvetica", 10, "bold"), bg="#064e3b", fg="white", bd=0, pady=6, cursor="hand2", command=self.enregistrer_arbre_db
        )
        self.btn_sauver.pack(fill="x", padx=15, pady=4)

        # Zone de notification et de confirmation
        self.lbl_status = tk.Label(
            self, text="", font=("Helvetica", 9, "italic"), bg="#f3f4f6", fg="#4b5563", height=2
        )
        self.lbl_status.pack(fill="x", side="bottom")

        self.bind("<Configure>", lambda e: self.ordonner_layout(self.winfo_width() < 550))
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)

    def ordonner_layout(self, is_mobile):
        if is_mobile == self.mode_mobile: return
        self.mode_mobile = is_mobile
        for c in self.candidats: self.labels[c].grid_forget(); self.entries[c].grid_forget()

        if is_mobile:
            # Rendu vertical optimisé pour smartphones
            for idx, c in enumerate(self.candidats):
                self.labels[c].grid(row=idx, column=0, sticky="w", pady=1)
                self.entries[c].grid(row=idx, column=1, sticky="w", padx=10, pady=1)
        else:
            # 🎯 HARMONISATION TOTAL AVEC LA PAGE TIERS : Grille à 4 colonnes de données
            for idx, c in enumerate(self.candidats):
                r, col = divmod(idx, 4)
                self.labels[c].grid(row=r, column=col*2, sticky="w", padx=4, pady=3)
                self.entries[c].grid(row=r, column=col*2+1, sticky="w", padx=10, pady=3)

    def action_langue(self, dic):
        if self.winfo_exists(): self.traduire_page(dic)
        
    def traduire_page(self, dic):
        """Met à jour dynamiquement l'intégralité des textes du module de l'arbre."""
        a = dic.get("arbre", {})
        h = dic.get("heritage", {})
        
        self.cadre_form.config(text=a.get("cadre_ajout", "Cellule Familiale"))
        self.btn_sauver.config(text=a.get("btn_ajouter_membre", "Enregistrer"))
        
        # 🎯 ALIGNEMENT RIGOUREUX DES 21 BÉNÉFICIAIRES DEPUIS LA SECTION JURISPRUDENTIELLE
        candidats_json = h.get("candidats", {})
        for c in self.candidats:
            self.labels[c].config(text=f"{candidats_json.get(c, c)} :")

    def enregistrer_arbre_db(self):
        """Compile la grille de l'arbre, valide la Sharia et sauvegarde en direct."""
        if not getattr(self.app, "est_mode_connecte", False):
            self.lbl_status.config(text="❌ Espace déconnecté.", bg="#fee2e2", fg="#991b1b")
            return
            
        try:
            # Extraction et assainissement des valeurs numériques des compteurs
            arbre_compile = {}
            for c in self.candidats:
                valeur = int(self.entries[c].get() or 0)
                if valeur > 0:
                    arbre_compile[c] = valeur

            # 🎯 GARDE-FOU CANONIQUE ABSOLU DU FIQH : Interdiction de double-conjoint
            if "epoux" in arbre_compile and "epouse" in arbre_compile:
                txt_err_double = "❌ Erreur Conjoints : Double présence impossible selon la Sharia."
                self.lbl_status.config(text=txt_err_double, bg="#fee2e2", fg="#991b1b")
                return

            # Sauvegarde de la structure consolidée pour le HeritageEngine
            if hasattr(self.app, "sync_engine") and self.app.sync_engine:
                self.app.sync_engine.executer_sauvegarde_module(
                    self.app.user_id_connecte, "ARBRE_FAMILIAL", arbre_compile
                )
                
            # Confirmation et mise à jour globale instantanée
            self.lbl_status.config(text="✓ Arbre familial synchronisé et mis à jour.", bg="#d1fae5", fg="#064e3b")
            
            if hasattr(self.app, "declencher_changement_global"):
                self.app.declencher_changement_global()
                
        except ValueError:
            self.lbl_status.config(text="❌ Erreur : Nombres entiers uniquement.", bg="#fee2e2", fg="#991b1b")

    def injecter_donnees(self, data):
        """Réinjecte la sauvegarde SQLite de l'arbre au sein des compteurs d'interface."""
        if not data: return
        for c in self.candidats:
            self.entries[c].delete(0, tk.END)
            self.entries[c].insert(0, str(data.get(c, 0)))

    def changer_langue(self, n_lang):
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)

    def actualiser_donnees_affichage(self):
        """Recharge l'arbre depuis la base de données à l'apparition de l'écran."""
        self.lbl_status.config(text="", bg="#f3f4f6", fg="#4b5563")
        if getattr(self.app, "est_mode_connecte", False) and getattr(self.app, "sync_engine", None):
            arbre_sauvegarde = self.app.sync_engine.charger_donnees_module(
                self.app.user_id_connecte, "ARBRE_FAMILIAL"
            )
            self.injecter_donnees(arbre_sauvegarde)
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)
