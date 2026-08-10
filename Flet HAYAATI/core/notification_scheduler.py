"""
NOTIFICATION SCHEDULER — Cross-Platform (Android + Windows/Linux/macOS)
Version 1.1 — Remplace adhan par core.adhan_compat (Python pur, compatible Android)

UTILISATION RAPIDE :
    from core.notification_scheduler import NotificationScheduler

    # Au démarrage de votre app Flet
    scheduler = NotificationScheduler(page=page, lat=6.13, lng=1.22, method="MuslimWorldLeague")
    await scheduler.bootstrap()          # Charge + pousse sur Android
    scheduler.schedule_prayer_period(30) # Programme 30 jours de prières
    scheduler.schedule_lunar_period(30)  # Programme 30 jours d'événements
    await scheduler.commit_android()     # Commit vers AlarmManager Android

DEPENDANCES :
    pip install plyer
    # Android uniquement :
    pip install flet-android-notifications

PERMISSIONS ANDROID (pyproject.toml) :
    [tool.flet.android.permission]
    "android.permission.POST_NOTIFICATIONS" = true
    "android.permission.SCHEDULE_EXACT_ALARM" = true
    "android.permission.RECEIVE_BOOT_COMPLETED" = true
    "android.permission.WAKE_LOCK" = true
    "android.permission.FOREGROUND_SERVICE" = true
"""
from __future__ import annotations

import json
import os
import sys
import time
import subprocess
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Callable

import flet as ft

# ---------------------------------------------------------------------------
# DÉTECTION PLATEFORME
# ---------------------------------------------------------------------------
_IS_ANDROID = (
    hasattr(sys, "getandroidapilevel")
    or "ANDROID_BOOTLOGO" in os.environ
    or "ANDROID_ROOT" in os.environ
)
_IS_DESKTOP = not _IS_ANDROID

# ---------------------------------------------------------------------------
# IMPORTS OPTIONNELS (backends spécifiques)
# ---------------------------------------------------------------------------
# 🆕 REMPLACEMENT : adhan → core.adhan_compat (Python pur, compatible Android)
try:
    from core.adhan_compat import Coordinates, PrayerTimes, CalculationMethod, Madhab
    _HAS_ADHAN = True
except ImportError:
    _HAS_ADHAN = False
    print("[SCHEDULER] WARNING: 'core.adhan_compat' introuvable. Vérifiez core/prayertimes.py et core/adhan_compat.py")

try:
    from plyer import notification as plyer_notification
    _HAS_PLYER = True
except ImportError:
    _HAS_PLYER = False

try:
    from flet_android_notifications import FletAndroidNotifications
    _HAS_ANDROID_PLUGIN = True
except ImportError:
    _HAS_ANDROID_PLUGIN = False

# Import des moteurs lunaires existants du projet (optionnel)
try:
    from core.time_engine import gregorien_vers_hegiri, obtenir_evenement_hegiri
    _HAS_CUSTOM_LUNAR = True
except ImportError:
    _HAS_CUSTOM_LUNAR = False


# ---------------------------------------------------------------------------
# CLASSE PRINCIPALE
# ---------------------------------------------------------------------------
class NotificationScheduler:
    """
    Planificateur de notifications locales cross-platform.

    • Android : utilise flet-android-notifications → AlarmManager exact
    • Desktop : thread daemon interne + Plyer (notifications système)
    """

    def __init__(
        self,
        page: Optional[ft.Page] = None,
        db_path: Optional[Path] = None,
        lat: float = 6.13,
        lng: float = 1.22,
        calc_method: str = "MuslimWorldLeague",
        madhab: str = "shafi",          # "shafi" ou "hanafi"
        lunar_event_fn: Optional[Callable[[int, int], Optional[str]]] = None,
    ):
        self.page = page
        self.lat = lat
        self.lng = lng
        self.calc_method = calc_method
        self.madhab = madhab.lower()
        self.lunar_event_fn = lunar_event_fn  # callback(mois_hijri, jour_hijri) -> str|None

        self.db_path = db_path or Path(__file__).parent.parent / "data" / "notification_schedule.json"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._schedule: list[dict] = []   # registre JSON des notifications
        self._lock = threading.Lock()
        self._running = False
        self._desktop_thread: Optional[threading.Thread] = None

        # Backend Android
        self._android_backend: Optional[FletAndroidNotifications] = None
        if _IS_ANDROID and _HAS_ANDROID_PLUGIN:
            try:
                self._android_backend = FletAndroidNotifications()
            except Exception as exc:
                print(f"[SCHEDULER] Impossible d'initialiser le backend Android : {exc}")

        self._load_schedule()

        if _IS_DESKTOP:
            self._start_desktop_scheduler()

    # -----------------------------------------------------------------------
    # PERSISTENCE JSON
    # -----------------------------------------------------------------------
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

    # -----------------------------------------------------------------------
    # API PUBLIQUE — Programmation unitaire
    # -----------------------------------------------------------------------
    def schedule_notification(
        self,
        notif_id: int,
        title: str,
        body: str,
        when: datetime,
        channel: str = "prieres",
    ) -> bool:
        """
        Ajoute une notification au planning (JSON + backend si Android).
        Retourne True si ajoutée, False si date dépassée.
        """
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
            # Dédoublonnage : même ID + même jour = remplacement
            jour = when.strftime("%Y-%m-%d")
            self._schedule = [
                s for s in self._schedule
                if not (s["id"] == notif_id and s["timestamp"].startswith(jour))
            ]
            self._schedule.append(entry)
            self._schedule.sort(key=lambda x: x["timestamp"])
            self._save_schedule()

        # Sur Android, on pousse immédiatement si le backend est dispo
        # (le commit final via commit_android() est toutefois recommandé)
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

    def cancel_all(self):
        """Annule toutes les notifications programmées."""
        with self._lock:
            self._schedule.clear()
            self._save_schedule()

        if _IS_ANDROID and self._android_backend and self.page:
            try:
                self.page.run_task(self._android_backend.cancel_all)
            except Exception as exc:
                print(f"[SCHEDULER] Cancel Android error : {exc}")

        print("[SCHEDULER] Toutes les notifications ont été annulées.")

    def cancel_by_channel(self, channel: str):
        """Annule uniquement les notifications d'un canal (prieres / lunaire)."""
        with self._lock:
            self._schedule = [s for s in self._schedule if s.get("channel") != channel]
            self._save_schedule()

    # -----------------------------------------------------------------------
    # PROGRAMMATION MASSIVE — PRIÈRES
    # -----------------------------------------------------------------------
    def schedule_prayer_period(self, days: int = 30) -> int:
        """
        Calcule et programme les 5 prières pour les N prochains jours.
        Retourne le nombre de notifications programmées.
        """
        if not _HAS_ADHAN:
            print("[SCHEDULER] ERREUR: core.adhan_compat requis. Vérifiez core/prayertimes.py et core/adhan_compat.py")
            return 0

        coords = Coordinates(self.lat, self.lng)

        # Méthode de calcul
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

        # Fiqh Asr
        if self.madhab == "hanafi":
            params.madhab = Madhab.HANAFI
        else:
            params.madhab = Madhab.SHAFI

        priere_map = {
            "fajr": "Fajr",
            "sunrise": "Chourouk",
            "dhuhr": "Dhuhr",
            "asr": "Asr",
            "maghrib": "Maghrib",
            "isha": "Isha",
        }

        base_id = 1000
        count = 0
        now = datetime.now()

        for delta in range(days):
            date_cible = now + timedelta(days=delta)
            # adhan attend un objet date sans timezone
            date_adhan = datetime(date_cible.year, date_cible.month, date_cible.day)

            try:
                prayers = PrayerTimes(coords, date_adhan, params)
            except Exception as exc:
                print(f"[SCHEDULER] Erreur calcul prières {date_adhan.date()} : {exc}")
                continue

            for idx, (cle, nom) in enumerate(priere_map.items()):
                heure = getattr(prayers, cle, None)
                if heure and heure > now:
                    notif_id = base_id + delta * 10 + idx
                    ok = self.schedule_notification(
                        notif_id=notif_id,
                        title=f"🕌 {nom}",
                        body=f"C'est l'heure de la prière {nom}.",
                        when=heure,
                        channel="prieres",
                    )
                    if ok:
                        count += 1

        print(f"[SCHEDULER] {count} prières programmées sur {days} jours.")
        return count

    # -----------------------------------------------------------------------
    # PROGRAMMATION MASSIVE — ÉVÉNEMENTS LUNAIRES
    # -----------------------------------------------------------------------
    def schedule_lunar_period(self, days: int = 30) -> int:
        """
        Détecte et programme les événements lunaires sur N jours.
        Retourne le nombre d'événements programmés.
        """
        count = 0
        now = datetime.now()
        base_id = 5000

        for delta in range(days):
            date_cible = now + timedelta(days=delta)

            # Utilise les fonctions existantes du projet si dispo
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
                # Notification à 06:00 du matin de l'événement
                heure_notif = date_cible.replace(hour=6, minute=0, second=0, microsecond=0)
                if heure_notif > now:
                    self.schedule_notification(
                        notif_id=base_id + delta,
                        title="🌙 HAYAATI — Événement sacré",
                        body=str(evt),
                        when=heure_notif,
                        channel="lunaire",
                    )
                    count += 1

        print(f"[SCHEDULER] {count} événements lunaires programmés sur {days} jours.")
        return count

    @staticmethod
    def _approx_hijri(date_greg: datetime) -> dict:
        """Approximation Hijri basique si les moteurs custom ne sont pas dispo."""
        # Différence approximative : 354.367 jours / an hégirien
        ref = datetime(2026, 2, 18)  # 1er Ramadan 1447 AH approx
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

    # -----------------------------------------------------------------------
    # BOOTSTRAP — À APPELER AU DÉMARRAGE DE L'APP
    # -----------------------------------------------------------------------
    async def bootstrap(self):
        """
        À appeler au démarrage de l'application Flet.
        Recharge le planning et, sur Android, re-commit les alarmes.
        Synchronise la position GPS avec AgendaEngine pour cohérence des horaires.
        """
        self._load_schedule()

        # 🆕 SYNCHRONISATION POSITION GPS avec AgendaEngine
        # AgendaEngine lance un thread qui détecte la position via ip-api.com.
        # On attend 0.5s pour qu'il ait potentiellement répondu, puis on lit son cache.
        try:
            from core.agenda_engine import AgendaEngine
            import asyncio
            await asyncio.sleep(0.5)
            cache = getattr(AgendaEngine, '_position_commune_cache', None)
            if cache:
                lat_detectee = cache.get('lat')
                lon_detectee = cache.get('lon')
                ville = cache.get('city', 'Inconnu')
                if lat_detectee is not None and lon_detectee is not None:
                    if abs(self.lat - lat_detectee) > 0.01 or abs(self.lng - lon_detectee) > 0.01:
                        self.lat = float(lat_detectee)
                        self.lng = float(lon_detectee)
                        print(f"[SCHEDULER] Position GPS synchronisée : {self.lat:.2f}, {self.lng:.2f} ({ville})")
                    else:
                        print(f"[SCHEDULER] Position par défaut confirmée : {self.lat:.2f}, {self.lng:.2f}")
        except Exception as exc:
            print(f"[SCHEDULER] Synchro GPS non critique : {exc}")

        if _IS_ANDROID:
            # 🆕 DEMANDE RUNTIME DES PERMISSIONS (Android 13+ obligatoire)
            if self._android_backend and self.page:
                try:
                    print("[SCHEDULER] Demande runtime permissions Android...")
                    perms_ok = await self._android_backend.request_permissions()
                    print(f"[SCHEDULER] Permissions accordées : {perms_ok}")
                except Exception as exc:
                    print(f"[SCHEDULER] Échec demande permissions : {exc}")
            await self.commit_android()
            print("[SCHEDULER] Bootstrap Android terminé.")
        else:
            print("[SCHEDULER] Bootstrap Desktop terminé (thread actif).")

    async def commit_android(self):
        """
        (Android uniquement) Pousse toutes les entrées JSON non envoyées
        vers le backend flet-android-notifications / AlarmManager.
        À exécuter via :  page.run_task(scheduler.commit_android)
        """
        if not (_IS_ANDROID and self._android_backend and self.page):
            return

        with self._lock:
            pending = [s for s in self._schedule if not s.get("sent")]

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
                pushed += 1
            except Exception as exc:
                print(f"[SCHEDULER] Commit Android ID={entry['id']} échoué : {exc}")

        print(f"[SCHEDULER] {pushed}/{len(pending)} notifications commitées sur Android.")

    # -----------------------------------------------------------------------
    # DESKTOP SCHEDULER — Thread daemon interne
    # -----------------------------------------------------------------------
    def _start_desktop_scheduler(self):
        if self._running:
            return
        self._running = True
        self._desktop_thread = threading.Thread(target=self._desktop_loop, daemon=True)
        self._desktop_thread.start()
        print("[SCHEDULER] Thread desktop démarré.")

    def _desktop_loop(self):
        """Boucle de surveillance : vérifie toutes les 30s les alarmes à déclencher."""
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
        """Envoie une notification sur Windows / Linux / macOS."""
        title = entry["title"]
        body = entry["body"]
        print(f"[SCHEDULER] DESKTOP NOTIFY → {title}")

        # 1) Plyer (tous OS)
        if _HAS_PLYER:
            try:
                plyer_notification.notify(
                    title=title,
                    message=body,
                    app_name="HAYAATI",
                    timeout=10,
                )
                return
            except Exception as exc:
                print(f"[SCHEDULER] Plyer échoué : {exc}")

        # 2) Linux — notify-send
        if sys.platform.startswith("linux"):
            try:
                subprocess.run(
                    ["notify-send", "-a", "HAYAATI", title, body],
                    check=False, timeout=5,
                )
                return
            except Exception:
                pass

        # 3) Windows — toast natif via PowerShell
        if sys.platform == "win32":
            try:
                ps = (
                    f'[Windows.UI.Notifications.ToastNotificationManager, '
                    f'Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null;'
                    f'$template = [Windows.UI.Notifications.ToastNotificationManager]::'
                    f'GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02);'
                    f'$template.SelectSingleNode("//text[@id=\'1\']").AppendChild('
                    f'$template.CreateTextNode("{title}")) | Out-Null;'
                    f'$template.SelectSingleNode("//text[@id=\'2\']").AppendChild('
                    f'$template.CreateTextNode("{body}")) | Out-Null;'
                    f'$toast = [Windows.UI.Notifications.ToastNotification]::new($template);'
                    f'[Windows.UI.Notifications.ToastNotificationManager]::'
                    f'CreateToastNotifier("HAYAATI").Show($toast);'
                )
                subprocess.run(
                    ["powershell", "-Command", ps],
                    check=False, timeout=5, capture_output=True,
                )
                return
            except Exception:
                pass

        # 4) Fallback SnackBar Flet (si l'app est ouverte)
        if self.page:
            try:
                snack = ft.SnackBar(
                    content=ft.Text(f"🔔 {title}\n{body}", size=12),
                    bgcolor="#064e3b",
                    duration=5000,
                    behavior=ft.SnackBarBehavior.FLOATING,
                )
                # Compatibilité ancienne / nouvelle API Flet
                try:
                    self.page.open(snack)
                except AttributeError:
                    self.page.show_snack_bar(snack)
            except Exception:
                pass

    def _cleanup_old(self):
        """Purge les notifications envoyées de +7 jours pour alléger le JSON."""
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
        """Arrête proprement le scheduler desktop (à appeler à la fermeture de l'app)."""
        self._running = False
        if self._desktop_thread:
            self._desktop_thread.join(timeout=2)
        print("[SCHEDULER] Arrêté.")

    # -----------------------------------------------------------------------
    # UTILITAIRES
    # -----------------------------------------------------------------------
    def get_next_prayer(self) -> Optional[dict]:
        """Retourne la prochaine prière programmée non encore envoyée."""
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
        """Statistiques rapides du planning."""
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
            "lunaires": lunaires,
        }
