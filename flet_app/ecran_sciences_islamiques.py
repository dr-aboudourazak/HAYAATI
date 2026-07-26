"""
ÉCRAN SCIENCES ISLAMIQUES EN FLET (FLET_APP/ECRAN_SCIENCES_ISLAMIQUES.PY)

Premier écran du contenu construit directement en Flet (décision prise le
jour où la preuve de concept Alphabet a été validée) : Coran, Hadith, Sîra,
Tawhid, Fiqh — même contenu JSON, même moteur core/, que la version Tkinter
encore en place. Les deux versions restent compatibles tant que la
migration complète n'est pas faite : elles lisent exactement le même
gui/dictionnaires/fr.json.

Nouveauté par rapport à la preuve de concept Alphabet : le type de leçon
"chronologie" (utilisé par Sîra) se rend comme une frise verticale plutôt
que comme une carte à retourner — chaque science a le format qui lui va.

Lancer : python flet_app/ecran_sciences_islamiques.py
"""
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import flet as ft
from core.langue_arabe_engine import normaliser_progres, marquer_item, resume_etape

CHEMIN_FR_JSON = os.path.join(os.path.dirname(__file__), "..", "gui", "dictionnaires", "fr.json")

TERRACOTTA = "#C1502E"
TERRACOTTA_CLAIR = "#F4E4DC"
OCRE = "#D9A441"
OCRE_CLAIR = "#FBF0DA"
VERT_SUCCES = "#27500A"
AMBRE_ATTENTE = "#d97706"
TEXTE_FONCE = "#2b1607"
GRIS_CLAIR = "#f3f4f6"
GRIS_TEXTE_CLAIR = "#6b7280"


def charger_sciences_islamiques():
    with open(CHEMIN_FR_JSON, encoding="utf-8") as f:
        d = json.load(f)
    return d.get("sciences_islamiques", {})


def bordure_uniforme(couleur, largeur=1):
    cote = ft.BorderSide(width=largeur, color=couleur)
    return ft.Border(top=cote, right=cote, bottom=cote, left=cote)


class EtatApplication:
    def __init__(self):
        self.progres = normaliser_progres(None)
        self.etape_active = 0
        self.index_lecon = 0


def construire_chronologie(chronologie):
    """Frise verticale : pastille numérotée + trait de connexion + date/événement,
    même vocabulaire visuel que le sentier déjà utilisé côté Tkinter, transposé
    ici avec le Canvas natif de Flet plutôt que Tkinter."""
    lignes = []
    for i, etape_chrono in enumerate(chronologie):
        puce = ft.Container(
            content=ft.Text(str(i + 1), color="white", size=11, weight=ft.FontWeight.BOLD),
            width=26, height=26, border_radius=13, bgcolor=TERRACOTTA,
            alignment=ft.Alignment(0, 0),
        )
        contenu = ft.Column(
            [
                ft.Text(etape_chrono["date"], size=12, weight=ft.FontWeight.BOLD, color=TERRACOTTA),
                ft.Text(etape_chrono["evenement"], size=11, color=TEXTE_FONCE),
            ],
            spacing=1, tight=True,
        )
        lignes.append(ft.Row([puce, contenu], spacing=10, vertical_alignment=ft.CrossAxisAlignment.START))
        if i < len(chronologie) - 1:
            lignes.append(ft.Container(width=2, height=14, bgcolor=OCRE, margin=ft.Margin(left=12)))
    return ft.Column(lignes, spacing=4, tight=True)


def construire_bloc_exemples(exemples):
    blocs = []
    for ex in exemples:
        blocs.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text(ex.get("arabe", ""), size=17, weight=ft.FontWeight.BOLD, color=TEXTE_FONCE),
                        ft.Text(f"{ex.get('translitteration','')} — {ex.get('sens','')}", size=10, color=TEXTE_FONCE),
                    ],
                    spacing=2, tight=True,
                ),
                border=bordure_uniforme(OCRE), border_radius=6, padding=10, margin=ft.Margin(bottom=6),
            )
        )
    return blocs


def construire_page_domaine(page, etat, contenu, zone_contenu, rafraichir):
    """Reconstruit la zone de droite (sentier + leçon courante) pour le domaine actif."""
    etapes = contenu.get("etapes", [])
    if not etapes:
        zone_contenu.controls = [ft.Text("Contenu non disponible.", color=TEXTE_FONCE)]
        return

    etape_courante = etapes[min(etat.etape_active, len(etapes) - 1)]

    # --- Sentier horizontal des 5 domaines (assez courts pour tenir sur une ligne) ---
    segments = []
    for i, e in enumerate(etapes):
        actif = (i == etat.etape_active)
        dispo = e.get("disponible", False)
        segments.append(
            ft.Container(
                content=ft.Text(e.get("titre", "").split(" - ")[0], size=11, weight=ft.FontWeight.BOLD if actif else ft.FontWeight.NORMAL,
                                 color="white" if actif else (TEXTE_FONCE if dispo else GRIS_TEXTE_CLAIR)),
                bgcolor=TERRACOTTA if actif else (OCRE_CLAIR if dispo else GRIS_CLAIR),
                padding=8, border_radius=6,
                on_click=(lambda e2, idx=i: choisir_etape(page, etat, contenu, zone_contenu, idx, rafraichir)) if dispo else None,
            )
        )
    barre_sentier = ft.Row(segments, wrap=True, spacing=4)

    if not etape_courante.get("disponible", False):
        zone_contenu.controls = [
            barre_sentier,
            ft.Container(
                content=ft.Text(f"⏳ {etape_courante.get('titre','')} — bientôt disponible.", color=OCRE),
                bgcolor=OCRE_CLAIR, padding=14, border_radius=6, margin=ft.Margin(top=10),
            ),
        ]
        return

    lecons = etape_courante.get("lecons", [])
    cle_progres = f"sciences_{etape_courante.get('cle', etat.etape_active)}"
    etat.index_lecon = min(etat.index_lecon, len(lecons) - 1) if lecons else 0

    resume = resume_etape(etat.progres, cle_progres, len(lecons))
    bandeau = ft.Container(
        content=ft.Text(f"✓ {resume['connues']} compris(es)   ·   🔁 {resume['a_revoir']} à revoir   ·   ⚪ {resume['non_vues']} pas encore vu(e)s",
                         size=12, weight=ft.FontWeight.BOLD, color=TEXTE_FONCE),
        bgcolor=OCRE_CLAIR, padding=10, border_radius=6, margin=ft.Margin(top=10, bottom=10),
    )

    if not lecons:
        zone_contenu.controls = [barre_sentier, bandeau, ft.Text("Aucune leçon.", color=TEXTE_FONCE)]
        return

    lecon = lecons[etat.index_lecon]
    identifiant = str(etat.index_lecon)

    corps_lecon = [
        ft.Text(lecon.get("titre", ""), size=15, weight=ft.FontWeight.BOLD, color=TERRACOTTA),
        ft.Text(lecon.get("explication", ""), size=12, color=TEXTE_FONCE),
    ]
    if lecon.get("type_visuel") == "chronologie":
        corps_lecon.append(ft.Container(content=construire_chronologie(lecon.get("chronologie", [])), margin=ft.Margin(top=8, bottom=8)))
    corps_lecon.extend(construire_bloc_exemples(lecon.get("exemples", [])))

    def marquer(e, connu):
        etat.progres = marquer_item(etat.progres, cle_progres, identifiant, connu)
        if etat.index_lecon < len(lecons) - 1:
            etat.index_lecon += 1
        rafraichir()

    pied = ft.Row(
        [
            ft.Button(ft.Text("✓ J'ai compris", size=11), bgcolor=VERT_SUCCES, color="white", height=32, on_click=lambda e: marquer(e, True)),
            ft.Button(ft.Text("🔁 À revoir", size=11), bgcolor=AMBRE_ATTENTE, color="white", height=32, on_click=lambda e: marquer(e, False)),
        ],
        spacing=8,
    )

    def naviguer(delta):
        etat.index_lecon += delta
        rafraichir()

    barre_pagination = ft.Row(
        [
            ft.Button(ft.Text("◂ Précédent", size=10), on_click=lambda e: naviguer(-1), disabled=(etat.index_lecon == 0)),
            ft.Text(f"{etat.index_lecon + 1} / {len(lecons)}", size=11, color=TEXTE_FONCE),
            ft.Button(ft.Text("Suivant ▸", size=10), on_click=lambda e: naviguer(1), disabled=(etat.index_lecon >= len(lecons) - 1)),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    carte = ft.Container(
        content=ft.Column(corps_lecon + [ft.Container(height=8), pied], spacing=6, tight=True),
        bgcolor=GRIS_CLAIR, border=bordure_uniforme(TERRACOTTA), border_radius=8, padding=16,
    )

    zone_contenu.controls = [barre_sentier, bandeau, carte, ft.Container(height=10), barre_pagination]


def choisir_etape(page, etat, contenu, zone_contenu, index, rafraichir):
    etat.etape_active = index
    etat.index_lecon = 0
    rafraichir()


def main(page: ft.Page):
    page.title = "HAYAATI — Sciences islamiques (Flet)"
    page.bgcolor = "white"
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20

    contenu = charger_sciences_islamiques()
    etat = EtatApplication()

    titre = ft.Text(contenu.get("titre", "🕌 Sciences islamiques"), size=20, weight=ft.FontWeight.BOLD, color=TERRACOTTA)
    sous_titre = ft.Text(contenu.get("sous_titre", ""), size=11, italic=True, color=TEXTE_FONCE)
    zone_contenu = ft.Column([], spacing=4)

    def rafraichir():
        construire_page_domaine(page, etat, contenu, zone_contenu, rafraichir)
        page.update()

    construire_page_domaine(page, etat, contenu, zone_contenu, rafraichir)
    page.add(titre, sous_titre, ft.Container(height=10), zone_contenu)


if __name__ == "__main__":
    # ft.run() n'existe qu'à partir de Flet 0.86.2 ; ft.app() reste disponible
    # (dépréciée mais fonctionnelle) sur les versions antérieures comme 0.86.1.
    if hasattr(ft, "run"):
        ft.run(main)
    else:
        ft.app(target=main)
