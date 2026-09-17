"""
NOTIFICATION SCHEDULER — Cross-Platform (Android + Desktop)
Version 3.5.2 — Import HayaatiAlarm corrigé, appel set_alarm réaligné,
                 is_alarm_active (jamais fonctionnelle) retirée.
  • Alarmes natives Android via HayaatiAlarm (plugin alarm v5.1.5)
  • Notifications programmées via FletAndroidNotifications (fallback + lunaire)
  • Permissions exact-alarm + full-screen-intent gérées via HayaatiAlarm
"""
from __future__ import annotations

import json
import os
import sys
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import Optional, Callable

import flet as ft

_IS_ANDROID = (
    hasattr(sys, "getandroidapilevel")
    or "ANDROID_BOOTLOGO" in os.environ
    or "ANDROID_ROOT" in os.environ
)
_IS_DESKTOP = not _IS_ANDROID

try:
    from core.adhan_compat import Coordinates, PrayerTimes, CalculationMethod, Madhab
    _HAS_ADHAN = True
except ImportError:
    _HAS_ADHAN = False
    print("[SCHEDULER] WARNING: core.adhan_compat introuvable.")

try:
    # ⚠️ 08/09/2026 : importé pour deux raisons désormais.
    # 1) Coordonnées par défaut : ce fichier avait son propre défaut
    #    (Lomé, 6.13/1.22), différent de celui d'agenda_engine.py
    #    (Dapaong, 10.86/0.20). Deux sources de vérité pour la même
    #    donnée, c'est le genre de duplication qui finit par diverger
    #    silencieusement. AgendaEngine est maintenant la source unique.
    # 2) FENETRE_RAPPEL_MINUTES : la même constante pilote l'alarme adhan
    #    ici et le bandeau d'avertissement sur onboarding, pour qu'ils
    #    restent synchronisés si la valeur change un jour.
    from core.agenda_engine import AgendaEngine
    _HAS_AGENDA_ENGINE = True
except ImportError:
    _HAS_AGENDA_ENGINE = False
    print("[SCHEDULER] WARNING: core.agenda_engine introuvable — coordonnées de secours utilisées.")

try:
    from plyer import notification as plyer_notification
    _HAS_PLYER = True
except ImportError:
    _HAS_PLYER = False

try:
    from core.time_engine import gregorien_vers_hegiri, obtenir_evenement_hegiri
    _HAS_CUSTOM_LUNAR = True
except ImportError:
    _HAS_CUSTOM_LUNAR = False

try:
    from gui.langues import DICTIONNAIRE_LANGUES
    _HAS_I18N = True
except ImportError:
    _HAS_I18N = False

try:
    # Correction 30/08/2026 : le paquet est installé sous le nom
    # "hayaati_alarm", jamais sous "flet_hayaati_alarm". Ce dernier nom
    # ne correspondait à rien de construit dans ce projet ; l'import
    # échouait silencieusement à chaque lancement et HayaatiAlarm restait
    # introuvable en permanence.
    from hayaati_alarm import HayaatiAlarm
    _HAS_HAYAATI_ALARM = True
except ImportError:
    _HAS_HAYAATI_ALARM = False
    print("[SCHEDULER] WARNING: hayaati_alarm introuvable.")

try:
    from flet_android_notifications import FletAndroidNotifications
    _HAS_ANDROID_PLUGIN = True
except ImportError:
    _HAS_ANDROID_PLUGIN = False
    print("[SCHEDULER] WARNING: flet_android_notifications introuvable.")


class NotificationScheduler:
    """Scheduler unifié : alarmes natives + notifications programmées Android + desktop."""

    # 🆕 04/09/2026 : chemins mis à jour vers les assets embarqués par
    # l'extension hayaati_alarm elle-même (convention Flutter standard
    # "packages/<nom>/<chemin>"), après découverte que les assets déclarés
    # côté Flet (dossier assets/ de l'app principale) ne sont jamais
    # exposés au système d'assets natif que consulte le paquet 'alarm'.
    # Preuve : le fichier compilé faisait 77 Mo avec ou sans les mp3, et
    # adhan.mp3 était absent de build/flutter/assets/sounds/ après build.
    DEFAULT_PRAYER_PREFS = {
        "fajr":    {"enabled": True,  "sound": "packages/hayaati_alarm/assets/sounds/adhan_fajr.mp3", "volume": 1.0, "vibrate": True},
        "sunrise": {"enabled": False, "sound": "packages/hayaati_alarm/assets/sounds/adhan.mp3",      "volume": 0.5, "vibrate": False},
        "dhuhr":   {"enabled": True,  "sound": "packages/hayaati_alarm/assets/sounds/adhan.mp3",      "volume": 1.0, "vibrate": True},
        "asr":     {"enabled": True,  "sound": "packages/hayaati_alarm/assets/sounds/adhan.mp3",      "volume": 1.0, "vibrate": True},
        "maghrib": {"enabled": True,  "sound": "packages/hayaati_alarm/assets/sounds/adhan.mp3",      "volume": 1.0, "vibrate": True},
        "isha":    {"enabled": True,  "sound": "packages/hayaati_alarm/assets/sounds/adhan.mp3",      "volume": 1.0, "vibrate": True},
    }

    # ⚠️ 11/09/2026 : RAPPEL_AVANT_PRIERE_MINUTES retirée. L'alarme sonnait
    # avant l'heure légale (5 min), mais en pratique les gens accomplissent
    # la prière 10 à 15 minutes après l'heure théorique calculée — cette
    # anticipation donnait l'impression que l'alarme sonnait trop tôt,
    # bien avant le moment réel de la prière. L'alarme sonne maintenant à
    # l'heure calculée exacte (voir schedule_prayer_period ci-dessous).
    #
    # Note : AgendaEngine.FENETRE_RAPPEL_MINUTES existe toujours et reste
    # utilisée par page_onboarding_alerts.py pour le bandeau "prière
    # imminente" — ce n'est pas le même besoin (un avertissement visuel
    # sur une autre page n'a pas à suivre la même règle que le
    # déclenchement du son de l'alarme elle-même).

    def __init__(
        self,
        page: Optional[ft.Page] = None,
        db_path: Optional[Path] = None,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        tz_offset: Optional[float] = None,
        calc_method: str = "MuslimWorldLeague",
        madhab: str = "shafi",
        lunar_event_fn: Optional[Callable[[int, int], Optional[str]]] = None,
        alarm_service: Optional[HayaatiAlarm] = None,
    ):
        self.page = page

        # ⚠️ 08/09/2026 : lat/lng/tz_offset ne sont plus codés en dur ici.
        # Si l'appelant ne les précise pas explicitement, on les lit
        # depuis AgendaEngine, seule source de vérité pour la position
        # (et désormais le fuseau civil réel) dans le projet.
        if (lat is None or lng is None or tz_offset is None) and _HAS_AGENDA_ENGINE:
            try:
                _position = AgendaEngine()
                lat = lat if lat is not None else _position.latitude
                lng = lng if lng is not None else _position.longitude
                tz_offset = tz_offset if tz_offset is not None else _position.fuseau_horaire
            except Exception as exc:
                print(f"[SCHEDULER] Lecture position AgendaEngine échouée : {exc}")
        self.lat = lat if lat is not None else 10.86
        self.lng = lng if lng is not None else 0.20
        # ⚠️ 08/09/2026 : fuseau civil réel (heures, fractionnaire pour
        # les pays à décalage non-entier : Inde +5.5, Iran +3.5...),
        # transmis à Coordinates dans schedule_prayer_period() pour que
        # le calcul ne dépende plus d'une estimation par longitude.
        self.tz_offset = tz_offset if tz_offset is not None else 0.0

        self.calc_method = calc_method
        self.madhab = madhab.lower()
        self.lunar_event_fn = lunar_event_fn
        self.alarm_service: Optional[HayaatiAlarm] = alarm_service

        if self.alarm_service is None and _HAS_HAYAATI_ALARM and page is not None:
            self._auto_inject_alarm_service()

        self.db_path = db_path or Path(__file__).parent.parent / "data" / "notification_schedule.json"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.prefs_path = self.db_path.parent / "notification_prefs.json"
        self.prayer_prefs: dict = {}
        self._load_prayer_preferences()

        self._schedule: list[dict] = []
        self._lock = threading.Lock()
        self._running = False
        self._desktop_thread: Optional[threading.Thread] = None

        self._android_backend: Optional[FletAndroidNotifications] = None
        if _IS_ANDROID and _HAS_ANDROID_PLUGIN:
            try:
                self._android_backend = FletAndroidNotifications()
                print("[SCHEDULER] Backend Android notifications initialisé.")
            except Exception as exc:
                print(f"[SCHEDULER] Impossible d'initialiser le backend Android : {exc}")

        self._load_schedule()

        if _IS_DESKTOP:
            self._start_desktop_scheduler()

    def _auto_inject_alarm_service(self):
        """Filet de sécurité : si aucun alarm_service n'a été fourni au
        constructeur, cherche une instance HayaatiAlarm déjà présente dans
        page.services, ou en crée une.

        Correction 03/09/2026 : cherchait et injectait via page.controls /
        page.add(), le mauvais canal pour un Service Flet (réservé à
        l'arbre visuel). Les services vivent dans page.services, avec leur
        propre cycle de vie côté Dart (init() ne se déclenche que pour les
        objets enregistrés là). C'est ce qui empêchait silencieusement
        toute méthode de HayaatiAlarm de répondre, même quand ce filet de
        sécurité croyait avoir réussi son injection."""
        try:
            if self.page is None:
                return
            for ctrl in self.page.services:
                if isinstance(ctrl, HayaatiAlarm):
                    self.alarm_service = ctrl
                    print("[SCHEDULER] HayaatiAlarm récupéré de page.services")
                    return
            self.alarm_service = HayaatiAlarm()
            self.page.services.append(self.alarm_service)
            self.page.update()
            print("[SCHEDULER] HayaatiAlarm auto-injecté dans page.services")
        except Exception as exc:
            print(f"[SCHEDULER] Échec auto-injection HayaatiAlarm : {exc}")

    def _load_prayer_preferences(self):
        if self.prefs_path.exists():
            try:
                with open(self.prefs_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self.prayer_prefs = {
                    k: {**self.DEFAULT_PRAYER_PREFS.get(k, {}), **saved.get(k, {})}
                    for k in self.DEFAULT_PRAYER_PREFS
                }
                # 🆕 04/09/2026 : migration automatique des anciens chemins
                # audio ("assets/sounds/...", jamais réellement exposés au
                # système d'assets natif de Flutter) vers les nouveaux,
                # embarqués par l'extension hayaati_alarm elle-même
                # ("packages/hayaati_alarm/assets/sounds/..."). Sans ça, un
                # ancien fichier de préférences déjà sauvegardé sur
                # l'appareil aurait continué à imposer le chemin cassé,
                # annulant silencieusement la correction du son de l'adhan.
                migration_effectuee = False
                for cle, pref in self.prayer_prefs.items():
                    son_actuel = pref.get("sound", "")
                    if son_actuel.startswith("assets/sounds/"):
                        nouveau_son = "packages/hayaati_alarm/" + son_actuel
                        pref["sound"] = nouveau_son
                        migration_effectuee = True
                        print(f"[SCHEDULER] Migration chemin audio {cle} : {son_actuel} → {nouveau_son}")
                if migration_effectuee:
                    self._save_prayer_preferences()
                print(f"[SCHEDULER] Préférences prières chargées : {self._prefs_summary()}")
            except Exception as exc:
                print(f"[SCHEDULER] Erreur chargement prefs : {exc}")
                self.prayer_prefs = {k: dict(v) for k, v in self.DEFAULT_PRAYER_PREFS.items()}
        else:
            self.prayer_prefs = {k: dict(v) for k, v in self.DEFAULT_PRAYER_PREFS.items()}
            self._save_prayer_preferences()

    def _save_prayer_preferences(self):
        try:
            with open(self.prefs_path, "w", encoding="utf-8") as f:
                json.dump(self.prayer_prefs, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            print(f"[SCHEDULER] Erreur sauvegarde prefs : {exc}")

    def _prefs_summary(self) -> str:
        return ", ".join(
            f"{k}={'ON' if v['enabled'] else 'OFF'}"
            for k, v in self.prayer_prefs.items()
        )

    def set_prayer_preference(self, prayer_key: str, enabled: Optional[bool] = None,
                              sound: Optional[str] = None, volume: Optional[float] = None,
                              vibrate: Optional[bool] = None):
        if prayer_key not in self.prayer_prefs:
            print(f"[SCHEDULER] Clé prière invalide : {prayer_key}")
            return
        if enabled is not None:
            self.prayer_prefs[prayer_key]["enabled"] = bool(enabled)
        if sound is not None:
            self.prayer_prefs[prayer_key]["sound"] = str(sound)
        if volume is not None:
            self.prayer_prefs[prayer_key]["volume"] = float(max(0.0, min(1.0, volume)))
        if vibrate is not None:
            self.prayer_prefs[prayer_key]["vibrate"] = bool(vibrate)
        self._save_prayer_preferences()
        print(f"[SCHEDULER] Préférence {prayer_key} mise à jour.")

    def is_prayer_enabled(self, prayer_key: str) -> bool:
        return self.prayer_prefs.get(prayer_key, {}).get("enabled", True)

    def _load_schedule(self):
        if self.db_path.exists():
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    self._schedule = json.load(f)
                print(f"[SCHEDULER] {len(self._schedule)} entrées chargées.")
            except Exception as exc:
                print(f"[SCHEDULER] Erreur chargement JSON : {exc}")
                self._schedule = []
        else:
            self._schedule = []

    def _save_schedule(self):
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(self._schedule, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            print(f"[SCHEDULER] Erreur sauvegarde JSON : {exc}")

    _EPOQUE_ID = date(2026, 1, 1)

    @classmethod
    def _stable_prayer_id(cls, date_obj: datetime, idx: int) -> int:
        jours = (date_obj.date() - cls._EPOQUE_ID).days
        return 100000 + jours * 10 + idx

    @classmethod
    def _stable_lunar_id(cls, date_obj: datetime) -> int:
        jours = (date_obj.date() - cls._EPOQUE_ID).days
        return 500000 + jours

    def schedule_notification(
        self,
        notif_id: int,
        title: str,
        body: str,
        when: datetime,
        channel: str = "prieres",
    ) -> bool:
        if when <= datetime.now():
            return False

        entry = {
            "id": notif_id,
            "title": str(title),
            "body": str(body),
            "timestamp": when.isoformat(),
            "channel": channel,
            "sent": False,
            "platform": "android" if _IS_ANDROID else "desktop",
        }

        with self._lock:
            self._schedule = [s for s in self._schedule if s["id"] != notif_id]
            self._schedule.append(entry)
            self._schedule.sort(key=lambda x: x["timestamp"])
            self._save_schedule()

        if _IS_ANDROID and self._android_backend and self.page:
            try:
                self.page.run_task(
                    self._android_backend.schedule_notification,
                    notification_id=notif_id,
                    title=str(title),
                    body=str(body),
                    scheduled_time=when,
                    channel_id=channel,
                    channel_name="Hayaati " + channel.capitalize(),
                    play_sound=True,
                    enable_vibration=True,
                    auto_cancel=True,
                )
            except Exception as exc:
                print(f"[SCHEDULER] Push Android immédiat échoué : {exc}")

        return True

    async def schedule_prayer_alarm(
        self,
        notif_id: int,
        title: str,
        body: str,
        when: datetime,
        prayer_key: str = "dhuhr",
    ) -> bool:
        if not self.is_prayer_enabled(prayer_key):
            print(f"[SCHEDULER] {prayer_key} désactivée — skip")
            return False

        if not _IS_ANDROID:
            return self.schedule_notification(notif_id, title, body, when)

        if self.alarm_service is None or not hasattr(self.alarm_service, 'set_alarm'):
            print("[SCHEDULER] Service d'alarme indisponible — fallback notification")
            return self.schedule_notification(notif_id, title, body, when)

        prefs = self.prayer_prefs.get(prayer_key, {})
        son = prefs.get("sound", "packages/hayaati_alarm/assets/sounds/adhan.mp3")
        vol = prefs.get("volume", 1.0)
        vib = prefs.get("vibrate", True)

        # Correction 30/08/2026 : la vérification is_alarm_active() a été
        # retirée. Elle levait systématiquement une exception (interceptée
        # ici et donc invisible) car _invoke_method() ne remonte pas de
        # valeur de façon synchrone dans ce projet. La prévention des
        # doublons est déjà assurée par cancel_all_prayer_alarms(),
        # appelée avant schedule_prayer_period() dans reschedule_all().

        stop_label = "Arrêter l'adhan"
        if _HAS_I18N:
            stop_label = (
                DICTIONNAIRE_LANGUES.actif.get("onboarding", {})
                .get("alarme_stop_btn", "Arrêter l'adhan")
            )

        try:
            # Correction 30/08/2026 : noms de paramètres alignés sur la
            # signature réelle de HayaatiAlarm.set_alarm() (voir
            # hayaati_alarm.py v1.1). fade_duration et
            # warning_notification_on_kill remplacent les anciens
            # datetime_iso / asset_audio / android_full_screen_intent /
            # stop_button_label / bypass_dnd, qui ne correspondaient à
            # aucun paramètre existant et faisaient échouer l'appel à
            # chaque tentative (TypeError intercepté ci-dessous).
            await self.alarm_service.set_alarm(
                id=notif_id,
                date_time_iso=when.isoformat(),
                asset_audio_path=son,
                title=str(title),
                body=str(body),
                loop_audio=True,
                vibrate=vib,
                full_screen_intent=True,
                volume=vol,
                fade_duration=3.0,
                warning_notification_on_kill=True,
                stop_button=stop_label,
            )

            entry = {
                "id": notif_id,
                "title": str(title),
                "body": str(body),
                "timestamp": when.isoformat(),
                "channel": "prieres",
                "sent": True,
                "platform": "android_alarm",
                "prayer_key": prayer_key,
                "sound": son,
            }
            with self._lock:
                self._schedule = [s for s in self._schedule if s["id"] != notif_id]
                self._schedule.append(entry)
                self._save_schedule()

            print(f"[SCHEDULER] ✅ Alarme {prayer_key} programmée ID={notif_id}")
            return True
        except Exception as exc:
            print(f"[SCHEDULER] ❌ Échec alarme Flet : {exc} — fallback notification")
            return self.schedule_notification(notif_id, title, body, when)

    async def cancel_all(self):
        if _IS_ANDROID and self.alarm_service:
            with self._lock:
                ids_alarmes = [s["id"] for s in self._schedule if s.get("platform") == "android_alarm"]
            for req_id in ids_alarmes:
                try:
                    await self.alarm_service.cancel_alarm(id=req_id)
                except Exception as exc:
                    print(f"[SCHEDULER] Annulation alarme ID={req_id} échouée : {exc}")

        if _IS_ANDROID and self._android_backend and self.page:
            try:
                self.page.run_task(self._android_backend.cancel_all)
            except Exception as exc:
                print(f"[SCHEDULER] Cancel Android error : {exc}")

        with self._lock:
            self._schedule.clear()
            self._save_schedule()
        print("[SCHEDULER] Toutes les notifications ont été annulées.")

    async def cancel_by_channel(self, channel: str):
        with self._lock:
            to_cancel = [s for s in self._schedule if s.get("channel") == channel]
            if _IS_ANDROID and self.alarm_service:
                for entry in to_cancel:
                    if entry.get("platform") == "android_alarm":
                        try:
                            await self.alarm_service.cancel_alarm(id=entry["id"])
                        except Exception as exc:
                            print(f"[SCHEDULER] Cancel channel alarm ID={entry['id']} : {exc}")
            self._schedule = [s for s in self._schedule if s.get("channel") != channel]
            self._save_schedule()

    async def cancel_all_prayer_alarms(self):
        with self._lock:
            to_cancel = [s for s in self._schedule if s.get("platform") == "android_alarm"]
            others = [s for s in self._schedule if s.get("platform") != "android_alarm"]

        if _IS_ANDROID and self.alarm_service:
            for entry in to_cancel:
                try:
                    await self.alarm_service.cancel_alarm(id=entry["id"])
                    print(f"[SCHEDULER] Alarme prière ID={entry['id']} annulée")
                except Exception as exc:
                    print(f"[SCHEDULER] Annulation ID={entry['id']} : {exc}")

        with self._lock:
            self._schedule = others
            self._save_schedule()

    async def reschedule_all(self, days: int = 30) -> dict:
        await self.cancel_all_prayer_alarms()
        n_prieres = await self.schedule_prayer_period(days)
        n_lunaire = self.schedule_lunar_period(days)

        if _IS_ANDROID and self.page:
            try:
                self.page.run_task(self.commit_android)
            except Exception as exc:
                print(f"[SCHEDULER] commit_android après reschedule_all a échoué : {exc}")

        print(f"[SCHEDULER] Replanification : {n_prieres} prière(s), {n_lunaire} lunaire(s).")
        return {"prieres": n_prieres, "lunaire": n_lunaire}

    async def schedule_prayer_period(self, days: int = 30) -> int:
        if not _HAS_ADHAN:
            print("[SCHEDULER] ERREUR: core.adhan_compat requis.")
            return 0

        # ⚠️ 08/09/2026 : timezone=self.tz_offset transmis explicitement,
        # au lieu de laisser adhan_compat l'estimer depuis la seule
        # longitude — nécessaire pour un calcul correct hors du Togo.
        coords = Coordinates(self.lat, self.lng, timezone=self.tz_offset)

        methods = {
            "MuslimWorldLeague": CalculationMethod.MuslimWorldLeague,
            "Egyptian": CalculationMethod.Egyptian,
            "Karachi": CalculationMethod.Karachi,
            "UmmAlQura": CalculationMethod.UmmAlQura,
            "Dubai": CalculationMethod.Dubai,
            "MoonsightingCommittee": CalculationMethod.MoonsightingCommittee,
            "NorthAmerica": CalculationMethod.NorthAmerica,
            "Kuwait": CalculationMethod.Kuwait,
            "Qatar": CalculationMethod.Qatar,
            "Singapore": CalculationMethod.Singapore,
            "Turkey": CalculationMethod.Turkey,
        }
        params = methods.get(self.calc_method, CalculationMethod.MuslimWorldLeague)()

        if self.madhab == "hanafi":
            params.madhab = Madhab.HANAFI
        else:
            params.madhab = Madhab.SHAFI

        priere_map = {
            "fajr":    ("Fajr",     "fajr"),
            "sunrise": ("Chourouk", "sunrise"),
            "dhuhr":   ("Dhuhr",    "dhuhr"),
            "asr":     ("Asr",      "asr"),
            "maghrib": ("Maghrib",  "maghrib"),
            "isha":    ("Isha",     "isha"),
        }

        count = 0
        now = datetime.now()

        noms_i18n = DICTIONNAIRE_LANGUES.actif.get("mouhasabah", {}).get("prieres", {}) if _HAS_I18N else {}
        txt_onb = DICTIONNAIRE_LANGUES.actif.get("onboarding", {}) if _HAS_I18N else {}

        for delta in range(days):
            date_cible = now + timedelta(days=delta)
            date_adhan = datetime(date_cible.year, date_cible.month, date_cible.day)

            try:
                prayers = PrayerTimes(coords, date_adhan, params)
            except Exception as exc:
                print(f"[SCHEDULER] Erreur calcul prières {date_adhan.date()} : {exc}")
                continue

            for idx, (cle, (nom, prayer_key)) in enumerate(priere_map.items()):
                heure = getattr(prayers, cle, None)
                if not heure:
                    continue

                # ⚠️ 11/09/2026 : retour à l'heure légale exacte, sans
                # anticipation. L'essai "5 min avant" donnait l'impression
                # de sonner trop tôt, puisqu'en pratique la prière elle-même
                # se fait 10 à 15 minutes après l'heure théorique calculée
                # — l'écart cumulé (anticipation + délai humain naturel)
                # rendait l'alarme prématurée à l'usage.
                if heure > now:
                    notif_id = self._stable_prayer_id(date_adhan, idx)
                    nom_traduit = noms_i18n.get(prayer_key, nom)
                    title = txt_onb.get("alarme_priere_titre", "🕌 {}").format(nom_traduit)
                    body = txt_onb.get(
                        "alarme_priere_body", "C'est l'heure de la prière {}."
                    ).format(nom_traduit)
                    ok = await self.schedule_prayer_alarm(
                        notif_id=notif_id,
                        title=title,
                        body=body,
                        when=heure,
                        prayer_key=prayer_key,
                    )
                    if ok:
                        count += 1

        print(f"[SCHEDULER] {count} prières programmées sur {days} jours.")
        return count

    def schedule_lunar_period(self, days: int = 30) -> int:
        count = 0
        now = datetime.now()

        for delta in range(days):
            date_cible = now + timedelta(days=delta)

            if _HAS_CUSTOM_LUNAR:
                try:
                    h_date = gregorien_vers_hegiri(
                        date_cible.year, date_cible.month, date_cible.day
                    )
                    evt = obtenir_evenement_hegiri(
                        h_date["mois_num"], h_date["jour"]
                    )
                except Exception:
                    continue
            elif self.lunar_event_fn:
                try:
                    h_date = self._approx_hijri(date_cible)
                    evt = self.lunar_event_fn(h_date["mois"], h_date["jour"])
                except Exception:
                    continue
            else:
                continue

            if evt:
                heure_notif = date_cible.replace(hour=6, minute=0, second=0, microsecond=0)
                if heure_notif > now:
                    txt_onb_lunar = DICTIONNAIRE_LANGUES.actif.get("onboarding", {}) if _HAS_I18N else {}
                    dict_evt = txt_onb_lunar.get("evenements", {})
                    phrase_traduite = dict_evt.get(str(evt).strip(), str(evt))
                    self.schedule_notification(
                        notif_id=self._stable_lunar_id(date_cible),
                        title=txt_onb_lunar.get("cadre_calendrier", "🌙 HAYAATI — Événement sacré"),
                        body=str(phrase_traduite),
                        when=heure_notif,
                        channel="lunaire",
                    )
                    count += 1

        print(f"[SCHEDULER] {count} événements lunaires programmés sur {days} jours.")
        return count

    @staticmethod
    def _approx_hijri(date_greg: datetime) -> dict:
        ref = datetime(2026, 2, 18)
        ref_h = {"annee": 1447, "mois": 9, "jour": 1}

        diff = (date_greg - ref).days
        total_jours = ref_h["jour"] + diff

        mois_duree = [30, 29, 30, 29, 30, 29, 30, 29, 30, 29, 30, 29]
        a, m, j = ref_h["annee"], ref_h["mois"], ref_h["jour"]

        while total_jours > mois_duree[m - 1]:
            total_jours -= mois_duree[m - 1]
            m += 1
            if m > 12:
                m = 1
                a += 1

        return {"annee": a, "mois": m, "jour": total_jours}

    async def bootstrap(self):
        self._load_schedule()
        self._load_prayer_preferences()

        try:
            from core.agenda_engine import AgendaEngine
            import asyncio
            await asyncio.sleep(0.5)
            cache = getattr(AgendaEngine, '_position_commune_cache', None)
            if cache:
                lat_detectee = cache.get('lat')
                lon_detectee = cache.get('lon')
                tz_detectee = cache.get('offset')
                ville = cache.get('city', 'Inconnu')
                if lat_detectee is not None and lon_detectee is not None:
                    if abs(self.lat - lat_detectee) > 0.01 or abs(self.lng - lon_detectee) > 0.01:
                        self.lat = float(lat_detectee)
                        self.lng = float(lon_detectee)
                        # ⚠️ 08/09/2026 : le fuseau suit la même resynchronisation
                        # que lat/lng — le thread de détection GPS/IP peut finir
                        # après __init__ mais avant ce point de bootstrap().
                        if tz_detectee is not None:
                            self.tz_offset = float(tz_detectee)
                        print(f"[SCHEDULER] Position GPS synchronisée : {self.lat:.2f}, {self.lng:.2f}, UTC{self.tz_offset:+.2f} ({ville})")
                    else:
                        print(f"[SCHEDULER] Position par défaut confirmée : {self.lat:.2f}, {self.lng:.2f}")
        except Exception as exc:
            print(f"[SCHEDULER] Synchro GPS non critique : {exc}")

        if _IS_ANDROID:
            if self._android_backend and self.page:
                try:
                    print("[SCHEDULER] Demande runtime permissions Android...")
                    perms_ok = await self._android_backend.request_permissions()
                    print(f"[SCHEDULER] Permissions runtime : {perms_ok}")
                except Exception as exc:
                    print(f"[SCHEDULER] Échec demande permissions backend : {exc}")

            if self.alarm_service:
                try:
                    print("[SCHEDULER] Demande permissions de base via HayaatiAlarm...")
                    base_perms = await self.alarm_service.request_permissions()
                    print(f"[SCHEDULER] Permissions de base : {base_perms}")
                except Exception as exc:
                    print(f"[SCHEDULER] Échec permissions de base : {exc}")

                try:
                    print("[SCHEDULER] Demande permission exact-alarm...")
                    exact_perms = await self.alarm_service.request_exact_alarm_permission()
                    print(f"[SCHEDULER] Exact-alarm permission : {exact_perms}")
                except Exception as exc:
                    print(f"[SCHEDULER] Échec exact-alarm permission : {exc}")

                try:
                    print("[SCHEDULER] Demande permission full-screen-intent...")
                    fs_perms = await self.alarm_service.request_full_screen_intent_permission()
                    print(f"[SCHEDULER] Full-screen-intent permission : {fs_perms}")
                except Exception as exc:
                    print(f"[SCHEDULER] Échec full-screen-intent permission : {exc}")

            await self.commit_android()
            print("[SCHEDULER] Bootstrap Android terminé.")
        else:
            print("[SCHEDULER] Bootstrap Desktop terminé (thread actif).")

    async def commit_android(self):
        if not (_IS_ANDROID and self._android_backend and self.page):
            return

        with self._lock:
            pending = [
                s for s in self._schedule
                if not s.get("sent") and s.get("platform") != "android_alarm"
            ]

        pushed = 0
        for entry in pending:
            try:
                ts = datetime.fromisoformat(entry["timestamp"])
                await self._android_backend.schedule_notification(
                    notification_id=entry["id"],
                    title=entry["title"],
                    body=entry["body"],
                    scheduled_time=ts,
                    channel_id=entry.get("channel", "prieres"),
                    channel_name="Hayaati Notifications",
                    play_sound=True,
                    enable_vibration=True,
                    auto_cancel=True,
                )
                with self._lock:
                    for s in self._schedule:
                        if s["id"] == entry["id"]:
                            s["sent"] = True
                            break
                self._save_schedule()
                pushed += 1
            except Exception as exc:
                print(f"[SCHEDULER] Commit Android ID={entry['id']} échoué : {exc}")

        print(f"[SCHEDULER] {pushed}/{len(pending)} notifications lunaires commitées sur Android.")

    def _start_desktop_scheduler(self):
        if self._running:
            return
        self._running = True
        self._desktop_thread = threading.Thread(target=self._desktop_loop, daemon=True)
        self._desktop_thread.start()
        print("[SCHEDULER] Thread desktop démarré.")

    def _desktop_loop(self):
        while self._running:
            now = datetime.now()
            to_flag = []

            with self._lock:
                for entry in self._schedule:
                    if entry.get("sent") or entry.get("platform") != "desktop":
                        continue
                    ts = datetime.fromisoformat(entry["timestamp"])
                    if ts <= now:
                        self._send_desktop(entry)
                        entry["sent"] = True
                        to_flag.append(entry)

                if to_flag:
                    self._save_schedule()

            self._cleanup_old()
            time.sleep(30)

    def _send_desktop(self, entry: dict):
        from core.notification_engine import envoyer_notification_hayaati
        envoyer_notification_hayaati(
            page=self.page,
            titre=entry["title"],
            message=entry["body"],
            timeout_plyer=10,
        )

    def _cleanup_old(self):
        cutoff = (datetime.now() - timedelta(days=7)).isoformat()
        with self._lock:
            original = len(self._schedule)
            self._schedule = [
                s for s in self._schedule
                if not (s.get("sent") and s["timestamp"] < cutoff)
            ]
            if len(self._schedule) != original:
                self._save_schedule()

    def stop(self):
        self._running = False
        if self._desktop_thread:
            self._desktop_thread.join(timeout=2)
        print("[SCHEDULER] Arrêté.")

    def get_next_prayer(self) -> Optional[dict]:
        now = datetime.now()
        with self._lock:
            for entry in self._schedule:
                if entry.get("sent"):
                    continue
                ts = datetime.fromisoformat(entry["timestamp"])
                if ts > now and entry.get("channel") == "prieres":
                    return {
                        "title": entry["title"],
                        "time": ts,
                        "in_seconds": int((ts - now).total_seconds()),
                    }
        return None

    def get_stats(self) -> dict:
        with self._lock:
            total = len(self._schedule)
            sent = sum(1 for s in self._schedule if s.get("sent"))
            pending = total - sent
            prieres = sum(1 for s in self._schedule if s.get("channel") == "prieres")
            lunaires = sum(1 for s in self._schedule if s.get("channel") == "lunaire")
        return {
            "total": total,
            "sent": sent,
            "pending": pending,
            "prieres": prieres,
            "lunaire": lunaires,
        }
