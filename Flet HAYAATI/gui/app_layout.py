"""
ORGANISATEUR ET ROUTEUR CENTRAL DES ÉCRANS (GUI/APP_LAYOUT.PY)
Version 5.0 — Intégration Encyclopédie, Langue arabe, Sciences islamiques
"""
from __future__ import annotations
import sys
import flet as ft
from gui.langues import DICTIONNAIRE_LANGUES

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

from gui.components.interface_zakat_tiers import EcranZakatTiers
from gui.components.interface_heritage_tiers import EcranHeritageTiers

from gui.pages.page_devoirs import PageDevoirs
from gui.pages.page_inventaire import PageInventaire

# 🆕 NOUVEAUX ÉCRANS INTÉGRÉS
from gui.pages.page_encyclopedie import PageEncyclopedie
from gui.pages.page_langue_arabe import PageLangueArabe
from gui.pages.page_sciences_islamiques import PageSciencesIslamiques
from gui.pages.page_madrassa import PageMadrassa


class OrganisateurLayout(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.page_flet = app_reference.page
        self.ecrans_instances: dict[str, ft.Container] = {}
        self.historique_navigation: list[str] = []

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
            "ZAKAT_TIERS": EcranZakatTiers,
            "HERITAGE_TIERS": EcranHeritageTiers,
            "DEVOIRS": PageDevoirs,
            "INVENTAIRE": PageInventaire,
            # 🆕 Nouvelles entrées de routage
            "ENCYCLOPEDIE": PageEncyclopedie,
            "LANGUE_ARABE": PageLangueArabe,
            "SCIENCES_ISLAMIQUES": PageSciencesIslamiques,
            "MADRASSA": PageMadrassa,
        }

        super().__init__(expand=True, bgcolor=ft.Colors.WHITE, alignment=ft.Alignment(0, -1), padding=0)

        if self.page_flet:
            self.page_flet.layout_principal = self

    def basculer_vers_ecran(self, cle_ecran: str):
        """Orchestre le changement d'écran avec historique de navigation."""
        ecran_actuel = getattr(self.page_flet, "ecran_courant", None)
        if ecran_actuel and ecran_actuel != cle_ecran:
            self.historique_navigation.append(ecran_actuel)
            if len(self.historique_navigation) > 10:
                self.historique_navigation.pop(0)

        self.app.ecran_courant = cle_ecran
        if self.page_flet:
            self.page_flet.ecran_courant = cle_ecran

        if cle_ecran not in self.ecrans_instances:
            classe_cible = self.configuration_ecrans.get(cle_ecran)
            if classe_cible:
                self.ecrans_instances[cle_ecran] = classe_cible(self.app)

        if cle_ecran in self.ecrans_instances:
            instance_active = self.ecrans_instances[cle_ecran]
            self.content = instance_active
            if hasattr(instance_active, "actualiser_donnees_affichage"):
                instance_active.actualiser_donnees_affichage()

        try:
            self.update()
        except Exception:
            pass

    def revenir_ecran_precedent(self) -> bool:
        if self.historique_navigation:
            ecran_precedent = self.historique_navigation.pop()
            print(f"[NAV] Retour arrière → {ecran_precedent}")
            self.basculer_vers_ecran(ecran_precedent)
            return True
        print("[NAV] Historique vide — pas de retour possible")
        return False

    def vider_historique(self):
        self.historique_navigation.clear()

    def propager_changement_langue(self, nouvelle_langue: str):
        try:
            DICTIONNAIRE_LANGUES.moteur_i18n.charger_dictionnaire_langue(nouvelle_langue)
            self.app.txt_global = DICTIONNAIRE_LANGUES.actif
        except Exception as e:
            print(f"[I18N ERROR] Échec de la mise à jour globale vers {nouvelle_langue} : {str(e)}")

        self.ecrans_instances.clear()
        self.historique_navigation.clear()
