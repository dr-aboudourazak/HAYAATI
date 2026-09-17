"""
gui/pages/page_onboarding_calendrier.py — 11/09/2026

Grille calendrier du mois grégorien en cours, avec le jour hégirien
correspondant affiché sous chaque date, et les journées portant un
événement du calendrier islamique mises en valeur.

Séparé de page_onboarding.py comme page_onboarding_alerts.py l'est déjà —
même convention de découpage dans ce projet.

Réutilise telle quelle la logique de conversion et de détection
d'événements déjà en place dans page_onboarding_alerts.py
(core.time_engine.gregorien_vers_hegiri / obtenir_evenement_hegiri, et
les mêmes clés i18n txt_onb["evenements"] / txt_onb["jours_blancs"] /
txt_onb["mois_nom_N"]) plutôt que de dupliquer une seconde logique de
traduction des événements.
"""
from __future__ import annotations
import calendar
from datetime import date
import flet as ft

from gui.langues import DICTIONNAIRE_LANGUES
from core.time_engine import gregorien_vers_hegiri, obtenir_evenement_hegiri

LARGEUR_CELLULE = 40
HAUTEUR_CELLULE = 44

MOIS_GREGORIENS_SECOURS = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]
JOURS_COURTS_SECOURS = ["L", "M", "M", "J", "V", "S", "D"]


def _texte_evenement_court(evt_cle: str | None, jour_hijri: int, txt_onb: dict) -> str | None:
    """Reprend exactement la même logique de résolution que
    page_onboarding_alerts.py (jours_blancs en clé de premier niveau,
    dhu_hijjah_N formaté, sinon clé directe dans le dict "evenements"),
    pour ne pas maintenir deux résolutions différentes du même événement."""
    if not evt_cle:
        return None
    dict_evt = txt_onb.get("evenements", {})
    if evt_cle == "evt_jours_blancs":
        return txt_onb.get("jours_blancs_court", txt_onb.get("jours_blancs", "Jours blancs"))
    if evt_cle.startswith("evt_dhu_hijjah_"):
        base = dict_evt.get("evt_dhu_hijjah_court", "Dhu al-Hijjah (jour {})")
        try:
            return base.format(jour_hijri)
        except Exception:
            return base
    return dict_evt.get(evt_cle, evt_cle)


def construire_grille_calendrier(ajustement_lune: int = 0) -> ft.Container:
    """Construit la grille du mois grégorien en cours, jour hégirien sous
    chaque date, événements mis en valeur. Rappelée à chaque rafraîchissement
    de l'onboarding (comme les 3 carrousels) plutôt que mise en cache,
    pour rester à jour si le mois change pendant que l'app reste ouverte."""
    txt_onb = DICTIONNAIRE_LANGUES.actif.get("onboarding", {})
    txt_cal_i18n = txt_onb.get("calendrier", {})

    aujourdhui = date.today()
    annee, mois = aujourdhui.year, aujourdhui.month

    noms_mois_greg = txt_cal_i18n.get("mois_gregoriens", MOIS_GREGORIENS_SECOURS)
    jours_courts = txt_cal_i18n.get("jours_semaine_courts", JOURS_COURTS_SECOURS)

    cal = calendar.Calendar(firstweekday=0)  # semaine commençant lundi
    semaines = cal.monthdayscalendar(annee, mois)

    def cellule_jour(jour_greg: int) -> ft.Container:
        if jour_greg == 0:
            return ft.Container(width=LARGEUR_CELLULE, height=HAUTEUR_CELLULE)

        d = date(annee, mois, jour_greg)
        h = gregorien_vers_hegiri(d.year, d.month, d.day, ajustement_fiqh=ajustement_lune)
        evt_cle = obtenir_evenement_hegiri(h["mois_num"], h["jour"])
        est_aujourdhui = (d == aujourdhui)
        a_evenement = evt_cle is not None

        if est_aujourdhui:
            bg, fg_greg, fg_hij = "#064e3b", "#ffffff", "#a7f3d0"
        elif a_evenement:
            bg, fg_greg, fg_hij = "#fef3c7", "#92400e", "#b45309"
        else:
            bg, fg_greg, fg_hij = "#ffffff", "#111827", "#9ca3af"

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(str(jour_greg), size=13, weight=ft.FontWeight.BOLD, color=fg_greg, text_align=ft.TextAlign.CENTER),
                    ft.Text(str(h["jour"]), size=9, color=fg_hij, text_align=ft.TextAlign.CENTER),
                ],
                spacing=0, tight=True,
                alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=LARGEUR_CELLULE, height=HAUTEUR_CELLULE,
            bgcolor=bg, border_radius=6, alignment=ft.Alignment.CENTER,
            border=None if est_aujourdhui else ft.Border.all(1, "#e5e7eb"),
            tooltip=_texte_evenement_court(evt_cle, h["jour"], txt_onb) if a_evenement else None,
        )

    lignes = [
        ft.Row([cellule_jour(j) for j in semaine], spacing=4, alignment=ft.MainAxisAlignment.CENTER)
        for semaine in semaines
    ]

    en_tete_jours = ft.Row(
        [
            ft.Container(content=ft.Text(j, size=10, weight=ft.FontWeight.BOLD, color="#6b7280"),
                         width=LARGEUR_CELLULE, alignment=ft.Alignment.CENTER)
            for j in jours_courts
        ],
        spacing=4, alignment=ft.MainAxisAlignment.CENTER,
    )

    h_aujourdhui = gregorien_vers_hegiri(annee, mois, aujourdhui.day, ajustement_fiqh=ajustement_lune)
    nom_mois_hijri = txt_onb.get(f"mois_nom_{h_aujourdhui['mois_num']}", h_aujourdhui["mois_nom"])
    titre = f"{noms_mois_greg[mois - 1]} {annee} — {nom_mois_hijri} {h_aujourdhui['annee']} AH"

    return ft.Container(
        content=ft.Column(
            [
                ft.Text(titre, size=13, weight=ft.FontWeight.BOLD, color="#064e3b", text_align=ft.TextAlign.CENTER),
                ft.Container(height=6),
                en_tete_jours,
                *lignes,
            ],
            spacing=6, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor="#ffffff", padding=12, border_radius=10, border=ft.Border.all(1, "#e5e7eb"),
    )
