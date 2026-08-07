"""
HAYAATI - POINT D'ENTRÉE OFFICIEL AVEC COMPILATION DES IMPORTATIONS
Version Finale Intégrale Réactive - Totalement compatible Flet 0.86.2, Python 3.14 & APK Android
"""
from __future__ import annotations
import os
import sys
import uuid
import warnings
import asyncio
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
    # 🎯 DEMANDE DE TOUTES LES PERMISSIONS ANDROID SYNC (NOTIFICATIONS & STOCKAGE PDF) [Poc]
    if hasattr(page, "request_permission"):
        try:
            # 1. Alerte Push (Obligatoire pour les rappels de prières dédoublonnés)
            page.request_permission("android.permission.POST_NOTIFICATIONS")
            
            # 2. Écriture sur l'espace de stockage externe (Rapports PDF dans Documents/Hayaati)
            page.request_permission("android.permission.WRITE_EXTERNAL_STORAGE")
            
            # 3. Lecture de l'espace de stockage externe (Chargement et partage des PDF)
            page.request_permission("android.permission.READ_EXTERNAL_STORAGE")
            
            # 4. Gestion des dossiers et documents sécurisés (MANAGE_DOCUMENTS)
            page.request_permission("android.permission.MANAGE_DOCUMENTS")
            
            # 5. Accès au réseau local et distant (Vérifications des Nisabs et taux)
            page.request_permission("android.permission.INTERNET")
        except Exception:
            pass

    page.title = "HAYAATI"
       
    # =========================================================================
    # 🎯 FORCE PERMISSIONS ANDROID VIA PLYER (ANTI-BLOCAGE AU PREMIER LANCEMENT)
    # =========================================================================
    if hasattr(sys, "getandroidapilevel"):
        try:
            # Appel asynchrone de secours pour forcer Android à afficher les invites
            from plyer import notification
            # Un micro-appel push forcé au démarrage réveille le gestionnaire de permissions d'Android
            notification.notify(
                title="HAYAATI",
                message="Initialisation des systèmes de vigilance...",
                timeout=1
            )
        except Exception:
            pass

    # =========================================================================
    # 🎯 INTERCEPTION ET BLINDAGE DU BOUTON RETOUR MATÉRIEL ANDROID
    # =========================================================================
    def action_bouton_retour_physique(e):
        try:
            # 1. Vérification de l'existence du routeur central d'écrans
            if hasattr(page, "layout_principal") and page.layout_principal:
                routeur = page.layout_principal
                
                # 2. Si l'écran actuel n'est pas l'accueil, on force le retour vers l'Onboarding
                if hasattr(page, "ecran_courant") and page.ecran_courant != "ONBOARDING":
                    routeur.basculer_vers_ecran("ONBOARDING")
                    page.update()
                    return # 🌟 CRITIQUE : Bloque l'action d'origine pour éviter la fermeture de l'app !
                    
            # 3. Si l'utilisateur est DÉJÀ sur l'Onboarding, l'app se réduit proprement
            # On laisse Android exécuter son comportement par défaut (réduction/fermeture)
        except Exception:
            pass

    # Liaison de l'intercepteur avec l'événement matériel Android global de Flet
    page.on_back_button = action_bouton_retour_physique

    # Reste de votre code d'initialisation d'origine...
    page.update()

    global APPLICATION_HAYAATI_INSTANCE
    print("[DIAGNOSTIC] Initialisation du système graphique Flet...")
    
    # Variable de contrôle interne pour ignorer les faux-départs ou états initiaux système
    APPLICATION_EST_CORRECTEMENT_LANCEE = False

    # =========================================================================
    # 🔒 SHIELD SÉCURITÉ — DÉCONNEXION AUTOMATIQUE (PC + Mobile)
    # =========================================================================
    # 🛠️ ROUTINE MUTEX DE PURGE UNIQUE ET SÉCURISÉE
    def executer_purge_securite_immediate():
        global APPLICATION_HAYAATI_INSTANCE
        if APPLICATION_HAYAATI_INSTANCE and getattr(APPLICATION_HAYAATI_INSTANCE, "est_mode_connecte", False):
            try:
                # 1. Détruit la session, ferme les onglets et reconfigure les menus
                APPLICATION_HAYAATI_INSTANCE.executer_deconnexion_session()
                print("[SECURITY SHIELD] Événement de réduction/arrière-plan détecté : session détruite.")

                # 2. Force le rafraîchissement global immédiat de la vue (best-effort)
                try:
                    page.update()
                except Exception:
                    pass
            except Exception as err:
                print(f"[SECURITY ERROR] Échec de la purge : {str(err)}")

    # 🛡️ État mutable partagé (évite les bugs global/nonlocal)
    _shield = {"pret": False}

    # 🔒 VERROU 1 : ÉCOUTEUR FENÊTRE PC (Minimisation + Fermeture)
    def gerer_evenements_fenetre_pc(e):
        signal = str(getattr(e, "data", "")).lower().strip()
        print(f"[WINDOW DIAGNOSTIC] Signal PC reçu : {signal}")

        if "focus" in signal or "show" in signal:
            _shield["pret"] = True
            # 🔄 Si déconnecté en arrière-plan, force le refresh UI au retour
            if APPLICATION_HAYAATI_INSTANCE and not getattr(APPLICATION_HAYAATI_INSTANCE, "est_mode_connecte", False):
                try:
                    APPLICATION_HAYAATI_INSTANCE.declencher_changement_global()
                except Exception:
                    pass
            return

        # Déclenche la purge sur minimisation ou masquage de fenêtre
        if _shield["pret"] and ("minimize" in signal or "hide" in signal):
            executer_purge_securite_immediate()

    def gerer_fermeture_fenetre(e):
        """Déconnecte puis autorise la fermeture de la fenêtre."""
        print("[WINDOW CLOSE] Fermeture demandée — purge sécurisée en cours...")
        executer_purge_securite_immediate()
        page.window_destroy()

    # 🔒 VERROU 2 : ÉCOUTEUR MOBILE APK (Passage en arrière-plan)
    def gerer_cycle_de_vie_mobile(e: ft.AppLifecycleChangeEvent):
        # BLINDAGE PC : ce canal est 100% mobile
        if not hasattr(sys, "getandroidapilevel"):
            return

        etat = str(e.state).lower().strip()
        print(f"[LIFECYCLE DIAGNOSTIC] État Mobile reçu : {etat}")

        if "resume" in etat or "show" in etat:
            _shield["pret"] = True
            # 🔄 Si déconnecté en arrière-plan, force le refresh UI au retour
            if APPLICATION_HAYAATI_INSTANCE and not getattr(APPLICATION_HAYAATI_INSTANCE, "est_mode_connecte", False):
                try:
                    APPLICATION_HAYAATI_INSTANCE.declencher_changement_global()
                except Exception:
                    pass
            return

        if _shield["pret"] and ("pause" in etat or "hidden" in etat or "detach" in etat or "inactive" in etat):
            executer_purge_securite_immediate()

    # CONFIGURATION OBLIGATOIRE DU COMPORTEMENT DE FENÊTRE POUR PC
    page.window_prevent_close = True
    page.on_window_event = gerer_evenements_fenetre_pc
    page.on_window_close = gerer_fermeture_fenetre
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

    # 🌟 FIX SMARTPHONE ZONE SÉCURISÉE : Évite que l'application passe sous la barre d'état Android
    # =========================================================================
    # 🎯 FIX AFFICHAGE INCOMPLET ANDROID : padding=0 + safe_area + on_resized
    # =========================================================================
    page.safe_area = True
    page.padding = 0  # Padding géré par le contenu interne, pas la page

    def on_page_resized(e):
        """Force un recalcul complet quand le viewport Android se stabilise."""
        try:
            page.update()
            print(f"[RESIZE] Viewport stabilisé : {page.width:.0f}x{page.height:.0f}")
        except Exception:
            pass

    page.on_resized = on_page_resized

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
    
    # VERROUILLAGE DE LA PERSISTANCE CELLULAIRE AU DÉMARRAGE
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
    
    # CONFIGURATION SÉCURISÉE DE L'AIGUILLAGE INITIAL SANS DOUBLE ROUTAGE CONCURRENT
    app.ecran_courant = "ONBOARDING"

    # L'application s'affiche et s'ancre à l'écran : on arme définitivement le bouclier
    APPLICATION_EST_CORRECTEMENT_LANCEE = True
    
    # 🎯 FIX ANTI-LENTEUR ET ÉCRAN FIGÉ SMARTPHONE : On affiche d'abord le squelette de l'application (0.0s)
    page.update()

    # Le chargement lourd de la base de données et des modules s'effectue en tâche de fond 50ms après
    async def amorçage_sequentiel_app_live(*args):
        await asyncio.sleep(0.05)
        if hasattr(app, "declencher_changement_global"):
            app.declencher_changement_global()
        try:
            page.update()
        except Exception:
            pass

    page.run_task(amorçage_sequentiel_app_live)

if __name__ == "__main__":
    if hasattr(ft, "run"):
        ft.run(initialiser_application_flet)
    else:
        # Configuration réglementaire de production pointant le dossier d'actifs
        ft.app(target=initialiser_application_flet, assets_dir="assets")
