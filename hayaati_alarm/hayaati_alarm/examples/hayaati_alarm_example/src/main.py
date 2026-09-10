"""
Banc de test minimal pour l'extension hayaati_alarm, isolé de HAYAATI.

But : vérifier en quelques secondes (pas en une heure de build Android)
si HayaatiAlarmService reçoit bien les appels _invoke_method() côté Dart.
Si le bouton "Tester" ci-dessous n'affiche jamais de résultat, même sur
PC, le problème est dans l'extension elle-même, indépendamment de tout
ce que fait HAYAATI. S'il fonctionne ici mais pas dans l'app complète,
le problème vient d'une interaction avec le reste du projet.

Lancer avec : py -3.14 src/main.py
(hayaati-alarm doit déjà être installé globalement, ce qui est déjà le
cas si tu as suivi les étapes d'installation de HAYAATI elle-même.)
"""
import flet as ft
from hayaati_alarm import HayaatiAlarm


def main(page: ft.Page):
    page.title = "Test isolé — hayaati_alarm"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # HayaatiAlarm est un Service, pas un widget : pas de tooltip, pas de
    # value, pas de content= dans un Container. Un Service Flet s'enregistre
    # via page.services.append(), jamais page.add() (réservé à l'arbre
    # visuel) — confirmé par tous les exemples officiels de services Flet
    # (ScreenBrightness, UserAccelerometer...), et c'était la vraie cause
    # du timeout qu'on cherchait depuis plusieurs jours.
    alarme = HayaatiAlarm()
    page.services.append(alarme)

    resultat = ft.Text("En attente d'un test...", size=14, selectable=True)

    async def tester_permissions(e):
        resultat.value = "Appel de request_permissions() en cours..."
        page.update()
        try:
            r = await alarme.request_permissions()
            resultat.value = f"✅ request_permissions() a répondu : {r}"
        except Exception as exc:
            resultat.value = f"❌ Exception : {exc}"
        page.update()

    async def tester_set_alarm(e):
        resultat.value = "Appel de set_alarm() en cours (dans 30s)..."
        page.update()
        from datetime import datetime, timedelta
        quand = (datetime.now() + timedelta(seconds=30)).isoformat()
        try:
            r = await alarme.set_alarm(
                id=999,
                date_time_iso=quand,
                asset_audio_path="assets/sounds/adhan.mp3",
                title="Test",
                body="Alarme de test isolé",
            )
            resultat.value = f"✅ set_alarm() a répondu : {r}"
        except Exception as exc:
            resultat.value = f"❌ Exception : {exc}"
        page.update()

    page.add(
        ft.Container(
            height=220,
            width=340,
            alignment=ft.Alignment.CENTER,
            bgcolor=ft.Colors.PURPLE_100,
            padding=20,
            content=ft.Column(
                [
                    ft.Text("Banc de test hayaati_alarm", weight=ft.FontWeight.BOLD),
                    ft.ElevatedButton(
                        "Tester request_permissions()",
                        on_click=lambda e: page.run_task(tester_permissions, e),
                    ),
                    ft.ElevatedButton(
                        "Tester set_alarm() (dans 30s)",
                        on_click=lambda e: page.run_task(tester_set_alarm, e),
                    ),
                    resultat,
                ],
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
    )


ft.run(main)