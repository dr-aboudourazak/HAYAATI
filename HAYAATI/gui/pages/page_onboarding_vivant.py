"""
gui/pages/page_onboarding_vivant.py — 17/09/2026

Deux petits éléments "vivants" pour la page onboarding, validés par
maquette avant intégration (voir l'échange sur les 3 previews) :

1. Badge Kaaba : cadran circulaire avec la direction de la Qiblah
   (calcul statique, pas de capteur boussole ici — c'est le rôle de
   page_priere.py) + compte à rebours textuel vers la prochaine prière,
   rafraîchi périodiquement.
   🔧 17/09/2026 : c'était jusqu'ici un simple texte à côté d'une icône —
   incohérent avec l'intention du module (import de calculer_direction_qibla
   jamais utilisé). Corrigé pour être effectivement le cadran circulaire
   à qiblah fixe annoncé ci-dessus.
2. Bandeau verset/hadith : alterne en fondu parmi un corpus, pour que
   la page ne montre pas toujours le même texte à chaque visite.
   🔧 17/09/2026 : puise désormais dans les leçons Coran/Hadith de
   Sciences Islamiques (déjà rédigées et traduites en 4 langues pour la
   Madrassa) plutôt que dans une petite liste figée en français —
   économise une traduction séparée et fait découvrir ce contenu à
   l'utilisateur. Le petit corpus d'origine est conservé en secours, au
   cas où cette section serait un jour vide ou restructurée.

Séparé de page_onboarding.py comme les autres modules compagnons
(page_onboarding_alerts.py, page_onboarding_calendrier.py).
"""
from __future__ import annotations
import asyncio
import math
import random
from datetime import datetime
import flet as ft

from core.agenda_engine import AgendaEngine
from core.qibla_engine import calculer_direction_qibla
from gui.langues import DICTIONNAIRE_LANGUES

ORDRE_PRIERES = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]

# Position de secours (Lomé) si AgendaEngine échoue — même valeur que
# page_priere.py, pour un cap Qiblah cohérent entre les deux pages.
LATITUDE_SECOURS = 10.86
LONGITUDE_SECOURS = 0.20

DIAMETRE_BADGE = 58
RAYON_INDICATEUR = DIAMETRE_BADGE / 2 - 9

# Secours si jamais sciences_islamiques.etapes est vide/absent (voir
# _puiser_versets_hadiths_madrassa). Contenu factuel et déjà largement
# diffusé (versets coraniques, hadiths de recueils reconnus).
CORPUS_VERSETS_SECOURS = [
    {"texte": "Certes, avec la difficulté est une facilité. (Sourate Ash-Sharh, 94:6)", "icone": "📖"},
    {"texte": "Et quiconque place sa confiance en Allah, Il lui suffit. (Sourate At-Talaq, 65:3)", "icone": "📖"},
    {"texte": "La prière est la lumière. (Rapporté par Muslim)", "icone": "🗣️"},
    {"texte": "Les actes ne valent que par leurs intentions. (Rapporté par Al-Bukhari et Muslim)", "icone": "🗣️"},
    {"texte": "Ton Seigneur n'a pas oublié. (Sourate Ad-Duha, 93:3)", "icone": "📖"},
    {"texte": "Le meilleur d'entre vous est celui qui apprend le Coran et l'enseigne. (Rapporté par Al-Bukhari)", "icone": "🗣️"},
]


def _position_polaire(angle_deg: float, rayon: float, cx: float, cy: float) -> tuple[float, float]:
    """Angle 0°=haut, sens horaire → coordonnées (x, y) dans un Stack
    centré sur (cx, cy). Même convention que page_priere.py."""
    rad = math.radians(angle_deg)
    return cx + rayon * math.sin(rad), cy - rayon * math.cos(rad)


def _puiser_versets_hadiths_madrassa(dic: dict) -> list[dict]:
    """Puise les versets/hadiths déjà rédigés et traduits pour la
    Madrassa (Sciences Islamiques → leçons Coran/Hadith), plutôt que de
    maintenir un second corpus séparé à traduire dans les 4 langues.
    Chaque "exemple" de leçon y est déjà au format {arabe,
    translitteration, sens}, la source étant citée dans "sens"."""
    etapes = (dic or {}).get("sciences_islamiques", {}).get("etapes", [])
    corpus: list[dict] = []
    for etape in etapes:
        cle = etape.get("cle")
        if cle not in ("coran", "hadith"):
            continue
        icone = "📖" if cle == "coran" else "🗣️"
        for lecon in etape.get("lecons", []):
            for exemple in lecon.get("exemples", []):
                # "sens" est vide en arabe (le texte source EST déjà le
                # sens dans cette langue) — repli sur "arabe" dans ce cas.
                texte = exemple.get("sens") or exemple.get("arabe")
                if texte:
                    corpus.append({"texte": texte, "icone": icone})
    return corpus


def construire_badge_kaaba(app_reference) -> tuple[ft.Container, "callable"]:
    """Construit le badge et retourne (widget, fonction_de_rafraichissement)
    — la fonction est à rappeler périodiquement par l'appelant, qui gère
    lui-même la boucle async et son arrêt (voir page_onboarding.py)."""
    try:
        moteur_position = AgendaEngine()
        lat, lon = moteur_position.latitude, moteur_position.longitude
    except Exception:
        lat, lon = LATITUDE_SECOURS, LONGITUDE_SECOURS

    cap_qibla = calculer_direction_qibla(lat, lon)
    cx = cy = DIAMETRE_BADGE / 2
    x_k, y_k = _position_polaire(cap_qibla, RAYON_INDICATEUR, cx, cy)

    lbl_countdown = ft.Text(size=10, weight=ft.FontWeight.BOLD, color="#064e3b", text_align=ft.TextAlign.CENTER)

    trait_direction = ft.Container(
        width=2, height=RAYON_INDICATEUR, bgcolor="#6ee7b7",
        left=cx - 1, top=cy - RAYON_INDICATEUR,
        rotate=ft.Rotate(angle=math.radians(cap_qibla), alignment=ft.Alignment(0, 1)),
    )

    cadran = ft.Container(
        width=DIAMETRE_BADGE, height=DIAMETRE_BADGE,
        border_radius=DIAMETRE_BADGE / 2,
        bgcolor="#f0fdf4", border=ft.Border.all(2, "#bbf7d0"),
        content=ft.Stack(
            [
                ft.Container(content=ft.Text("N", size=8, weight=ft.FontWeight.BOLD, color="#86efac"),
                             left=cx - 4, top=2),
                trait_direction,
                ft.Container(width=6, height=6, border_radius=3, bgcolor="#064e3b", left=cx - 3, top=cy - 3),
                ft.Container(content=ft.Text("🕋", size=14), left=x_k - 8, top=y_k - 9),
            ],
            width=DIAMETRE_BADGE, height=DIAMETRE_BADGE,
        ),
    )

    def rafraichir():
        q = DICTIONNAIRE_LANGUES.actif.get("qiblah", {}) if hasattr(DICTIONNAIRE_LANGUES, "actif") else {}
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
        nom_traduit = q.get(f"priere_{prochaine_nom.lower()}", prochaine_nom) if prochaine_nom else None
        if prochaine_nom is None:
            lbl_countdown.value = q.get("badge_kaaba_label", "Qiblah")
        else:
            minutes_restantes = max(0, int((prochaine_dt - maintenant).total_seconds() // 60))
            lbl_countdown.value = q.get("badge_kaaba_compte_a_rebours", "{priere} dans {minutes} min").format(
                priere=nom_traduit, minutes=minutes_restantes
            )
        try:
            lbl_countdown.update()
        except Exception:
            pass

    badge = ft.Container(
        content=ft.Column([cadran, lbl_countdown], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding(4, 4, 4, 4),
    )
    rafraichir()
    return badge, rafraichir


def construire_bandeau_versets() -> tuple[ft.Container, "callable"]:
    """Bandeau qui alterne un verset/hadith en fondu, puisé dans la
    langue active. Retourne (widget, fonction_de_bascule) — l'appelant
    gère la boucle et l'arrêt."""

    def _tirer() -> dict:
        dic = DICTIONNAIRE_LANGUES.actif if hasattr(DICTIONNAIRE_LANGUES, "actif") else {}
        corpus = _puiser_versets_hadiths_madrassa(dic) or CORPUS_VERSETS_SECOURS
        return random.choice(corpus)

    def _formater(v: dict) -> str:
        return f"{v['icone']}  « {v['texte']} »"

    lbl_texte = ft.Text(
        _formater(_tirer()),
        size=12, italic=True, color="#064e3b", text_align=ft.TextAlign.CENTER,
    )
    conteneur = ft.Container(
        content=lbl_texte,
        bgcolor="#f8fafc", padding=ft.Padding(12, 10, 12, 10), border_radius=8,
        border=ft.Border.all(1, "#e5e7eb"),
        opacity=1, animate_opacity=400,
    )

    def basculer():
        lbl_texte.value = _formater(_tirer())

    return conteneur, basculer
