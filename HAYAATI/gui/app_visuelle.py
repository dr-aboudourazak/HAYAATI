"""
ORCHESTRATEUR GRAPHIQUE ET CONTRÔLEUR DE SESSION MAÎTRE (GUI/APP_VISUELLE.PY)
Version 3.4 — Correction du patron hasattr(x, "page") and x.page, cassé
              partout dans ce fichier : hasattr() ne protège que contre
              AttributeError, alors que Flet lève un RuntimeError explicite
              quand un contrôle n'est pas encore monté sur la page
              ("Control must be added to the page first"). Ce RuntimeError
              remontait donc sans être intercepté, faisant planter
              silencieusement des tâches asynchrones en arrière-plan
              (visible en logcat/console comme "exception calling callback
              for Future", sans crash de l'app mais avec des mises à jour
              d'interface sautées en plein milieu). Remplacé par
              _est_monte(), qui capture explicitement RuntimeError.
"""
from __future__ import annotations
import sys
import flet as ft

from gui.app_layout import OrganisateurLayout
from gui.app_visuelle_toolbar import configurer_bandeau_superieur, dessiner_boutons_navigation
from core.sync_engine import SyncEngine
from gui.langues import DICTIONNAIRE_LANGUES


def _est_monte(control) -> bool:
    """Vérifie qu'un contrôle Flet est réellement monté sur la page,
    sans jamais laisser remonter le RuntimeError que Flet lève pour un
    contrôle pas encore attaché. hasattr(control, "page") ne suffit pas :
    hasattr() n'avale qu'AttributeError, pas RuntimeError."""
    if control is None:
        return False
    try:
        return control.page is not None
    except RuntimeError:
        return False


class ApplicationHayaati:
    def __init__(self, page: ft.Page, controleur_authentification=None):
        self.page = page
        self.controleur_auth = controleur_authentification
        self.sync_engine = SyncEngine()

        self.est_mode_connecte = False
        self.mode_persistant_actif = False
        self.user_id_connecte = None
        self.nom_utilisateur_connecte = "Visiteur"
        self.email_utilisateur_connecte = ""

        self.devise_active = "XOF"
        self.langue_actuelle = "FR"
        self.madhhab_actif = "Malikite"
        self.ecran_courant = "ONBOARDING"
        self.mode_smartphone_actif = False

        self.cle_nisab_active_memoire = "PLUS_BAS"
        self.ville_utilisateur = "-"
        self.pays_utilisateur = "-"
        self.telephone_utilisateur = "-"

        self.page.title = "HAYAATI"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = ft.Colors.WHITE

        self.barre_outils = ft.Container(bgcolor="#064e3b", height=65, padding=ft.Padding(10, 0, 10, 0))
        self.barre_navigation = ft.Container(bgcolor="#f3f4f6")
        self.layout_central = OrganisateurLayout(self)

        self.conteneur_corps_principal = ft.Container(expand=True)

        # SafeArea retiré du bandeau. Le padding top pour la barre de
        # statut mobile est géré dynamiquement dans
        # configurer_bandeau_superieur() (app_visuelle_toolbar.py).
        self.zone_barre_outils_safe = ft.Container(content=self.barre_outils, expand=False)

        self.page.controls.extend([self.zone_barre_outils_safe, self.conteneur_corps_principal])

        configurer_bandeau_superieur(self)
        dessiner_boutons_navigation(self)

        self.page.on_resize = self.evaluer_format_ecran_responsive

    @property
    def txt_global(self):
        return DICTIONNAIRE_LANGUES.actif or {}

    @txt_global.setter
    def txt_global(self, valeur):
        pass

    def evaluer_format_ecran_responsive(self, e):
        # 🆕 04/09/2026 : verrou de réentrance. Reconstruire le contenu et
        # appeler page.update() à chaque resize, même quand le mode n'a
        # pas changé, pouvait redéclencher un nouvel événement de resize
        # avant la fin du précédent, provoquant une boucle sans fin
        # (rafale de mises à jour, connexion saturée, réinitialisation
        # complète de session en cascade). Ce verrou bloque tout appel
        # imbriqué pendant qu'un premier est encore en cours.
        if getattr(self, "_resize_en_cours", False):
            return
        self._resize_en_cours = True
        try:
            self._evaluer_format_ecran_responsive_impl(e)
        finally:
            self._resize_en_cours = False

    def _evaluer_format_ecran_responsive_impl(self, e):
        if not self.page or not self.conteneur_corps_principal:
            return

        plateforme = str(getattr(self.page, "platform", "") or "").upper()
        est_plateforme_mobile = plateforme in ("ANDROID", "IOS") or hasattr(sys, "getandroidapilevel")

        largeur = self.page.width
        if largeur is None or largeur == 0:
            largeur = 400 if est_plateforme_mobile else 800
            print(f"[RESPONSIVE] Width indisponible — fallback {largeur}px "
                  f"({'Android/iOS' if est_plateforme_mobile else 'Desktop'})")

        nouveau_mode = est_plateforme_mobile or largeur < 550

        # 🆕 04/09/2026 : si rien n'a réellement changé depuis le dernier
        # appel traité (ni le mode, ni la largeur de façon significative),
        # on ne reconstruit rien et on n'appelle aucun update(). Le verrou
        # de réentrance ci-dessus ne protège que les appels imbriqués dans
        # la même pile ; celui-ci protège aussi contre une rafale d'appels
        # séparés et successifs, le vrai scénario probable d'une boucle de
        # rétroaction resize → update → resize.
        derniere_largeur = getattr(self, "_derniere_largeur_traitee", None)
        mode_inchange = (nouveau_mode == self.mode_smartphone_actif)
        largeur_stable = (derniere_largeur is not None and abs(largeur - derniere_largeur) < 5)
        if mode_inchange and largeur_stable and self.conteneur_corps_principal.content is not None:
            return
        self._derniere_largeur_traitee = largeur

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
            if _est_monte(self.barre_navigation):
                dessiner_boutons_navigation(self)
                try: self.barre_navigation.update()
                except Exception: pass
            if _est_monte(self.conteneur_corps_principal):
                try: self.conteneur_corps_principal.update()
                except Exception: pass
        else:
            if _est_monte(self.conteneur_corps_principal):
                try: self.conteneur_corps_principal.update()
                except Exception: pass

        try: self.page.update()
        except Exception: pass

    def basculer_ecran(self, cle_ecran: str):
        self.ecran_courant = cle_ecran
        if hasattr(self, "layout_central") and self.layout_central:
            try: self.layout_central.basculer_vers_ecran(cle_ecran)
            except Exception: pass
        dessiner_boutons_navigation(self)
        if _est_monte(self.barre_navigation):
            try: self.barre_navigation.update()
            except Exception: pass

    def changer_langue_globale(self, code_langue: str):
        self.langue_actuelle = code_langue.upper()

        async def tache_changement_langue_decouple(*args):
            import asyncio
            await asyncio.sleep(0.05)

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

            if hasattr(self, "notification_scheduler") and self.notification_scheduler:
                try:
                    if self.page:
                        self.page.run_task(self.notification_scheduler.reschedule_all, 30)
                except Exception as exc:
                    print(f"[LANGUE] Replanification des notifications échouée : {exc}")

        if self.page:
            self.page.run_task(tache_changement_langue_decouple)

    def declencher_changement_global(self):
        async def tache_changement_global_decouple(*args):
            import asyncio
            await asyncio.sleep(0.05)

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
            self.page.run_task(tache_changement_global_decouple)

    def executer_connexion_session(self, user_id, username, email):
        self.est_mode_connecte = True
        self.mode_persistant_actif = True
        self.user_id_connecte = user_id
        self.nom_utilisateur_connecte = str(username).upper()
        self.email_utilisateur_connecte = email
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

        if hasattr(self, "layout_central") and self.layout_central:
            if hasattr(self.layout_central, "ecrans_instances"):
                self.layout_central.ecrans_instances.clear()

        # 🆕 04/09/2026 : l'appel explicite à basculer_vers_ecran("ONBOARDING")
        # qui suivait ici a été retiré. declencher_changement_global() bascule
        # déjà vers self.ecran_courant (déjà "ONBOARDING" à ce stade, fixé
        # trois lignes plus haut). Les deux appels quasi simultanés
        # construisaient chacun leur propre instance de PageOnboarding et
        # programmaient chacun leur propre tâche de fond via page.run_task(),
        # provoquant des erreurs "session détruite" en cascade au moment
        # précis de la connexion.
        self.declencher_changement_global()

    def executer_deconnexion_session(self):
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

        if hasattr(self, "layout_central") and self.layout_central:
            if hasattr(self.layout_central, "ecrans_instances"):
                self.layout_central.ecrans_instances.clear()
            if hasattr(self.layout_central, "historique_navigation"):
                self.layout_central.historique_navigation.clear()

        from gui.app_visuelle_toolbar import configurer_bandeau_superieur, dessiner_boutons_navigation
        try:
            configurer_bandeau_superieur(self)
        except Exception:
            pass
        try:
            dessiner_boutons_navigation(self)
        except Exception:
            pass

        # 🆕 04/09/2026 : appel direct à basculer_vers_ecran("ONBOARDING")
        # retiré ici aussi, pour la même raison qu'en connexion —
        # declencher_changement_global(), juste en dessous, bascule déjà
        # vers self.ecran_courant. Le doublon provoquait la même
        # instabilité de session qu'à la connexion.
        try:
            self.declencher_changement_global()
        except Exception:
            pass
