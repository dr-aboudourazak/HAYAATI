"""
ORGANISATEUR ET ROUTEUR CENTRAL DES ÉCRANS (GUI/APP_LAYOUT.PY)
Version 5.1 - Intégration du rafraîchissement géométrique réactif et de la propagation i18n descendante.
"""
import tkinter as tk
from tkinter import ttk

from gui.interface_finances import EcranFinances
from gui.interface_zakat import EcranZakat
from gui.interface_arbre import EcranArbre
from gui.interface_heritage import EcranHeritage
from gui.interface_testament import EcranTestament
from gui.interface_mouhasabah import EcranMouhasabah
from gui.interface_audit import InterfaceAudit
from gui.interface_encyclopedie import EcranEncyclopedie
from gui.interface_langue_arabe import EcranLangueArabe

from gui.interface_zakat_tiers import EcranZakatTiers
from gui.interface_heritage_tiers import EcranHeritageTiers

from gui.page_onboarding import PageOnboarding
from gui.page_inscription import PageInscription
from gui.page_connexion import PageConnexion
from gui.page_profil import PageProfil
from gui.page_reglages import PageReglages

from gui.langues import DICTIONNAIRE_LANGUES # Importation de la matrice globale

class OrganisateurLayout(tk.Frame):
    def __init__(self, parent, app_reference):
        super().__init__(parent, bg="#ffffff")
        self.app = app_reference
        self.ecrans = {}
        
        self.zone_contenu = tk.Frame(self, bg="#ffffff")
        self.zone_contenu.pack(fill=tk.BOTH, expand=True)
        
        self.initialiser_tous_les_ecrans()

    def initialiser_tous_les_ecrans(self):
        configuration_ecrans = {
            "ONBOARDING": (PageOnboarding, [self.app]),
            "INSCRIPTION": (PageInscription, [self.app]),
            "CONNEXION": (PageConnexion, [self.app]),
            "PROFIL": (PageProfil, [self.app]),
            "REGLAGES": (PageReglages, [self.app]),
            
            "FINANCES": (EcranFinances, [self.app]),
            "ZAKAT_LIVE": (EcranZakat, [self.app]),
            "ARBRE": (EcranArbre, [self.app]),
            "HERITAGE_LIVE": (EcranHeritage, [self.app]),
            "TESTAMENT": (EcranTestament, [self.app]),
            "MOUHASABAH": (EcranMouhasabah, [self.app]),
            
            "AUDIT": (InterfaceAudit, [self.app]),
            "ENCYCLOPEDIE": (EcranEncyclopedie, [self.app]),
            "LANGUE_ARABE": (EcranLangueArabe, [self.app]),
            
            "ZAKAT_TIERS": (EcranZakatTiers, [self.app]),
            "HERITAGE_TIERS": (EcranHeritageTiers, [self.app])
        }

        for cle, (classe_ecran, arguments) in configuration_ecrans.items():
            try:
                instance = classe_ecran(self.zone_contenu, *arguments)
                self.ecrans[cle] = instance
            except Exception as e:
                print(f"[LAYOUT ERROR] Initialisation compromise pour '{cle}': {str(e)}")

    def basculer_vers_ecran(self, cle_ecran):
        if cle_ecran not in self.ecrans:
            return

        # Masquer les autres écrans de la mémoire d'affichage
        for instance_ecran in self.ecrans.values():
            instance_ecran.pack_forget()

        ecran_cible = self.ecrans[cle_ecran]
        
        if hasattr(ecran_cible, "actualiser_donnees_affichage"):
            ecran_cible.actualiser_donnees_affichage()
        if hasattr(ecran_cible, "actualiser_contexte"):
            ecran_cible.actualiser_contexte()

        # Affichage plein écran de la cible
        ecran_cible.pack(fill=tk.BOTH, expand=True)
        
        # CRUCIAL POUR SMARTPHONE : Force l'écran qui apparaît à recalculer instantanément
        # sa grille et sa taille par rapport aux dimensions actuelles de la fenêtre de l'application
        self.update_idletasks()
        if hasattr(ecran_cible, "update"):
            ecran_cible.event_generate("<Configure>")

    def propager_changement_langue(self, nouvelle_langue):
        """
        Garantit la compatibilité ascendante avec la barre d'outils.
        Charge la langue globalement. Les écrans abonnés se mettront à jour d'eux-mêmes.
        """
        try:
            # Déclenche le chargement JSON et la notification automatique globale
            DICTIONNAIRE_LANGUES.moteur_i18n.charger_dictionnaire_langue(nouvelle_langue)
            self.app.txt_global = DICTIONNAIRE_LANGUES[nouvelle_langue]
        except Exception as e:
            print(f"[I18N ERROR] Échec de la mise à jour globale vers {nouvelle_langue} : {str(e)}")

        # Forcer la mise à jour immédiate de tous les écrans instanciés
        for cle, instance_ecran in self.ecrans.items():
            if hasattr(instance_ecran, "changer_langue"):
                try:
                    instance_ecran.changer_langue(nouvelle_langue)
                except Exception as e:
                    pass
            if hasattr(instance_ecran, "actualiser_donnees_affichage"):
                try:
                    instance_ecran.actualiser_donnees_affichage()
                except Exception as e:
                    pass
