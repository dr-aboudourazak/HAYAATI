"""
gui/pages/page_onboarding_vivant.py — 12/09/2026

Deux petits éléments "vivants" pour la page onboarding, validés par
maquette avant intégration (voir l'échange sur les 3 previews) :

1. Badge Kaaba : direction de la Qiblah (calcul statique, pas de capteur
   boussole ici — c'est le rôle de page_priere.py) + compte à rebours
   textuel vers la prochaine prière, rafraîchi périodiquement.
2. Bandeau verset/hadith : alterne en fondu parmi un petit corpus, pour
   que la page ne montre pas toujours le même texte à chaque visite.

Séparé de page_onboarding.py comme les autres modules compagnons
(page_onboarding_alerts.py, page_onboarding_calendrier.py).
"""
from __future__ import annotations
import asyncio
import random
from datetime import datetime
import flet as ft

from core.agenda_engine import AgendaEngine
from core.qibla_engine import calculer_direction_qibla

ORDRE_PRIERES = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]

# Corpus court, verset/hadith + référence. Contenu factuel et déjà
# largement diffusé (versets coraniques, hadiths de recueils reconnus) —
# même principe que les citations déjà utilisées dans l'encyclopédie.
CORPUS_VERSETS = [
    {"texte": "Certes, avec la difficulté est une facilité.", "ref": "Sourate Ash-Sharh, 94:6"},
    {"texte": "Et quiconque place sa confiance en Allah, Il lui suffit.", "ref": "Sourate At-Talaq, 65:3"},
    {"texte": "La prière est la lumière.", "ref": "Rapporté par Muslim"},
    {"texte": "Les actes ne valent que par leurs intentions.", "ref": "Rapporté par Al-Bukhari et Muslim"},
    {"texte": "Ton Seigneur n'a pas oublié.", "ref": "Sourate Ad-Duha, 93:3"},
    {"texte": "Le meilleur d'entre vous est celui qui apprend le Coran et l'enseigne.", "ref": "Rapporté par Al-Bukhari"},
]


def construire_badge_kaaba(app_reference) -> tuple[ft.Container, "callable"]:
    """Construit le badge et retourne (widget, fonction_de_rafraichissement)
    — la fonction est à rappeler périodiquement par l'appelant, qui gère
    lui-même la boucle async et son arrêt (voir page_onboarding.py)."""
    lbl_countdown = ft.Text(size=11, weight=ft.FontWeight.BOLD, color="#064e3b")
    icone_kaaba = ft.Text("🕋", size=16)

    def rafraichir():
        horaires = getattr(app_reference, "horaires_prieres_aujourdhui", {}) or {}
        maintenant = datetime.now()
        prochaine_nom, prochaine_dt = None, None
        for nom in ORDRE_PRIERES:
            heure_str = horaires.get(nom)
            if not heure_str or ":" not in heure_str:
                continue
            h, m = map(int, heure_str.split(":"))
            candidate = maintenant.replace(hour=h, minute=m, second=0, microsecond=0)
            if candidate > maintenant:
                prochaine_nom, prochaine_dt = nom, candidate
                break
        if prochaine_nom is None:
            lbl_countdown.value = "🕋 Qiblah"
        else:
            minutes_restantes = max(0, int((prochaine_dt - maintenant).total_seconds() // 60))
            lbl_countdown.value = f"{prochaine_nom} dans {minutes_restantes} min"
        try:
            lbl_countdown.update()
        except Exception:
            pass

    badge = ft.Container(
        content=ft.Row([icone_kaaba, lbl_countdown], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
        bgcolor="#f0fdf4", padding=ft.Padding(10, 6, 10, 6), border_radius=20,
        border=ft.Border.all(1, "#bbf7d0"),
    )
    rafraichir()
    return badge, rafraichir


def construire_bandeau_versets() -> tuple[ft.Container, "callable"]:
    """Bandeau qui alterne un verset/hadith en fondu. Retourne
    (widget, fonction_de_bascule) — l'appelant gère la boucle et l'arrêt."""
    verset_initial = random.choice(CORPUS_VERSETS)
    lbl_texte = ft.Text(
        f"« {verset_initial['texte']} » — {verset_initial['ref']}",
        size=12, italic=True, color="#064e3b", text_align=ft.TextAlign.CENTER,
    )
    conteneur = ft.Container(
        content=lbl_texte,
        bgcolor="#f8fafc", padding=ft.Padding(12, 10, 12, 10), border_radius=8,
        border=ft.Border.all(1, "#e5e7eb"),
        opacity=1, animate_opacity=400,
    )

    def basculer():
        nouveau = random.choice(CORPUS_VERSETS)
        lbl_texte.value = f"« {nouveau['texte']} » — {nouveau['ref']}"

    return conteneur, basculer
