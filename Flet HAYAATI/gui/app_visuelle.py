"""
ORCHESTRATEUR GRAPHIQUE ET CONTRÔLEUR DE SESSION MAÎTRE (GUI/APP_VISUELLE.PY)
Version Finale Intégrale Statique - Totalement compatible Flet 0.86.2, Python 3.14 & APK Android (Partie 1)
"""
from __future__ import annotations
import flet as ft
import threading

# 🎯 IMPORTS STATIQUES UNIFIÉS AU SOMMET : Plus aucun chargement paresseux masqué
from gui.app_layout import OrganisateurLayout
from gui.app_visuelle_toolbar import configurer_bandeau_superieur, dessiner_boutons_navigation
from core.sync_engine import SyncEngine
from gui.langues import DICTIONNAIRE_LANGUES

class ApplicationHayaati:
    def __init__(self, page: ft.Page, controleur_authentification=None):
        self.page = page
        self.controleur_auth = controleur_authentification
        self.sync_engine = SyncEngine()
        self.txt_global = DICTIONNAIRE_LANGUES.actif
        
        # --- REGISTRE DES VARIABLES PERSISTANTES DE SESSION ---
        self.est_mode_connecte = False
        self.mode_persistant_actif = False
        self.user_id_connecte = None
        self.nom_utilisateur_connecte = "Visiteur"
        self.email_utilisateur_connecte = ""
        
        # --- PARAMÈTRES ET POINTEURS DOCTRINAUX GLOBAUX ---
        self.devise_active = "XOF"
        self.langue_actuelle = "FR"
        self.madhhab_actif = "Malikite"
        self.ecran_courant = "ONBOARDING"
        self.mode_smartphone_actif = False
        
        # Variables de mémoire inter-modules (Zakat / Succession)
        self.cle_nisab_active_memoire = "PLUS_BAS"
        self.ville_utilisateur = "-"
        self.pays_utilisateur = "-"
        self.telephone_utilisateur = "-"

        # Configuration du canevas graphique Flet
        self.page.title = "HAYAATI"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = ft.Colors.WHITE
        
        self.barre_outils = ft.Container(bgcolor="#064e3b", height=65, padding=ft.Padding(10, 0, 10, 0))
        self.barre_navigation = ft.Container(bgcolor="#f3f4f6")
        self.layout_central = OrganisateurLayout(self)

        self.conteneur_corps_principal = ft.Container(expand=True)

        # 🎯 FIX DE RENDU DE PREMIER NIVEAU : Découplage strict pour libérer le focus des Dropdowns
        self.page.add(self.barre_outils)
        self.page.add(self.conteneur_corps_principal)

        configurer_bandeau_superieur(self)
        dessiner_boutons_navigation(self)
        
        # ❌ L'ANCIEN APPEL REDONDANT EST SUPPRIMÉ ICI POUR EVITER L'ERREUR CONTAINER
        
        self.page.on_resize = self.evaluer_format_ecran_responsive
        
        # 🎯 RECTIFICATION DIRECTE MOBILE : On planifie l'évaluation de façon thread-safe
        # pour attendre que le container soit physiquement ancré sur l'écran du téléphone
        if self.page:
            self.page.run_task(self.initialiser_contexte_global_mobile_securise)

    async def initialiser_contexte_global_mobile_securise(self, *args):
        """Cycle de vie asynchrone mobile : Force un double recalcul responsive à l'ouverture."""
        import asyncio
        await asyncio.sleep(0.15)  # Premier ancrage
        try:
            self.evaluer_format_ecran_responsive(None)
            if hasattr(self, "layout_central") and self.layout_central:
                self.layout_central.basculer_vers_ecran(self.ecran_courant)
            
            # 🎯 LE DOUBLE VERROU RESPONSIVE : On ré-évalue 200ms après pour écraser le bug d'affichage initial
            await asyncio.sleep(0.20)
            self.evaluer_format_ecran_responsive(None)
            self.page.update()
        except Exception:
            pass

    def evaluer_format_ecran_responsive(self, e):
        """Ajuste dynamiquement l'interface selon la taille de la fenêtre (PC vs Mobile)."""
        # 🛡️ SÉCURISATION MOBILE CRITIQUE : Si la page n'est pas encore prête, on avorte
        if not self.page or not self.conteneur_corps_principal:
            return

        largeur = self.page.width if self.page.width else 800
        nouveau_mode = largeur < 550
        
        if nouveau_mode:
            self.barre_navigation.width = None
            self.barre_navigation.height = 65
            self.layout_central.expand = True
            self.conteneur_corps_principal.content = ft.Column(
                controls=[self.layout_central, self.barre_navigation], expand=True, spacing=0
            )
        else:
            self.barre_navigation.width = 220
            self.barre_navigation.height = None
            self.layout_central.expand = True
            self.conteneur_corps_principal.content = ft.Row(
                controls=[self.barre_navigation, self.layout_central], expand=True, spacing=0, vertical_alignment=ft.CrossAxisAlignment.START
            )

        if nouveau_mode != self.mode_smartphone_actif:
            self.mode_smartphone_actif = nouveau_mode
            if hasattr(self, "barre_navigation") and self.barre_navigation and hasattr(self.barre_navigation, "page") and self.barre_navigation.page:
                dessiner_boutons_navigation(self)
                try: self.barre_navigation.update()
                except Exception: pass
            if hasattr(self, "conteneur_corps_principal") and self.conteneur_corps_principal and hasattr(self.conteneur_corps_principal, "page") and self.conteneur_corps_principal.page:
                try: self.conteneur_corps_principal.update()
                except Exception: pass
        else:
            # Force la mise à jour du conteneur si la page existe
            if hasattr(self.conteneur_corps_principal, "page") and self.conteneur_corps_principal.page:
                try: self.conteneur_corps_principal.update()
                except Exception: pass
                
        try: self.page.update()
        except Exception: pass

    def basculer_ecran(self, cle_ecran: str):
        """Route l'affichage vers l'écran désigné et gère le cycle de rafraîchissement."""
        self.ecran_courant = cle_ecran
        if hasattr(self, "layout_central") and self.layout_central:
            try: self.layout_central.basculer_vers_ecran(cle_ecran)
            except Exception: pass
        dessiner_boutons_navigation(self)
        if hasattr(self, "barre_navigation") and self.barre_navigation and hasattr(self.barre_navigation, "page") and self.barre_navigation.page:
            try: self.barre_navigation.update()
            except Exception: pass

    def changer_langue_globale(self, code_langue: str):
        """Bascule la langue maîtresse de l'application de façon thread-safe avec signature universelle."""
        self.langue_actuelle = code_langue.upper()
        
        # 🎯 FIX SIGNATURE : Utilisation de *args pour capter l'argument optionnel injecté par Flet 0.86.2
        async def tâche_changement_langue_decouple(*args):
            import asyncio
            await asyncio.sleep(0.05)  # Laisse le dropdown finaliser son animation interne
            
            if hasattr(self, "layout_central") and self.layout_central:
                try: self.layout_central.propager_changement_langue(self.langue_actuelle)
                except Exception: pass
                
            self.txt_global = DICTIONNAIRE_LANGUES.actif
            
            configurer_bandeau_superieur(self)
            dessiner_boutons_navigation(self)
            
            try:
                self.barre_outils.update()
                self.barre_navigation.update()
                self.page.update()
            except Exception:
                pass

        if self.page:
            self.page.run_task(tâche_changement_langue_decouple)

    def declencher_changement_global(self):
        """Force un rafraîchissement d'état complet de façon thread-safe avec signature universelle."""
        
        # 🎯 FIX SIGNATURE : Utilisation de *args pour capter l'argument optionnel injecté par Flet 0.86.2
        async def tâche_changement_global_decouple(*args):
            import asyncio
            await asyncio.sleep(0.05)  # Laisse le dropdown finaliser son animation interne
            
            self.txt_global = DICTIONNAIRE_LANGUES.actif
            configurer_bandeau_superieur(self)
            dessiner_boutons_navigation(self)
            
            if hasattr(self, "layout_central") and self.layout_central:
                try:
                    self.layout_central.basculer_vers_ecran(self.ecran_courant)
                except Exception:
                    pass
            
            try:
                self.barre_outils.update()
                self.barre_navigation.update()
                self.page.update()
            except Exception:
                pass

        if self.page:
            self.page.run_task(tâche_changement_global_decouple)

    def executer_connexion_session(self, user_id, username, email):
        """Instancie les verrous de session connectée premium, synchronise le profil et sécurise l'aiguillage."""
        self.est_mode_connecte = True
        self.mode_persistant_actif = True
        self.user_id_connecte = user_id
        self.nom_utilisateur_connecte = str(username).upper()
        self.email_utilisateur_connecte = email
        
        # 🎯 LE VERROU ANTI-FANTÔME CRITIQUE : Mutation synchrone de l'aiguillage courant
        # On force la destination vers l'Accueil avant que le déclencheur global ne repeuple l'IHM
        self.ecran_courant = "ONBOARDING"

        try:
            c_p = self.sync_engine.charger_donnees_module(user_id, "PREFERENCES")
            if c_p: 
                self.cle_nisab_active_memoire = str(c_p.get("arbitrage_nisab", "PLUS_BAS")).upper()
            
            c_arb = self.sync_engine.charger_donnees_module(user_id, "PROFIL")
            if c_arb:
                self.ville_utilisateur = c_arb.get("ville", "-")
                self.pays_utilisateur = c_arb.get("pays", "-")
                self.telephone_utilisateur = c_arb.get("tel", "-")
        except Exception: 
            pass

        # 🎯 PURGE DE LA MÉMOIRE VIVE : Élimine l'ancienne instance de l'écran d'authentification
        if hasattr(self, "layout_central") and self.layout_central:
            if hasattr(self.layout_central, "ecrans_instances"):
                self.layout_central.ecrans_instances.clear()

        # Déclenchement de la reconstruction saine et synchrone des barres et sous-onglets
        self.declencher_changement_global()

        # Injection physique Material 3 immédiate à l'écran après connexion
        if hasattr(self, "layout_central") and self.layout_central:
            try:
                self.layout_central.basculer_vers_ecran("ONBOARDING")
            except Exception:
                pass

    def executer_deconnexion_session(self):
        """Purge proprement les verrous de session et bascule en mode Visiteur anonyme de façon étanche."""
        # 🛡️ ÉTAPE 1 — PURGE SYNCHRONE IMMÉDIATE DES DONNÉES SENSIBLES
        # Cette section DOIT s'exécuter même si l'UI est inaccessible (arrière-plan)
        self.est_mode_connecte = False
        self.mode_persistant_actif = False
        self.user_id_connecte = None
        self.nom_utilisateur_connecte = "Visiteur"
        self.email_utilisateur_connecte = ""
        self.ecran_courant = "ONBOARDING"
        self.cle_nisab_active_memoire = "PLUS_BAS"
        self.ville_utilisateur = "-"
        self.pays_utilisateur = "-"
        self.telephone_utilisateur = "-"
        
        # 🛡️ ÉTAPE 2 — VIDAGE DU CACHE D'ÉCRANS (détruit les fantômes de session)
        if hasattr(self, "layout_central") and self.layout_central:
            if hasattr(self.layout_central, "ecrans_instances"):
                self.layout_central.ecrans_instances.clear()
            if hasattr(self.layout_central, "historique_navigation"):
                self.layout_central.historique_navigation.clear()
        
        # 🛡️ ÉTAPE 3 — RECONSTRUCTION UI (best-effort, chaque appel isolé)
        from gui.app_visuelle_toolbar import configurer_bandeau_superieur, dessiner_boutons_navigation
        try:
            configurer_bandeau_superieur(self)
        except Exception:
            pass
        try:
            dessiner_boutons_navigation(self)
        except Exception:
            pass
        
        # 🛡️ ÉTAPE 4 — ROUTAGE VERS ONBOARDING (best-effort)
        if hasattr(self, "layout_central") and self.layout_central:
            try:
                self.layout_central.basculer_vers_ecran("ONBOARDING")
            except Exception:
                pass
        
        # 🛡️ ÉTAPE 5 — RAFRAÎCHISSEMENT GLOBAL (asynchrone, non-bloquant)
        try:
            self.declencher_changement_global()
        except Exception:
            pass
