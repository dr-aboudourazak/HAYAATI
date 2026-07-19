"""
FENÊTRE PRINCIPALE GRAPHIQUE (GUI/APP_VISUELLE.PY) - COMPOSANT MAÎTRE
Version 11.9 - Rectification complète des liaisons directes d'initialisation et alignement i18n total.
"""
import tkinter as tk
from tkinter import ttk
from gui.app_layout import OrganisateurLayout
from gui.langues import DICTIONNAIRE_LANGUES

# 🎯 ENCAPSULATION STATIQUE DIRECTE DES APPELS DE COMPOSANTS EXTERNES
from gui.app_visuelle_toolbar import configurer_bandeau_superieur, dessiner_boutons_navigation

class ApplicationHayaati(tk.Tk):
    def __init__(self, controleur_authentification=None):
        super().__init__()
        
        # --- ÉTATS GLOBAUX DIRECTS DYNAMIQUES ---
        self.langue_actuelle = "FR"
        self.devise_active = "XOF"
        self.madhhab_actif = "Malikite"
        self.est_mode_connecte = False
        self.user_id_connecte = None
        self.nom_utilisateur_connecte = "Visiteur"
        self.email_utilisateur_connecte = ""
        
        self.telephone_utilisateur = "-"
        self.pays_utilisateur = "Togo"
        self.ville_utilisateur = "Dapaong"
        self.profession_utilisateur = "-"
        
        self.mode_persistant_actif = False
        self.ecran_courant = "ONBOARDING"
        self.mode_smartphone_actif = None
        self.controleur_auth = controleur_authentification
        self.txt_global = DICTIONNAIRE_LANGUES[self.langue_actuelle]

        # Application dynamique du titre depuis l'en-tête i18n
        self.title(f"{self.txt_global['barre_outils']['titre_app']} - Audit Patrimonial & Doctrinal")
        self.geometry("1050x740")
        self.minsize(360, 550)
        self.configure(bg="#ffffff")

        from core.sync_engine import SyncEngine
        self.sync_engine = SyncEngine()

        # --- BLOCS STRUCTURELS FIXES ---
        self.barre_outils = tk.Frame(self, bg="#064e3b", height=65)
        self.barre_outils.pack(fill="x", side="top")
        
        self.barre_navigation = tk.Frame(self, bg="#f3f4f6")
        self.layout_central = OrganisateurLayout(self, self)

        # 🎯 EXÉCUTION SÉCURISÉE DES COMPOSANTS DIRECTS SANS INTERVENTION DE __GETATTR__
        configurer_bandeau_superieur(self)
        dessiner_boutons_navigation(self)
        
        self.basculer_ecran("ONBOARDING")

        # Appel automatique de la vérification linguistique obligatoire
        self.verifier_langue_premier_lancement()

        # Écouteurs globaux d'événements
        self.bind("<Unmap>", self.intercepter_mise_en_veille_furtive)
        self.bind("<Configure>", self.evaluer_format_ecran_responsive)

    def verifier_langue_premier_lancement(self):
        """Vérifie la présence d'une configuration de langue, sinon bloque l'IHM."""
        c_p = self.sync_engine.charger_donnees_module("INVITE", "PREFERENCES")
        if "langue_actuelle" not in c_p:
            self.ouvrir_selecteur_langue_installation()

    def abrir_selecteur_langue_installation(self):
        """Alias de secours."""
        self.ouvrir_selecteur_langue_installation()

    def ouvrir_selecteur_langue_installation(self):
        """Affiche un panneau d'installation automatique basé sur les fichiers JSON physiques trouvés."""
        fen = tk.Toplevel(self)
        fen.title(self.txt_global["menu"]["reglages"])
        fen.geometry("420x240")
        fen.configure(bg="#ffffff")
        fen.transient(self)
        fen.grab_set()
        fen.resizable(False, False)

        tk.Label(fen, text=self.txt_global["auth"]["titre_inscription"], font=("Helvetica", 10, "bold"), fg="#064e3b", bg="#ffffff").pack(pady=(15, 2))
        tk.Label(fen, text=self.txt_global["reglages"]["lbl_guide_langue"], font=("Helvetica", 8, "italic"), fg="#4b5563", bg="#ffffff").pack(pady=(0, 15))

        # Cartographie inversée dynamique directe
        m_index = DICTIONNAIRE_LANGUES.moteur_i18n.langues_disponibles_index
        langues_map_inverse = {nom: code for code, nom in m_index.items()}
        
        cb = ttk.Combobox(fen, values=list(langues_map_inverse.keys()), state="readonly", width=18, font=("Arial", 10))
        cb.set(m_index.get("FR", list(langues_map_inverse.keys())[0] if langues_map_inverse else "FR"))
        cb.pack(pady=5)

        def valider_installation():
            label_selectionne = cb.get()
            langue_code = langues_map_inverse.get(label_selectionne, "FR")
            self.langue_actuelle = langue_code
            
            p_dict = self.sync_engine.charger_donnees_module("INVITE", "PREFERENCES")
            if not isinstance(p_dict, dict): p_dict = {}
            p_dict["langue_actuelle"] = langue_code
            self.sync_engine.executer_sauvegarde_module("INVITE", "PREFERENCES", p_dict)
            
            DICTIONNAIRE_LANGUES.moteur_i18n.charger_dictionnaire_langue(langue_code)
            self.changer_langue_globale(langue_code)
            fen.destroy()

        tk.Button(fen, text=self.txt_global["auth"]["btn_soumettre"], font=("Helvetica", 9, "bold"), bg="#064e3b", fg="white", bd=0, padx=15, pady=6, command=valider_installation).pack(pady=20)

    def intercepter_mise_en_veille_furtive(self, event):
        """Déclenche le verrouillage automatique si la session active est réduite."""
        if event.widget != self: return
        if self.est_mode_connecte and (self.state() == "iconic" or self.winfo_viewable() == 0):
            print("[SÉCURITÉ] Verrouillage automatique de session.")
            self.executer_deconnexion_session()

    def evaluer_format_ecran_responsive(self, event):
        """Détecte les changements de dimensions pour basculer en mode responsive."""
        if event.widget != self: return
        nouveau_mode = self.winfo_width() < 650
        if nouveau_mode != self.mode_smartphone_actif:
            self.mode_smartphone_actif = nouveau_mode
            self.appliquer_layout_responsive()

    def appliquer_layout_responsive(self):
        """Modifie dynamiquement la disposition de la barre de navigation selon le terminal."""
        self.barre_navigation.pack_forget()
        self.layout_central.pack_forget()

        if self.mode_smartphone_actif:
            self.barre_navigation.config(width=0, height=55)
            self.barre_navigation.pack_propagate(True)
            self.barre_navigation.pack(fill="x", side="bottom")
            self.layout_central.pack(fill=tk.BOTH, expand=True, side="top")
        else:
            self.barre_navigation.config(width=220, height=0)
            self.barre_navigation.pack_propagate(False)
            self.barre_navigation.pack(fill="y", side="left")
            self.layout_central.pack(fill=tk.BOTH, expand=True, side="right")

        self.construire_menu_navigation()

    def construire_barre_outils(self):
        """Routeur interne vers le module de configuration de la barre supérieure."""
        configurer_bandeau_superieur(self)

    def construire_menu_navigation(self):
        """Routeur interne vers le module d'affichage des boutons de menu."""
        dessiner_boutons_navigation(self)

    def basculer_ecran(self, cle):
        """Gère le routage centralisé de l'affichage vers un module précis."""
        self.ecran_courant = cle  
        self.layout_central.basculer_vers_ecran(cle)
        for enfant in self.layout_central.winfo_children():
            if enfant.winfo_ismapped() and hasattr(enfant, "actualiser_donnees_affichage"):
                enfant.actualiser_donnees_affichage()
        if self.mode_smartphone_actif is not None: 
            self.construire_menu_navigation()

    def changer_langue_globale(self, code_langue):
        """Met à jour l'état linguistique de l'application entière."""
        self.langue_actuelle = code_langue
        self.txt_global = DICTIONNAIRE_LANGUES[code_langue]
        self.declencher_changement_global()

    def declencher_changement_global(self):
        """Force le rafraîchissement visuel de l'IHM et propage la nouvelle langue."""
        self.txt_global = DICTIONNAIRE_LANGUES[self.langue_actuelle]
        self.title(f"{self.txt_global['barre_outils']['titre_app']} - Audit Patrimonial & Doctrinal")
        
        self.construire_barre_outils()
        self.construire_menu_navigation()
        self.layout_central.propager_changement_langue(self.langue_actuelle)
        self.layout_central.basculer_vers_ecran(self.ecran_courant)

    def executer_connexion_session(self, user_id, username, email):
        """Initialise la session de l'utilisateur connecté avec persistance."""
        self.est_mode_connecte = True
        self.mode_persistant_actif = True
        self.user_id_connecte = user_id
        self.nom_utilisateur_connecte = username
        self.email_utilisateur_connecte = email
        self.langue_actuelle = self.langue_actuelle or "FR"
        self.changer_langue_globale(self.langue_actuelle)
        self.basculer_ecran("ONBOARDING")

    def executer_deconnexion_session(self):
        """Purge la session et réinitialise l'application sur la page Connexion."""
        self.est_mode_connecte = False
        self.mode_persistant_actif = False
        self.user_id_connecte = None
        self.nom_utilisateur_connecte = "Visiteur"
        self.email_utilisateur_connecte = ""
        self.telephone_utilisateur = "-"
        self.pays_utilisateur = "Togo"
        self.ville_utilisateur = "Dapaong"
        self.profession_utilisateur = "-"
        
        self.txt_global = DICTIONNAIRE_LANGUES[self.langue_actuelle]
        self.title(f"{self.txt_global['barre_outils']['titre_app']} - Audit Patrimonial & Doctrinal")
        
        self.construire_barre_outils()
        self.construire_menu_navigation()
        self.layout_central.propager_changement_langue(self.langue_actuelle)
        self.basculer_ecran("CONNEXION")
