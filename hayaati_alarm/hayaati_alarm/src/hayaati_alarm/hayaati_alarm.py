"""
hayaati_alarm/hayaati_alarm.py

Service Flet pour un vrai réveil natif (son en boucle, plein écran,
volume forcé, bouton d'arrêt), construit sur le paquet Flutter mature et
maintenu 'alarm' (gdelataillade/alarm sur pub.dev), plutôt que sur du code
Android JNI/pyjnius écrit à la main.

Toute la communication passe par le protocole Flet standard
(invoke_method), exactement le même mécanisme que flet-android-notifications
utilise déjà avec succès dans ce projet. Aucun jnius, aucun autoclass,
aucun risque de crash JNI natif : une erreur ici redevient une Exception
Python normale, interceptable.

⚠️ CONFIRMÉ : la méthode d'appel héritée de ft.Service est bien
_invoke_method (avec underscore), vérifié par
python -c "import flet as ft; print([m for m in dir(ft.Service) if 'invoke' in m.lower()])"
qui renvoie ['_invoke_method'].

── Journal des corrections (30/08/2026) ─────────────────────────────
v1.1 :
  • Ajout de fade_duration (fondu sonore progressif, en secondes) et de
    warning_notification_on_kill (notification si l'utilisateur tue
    l'appli avant que l'alarme sonne). Ces deux options existent côté
    Dart (paquet alarm v5.1.5) mais n'étaient pas exposées ici, ce qui
    obligeait notification_scheduler.py à appeler des noms de paramètres
    qui n'existaient pas.
  • Suppression de toute référence à is_alarm_active() : cette méthode
    n'a jamais fonctionné, _invoke_method() ne remonte pas de valeur de
    façon synchrone dans ce projet. La prévention des doublons est déjà
    assurée par cancel_all_prayer_alarms(), appelée avant chaque
    reschedule_all() côté notification_scheduler.py.
  • bypass_dnd n'a pas été repris : aucune trace confirmée d'un tel
    paramètre dans l'API du paquet 'alarm'. Le contournement du mode
    Ne pas déranger est en pratique déjà couvert par
    androidFullScreenIntent, qui s'appuie sur AlarmManager en catégorie
    alarme côté Android.
─────────────────────────────────────────────────────────────────────

── Vérification de cohérence (09/09/2026) ────────────────────────────
Aucun changement fonctionnel : les noms de méthodes et de paramètres
restent exactement alignés avec core/notification_scheduler.py et
hayaati_alarm.dart. Seule correction : les deux exemples de chemin
d'asset dans les docstrings ci-dessous montraient encore
'assets/sounds/adhan.mp3' sans le préfixe 'packages/hayaati_alarm/',
alors que ce préfixe s'est révélé nécessaire (voir hayaati_alarm.dart,
_ensureAudioFileExtracted). Un exemple resté périmé aurait pu
réintroduire ce bug si quelqu'un le recopiait tel quel.
─────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations
import flet as ft


@ft.control("HayaatiAlarm")
class HayaatiAlarm(ft.Service):
    """
    Réveil natif avec son en boucle et écran plein écran.

    Utilisation :
        alarme = HayaatiAlarm()
        page.services.append(alarme)  # ou l'équivalent d'enregistrement
                                        # de service utilisé ailleurs dans
                                        # le projet pour flet-android-notifications

        alarme.set_alarm(
            id=1010,
            date_time_iso="2026-08-25T05:12:00",
            asset_audio_path="packages/hayaati_alarm/assets/sounds/adhan_fajr.mp3",
            title="🕌 Fajr",
            body="C'est l'heure de la prière Fajr.",
        )
    """

    async def set_alarm(
        self,
        id: int,
        date_time_iso: str,
        asset_audio_path: str,
        title: str,
        body: str,
        loop_audio: bool = True,
        vibrate: bool = True,
        full_screen_intent: bool = True,
        volume: float = 1.0,
        fade_duration: float | None = None,
        warning_notification_on_kill: bool = False,
        stop_button: str = "Arrêter",
    ) -> None:
        """Programme une alarme native.

        asset_audio_path est la clé d'asset Flutter COMPLÈTE, avec le
        préfixe du package (ex. 'packages/hayaati_alarm/assets/sounds/adhan.mp3'),
        pas un chemin relatif type 'assets/sounds/adhan.mp3'. Confirmé le
        08/09/2026 en inspectant l'APK décompressé (voir
        core/notification_scheduler.py, DEFAULT_PRAYER_PREFS) : sans le
        préfixe packages/hayaati_alarm/, hayaati_alarm.dart échoue
        silencieusement à extraire le fichier audio du bundle.

        fade_duration : durée du fondu sonore progressif, en secondes.
        Laisser à None pour un volume fixe dès le début de l'alarme
        (comportement d'origine, inchangé par défaut).

        ⚠️ 31/08→01/09/2026 : _invoke_method() s'est révélée être une
        coroutine dans cette version de Flet (confirmé par le
        RuntimeWarning 'coroutine ... was never awaited' vu en logcat).
        Toutes les méthodes de ce fichier sont donc désormais async et
        utilisent await ; tous les appelants (notification_scheduler.py,
        main.py) ont dû être mis à jour en cascade.
        """
        await self._invoke_method(
            "setAlarm",
            {
                "id": id,
                "dateTime": date_time_iso,
                "assetAudioPath": asset_audio_path,
                "loopAudio": loop_audio,
                "vibrate": vibrate,
                "androidFullScreenIntent": full_screen_intent,
                "volume": volume,
                "fadeDuration": fade_duration,
                "warningNotificationOnKill": warning_notification_on_kill,
                "title": title,
                "body": body,
                "stopButton": stop_button,
            },
        )

    async def cancel_alarm(self, id: int) -> None:
        """Annule une alarme précise par son identifiant."""
        await self._invoke_method("cancelAlarm", {"id": id})

    async def stop_all_alarms(self) -> None:
        """Coupe toutes les alarmes en cours et à venir (ex. avant une
        replanification complète, comme reschedule_all())."""
        await self._invoke_method("stopAll", {})

    async def request_permissions(self) -> None:
        """Demande la permission de notification de base (POST_NOTIFICATIONS
        sur Android 13+), via permission_handler côté Dart."""
        await self._invoke_method("requestPermissions", {})

    async def request_exact_alarm_permission(self) -> None:
        """Demande la permission d'alarme exacte (SCHEDULE_EXACT_ALARM sur
        Android 12+), via permission_handler côté Dart. Sans cette
        permission accordée, Android peut retarder ou ignorer une alarme
        programmée avec Alarm.set(), sans erreur visible."""
        await self._invoke_method("requestExactAlarmPermission", {})

    async def request_full_screen_intent_permission(self) -> None:
        """Vérifie/journalise l'état de la permission plein écran
        (USE_FULL_SCREEN_INTENT sur Android 14+).

        ⚠️ Non implémenté en profondeur pour l'instant : permission_handler
        ne propose pas cette permission (demande de fonctionnalité fermée
        "not planned" par les mainteneurs). La demander correctement
        nécessiterait du code natif Android (Kotlin) dans l'extension,
        ce qui n'a pas été fait. Les applications ayant une vraie fonction
        d'alarme, comme HAYAATI, reçoivent normalement cette permission
        accordée par défaut à l'installation (contrairement aux
        applications qui en abusent pour des publicités plein écran) :
        https://source.android.com/docs/core/permissions/fsi-limits
        Cet appel journalise simplement l'intention côté Dart pour
        l'instant ; à vérifier sur le terrain avant d'investir dans le
        code natif si un test réel montre que ce n'est pas suffisant."""
        await self._invoke_method("requestFullScreenIntentPermission", {})
