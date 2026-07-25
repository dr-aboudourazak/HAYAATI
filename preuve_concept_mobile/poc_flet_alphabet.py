"""
PREUVE DE CONCEPT — ÉCRAN ALPHABET EN FLET (PREUVE_CONCEPT_MOBILE/POC_FLET_ALPHABET.PY)

But : vérifier concrètement, pas en théorie, que la bascule vers Flet est
réaliste pour HAYAATI. Ce fichier :
  1) réutilise core/langue_arabe_engine.py SANS AUCUNE MODIFICATION,
  2) réutilise le contenu réel de gui/dictionnaires/fr.json (les 28 lettres),
  3) reconstruit la carte retournable (recto/verso) et le suivi "connu / à
     revoir" avec les primitives natives de Flet (donc portable ensuite vers
     Android/iOS/Web/Desktop depuis ce même fichier, sans réécriture).

Pour le lancer réellement (nécessite un écran, donc pas exécutable dans le
bac à sable où ce fichier a été écrit) :
    pip install flet
    flet run preuve_concept_mobile/poc_flet_alphabet.py
"""
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import flet as ft
from core.langue_arabe_engine import normaliser_progres, marquer_item, resume_etape

CHEMIN_FR_JSON = os.path.join(os.path.dirname(__file__), "..", "gui", "dictionnaires", "fr.json")

TERRACOTTA = "#C1502E"
OCRE = "#D9A441"
VERT_SUCCES = "#27500A"
AMBRE_ATTENTE = "#d97706"
TEXTE_FONCE = "#2b1607"


def charger_lettres():
    """Réutilise le contenu JSON existant tel quel — aucune donnée dupliquée ou réécrite."""
    with open(CHEMIN_FR_JSON, encoding="utf-8") as f:
        d = json.load(f)
    for etape in d["langue_arabe"]["etapes"]:
        if etape["cle"] == "alphabet":
            return etape["lettres"]
    return []


class EtatApplication:
    """Équivalent du 'progres' déjà utilisé côté Tkinter — même moteur, même format."""
    def __init__(self):
        self.progres = normaliser_progres(None)  # en mémoire pour la preuve de concept ;
        # sur le vrai portage mobile, ce serait lu/écrit via une API exposant sync_engine.


def construire_carte_lettre(lettre, index, etat, rafraichir_resume):
    """Une carte retournable : clic pour voir le détail, boutons pour marquer.
    Équivalent direct de _construire_carte_item côté Tkinter (interface_langue_arabe.py)."""
    def _bordure_uniforme(couleur, largeur=2):
        cote = ft.BorderSide(width=largeur, color=couleur)
        return ft.Border(top=cote, right=cote, bottom=cote, left=cote)

    def couleur_bordure():
        if str(index) in etat.progres.get("alphabet", {}).get("connues", []):
            return VERT_SUCCES
        if str(index) in etat.progres.get("alphabet", {}).get("a_revoir", []):
            return AMBRE_ATTENTE
        return TERRACOTTA

    contenu_recto = ft.Column(
        [
            ft.Text(lettre["lettre"], size=32, weight=ft.FontWeight.BOLD, color=TEXTE_FONCE),
            ft.Text(lettre["nom"], size=12, color=TEXTE_FONCE),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
    )

    carte_container = ft.Container(
        content=contenu_recto,
        width=150, height=140,
        border=_bordure_uniforme(couleur_bordure()),
        border_radius=10,
        alignment=ft.Alignment(0, 0),
        padding=10,
    )

    def construire_verso():
        occurrences = lettre.get("occurrences", [])
        lignes = [
            ft.Text(f"{lettre['lettre']} · {lettre['nom']}", size=14, weight=ft.FontWeight.BOLD, color=TERRACOTTA),
            ft.Text(f"Translittération : {lettre['translitteration']}", size=10, color=TEXTE_FONCE),
        ]
        for occ in occurrences[:2]:  # 2 dans la preuve de concept, pas de limite structurelle
            lignes.append(ft.Text(f"{occ['position'].capitalize()} : {occ['mot']} — {occ['sens']}", size=9, color=TEXTE_FONCE))

        def marquer(e, connu):
            etat.progres = marquer_item(etat.progres, "alphabet", str(index), connu)
            rafraichir_resume()
            carte_container.content = contenu_recto
            carte_container.border = _bordure_uniforme(couleur_bordure())
            carte_container.update()

        lignes.append(
            ft.Row(
                [
                    ft.ElevatedButton("✓ Je la connais", bgcolor=VERT_SUCCES, color="white",
                                       on_click=lambda e: marquer(e, True), height=30),
                    ft.ElevatedButton("🔁 À revoir", bgcolor=AMBRE_ATTENTE, color="white",
                                       on_click=lambda e: marquer(e, False), height=30),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            )
        )
        return ft.Column(lignes, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4)

    def basculer(e):
        if carte_container.content == contenu_recto:
            carte_container.content = construire_verso()
        else:
            carte_container.content = contenu_recto
        carte_container.update()

    return ft.GestureDetector(content=carte_container, on_tap=basculer)


def main(page: ft.Page):
    page.title = "HAYAATI — Preuve de concept Flet"
    page.bgcolor = "white"
    page.scroll = ft.ScrollMode.AUTO

    lettres = charger_lettres()
    etat = EtatApplication()

    def texte_resume():
        r = resume_etape(etat.progres, "alphabet", len(lettres))
        return f"✓ {r['connues']} connu(e)s   ·   🔁 {r['a_revoir']} à revoir   ·   ⚪ {r['non_vues']} pas encore vu(e)s"

    # La valeur initiale se règle directement (pas de .update() : le contrôle n'est pas
    # encore attaché à la page à ce stade). rafraichir_resume(), elle, ne sera appelée
    # qu'après page.add() — donc en toute sécurité, une fois le contrôle bien attaché.
    resume_texte = ft.Text(texte_resume(), size=13, weight=ft.FontWeight.BOLD, color=TEXTE_FONCE)

    def rafraichir_resume():
        resume_texte.value = texte_resume()
        resume_texte.update()

    grille = ft.Row(wrap=True, spacing=10, run_spacing=10)
    for i, lettre in enumerate(lettres):
        grille.controls.append(construire_carte_lettre(lettre, i, etat, rafraichir_resume))

    page.add(
        ft.Text("🔤 Langue arabe — Alphabet (preuve de concept Flet)", size=20, weight=ft.FontWeight.BOLD, color=TERRACOTTA),
        ft.Container(content=resume_texte, bgcolor="#FBF0DA", padding=10, border_radius=6),
        grille,
    )


if __name__ == "__main__":
    ft.run(main)