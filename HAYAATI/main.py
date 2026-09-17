"""
HAYAATI — POINT D'ENTRÉE OFFICIEL v3.6
Migration alarme : remplacement total de PyJnius / JNI par l'extension
Flet native hayaati_alarm (plugin Flutter alarm v5+).

── Journal des corrections (01/09/2026) ──────────────────────────────
v3.6 :
  • Import corrigé : from hayaati_alarm import HayaatiAlarm (l'ancien
    from flet_hayaati_alarm import HayaatiAlarm ne correspondait à rien
    de réellement installé, échec silencieux intercepté par le
    except Exception plus bas — jamais visible sans lire les logs).
  • _AlarmServiceMock (utilisé sur PC uniquement) rendu asynchrone :
    toutes les méthodes de HayaatiAlarm sont désormais des coroutines
    (_invoke_method() de ft.Service en est une dans cette version de
    Flet), et notification_scheduler.py les appelle maintenant avec
    await. Le mock devait suivre la même forme, sinon
    "await self.alarm_service.set_alarm(...)" lève un TypeError sur PC
    (on ne peut pas awaiter une fonction synchrone).
  • await ajouté sur schedule_prayer_period(30), pour la même raison :
    cette méthode est devenue async côté notification_scheduler.py.
─────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations
import os
import sys
import uuid
import warnings
import asyncio
import flet as ft

from gui.app_visuelle import ApplicationHayaati
from gui.langues import DICTIONNAIRE_LANGUES
import core.database_manager as db_module

warnings.filterwarnings("ignore", category=DeprecationWarning)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

_IS_ANDROID = (
    hasattr(sys, "getandroidapilevel")
    or "ANDROID_BOOTLOGO" in os.environ
    or "ANDROID_ROOT" in os.environ
)

APPLICATION_HAYAATI_INSTANCE: ApplicationHayaati | None = None


class ControleurVisiteurGenerique:
    def __init__(self, chemin=""):
        self.chemin = chemin

    def modifier_donnees_profil_securite(self, *args, **kwargs):
        return False, "Indisponible."

    def sauvegarder_preferences_reglages(self, *args, **kwargs):
        return False, "Indisponible."

    def enregistrer_feedback_utilisateur(self, *args, **kwargs):
        return False, "Indisponible."

    def verifier_connexion_utilisateur(self, *args, **kwargs):
        return False, None, "Mode visiteur actif."

    def enregistrer_nouvel_utilisateur(self, *args, **kwargs):
        return False, "Mode visiteur actif."


def initialiser_application_flet(page: ft.Page):
    global APPLICATION_HAYAATI_INSTANCE

    if _IS_ANDROID:
        try:
            from plyer import notification
            notification.notify(
                title="HAYAATI",
                message="Initialisation des systèmes de vigilance...",
                timeout=1
            )
        except Exception:
            pass

    page.title = "HAYAATI"

    def action_bouton_retour_physique(e):
        try:
            if hasattr(page, "layout_principal") and page.layout_principal:
                routeur = page.layout_principal
                if hasattr(routeur, "revenir_ecran_precedent"):
                    retour_ok = routeur.revenir_ecran_precedent()
                    if retour_ok:
                        return
            page.window_destroy()
        except Exception as exc:
            print(f"[BACK BUTTON] Erreur : {exc}")
            try:
                page.window_destroy()
            except Exception:
                pass

    page.on_back_button = action_bouton_retour_physique

    def executer_purge_securite_immediate():
        global APPLICATION_HAYAATI_INSTANCE
        if APPLICATION_HAYAATI_INSTANCE and getattr(APPLICATION_HAYAATI_INSTANCE, "est_mode_connecte", False):
            try:
                APPLICATION_HAYAATI_INSTANCE.executer_deconnexion_session()
                print("[SECURITY SHIELD] Session detruite.")
                try:
                    page.update()
                except Exception:
                    pass
            except Exception as err:
                print(f"[SECURITY ERROR] Echec purge : {str(err)}")

    _shield = {"pret": False}

    def gerer_evenements_fenetre_pc(e):
        signal = str(getattr(e, "data", "")).lower().strip()
        print(f"[WINDOW DIAGNOSTIC] Signal PC : {signal}")
        if "focus" in signal or "show" in signal:
            _shield["pret"] = True
            if APPLICATION_HAYAATI_INSTANCE and not getattr(APPLICATION_HAYAATI_INSTANCE, "est_mode_connecte", False):
                try:
                    APPLICATION_HAYAATI_INSTANCE.declencher_changement_global()
                except Exception:
                    pass
            return
        if _shield["pret"] and ("minimize" in signal or "hide" in signal):
            executer_purge_securite_immediate()

    def gerer_fermeture_fenetre(e):
        print("[WINDOW CLOSE] Fermeture — purge securisee...")
        executer_purge_securite_immediate()
        page.window_destroy()

    def gerer_cycle_de_vie_mobile(e: ft.AppLifecycleChangeEvent):
        if not _IS_ANDROID:
            return
        etat = str(e.state).lower().strip()
        print(f"[LIFECYCLE DIAGNOSTIC] Etat Mobile : {etat}")
        if "resume" in etat or "show" in etat:
            _shield["pret"] = True
            if APPLICATION_HAYAATI_INSTANCE:
                try:
                    APPLICATION_HAYAATI_INSTANCE.declencher_changement_global()
                except Exception:
                    pass
            return
        if _shield["pret"] and ("pause" in etat or "hidden" in etat or "detach" in etat or "inactive" in etat):
            executer_purge_securite_immediate()

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

    page.fonts = {
        "NotoSansArabic": "fonts/NotoSansArabic-Regular.ttf",
        "NotoSansSC": "fonts/NotoSansSC-Regular.ttf"
    }

    page.safe_area = True
    page.padding = 0

    def on_page_resized(e):
        try:
            page.update()
            print(f"[RESIZE] Viewport : {page.width:.0f}x{page.height:.0f}")
        except Exception:
            pass

    page.on_resize = on_page_resized

    alarm_service = None
    if _IS_ANDROID:
        try:
            from hayaati_alarm import HayaatiAlarm
            alarm_service = HayaatiAlarm()
            # Correction 03/09/2026 : un Service Flet doit être enregistré
            # via page.services.append(), pas page.add(). page.add() est
            # réservé à l'arbre visuel — c'est ce qui empêchait init() de
            # se déclencher côté Dart, malgré une extension par ailleurs
            # correctement enregistrée (confirmé par tous les exemples
            # officiels de services Flet : ScreenBrightness,
            # UserAccelerometer, etc., qui utilisent tous
            # page.services.append()).
            page.services.append(alarm_service)
            page.update()
            print("[ALARM SERVICE] HayaatiAlarm injecté dans page.services.")
        except Exception as e:
            print(f"[ALARM SERVICE] Erreur initialisation : {e}")
    else:
        class _AlarmServiceMock:
            """Mock utilisé sur PC (aucune alarme native n'existe hors
            Android). Toutes les méthodes sont async pour matcher
            exactement la forme de la vraie classe HayaatiAlarm, dont
            chaque méthode attend désormais _invoke_method() (une
            coroutine dans cette version de Flet). Sans ce mimétisme,
            "await self.alarm_service.set_alarm(...)" lèverait un
            TypeError sur PC, puisqu'on ne peut pas awaiter une
            fonction synchrone."""
            async def set_alarm(self, **kwargs):
                print(f"[ALARM MOCK] set_alarm appelé (PC — aucune action) : id={kwargs.get('id')}")
            async def cancel_alarm(self, id):
                print(f"[ALARM MOCK] cancel_alarm({id}) (PC)")
            async def stop_all_alarms(self):
                print("[ALARM MOCK] stop_all_alarms() (PC)")
            async def request_permissions(self):
                return True
            async def request_exact_alarm_permission(self):
                return True
            async def request_full_screen_intent_permission(self):
                return True
        alarm_service = _AlarmServiceMock()
        print("[ALARM SERVICE] Mode PC — mock async actif.")

    chemin_db = os.path.join("core", "hayaati_private.db")

    try:
        if hasattr(db_module, "DatabaseManager"):
            manager_brut = db_module.DatabaseManager(chemin_db)
            print("[SQLITE SUCCESS] DatabaseManager initialise.")

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
        print(f"[SQLITE WARNING] Contournement : {str(e)}")

    app = ApplicationHayaati(page=page, controleur_authentification=controleur_auth)
    app.controleur_auth = controleur_auth
    APPLICATION_HAYAATI_INSTANCE = app

    try:
        from core.notification_scheduler import NotificationScheduler
        # ⚠️ 08/09/2026 : lat=6.13, lng=1.22 (Lomé) retirés. Ces valeurs
        # neutralisaient la correction faite dans notification_scheduler.py,
        # qui lit désormais les coordonnées depuis AgendaEngine par défaut
        # quand lat/lng ne sont pas fournis explicitement — un argument
        # explicite gagne toujours contre un défaut, donc tant que ces deux
        # valeurs restaient ici, la correction ne pouvait jamais s'appliquer.
        app.notification_scheduler = NotificationScheduler(
            page=page,
            calc_method="MuslimWorldLeague",
            madhab="shafi",
            alarm_service=alarm_service,
        )
        print("[SCHEDULER] NotificationScheduler instancié.")

        async def demarrer_scheduler_hayaati():
            await asyncio.sleep(0.3)

            # 🆕 08/09/2026 : tentative de géolocalisation native (GPS/réseau),
            # plus précise que la détection par IP. Le repli IP tourne déjà
            # en arrière-plan depuis le tout premier AgendaEngine()
            # instancié (via NotificationScheduler.__init__ plus haut) :
            # si la tentative GPS échoue ou expire, la position déjà en
            # cache (IP ou valeur de secours) reste utilisée sans rien à
            # faire de plus ici.
            try:
                from core.geolocation_natif import tenter_geolocalisation_native
                await tenter_geolocalisation_native(page)
            except Exception as exc:
                print(f"[SCHEDULER] Géolocalisation native indisponible : {exc}")

            # ⚠️ 08/09/2026 : le madhhab réel de l'utilisateur (app.madhhab_actif,
            # ex. "Malikite", "Hanafite"...) n'est chargé depuis les préférences
            # qu'après la création du scheduler ci-dessus, qui démarre donc
            # toujours avec "shafi" par défaut. Ça reste correct pour Malikite/
            # Chafiite/Hanbalite, qui partagent la même convention Asr à une
            # ombre, mais c'est faux pour un utilisateur Hanafite (deux ombres,
            # Asr plus tardif). On resynchronise ici, juste avant de programmer
            # les alarmes, une fois app.madhhab_actif réellement disponible.
            madhhab_utilisateur = str(getattr(app, "madhhab_actif", "Malikite")).strip().capitalize()
            app.notification_scheduler.madhab = "hanafi" if madhhab_utilisateur == "Hanafite" else "shafi"
            print(f"[SCHEDULER] Madhhab synchronisé pour l'Asr : {madhhab_utilisateur} → {app.notification_scheduler.madhab}")

            await app.notification_scheduler.bootstrap()

            # 🆕 08/09/2026 : app.horaires_prieres_aujourdhui n'était fixé
            # nulle part dans le projet. page_onboarding.py, page_onboarding_alerts.py
            # et interface_mouhasabah.py s'en servent tous pour décider de
            # l'heure de bascule du jour Sharia (Fajr - 1h), mais retombaient
            # systématiquement sur le "05:00" de secours, quels que soient la
            # position et la saison réelles. On le calcule ici avec le même
            # moteur (AgendaEngine → adhan_compat) que tout le reste.
            try:
                from core.agenda_engine import AgendaEngine
                heures_du_jour = AgendaEngine().obtenir_heures_prieres_journee(app.madhhab_actif)
                app.horaires_prieres_aujourdhui = {
                    nom.capitalize(): f"{h.hour:02d}:{h.minute:02d}"
                    for nom, h in heures_du_jour.items()
                }
                print(f"[SCHEDULER] horaires_prieres_aujourdhui : {app.horaires_prieres_aujourdhui}")
            except Exception as exc:
                print(f"[SCHEDULER] Échec calcul horaires du jour : {exc}")
                app.horaires_prieres_aujourdhui = {}

            # Correction 01/09/2026 : schedule_prayer_period() est devenue
            # async (elle attend maintenant schedule_prayer_alarm(), qui
            # attend elle-même alarm_service.set_alarm()). await ajouté.
            await app.notification_scheduler.schedule_prayer_period(30)
            # schedule_lunar_period() ne touche jamais alarm_service,
            # elle reste synchrone, inchangée.
            app.notification_scheduler.schedule_lunar_period(30)
            await app.notification_scheduler.commit_android()
            print("[SCHEDULER] 30j prières + 30j lunaires programmés.")

        page.run_task(demarrer_scheduler_hayaati)
    except Exception as exc:
        print(f"[SCHEDULER WARNING] Non initialisé : {exc}")
        app.notification_scheduler = None

    c_pref_init = app.sync_engine.charger_donnees_module("INVITE", "PREFERENCES") or {}

    l_init = str(c_pref_init.get("langue_actuelle", "FR")).upper()
    d_init = str(c_pref_init.get("devise_defaut", "XOF")).upper()
    f_init = str(c_pref_init.get("fiqh_defaut", "Malikite"))
    n_init = str(c_pref_init.get("arbitrage_nisab", "PLUS_BAS")).upper()

    app.langue_actuelle = l_init
    app.devise_active = d_init
    app.madhhab_actif = f_init
    app.cle_nisab_active_memoire = n_init

    DICTIONNAIRE_LANGUES.moteur_i18n.charger_dictionnaire_langue(l_init)
    app.ecran_courant = "ONBOARDING"

    async def amorcage_final_hayaati():
        await asyncio.sleep(0.15)
        app.evaluer_format_ecran_responsive(None)
        if hasattr(app, "layout_central") and app.layout_central:
            app.layout_central.basculer_vers_ecran("ONBOARDING")
        page.update()
        print("[BOOT] Amorçage asynchrone finalisé — layout rendu.")

        await asyncio.sleep(0.6)
        app.evaluer_format_ecran_responsive(None)
        try:
            page.update()
        except Exception:
            pass

        await asyncio.sleep(0.4)
        if APPLICATION_HAYAATI_INSTANCE:
            try:
                APPLICATION_HAYAATI_INSTANCE.declencher_changement_global()
                print("[BOOT] Passe de garantie finale exécutée.")
            except Exception as exc:
                print(f"[BOOT] Passe de garantie finale échouée : {exc}")

    page.run_task(amorcage_final_hayaati)


if __name__ == "__main__":
    if hasattr(ft, "run"):
        ft.run(initialiser_application_flet)
    else:
        ft.app(target=initialiser_application_flet, assets_dir="assets")
