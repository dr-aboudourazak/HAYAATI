"""
PANNEAU D'ACCUEIL GRAPHIQUE AVEC LOGO ARABE CORRIGÉ RTL (GUI/APP_VISUELLE.PY)
Version 1.8 - Version finale stabilisée avec tracé textuel haute définition pour le blason.
"""
import tkinter as tk
from tkinter import font, ttk
from gui.langues import DICTIONNAIRE_LANGUES
from gui.interface_zakat import EcranZakat
from gui.interface_heritage import EcranHeritage
from gui.interface_audit import EcranAudit

# IMPORTATION DES MOTEURS DE RENDU ARABE POUR L'ACCUEIL
import arabic_reshaper
from bidi.algorithm import get_display

class HayaatiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hayaati (حياتي) — Plateforme Intégrale Éthique")
        self.root.geometry("1100x680")
        self.root.configure(bg="#f9fafb")

        # États globaux de la session utilisateur
        self.langue_active = "FR"
        self.devise_active = "€"
        self.madhhab_actif = "Maliki"

        self.police_titre = font.Font(family="Helvetica", size=24, weight="bold")
        self.police_salam = font.Font(family="Helvetica", size=15, weight="bold")
        self.police_soustitre = font.Font(family="Helvetica", size=10, slant="italic")
        self.police_bouton = font.Font(family="Helvetica", size=11, weight="bold")

        # --- BARRE DE CONFIGURATION SUPERIEURE ---
        self.cadre_config = tk.Frame(self.root, bg="#f9fafb")
        self.cadre_config.pack(fill="x", side="top", padx=15, pady=8)
        
        self.lbl_select_langue = tk.Label(self.cadre_config, text="Langue :", bg="#f9fafb", fg="#4b5563")
        self.lbl_select_langue.pack(side="left", padx=2)
        self.combo_langue = ttk.Combobox(self.cadre_config, values=["FR", "EN", "AR", "HA", "ES", "ZH"], width=5, state="readonly")
        self.combo_langue.set(self.langue_active)
        self.combo_langue.pack(side="left", padx=5)
        self.combo_langue.bind("<<ComboboxSelected>>", self.declencher_changement_global)
        
        self.lbl_select_devise = tk.Label(self.cadre_config, text="Devise :", bg="#f9fafb", fg="#4b5563")
        self.lbl_select_devise.pack(side="left", padx=(10, 2))
        liste_devises = ["€", "$", "£", "CFA", "¥", "₦", "GH₵", "SAR", "AED", "KWD", "DZD", "MAD", "TND"]
        self.combo_devise = ttk.Combobox(self.cadre_config, values=liste_devises, width=6, state="readonly")
        self.combo_devise.set(self.devise_active)
        self.combo_devise.pack(side="left", padx=5)
        self.combo_devise.bind("<<ComboboxSelected>>", self.declencher_changement_global)

        self.lbl_select_fiqh_txt = tk.Label(self.cadre_config, text="Fiqh :", bg="#f9fafb", fg="#4b5563")
        self.lbl_select_fiqh_txt.pack(side="left", padx=(10, 2))
        self.combo_fiqh = ttk.Combobox(self.cadre_config, values=["Maliki", "Hanafi", "Shafi'i", "Hanbali"], width=8, state="readonly")
        self.combo_fiqh.set(self.madhhab_actif)
        self.combo_fiqh.pack(side="left", padx=5)
        self.combo_fiqh.bind("<<ComboboxSelected>>", self.declencher_changement_global)

        # --- ZONE D'EN-TÊTE PREMIUM ---
        self.cadre_entete = tk.Frame(self.root, bg="#064e3b", height=190)
        self.cadre_entete.pack(fill="x", side="top")
        self.cadre_entete.pack_propagate(False)

        # CANVAS LOGO INTERFACE (70x70 Pixels)
        self.canvas_logo = tk.Canvas(self.cadre_entete, width=70, height=70, bg="#064e3b", highlightthickness=0)
        self.canvas_logo.pack(pady=(10, 0))
        self.dessiner_logo_interface()

        self.lbl_titre = tk.Label(self.cadre_entete, font=self.police_titre, fg="#f59e0b", bg="#064e3b")
        self.lbl_titre.pack(pady=(2, 2))

        self.lbl_salam = tk.Label(self.cadre_entete, text="السَّلَامُ عَلَيْكُمْ وَرَحْمَةُ اللهِ وَبَرَكَاتُهُ", font=self.police_salam, fg="#ffffff", bg="#064e3b")
        self.lbl_salam.pack(pady=2)

        self.lbl_soustitre = tk.Label(self.cadre_entete, font=self.police_soustitre, fg="#e5e7eb", bg="#064e3b")
        self.lbl_soustitre.pack()

        # --- CONTENEUR PRINCIPAL DE TRAVAIL (SPLIT 2 COLONNES) ---
        self.cadre_principal = tk.Frame(self.root, bg="#f9fafb")
        self.cadre_principal.pack(fill="both", expand=True, pady=10, padx=10)

        # COLONNE GAUCHE (PERMANENTE) : IDENTIFICATION DE L'UTILISATEUR
        self.cadre_identite = tk.LabelFrame(self.cadre_principal, text=" 👤 Profil du Bénéficiaire ", font=("Helvetica", 10, "bold"), fg="#064e3b", bg="#f9fafb", padx=15, pady=15)
        self.cadre_identite.pack(side="left", fill="y", padx=(5, 10))

        # Champs du formulaire d'identité
        champs_id_config = [("prenom", "Prénom :"), ("nom", "Nom de famille :"), ("pays", "Pays :"), ("ville", "Ville :"), ("telephone", "Téléphone :")]
        self.entrees_identite = {}
        for i, (cle, libelle) in enumerate(champs_id_config):
            tk.Label(self.cadre_identite, text=libelle, font=("Helvetica", 9), bg="#f9fafb", fg="#374151", anchor="w").pack(anchor="w", pady=(8, 2))
            entree = tk.Entry(self.cadre_identite, font=("Arial", 10), bd=1, relief="solid", width=22)
            entree.pack(pady=2)
            self.entrees_identite[cle] = entree

        # Boutons d'interrupteurs pour les modules (Placés sous le bloc d'identité)
        tk.Label(self.cadre_identite, text="⚡ Modules de calcul :", font=("Helvetica", 9, "bold"), bg="#f9fafb", fg="#4b5563").pack(anchor="w", pady=(25, 5))
        self.btn_nav_zk = tk.Button(self.cadre_identite, text="🏦 Zakat", font=self.police_bouton, bg="#064e3b", fg="white", width=18, command=self.basculer_vers_zakat)
        self.btn_nav_zk.pack(pady=4)
        self.btn_nav_her = tk.Button(self.cadre_identite, text="📜 Héritage", font=self.police_bouton, bg="#ffffff", fg="#b45309", bd=1, relief="solid", width=18, command=self.basculer_vers_heritage)
        self.btn_nav_her.pack(pady=4)
        self.btn_nav_aud = tk.Button(self.cadre_identite, text="📖 Audit & Textes", font=self.police_bouton, bg="#ffffff", fg="#d97706", bd=1, relief="solid", width=18, command=self.basculer_vers_audit)
        self.btn_nav_aud.pack(pady=4)

        # COLONNE DROITE (DYNAMIQUE) : ESPACE DE TRAVAIL DES MODULES
        self.cadre_workspace = tk.Frame(self.cadre_principal, bg="#ffffff", bd=1, relief="solid")
        self.cadre_workspace.pack(side="right", fill="both", expand=True, padx=(5, 5))

        # Initialisation physique des écrans
        self.page_zakat = EcranZakat(self.cadre_workspace, self)
        self.page_heritage = EcranHeritage(self.cadre_workspace, self)
        self.page_audit = EcranAudit(self.cadre_workspace, self)

        # Affichage du premier module par défaut (Zakat)
        self.basculer_vers_zakat()
        self.rafraichir_textes_interface()

    def dessiner_logo_interface(self):
        """Trace le blason émeraude et or avec l'écriture arabe stabilisée."""
        self.canvas_logo.delete("all")
        
        # 1. Double cercle de prestige émeraude et or
        self.canvas_logo.create_oval(4, 4, 66, 66, outline="#d97706", width=2, fill="#064e3b")
        self.canvas_logo.create_oval(8, 8, 62, 62, outline="#f59e0b", width=1)
        
        # 2. Rendu textuel de prestige de la lettre 'ح' (Hâ) parfaitement centrée
        # Résout définitivement les plantages liés aux polygones vides
        self.canvas_logo.create_text(35, 33, text="ح", fill="#f59e0b", font=("Arial", 26, "bold"))
        
        # 3. Application du filtre RTL bidi pour l'écriture cursive 'حياتي' au bas du blason
        nom_reshaped = arabic_reshaper.reshape("حياتي")
        nom_affichage_correct = get_display(nom_reshaped)
        self.canvas_logo.create_text(35, 53, text=nom_affichage_correct, fill="#ffffff", font=("Arial", 9, "bold"))

    def obtenir_identite_saisie(self):
        return {cle: entree.get().strip() for cle, entree in self.entrees_identite.items()}

    def basculer_vers_zakat(self):
        self.page_heritage.pack_forget()
        self.page_audit.pack_forget()
        self.page_zakat.pack(fill="both", expand=True)
        self.btn_nav_zk.config(bg="#064e3b", fg="white")
        self.btn_nav_her.config(bg="#ffffff", fg="#b45309")
        self.btn_nav_aud.config(bg="#ffffff", fg="#d97706")

    def basculer_vers_heritage(self):
        self.page_zakat.pack_forget()
        self.page_audit.pack_forget()
        self.page_heritage.pack(fill="both", expand=True)
        self.btn_nav_her.config(bg="#b45309", fg="white")
        self.btn_nav_zk.config(bg="#ffffff", fg="#064e3b")
        self.btn_nav_aud.config(bg="#ffffff", fg="#d97706")

    def basculer_vers_audit(self):
        self.page_zakat.pack_forget()
        self.page_heritage.pack_forget()
        self.page_audit.pack(fill="both", expand=True)
        self.btn_nav_aud.config(bg="#d97706", fg="white")
        self.btn_nav_zk.config(bg="#ffffff", fg="#064e3b")
        self.btn_nav_her.config(bg="#ffffff", fg="#b45309")

    def declencher_changement_global(self, event=None):
        self.langue_active = self.combo_langue.get()
        self.devise_active = self.combo_devise.get()
        self.madhhab_actif = self.combo_fiqh.get()
        
        self.rafraichir_textes_interface()
        self.page_zakat.actualiser_contexte()
        self.page_heritage.actualiser_contexte()
        self.page_audit.actualiser_contexte()

    def rafraichir_textes_interface(self):
        lang = DICTIONNAIRE_LANGUES[self.langue_active]
        self.lbl_select_langue.config(text=lang["selection_langue"])
        self.lbl_select_devise.config(text=lang["selection_devise"])
        self.lbl_select_fiqh_txt.config(text=lang.get("selection_fiqh", "Fiqh :"))
        self.lbl_titre.config(text=lang["titre_app"])
        self.lbl_soustitre.config(text=lang["sous_titre"])

if __name__ == "__main__":
    root = tk.Tk()
    app = HayaatiApp(root)
    root.mainloop()
