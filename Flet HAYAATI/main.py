"""
HAYAATI - POINT D'ENTRÉE OFFICIEL AVEC COMPILATION DES IMPORTATIONS
Version Finale Intégrale Réactive - Totalement compatible Flet 0.86.2, Python 3.14 & APK Android
"""
from __future__ import annotations
import os       # 🎯 RECTIFICATION : Ré-introduction indispensable pour os.path
import sys
import uuid     # 🎯 RECTIFICATION : Ré-introduction indispensable pour uuid.uuid4()
import warnings
import flet as ft

# Importation directe des composants pivots du dôme applicatif
from gui.app_visuelle import ApplicationHayaati
from gui.langues import DICTIONNAIRE_LANGUES
import core.database_manager as db_module

warnings.filterwarnings("ignore", category=DeprecationWarning)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# POINTEUR DE SÉCURITÉ MAÎTRE : Référence globale pour la purge de session en arrière-plan
APPLICATION_HAYAATI_INSTANCE: ApplicationHayaati | None = None

class ControleurVisiteurGenerique:
    def __init__(self, chemin=""): 
        self.chemin = chemin
    def modifier_donnees_profil_securite(self, *args, **kwargs): return False, "Indisponible."
    def sauvegarder_preferences_reglages(self, *args, **kwargs): return False, "Indisponible."
    def enregistrer_feedback_utilisateur(self, *args, **kwargs): return False, "Indisponible."
    def verifier_connexion_utilisateur(self, *args, **kwargs): return False, None, "Mode visiteur actif."
    def enregistrer_nouvel_utilisateur(self, *args, **kwargs): return False, "Mode visiteur actif."

def initialiser_application_flet(page: ft.Page):
    global APPLICATION_HAYAATI_INSTANCE
    print("[DIAGNOSTIC] Initialisation du système graphique Flet...")
    
    # Variable de contrôle interne pour ignorer les faux-départs ou états initiaux système
    APPLICATION_EST_CORRECTEMENT_LANCEE = False

    # 🛠️ ROUTINE MUTEX DE PURGE UNIQUE ET SÉCURISÉE
    def executer_purge_securite_immediate():
        global APPLICATION_HAYAATI_INSTANCE
        if APPLICATION_HAYAATI_INSTANCE and getattr(APPLICATION_HAYAATI_INSTANCE, "est_mode_connecte", False):
            try:
                # 1. Détruit la session, ferme les onglets et reconfigure les menus
                APPLICATION_HAYAATI_INSTANCE.executer_deconnexion_session()
                print("[SECURITY SHIELD] Événement de focus ou réduction détecté : session détruite.")
                
                # 2. Force le rafraîchissement global immédiat de la vue
                page.update()
            except Exception as err:
                print(f"[SECURITY ERROR] Échec de la purge de focus : {str(err)}")

    # 🔒 VERROU 1 : ÉCOUTEUR DES ÉVÉNEMENTS FENÊTRE PC (Minimisation / Clic extérieur)
    def gerer_evenements_fenetre_pc(e: ft.WindowEvent):
        global APPLICATION_EST_CORRECTEMENT_LANCEE
        signal = str(e.data).lower().strip()
        print(f"[WINDOW DIAGNOSTIC] Signal PC reçu : {signal}")
        
        if "focus" in signal or "show" in signal:
            APPLICATION_EST_CORRECTEMENT_LANCEE = True
            return
            
        # Intercepte le clic sur l'icône de réduction (_) ou la perte de focus (clic en dehors de l'app)
        if APPLICATION_EST_CORRECTEMENT_LANCEE and ("minimize" in signal or "blur" in signal):
            executer_purge_securite_immediate()

    # 🔒 VERROU 2 : ÉCOUTEUR MOBILE APK ANDROID (Passage en arrière-plan / Verrouillage écran)
    def gerer_cycle_de_vie_mobile(e: ft.AppLifecycleChangeEvent):
        global APPLICATION_EST_CORRECTEMENT_LANCEE
        etat = str(e.state).lower().strip()
        print(f"[LIFECYCLE DIAGNOSTIC] État Mobile reçu : {etat}")
        
        if "resume" in etat or "show" in etat:
            APPLICATION_EST_CORRECTEMENT_LANCEE = True
            return

        if APPLICATION_EST_CORRECTEMENT_LANCEE and ("pause" in etat or "hidden" in etat or "detach" in etat):
            executer_purge_securite_immediate()

    # 🎯 CONFIGURATION OBLIGATOIRE DU COMPORTEMENT DE FENÊTRE POUR PC
    # Force Flet à écouter et à envoyer activement tous les micro-événements Windows
    page.window_prevent_close = True  
    
    # Branchement étanche des deux canaux d'écoute matériels sur leurs capteurs respectifs
    page.on_window_event = gerer_evenements_fenetre_pc
    page.on_app_lifecycle_change = gerer_cycle_de_vie_mobile

    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            surface=ft.Colors.WHITE,
            on_surface=ft.Colors.BLACK,
        )
    )
    
    page.title = "HAYAATI"
    page.fonts = {
        "NotoSansArabic": "fonts/NotoSansArabic-Regular.ttf",
        "NotoSansSC": "fonts/NotoSansSC-Regular.ttf"
    }

    chemin_db = os.path.join("core", "hayaati_private.db")
    
    # Étape 1 : Construction et injection étanche du contrôleur d'authentification SQLite
    try:
        if hasattr(db_module, "DatabaseManager"):
            manager_brut = db_module.DatabaseManager(chemin_db)
            print("[SQLITE SUCCESS] Classe DatabaseManager initialisée avec succès.")
            
            def adaptateur_connexion_hayaati(login, password):
                succes, msg, u_id, email, compte = manager_brut.verifier_identifiants_connexion(login, password)
                return succes, u_id, email

            def adaptateur_inscription_hayaati(username, email, password):
                id_genere = str(uuid.uuid4())[:8].upper()
                return manager_brut.creer_compte_utilisateur(id_genere, username, email, password)

            manager_brut.verifier_connexion_utilisateur = adaptateur_connexion_hayaati
            manager_brut.enregistrer_nouvel_utilisateur = adaptateur_inscription_hayaati
            controleur_auth = manager_brut
        else:
            controleur_auth = ControleurVisiteurGenerique(chemin_db)
    except Exception as e:
        controleur_auth = ControleurVisiteurGenerique(chemin_db)
        print(f"[SQLITE WARNING] Chargement base de données contourné : {str(e)}")

    # Étape 2 : Instanciation de l'application Hayaati raccordée
    app = ApplicationHayaati(page=page, controleur_authentification=controleur_auth)
    app.controleur_auth = controleur_auth
    
    # Sauvegarde dans le pointeur global pour l'écouteur d'arrière-plan
    APPLICATION_HAYAATI_INSTANCE = app
    
    # 🎯 VERROUILLAGE DE LA PERSISTANCE CELLULAIRE AU DÉMARRAGE
    c_pref_init = app.sync_engine.charger_donnees_module("INVITE", "PREFERENCES") or {}
    
    l_init = str(c_pref_init.get("langue_actuelle", "FR")).upper()
    d_init = str(c_pref_init.get("devise_defaut", "XOF")).upper()
    f_init = str(c_pref_init.get("fiqh_defaut", "Malikite"))
    n_init = str(c_pref_init.get("arbitrage_nisab", "PLUS_BAS")).upper()
    
    # Injection stricte dans l'instance de session
    app.langue_actuelle = l_init
    app.devise_active = d_init
    app.madhhab_actif = f_init
    app.cle_nisab_active_memoire = n_init
    
    # Hydratation immédiate du dictionnaire i18n
    DICTIONNAIRE_LANGUES.moteur_i18n.charger_dictionnaire_langue(l_init)
    
    if hasattr(app, "declencher_changement_global"):
        app.declencher_changement_global()

    # L'application s'affiche et s'ancre à l'écran : on arme définitivement le bouclier
    APPLICATION_EST_CORRECTEMENT_LANCEE = True
    
    app.basculer_ecran("ONBOARDING")
    page.update()

if __name__ == "__main__":
    if hasattr(ft, "run"):
        ft.run(initialiser_application_flet)
    else:
        # Configuration réglementaire de production pointant le dossier d'actifs
        ft.app(target=initialiser_application_flet, assets_dir="assets")
