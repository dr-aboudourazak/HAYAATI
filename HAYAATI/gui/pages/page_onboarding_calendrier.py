"""
gui/pages/page_onboarding_calendrier.py — 17/09/2026

Grille calendrier du mois HÉGIRIEN en cours (1 au 29 ou 30), avec la date
grégorienne correspondante affichée en secondaire sous chaque jour, et
les journées portant un événement du calendrier islamique mises en
valeur.

🔧 17/09/2026 : paradigme inversé à la demande explicite — Hayaati étant
une application islamique, le calendrier hégirien doit être au premier
plan et le grégorien secondaire, alors que c'était l'inverse jusqu'ici
(grille bâtie sur le mois grégorien, jour hégirien en sous-titre). La
grille est donc maintenant bâtie en avançant jour par jour depuis le 1er
jour hégirien du mois courant plutôt qu'avec calendar.Calendar (qui
raisonne en mois grégorien) — la longueur réelle du mois (29 ou 30) est
déterminée dynamiquement plutôt que supposée, pour rester cohérente avec
ajustement_lune (qui peut décaler la bascule d'un jour).

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
from datetime import date, timedelta
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
    """Construit la grille du mois hégirien en cours (1 au 29/30), date
    grégorienne sous chaque jour, événements mis en valeur. Rappelée à
    chaque rafraîchissement de l'onboarding (comme les 3 carrousels)
    plutôt que mise en cache, pour rester à jour si le mois change
    pendant que l'app reste ouverte."""
    txt_onb = DICTIONNAIRE_LANGUES.actif.get("onboarding", {})
    txt_cal_i18n = txt_onb.get("calendrier", {})

    aujourdhui = date.today()
    noms_mois_greg = txt_cal_i18n.get("mois_gregoriens", MOIS_GREGORIENS_SECOURS)
    jours_courts = txt_cal_i18n.get("jours_semaine_courts", JOURS_COURTS_SECOURS)

    # --- 1. Mois hégirien cible (celui d'aujourd'hui, selon l'ajustement fiqh actif) ---
    h_aujourdhui = gregorien_vers_hegiri(aujourdhui.year, aujourdhui.month, aujourdhui.day, ajustement_fiqh=ajustement_lune)
    mois_h_cible, annee_h_cible = h_aujourdhui["mois_num"], h_aujourdhui["annee"]

    # --- 2. Date grégorienne du 1er jour hégirien de ce mois (on remonte
    #     simplement de (jour_actuel - 1) jours, pas besoin d'une
    #     conversion inverse) ---
    premier_jour_greg = aujourdhui - timedelta(days=h_aujourdhui["jour"] - 1)

    # --- 3. Longueur réelle du mois (29 ou 30), déterminée en avançant
    #     jour par jour avec le même ajustement_fiqh plutôt que supposée,
    #     pour rester cohérente avec le curseur de réglages ---
    longueur_mois = 0
    d_scan = premier_jour_greg
    while longueur_mois < 30:
        h_scan = gregorien_vers_hegiri(d_scan.year, d_scan.month, d_scan.day, ajustement_fiqh=ajustement_lune)
        if h_scan["mois_num"] != mois_h_cible or h_scan["annee"] != annee_h_cible:
            break
        longueur_mois += 1
        d_scan += timedelta(days=1)

    def cellule_jour(jour_hijri: int) -> ft.Container:
        d = premier_jour_greg + timedelta(days=jour_hijri - 1)
        evt_cle = obtenir_evenement_hegiri(mois_h_cible, jour_hijri)
        est_aujourdhui = (d == aujourdhui)
        a_evenement = evt_cle is not None

        if est_aujourdhui:
            bg, fg_hij, fg_greg = "#064e3b", "#ffffff", "#a7f3d0"
        elif a_evenement:
            bg, fg_hij, fg_greg = "#fef3c7", "#92400e", "#b45309"
        else:
            bg, fg_hij, fg_greg = "#ffffff", "#111827", "#9ca3af"

        # Jour grégorien seul la plupart du temps ; mois abrégé ajouté
        # uniquement au changement de mois grégorien (le mois hégirien
        # peut chevaucher deux mois grégoriens), pour rester lisible
        # dans une cellule de 40px sans clé i18n supplémentaire.
        if d.day == 1:
            libelle_greg = f"{d.day} {noms_mois_greg[d.month - 1][:3]}"
        else:
            libelle_greg = str(d.day)

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(str(jour_hijri), size=13, weight=ft.FontWeight.BOLD, color=fg_hij, text_align=ft.TextAlign.CENTER),
                    ft.Text(libelle_greg, size=8, color=fg_greg, text_align=ft.TextAlign.CENTER),
                ],
                spacing=0, tight=True,
                alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=LARGEUR_CELLULE, height=HAUTEUR_CELLULE,
            bgcolor=bg, border_radius=6, alignment=ft.Alignment.CENTER,
            border=None if est_aujourdhui else ft.Border.all(1, "#e5e7eb"),
            tooltip=_texte_evenement_court(evt_cle, jour_hijri, txt_onb) if a_evenement else None,
        )

    def case_vide() -> ft.Container:
        return ft.Container(width=LARGEUR_CELLULE, height=HAUTEUR_CELLULE)

    # --- 4. Grille : alignée sur le vrai jour de semaine du 1er jour
    #     hégirien du mois (0 = lundi, comme l'en-tête ci-dessous) ---
    decalage = premier_jour_greg.weekday()
    cellules = [None] * decalage + [cellule_jour(j) for j in range(1, longueur_mois + 1)]
    while len(cellules) % 7 != 0:
        cellules.append(None)

    lignes = [
        ft.Row([c or case_vide() for c in cellules[i:i + 7]], spacing=4, alignment=ft.MainAxisAlignment.CENTER)
        for i in range(0, len(cellules), 7)
    ]

    en_tete_jours = ft.Row(
        [
            ft.Container(content=ft.Text(j, size=10, weight=ft.FontWeight.BOLD, color="#6b7280"),
                         width=LARGEUR_CELLULE, alignment=ft.Alignment.CENTER)
            for j in jours_courts
        ],
        spacing=4, alignment=ft.MainAxisAlignment.CENTER,
    )

    nom_mois_hijri = txt_onb.get(f"mois_nom_{mois_h_cible}", h_aujourdhui["mois_nom"])

    dernier_jour_greg = premier_jour_greg + timedelta(days=max(longueur_mois - 1, 0))
    if (premier_jour_greg.year, premier_jour_greg.month) == (dernier_jour_greg.year, dernier_jour_greg.month):
        portion_greg = f"{noms_mois_greg[premier_jour_greg.month - 1]} {premier_jour_greg.year}"
    else:
        m1 = noms_mois_greg[premier_jour_greg.month - 1][:3]
        m2 = noms_mois_greg[dernier_jour_greg.month - 1][:3]
        if premier_jour_greg.year == dernier_jour_greg.year:
            portion_greg = f"{m1}–{m2} {dernier_jour_greg.year}"
        else:
            portion_greg = f"{m1} {premier_jour_greg.year} – {m2} {dernier_jour_greg.year}"

    titre = f"{nom_mois_hijri} {annee_h_cible} AH — {portion_greg}"

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
