"""
ORGANISATEUR ET ROUTEUR CENTRAL DES ÉCRANS (GUI/APP_LAYOUT.PY)
Version 5.2 — Correction affichage vide au premier lancement : 
              actualiser_donnees_affichage() appelé après le montage réel
              de l'écran (self.update()), plus avant. L'appel précédent,
              placé avant self.update(), tombait systématiquement sur un
              RuntimeError côté PageOnboarding (self.page pas encore
              défini), avalé silencieusement — d'où la page visiteur vide
              au premier lancement, corrigée seulement par le minuteur de
              secours à 0.3s de PageOnboarding, lui-même pas toujours
              gagnant contre les autres tâches asynchrones du démarrage
              (scheduler, HayaatiAlarm, permissions).
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
        self._skip_next_history: bool = False  # 🆕 Garde-fou anti-circulaire

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
            "ENCYCLOPEDIE": PageEncyclopedie,
            "LANGUE_ARABE": PageLangueArabe,
            "SCIENCES_ISLAMIQUES": PageSciencesIslamiques,
            "MADRASSA": PageMadrassa,
        }

        super().__init__(expand=True, bgcolor=ft.Colors.WHITE, alignment=ft.Alignment(0, -1), padding=0)

        if self.page_flet:
            self.page_flet.layout_principal = self

    def basculer_vers_ecran(self, cle_ecran: str, skip_historique: bool = False):
        """Orchestre le changement d'écran avec historique de navigation."""
        ecran_actuel = getattr(self.page_flet, "ecran_courant", None)
        if ecran_actuel and ecran_actuel != cle_ecran:
            # 🆕 Empêche l'ajout circulaire quand on revient d'un retour arrière
            if not skip_historique and not self._skip_next_history:
                self.historique_navigation.append(ecran_actuel)
                if len(self.historique_navigation) > 10:
                    self.historique_navigation.pop(0)
            self._skip_next_history = False

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

        try:
            self.update()
        except Exception:
            pass

        # 🆕 Correction 04/09/2026 : actualiser_donnees_affichage() est
        # désormais appelé APRÈS self.update(), une fois l'instance
        # réellement montée sur la page (instance_active.page défini).
        # Avant, cet appel se faisait juste après self.content = ...,
        # donc avant tout montage réel côté client — instance_active.page
        # levait un RuntimeError, avalé silencieusement dans les pages
        # qui protègent leur appel à self.update() par un try/except
        # (PageOnboarding en particulier). C'était la vraie cause de la
        # page visiteur qui restait vide au premier lancement : ce n'était
        # pas une question de lenteur ou de poids de la page, l'appel
        # échouait de façon déterministe à chaque toute première
        # construction d'un écran, indépendamment de la vitesse du
        # téléphone.
        if cle_ecran in self.ecrans_instances:
            instance_active = self.ecrans_instances[cle_ecran]
            if hasattr(instance_active, "actualiser_donnees_affichage"):
                instance_active.actualiser_donnees_affichage()

    def revenir_ecran_precedent(self) -> bool:
        """Retourne à l'écran précédent dans l'historique. Retourne True si OK, False si vide."""
        if self.historique_navigation:
            ecran_precedent = self.historique_navigation.pop()
            print(f"[NAV] Retour arrière → {ecran_precedent}")
            self._skip_next_history = True  # 🆕 Empêche le ré-ajout de l'écran actuel
            self.basculer_vers_ecran(ecran_precedent)
            return True
        print("[NAV] Historique vide — fermeture de l'app")
        return False

    def vider_historique(self):
        self.historique_navigation.clear()

    def propager_changement_langue(self, nouvelle_langue: str):
        try:
            DICTIONNAIRE_LANGUES.moteur_i18n.charger_dictionnaire_langue(nouvelle_langue)
            # self.app.txt_global est désormais une propriété vivante (voir ApplicationHayaati) :
            # plus besoin de la réaffecter ici, elle reflète déjà DICTIONNAIRE_LANGUES.actif.
        except Exception as e:
            print(f"[I18N ERROR] Échec de la mise à jour globale vers {nouvelle_langue} : {str(e)}")

        self.ecrans_instances.clear()
        self.historique_navigation.clear()
