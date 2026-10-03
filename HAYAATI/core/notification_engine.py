"""
MOTEUR DE NOTIFICATIONS LOCALES UNIFIÉ (CORE/NOTIFICATION_ENGINE.PY)
Version 4.4 — Logs ultra-détaillés, SnackBar robuste (overlay+open), bypass dédoublonnage possible
"""
from __future__ import annotations
import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import flet as ft


def _is_android() -> bool:
    return (
        hasattr(sys, "getandroidapilevel")
        or "ANDROID_BOOTLOGO" in os.environ
        or "ANDROID_ROOT" in os.environ
        or getattr(sys, "platform", "").startswith("android")
    )


def envoyer_notification_hayaati(
    page: ft.Page | None,
    titre: str,
    message: str,
    *,
    duree_snackbar: int = 5000,
    timeout_plyer: int = 6,
    icone: str | None = None,
) -> bool:
    """
    Envoie une notification locale.
    PC : SnackBar Flet TOUJOURS (méthode overlay + open = True, très fiable)
         + Plyer / OS natif en bonus.
    Android : Plyer prioritaire + SnackBar fallback.
    """
    print(f"[NOTIF-ENGINE] ==========================================")
    print(f"[NOTIF-ENGINE] TITRE  : {titre}")
    print(f"[NOTIF-ENGINE] MESSAGE: {message}")
    print(f"[NOTIF-ENGINE] PAGE   : {page is not None}")
    print(f"[NOTIF-ENGINE] ANDROID: {_is_android()}")

    if not titre or not message:
        print("[NOTIF-ENGINE] ❌ Titre ou message vide — ABANDON")
        return False

    succes_snack = False
    succes_systeme = False

    # ------------------------------------------------------------------
    # CANAL 1 : SNACKBAR FLET — PRIORITAIRE SUR PC, FALLBACK SUR ANDROID
    # ------------------------------------------------------------------
    if page is not None:
        try:
            snack = ft.SnackBar(
                content=ft.Text(
                    f"🔔 {titre}\n{message}",
                    size=13,
                    weight=ft.FontWeight.W_500,
                ),
                bgcolor="#064e3b",
                duration=duree_snackbar,
                behavior=ft.SnackBarBehavior.FLOATING,
                action="OK",
            )
            # 🆕 Méthode la plus compatible : overlay.append + open = True
            if snack not in page.overlay:
                page.overlay.append(snack)
            snack.open = True
            page.update()
            print("[NOTIF-ENGINE] ✅ SnackBar AFFICHÉ (overlay + open=True)")
            succes_snack = True
        except Exception as exc:
            print(f"[NOTIF-ENGINE] ❌ SnackBar overlay échoué : {exc}")
            # Fallback API moderne
            try:
                page.open(snack)
                print("[NOTIF-ENGINE] ✅ SnackBar AFFICHÉ (page.open)")
                succes_snack = True
            except Exception as exc2:
                print(f"[NOTIF-ENGINE] ❌ SnackBar page.open échoué : {exc2}")
                # Fallback API ancienne
                try:
                    page.show_snack_bar(snack)
                    print("[NOTIF-ENGINE] ✅ SnackBar AFFICHÉ (page.show_snack_bar)")
                    succes_snack = True
                except Exception as exc3:
                    print(f"[NOTIF-ENGINE] ❌ SnackBar tous canaux échoués : {exc3}")
    else:
        print("[NOTIF-ENGINE] ⚠️ page=None — SnackBar impossible")

    # ------------------------------------------------------------------
    # CANAL 2 : NOTIFICATION SYSTÈME (Plyer / OS natif)
    # ------------------------------------------------------------------
    # Résolution icône
    icon_path = icone
    if not icon_path:
        for base in [Path(__file__).parent.parent / "assets", Path(os.getcwd()) / "assets"]:
            for ext in ("ico", "png"):
                p = base / f"icon.{ext}"
                if p.exists():
                    icon_path = str(p.resolve())
                    break
            if icon_path:
                break

    # Plyer
    try:
        from plyer import notification as plyer_notification
        kwargs = {
            "title": str(titre),
            "message": str(message),
            "app_name": "HAYAATI",
            "timeout": timeout_plyer,
        }
        if icon_path and os.path.exists(icon_path) and not sys.platform == "win32":
            kwargs["app_icon"] = icon_path
        plyer_notification.notify(**kwargs)
        print("[NOTIF-ENGINE] ✅ Plyer OK")
        succes_systeme = True
    except Exception as exc:
        print(f"[NOTIF-ENGINE] ⚠️ Plyer échoué : {exc}")

    # Windows PowerShell Toast
    if not succes_systeme and sys.platform == "win32":
        try:
            ps = (
                f'Add-Type -AssemblyName System.Runtime.WindowsRuntime;'
                f'$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent('
                f'[Windows.UI.Notifications.ToastTemplateType]::ToastText02);'
                f'$template.SelectSingleNode("//text[@id=\'1\']").AppendChild('
                f'$template.CreateTextNode("{str(titre)}")) | Out-Null;'
                f'$template.SelectSingleNode("//text[@id=\'2\']").AppendChild('
                f'$template.CreateTextNode("{str(message)}")) | Out-Null;'
                f'$toast = [Windows.UI.Notifications.ToastNotification]::new($template);'
                f'[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("HAYAATI").Show($toast);'
            )
            result = subprocess.run(
                ["powershell", "-Command", ps],
                check=False, timeout=5, capture_output=True,
            )
            if result.returncode == 0:
                print("[NOTIF-ENGINE] ✅ Windows Toast OK")
                succes_systeme = True
            else:
                err = result.stderr.decode('utf-8', errors='ignore')[:80]
                print(f"[NOTIF-ENGINE] ⚠️ Windows Toast stderr : {err}")
        except Exception as exc:
            print(f"[NOTIF-ENGINE] ⚠️ Windows Toast échoué : {exc}")

    # Linux notify-send
    if not succes_systeme and sys.platform.startswith("linux"):
        try:
            subprocess.run(
                ["notify-send", "-a", "HAYAATI", str(titre), str(message)],
                check=False, timeout=5, capture_output=True,
            )
            print("[NOTIF-ENGINE] ✅ notify-send OK")
            succes_systeme = True
        except Exception as exc:
            print(f"[NOTIF-ENGINE] ⚠️ notify-send échoué : {exc}")

    # macOS osascript
    if not succes_systeme and sys.platform == "darwin":
        try:
            subprocess.run(
                ["osascript", "-e", f'display notification "{str(message)}" with title "{str(titre)}"'],
                check=False, timeout=5, capture_output=True,
            )
            print("[NOTIF-ENGINE] ✅ macOS osascript OK")
            succes_systeme = True
        except Exception as exc:
            print(f"[NOTIF-ENGINE] ⚠️ macOS osascript échoué : {exc}")

    # ------------------------------------------------------------------
    # RÉSULTAT
    # ------------------------------------------------------------------
    if not succes_snack and not succes_systeme:
        print(f"[NOTIF-ENGINE] ❌ TOTAL ÉCHEC — Print fallback : {titre} | {message}")
    else:
        print(f"[NOTIF-ENGINE] ✅ RÉSULTAT — SnackBar:{succes_snack} Système:{succes_systeme}")

    print(f"[NOTIF-ENGINE] ==========================================")
    return succes_snack or succes_systeme


def notifier_via_scheduler(
    scheduler,
    page: ft.Page | None,
    titre: str,
    message: str,
) -> bool:
    """Route vers le scheduler sur Android, ou envoi immédiat sur Desktop."""
    if scheduler is None:
        print("[NOTIF-ENGINE] scheduler=None → envoi immédiat")
        return envoyer_notification_hayaati(page, titre, message)

    if _is_android():
        try:
            notif_id = int(datetime.now().timestamp()) % 100000
            when = datetime.now() + timedelta(seconds=2)
            scheduler.schedule_notification(
                notif_id=notif_id, title=str(titre), body=str(message),
                when=when, channel="alertes",
            )
            if page:
                page.run_task(scheduler.commit_android)
            print(f"[NOTIF-ENGINE] Programmée Android ID={notif_id}")
            return True
        except Exception as exc:
            print(f"[NOTIF-ENGINE] Échec scheduler Android : {exc}")
            return envoyer_notification_hayaati(page, titre, message)
    else:
        print("[NOTIF-ENGINE] Desktop → envoi immédiat")
        return envoyer_notification_hayaati(page, titre, message)
