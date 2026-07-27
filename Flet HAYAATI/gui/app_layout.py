"""
ORGANISATEUR ET ROUTEUR CENTRAL DES ÉCRANS (GUI/APP_LAYOUT.PY)
Version Finale Intégrale Statique - Totalement compatible Flet 0.86.2, Python 3.14 & APK Android
"""
from __future__ import annotations
import flet as ft
from gui.langues import DICTIONNAIRE_LANGUES

# 🎯 IMPORTS STATIQUES UNIFIÉS AU SOMMET : Éradication totale du Lazy Loading Tkinter
from gui.pages.page_onboarding import PageOnboarding
from gui.pages.page_inscription import PageInscription
from gui.pages.page_connexion import PageConnexion
from gui.pages.page_profil import PageProfil
from gui.pages.page_reglages import PageReglages

from gui.components.interface_finances import EcranFinances
from gui.components.interface_zakat import EcranZakat
from gui.components.interface_arbre import EcranArbre
from gui.components.interface_heritage import EcranHeritage
from gui.components.interface_testament import EcranTestament
from gui.components.interface_mouhasabah import EcranMouhasabah
from gui.components.interface_audit import InterfaceAudit 

# Coquilles d'IHM temporaires pour la compilation (À remplacer au fil de la migration)
from gui.components.interface_zakat_tiers import EcranZakatTiers
from gui.components.interface_heritage_tiers import EcranHeritageTiers

class OrganisateurLayout(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.page_flet = app_reference.page
        self.ecrans_instances: dict[str, ft.Container] = {}
        
        # Cartographie stricte des classes pour Flet 0.86.2
        self.configuration_ecrans = {
            "ONBOARDING": PageOnboarding,
            "INSCRIPTION": PageInscription,
            "CONNEXION": PageConnexion,
            "PROFIL": PageProfil,
            "REGLAGES": PageReglages,
            
            "FINANCES": EcranFinances,
            "ZAKAT_LIVE": EcranZakat,
            "ARBRE": EcranArbre,
            "HERITAGE_LIVE": EcranHeritage,
            "TESTAMENT": EcranTestament,
            "MOUHASABAH": EcranMouhasabah,
            "AUDIT": InterfaceAudit,            
            "ZAKAT_TIERS": EcranZakatTiers,
            "HERITAGE_TIERS": EcranHeritageTiers
        }
        
        super().__init__(expand=True, bgcolor=ft.Colors.WHITE, alignment=ft.Alignment(0, -1))

    def basculer_vers_ecran(self, cle_ecran: str):
        """Orchestre le changement d'écran de manière fluide à l'intérieur du Container."""
        self.app.ecran_courant = cle_ecran
        
        if cle_ecran not in self.ecrans_instances:
            classe_cible = self.configuration_ecrans.get(cle_ecran)
            if classe_cible:
                self.ecrans_instances[cle_ecran] = classe_cible(self.app)
                
        if cle_ecran in self.ecrans_instances:
            instance_active = self.ecrans_instances[cle_ecran]
            
            if hasattr(instance_active, "actualiser_donnees_affichage"):
                instance_active.actualiser_donnees_affichage()
                
            # Assignation de l'écran comme contenu unique du Container
            self.content = instance_active
            
        # 🎯 UNIFICATION DU RAFRAÎCHISSEMENT : Un seul appel synchrone et léger pour Flet
        try:
            self.update()
        except Exception:
            pass

    def propager_changement_langue(self, nouvelle_langue: str):
        """Purge les instances en cache pour forcer la relocalisation textuelle complète."""
        try:
            # Rechargement forcé du fichier JSON sur le disque dur
            DICTIONNAIRE_LANGUES.moteur_i18n.charger_dictionnaire_langue(nouvelle_langue)
            self.app.txt_global = DICTIONNAIRE_LANGUES.actif
        except Exception as e:
            print(f"[I18N ERROR] Échec de la mise à jour globale vers {nouvelle_langue} : {str(e)}")

        # Vider le cache pour reconstruire l'IHM active avec ses nouveaux libellés
        self.ecrans_instances.clear()
