"""
ÉCRAN LANGUE ARABE EN FLET (FLET_APP/ECRAN_LANGUE_ARABE.PY)

Portage complet des 6 étapes (Alphabet, Vocabulaire, Conjugaison, Grammaire,
Lecture, Caravane du Savoir), sur le même contenu JSON et le même moteur
core/langue_arabe_engine.py que la version Tkinter — les deux restent
compatibles, aucune donnée dupliquée ou réécrite.

Lancer : python flet_app/ecran_langue_arabe.py
"""
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import flet as ft
from core.langue_arabe_engine import normaliser_progres, marquer_item, resume_etape
from core.caravane_savoir_engine import construire_session_revision, compter_points_a_revoir

CHEMIN_FR_JSON = os.path.join(os.path.dirname(__file__), "..", "gui", "dictionnaires", "fr.json")
CLE_MODULE_LANGUE_ARABE = "LANGUE_ARABE_PROGRES"
CLE_MODULE_SCIENCES_ISLAMIQUES = "SCIENCES_ISLAMIQUES_PROGRES"

TERRACOTTA = "#C1502E"
TERRACOTTA_CLAIR = "#F4E4DC"
OCRE = "#D9A441"
OCRE_CLAIR = "#FBF0DA"
VERT_SUCCES = "#27500A"
AMBRE_ATTENTE = "#d97706"
TEXTE_FONCE = "#2b1607"
GRIS_CLAIR = "#f3f4f6"
GRIS_TEXTE_CLAIR = "#6b7280"


def charger_json_complet():
    with open(CHEMIN_FR_JSON, encoding="utf-8") as f:
        return json.load(f)


def bordure_uniforme(couleur, largeur=1):
    cote = ft.BorderSide(width=largeur, color=couleur)
    return ft.Border(top=cote, right=cote, bottom=cote, left=cote)


def marge(left=0, top=0, right=0, bottom=0):
    """Certaines versions de Flet exigent les 4 côtés explicitement (pas de
    valeur par défaut sur Margin) ; cet utilitaire les fournit toujours."""
    return ft.Margin(left=left, top=top, right=right, bottom=bottom)


class EtatApplication:
    def __init__(self):
        self.progres = normaliser_progres(None)          # LANGUE_ARABE_PROGRES (en mémoire, preuve de concept)
        self.progres_sciences = normaliser_progres(None)  # SCIENCES_ISLAMIQUES_PROGRES, pour la Caravane
        self.etape_active = 0
        self.page_alphabet = 0
        self.index_liste_vocabulaire = 0
        self.onglet_temps_conjugaison = 0
        self.page_conjugaison = 0
        self.onglet_bab_grammaire = 0
        self.onglet_sous_rubrique_grammaire = 0
        self.index_lecon_grammaire = 0
        self.index_texte_lecture = 0
        self.index_caravane = 0


# =========================================================================
# GRILLE DE CARTES GÉNÉRIQUE (Alphabet / Vocabulaire / Conjugaison)
# =========================================================================

def construire_carte_flip(item, cle_etape, etat, rafraichir):
    """item : {"id", "principal", "taille_recto", "sous_titre_recto",
    "icone"?, "couleur_hex"?, "lignes_detail":[(texte,taille,gras)]}"""
    identifiant = item["id"]

    def couleur_bordure():
        e = etat.progres.get(cle_etape, {"connues": [], "a_revoir": []})
        if identifiant in e["connues"]:
            return VERT_SUCCES
        if identifiant in e["a_revoir"]:
            return AMBRE_ATTENTE
        return TERRACOTTA

    contenu_recto_elements = []
    if item.get("couleur_hex"):
        contenu_recto_elements.append(ft.Container(width=36, height=36, border_radius=18, bgcolor=item["couleur_hex"], border=bordure_uniforme(TEXTE_FONCE)))
    elif item.get("icone"):
        contenu_recto_elements.append(ft.Text(item["icone"], size=22))
    contenu_recto_elements.append(ft.Text(item.get("principal", "?"), size=item.get("taille_recto", 20), weight=ft.FontWeight.BOLD, color=TEXTE_FONCE, text_align=ft.TextAlign.CENTER))
    contenu_recto_elements.append(ft.Text(item.get("sous_titre_recto", ""), size=10, color=TEXTE_FONCE, text_align=ft.TextAlign.CENTER))
    contenu_recto = ft.Column(contenu_recto_elements, horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, spacing=4, tight=True)

    carte_container = ft.Container(
        content=contenu_recto, width=150,
        border=bordure_uniforme(couleur_bordure(), 2), border_radius=10,
        alignment=ft.Alignment(0, 0), padding=10,
    )

    def construire_verso():
        lignes = [ft.Text(texte, size=taille, weight=(ft.FontWeight.BOLD if gras else ft.FontWeight.NORMAL), color=TEXTE_FONCE, text_align=ft.TextAlign.CENTER)
                  for texte, taille, gras in item.get("lignes_detail", [])]

        def marquer(e, connu):
            etat.progres = marquer_item(etat.progres, cle_etape, identifiant, connu)
            carte_container.content = contenu_recto
            carte_container.border = bordure_uniforme(couleur_bordure(), 2)
            rafraichir()

        lignes.append(
            ft.Column(
                [
                    ft.Button(ft.Text("✓ Je la connais", size=10), bgcolor=VERT_SUCCES, color="white", height=28, on_click=lambda e: marquer(e, True)),
                    ft.Button(ft.Text("🔁 À revoir", size=10), bgcolor=AMBRE_ATTENTE, color="white", height=28, on_click=lambda e: marquer(e, False)),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4, tight=True,
            )
        )
        return ft.Column(lignes, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3, tight=True)

    def basculer(e):
        if carte_container.content == contenu_recto:
            carte_container.content = construire_verso()
        else:
            carte_container.content = contenu_recto
        carte_container.update()

    return ft.GestureDetector(content=carte_container, on_tap=basculer)


def construire_grille(items, cle_etape, etat, rafraichir):
    return ft.Row([construire_carte_flip(it, cle_etape, etat, rafraichir) for it in items], wrap=True, spacing=10, run_spacing=10)


def bandeau_resume(resume):
    return ft.Container(
        content=ft.Text(f"✓ {resume['connues']} connu(e)s   ·   🔁 {resume['a_revoir']} à revoir   ·   ⚪ {resume['non_vues']} pas encore vu(e)s",
                         size=12, weight=ft.FontWeight.BOLD, color=TEXTE_FONCE),
        bgcolor=OCRE_CLAIR, padding=10, border_radius=6, margin=marge(top=6, bottom=10),
    )


def barre_pagination(page_actuelle, nb_pages, libelle, on_precedent, on_suivant):
    return ft.Row(
        [
            ft.Button(ft.Text("◂ Précédent", size=10), on_click=on_precedent, disabled=(page_actuelle == 0)),
            ft.Text(libelle, size=11, color=TEXTE_FONCE),
            ft.Button(ft.Text("Suivant ▸", size=10), on_click=on_suivant, disabled=(page_actuelle >= nb_pages - 1)),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    ) if nb_pages > 1 else ft.Container()


# =========================================================================
# ÉTAPE 1 : ALPHABET
# =========================================================================

PAR_PAGE_ALPHABET = 16

def construire_etape_alphabet(etape, etat, rafraichir):
    lettres = etape.get("lettres", [])
    resume = resume_etape(etat.progres, "alphabet", len(lettres))
    nb_pages = max(1, (len(lettres) + PAR_PAGE_ALPHABET - 1) // PAR_PAGE_ALPHABET)
    etat.page_alphabet = min(etat.page_alphabet, nb_pages - 1)
    debut = etat.page_alphabet * PAR_PAGE_ALPHABET
    page_lettres = list(enumerate(lettres))[debut:debut + PAR_PAGE_ALPHABET]

    items = []
    for i, l in page_lettres:
        lignes = [
            (f"{l['lettre']} · {l['nom']}", 14, True),
            (f"Translittération : {l['translitteration']}", 9, False),
            (f"Connexion : {l['connexion']}", 9, False),
            (l.get("son", ""), 9, False),
        ]
        for occ in l.get("occurrences", []):
            lignes.append((f"{occ['position'].capitalize()} : {occ['mot']} — {occ['sens']}", 9, False))
        items.append({"id": str(i), "principal": l["lettre"], "taille_recto": 28, "sous_titre_recto": l["nom"], "lignes_detail": lignes})

    def naviguer(delta):
        def handler(e):
            etat.page_alphabet += delta
            rafraichir()
        return handler

    return ft.Column([
        bandeau_resume(resume),
        construire_grille(items, "alphabet", etat, rafraichir),
        barre_pagination(etat.page_alphabet, nb_pages, f"Page {etat.page_alphabet + 1} / {nb_pages}", naviguer(-1), naviguer(1)),
    ], spacing=6)


# =========================================================================
# ÉTAPE 2 : VOCABULAIRE
# =========================================================================

def construire_etape_vocabulaire(etape, etat, rafraichir):
    listes = etape.get("listes", [])
    if not listes:
        return ft.Text("Contenu non disponible.", color=TEXTE_FONCE)

    total_mots = sum(len(l.get("mots", [])) for l in listes)
    resume = resume_etape(etat.progres, "vocabulaire", total_mots)
    etat.index_liste_vocabulaire = min(etat.index_liste_vocabulaire, len(listes) - 1)
    i_liste = etat.index_liste_vocabulaire
    liste = listes[i_liste]

    items = []
    for i_mot, mot in enumerate(liste.get("mots", [])):
        identifiant = f"liste{i_liste}_mot{i_mot}"
        items.append({
            "id": identifiant, "principal": mot["arabe"], "taille_recto": 16, "sous_titre_recto": mot["sens"],
            "icone": mot.get("icone"), "couleur_hex": mot.get("couleur_hex"),
            "lignes_detail": [(mot["arabe"], 16, True), (mot["translitteration"], 10, False), (f"« {mot['sens']} »", 10, False)],
        })

    def naviguer(delta):
        def handler(e):
            etat.index_liste_vocabulaire += delta
            rafraichir()
        return handler

    return ft.Column([
        bandeau_resume(resume),
        ft.Text(liste.get("titre", ""), size=15, weight=ft.FontWeight.BOLD, color=TERRACOTTA),
        construire_grille(items, "vocabulaire", etat, rafraichir),
        barre_pagination(i_liste, len(listes), f"{i_liste + 1} / {len(listes)} — {liste.get('titre','')}", naviguer(-1), naviguer(1)),
    ], spacing=6)


# =========================================================================
# ÉTAPE 3 : CONJUGAISON
# =========================================================================

PAR_PAGE_CONJUGAISON = 12

def construire_etape_conjugaison(etape, etat, rafraichir):
    verbe = etape.get("verbe_modele", {})
    temps_liste = etape.get("temps", [])
    if not temps_liste:
        return ft.Text("Contenu non disponible.", color=TEXTE_FONCE)

    etat.onglet_temps_conjugaison = min(etat.onglet_temps_conjugaison, len(temps_liste) - 1)

    def choisir_temps(idx):
        def handler(e):
            etat.onglet_temps_conjugaison = idx
            etat.page_conjugaison = 0
            rafraichir()
        return handler

    segments = [
        ft.Container(
            content=ft.Text(t.get("titre", "").split(" - ")[-1], size=11, weight=ft.FontWeight.BOLD if i == etat.onglet_temps_conjugaison else ft.FontWeight.NORMAL,
                             color="white" if i == etat.onglet_temps_conjugaison else TEXTE_FONCE),
            bgcolor=TERRACOTTA if i == etat.onglet_temps_conjugaison else GRIS_CLAIR,
            padding=8, border_radius=6, on_click=choisir_temps(i),
        )
        for i, t in enumerate(temps_liste)
    ]

    temps_actif = temps_liste[etat.onglet_temps_conjugaison]
    cle_progres = f"conjugaison_{temps_actif.get('cle', etat.onglet_temps_conjugaison)}"
    conjugaisons = temps_actif.get("conjugaisons", [])
    resume = resume_etape(etat.progres, cle_progres, len(conjugaisons))

    blocs_note = []
    note = temps_actif.get("note_pedagogique", "")
    if note:
        blocs_note.append(ft.Container(content=ft.Text(f"💡 {note}", size=10, color=TEXTE_FONCE), bgcolor=OCRE_CLAIR, padding=10, border_radius=6, margin=marge(bottom=8)))

    nb_pages = max(1, (len(conjugaisons) + PAR_PAGE_CONJUGAISON - 1) // PAR_PAGE_CONJUGAISON)
    etat.page_conjugaison = min(etat.page_conjugaison, nb_pages - 1)
    debut = etat.page_conjugaison * PAR_PAGE_CONJUGAISON
    page_items = list(enumerate(conjugaisons))[debut:debut + PAR_PAGE_CONJUGAISON]

    items = []
    for i, c in page_items:
        items.append({
            "id": f"{cle_progres}_{i}", "principal": c["forme"], "taille_recto": 18, "sous_titre_recto": c["pronom"],
            "lignes_detail": [
                (f"{c['pronom']} ({c['pronom_translitteration']})", 11, True),
                (c["personne"], 8, False),
                (c["forme"], 18, True),
                (c["translitteration"], 10, False),
                (f"« {c['sens']} »", 10, False),
            ],
        })

    def naviguer(delta):
        def handler(e):
            etat.page_conjugaison += delta
            rafraichir()
        return handler

    return ft.Column([
        ft.Container(content=ft.Text(f"Verbe modèle : {verbe.get('forme_base','')} · racine {verbe.get('racine','')} · « {verbe.get('sens','')} »", size=11, weight=ft.FontWeight.BOLD, color=TERRACOTTA),
                      bgcolor=TERRACOTTA_CLAIR, padding=10, border_radius=6, margin=marge(bottom=8)),
        ft.Row(segments, wrap=True, spacing=4),
        bandeau_resume(resume),
        *blocs_note,
        construire_grille(items, cle_progres, etat, rafraichir),
        barre_pagination(etat.page_conjugaison, nb_pages, f"Page {etat.page_conjugaison + 1} / {nb_pages}", naviguer(-1), naviguer(1)),
    ], spacing=6)


# =========================================================================
# ÉTAPE 4 : GRAMMAIRE (Bab -> sous-rubrique -> leçon)
# =========================================================================

def construire_bloc_exemples(exemples):
    return [
        ft.Container(
            content=ft.Column([
                ft.Text(ex.get("arabe", ""), size=17, weight=ft.FontWeight.BOLD, color=TEXTE_FONCE),
                ft.Text(f"{ex.get('translitteration','')} — {ex.get('sens','')}", size=10, color=TEXTE_FONCE),
            ], spacing=2, tight=True),
            border=bordure_uniforme(OCRE), border_radius=6, padding=10, margin=marge(bottom=6),
        )
        for ex in exemples
    ]


def construire_etape_grammaire(etape, etat, rafraichir):
    babs = etape.get("babs", [])
    if not babs:
        return ft.Text("Contenu non disponible.", color=TEXTE_FONCE)

    etat.onglet_bab_grammaire = min(etat.onglet_bab_grammaire, len(babs) - 1)

    def choisir_bab(idx):
        def handler(e):
            etat.onglet_bab_grammaire = idx
            etat.onglet_sous_rubrique_grammaire = 0
            etat.index_lecon_grammaire = 0
            rafraichir()
        return handler

    segments_bab = [
        ft.Container(
            content=ft.Text(b.get("titre", f"Bab {i+1}"), size=11, weight=ft.FontWeight.BOLD if i == etat.onglet_bab_grammaire else ft.FontWeight.NORMAL,
                             color="white" if i == etat.onglet_bab_grammaire else TEXTE_FONCE),
            bgcolor=TERRACOTTA if i == etat.onglet_bab_grammaire else GRIS_CLAIR, padding=8, border_radius=6, on_click=choisir_bab(i),
        )
        for i, b in enumerate(babs)
    ]

    bab_actif = babs[etat.onglet_bab_grammaire]
    contenu = [ft.Row(segments_bab, wrap=True, spacing=4),
               ft.Text(bab_actif.get("sous_titre", ""), size=14, weight=ft.FontWeight.BOLD, color=TERRACOTTA_CLAIR if False else TERRACOTTA, margin=marge(top=6, bottom=6))]

    sous_rubriques = bab_actif.get("sous_rubriques")
    cle_bab = bab_actif.get("cle", str(etat.onglet_bab_grammaire))

    if sous_rubriques:
        etat.onglet_sous_rubrique_grammaire = min(etat.onglet_sous_rubrique_grammaire, len(sous_rubriques) - 1)

        def choisir_sr(idx):
            def handler(e):
                etat.onglet_sous_rubrique_grammaire = idx
                etat.index_lecon_grammaire = 0
                rafraichir()
            return handler

        segments_sr = [
            ft.Container(
                content=ft.Text(sr.get("titre", ""), size=10, weight=ft.FontWeight.BOLD if i == etat.onglet_sous_rubrique_grammaire else ft.FontWeight.NORMAL,
                                 color="white" if i == etat.onglet_sous_rubrique_grammaire else TEXTE_FONCE),
                bgcolor=OCRE if i == etat.onglet_sous_rubrique_grammaire else GRIS_CLAIR, padding=6, border_radius=6, on_click=choisir_sr(i),
            )
            for i, sr in enumerate(sous_rubriques)
        ]
        contenu.append(ft.Row(segments_sr, wrap=True, spacing=4))
        sr_active = sous_rubriques[etat.onglet_sous_rubrique_grammaire]
        lecons = sr_active.get("lecons", [])
        cle_progres = f"grammaire_{cle_bab}_{sr_active.get('cle', etat.onglet_sous_rubrique_grammaire)}"
    else:
        lecons = bab_actif.get("lecons", [])
        cle_progres = f"grammaire_{cle_bab}"

    if not lecons:
        contenu.append(ft.Text("Aucune leçon.", color=TEXTE_FONCE))
        return ft.Column(contenu, spacing=6)

    resume = resume_etape(etat.progres, cle_progres, len(lecons))
    contenu.append(bandeau_resume(resume))

    etat.index_lecon_grammaire = min(etat.index_lecon_grammaire, len(lecons) - 1)
    lecon = lecons[etat.index_lecon_grammaire]
    identifiant = str(etat.index_lecon_grammaire)

    def marquer(e, connu):
        etat.progres = marquer_item(etat.progres, cle_progres, identifiant, connu)
        if etat.index_lecon_grammaire < len(lecons) - 1:
            etat.index_lecon_grammaire += 1
        rafraichir()

    def naviguer(delta):
        def handler(e):
            etat.index_lecon_grammaire += delta
            rafraichir()
        return handler

    carte = ft.Container(
        content=ft.Column(
            [ft.Text(lecon.get("titre", ""), size=15, weight=ft.FontWeight.BOLD, color=TERRACOTTA),
             ft.Text(lecon.get("explication", ""), size=12, color=TEXTE_FONCE)]
            + construire_bloc_exemples(lecon.get("exemples", []))
            + [ft.Row([
                    ft.Button(ft.Text("✓ J'ai compris", size=11), bgcolor=VERT_SUCCES, color="white", height=32, on_click=lambda e: marquer(e, True)),
                    ft.Button(ft.Text("🔁 À revoir", size=11), bgcolor=AMBRE_ATTENTE, color="white", height=32, on_click=lambda e: marquer(e, False)),
                ], spacing=8)],
            spacing=6, tight=True,
        ),
        bgcolor=GRIS_CLAIR, border=bordure_uniforme(TERRACOTTA), border_radius=8, padding=16,
    )
    contenu.append(carte)
    contenu.append(barre_pagination(etat.index_lecon_grammaire, len(lecons), f"{etat.index_lecon_grammaire + 1} / {len(lecons)}", naviguer(-1), naviguer(1)))
    return ft.Column(contenu, spacing=6)


# =========================================================================
# ÉTAPE 5 : LECTURE
# =========================================================================

def construire_etape_lecture(etape, etat, rafraichir):
    textes = etape.get("textes", [])
    if not textes:
        return ft.Text("Contenu non disponible.", color=TEXTE_FONCE)

    resume = resume_etape(etat.progres, "lecture", len(textes))
    etat.index_texte_lecture = min(etat.index_texte_lecture, len(textes) - 1)
    texte = textes[etat.index_texte_lecture]
    identifiant = str(etat.index_texte_lecture)

    blocs_lignes = []
    for ligne in texte.get("lignes", []):
        elements = []
        if ligne.get("locuteur"):
            elements.append(ft.Text(f"— {ligne['locuteur']} —", size=9, italic=True, weight=ft.FontWeight.BOLD, color=OCRE))
        elements.append(ft.Text(ligne.get("arabe", ""), size=16, weight=ft.FontWeight.BOLD, color=TEXTE_FONCE))
        elements.append(ft.Text(ligne.get("traduction", ""), size=10, italic=True, color=TEXTE_FONCE))
        blocs_lignes.append(ft.Container(content=ft.Column(elements, spacing=2, tight=True), bgcolor=GRIS_CLAIR, border=bordure_uniforme(OCRE), border_radius=6, padding=10, margin=marge(bottom=4)))

    def marquer(e, connu):
        etat.progres = marquer_item(etat.progres, "lecture", identifiant, connu)
        if etat.index_texte_lecture < len(textes) - 1:
            etat.index_texte_lecture += 1
        rafraichir()

    def naviguer(delta):
        def handler(e):
            etat.index_texte_lecture += delta
            rafraichir()
        return handler

    return ft.Column([
        bandeau_resume(resume),
        ft.Container(content=ft.Column([ft.Text(texte.get("titre", ""), size=14, weight=ft.FontWeight.BOLD, color=TERRACOTTA),
                                          ft.Text(f"Niveau : {texte.get('niveau','')}", size=9, italic=True, color=TERRACOTTA)], spacing=2, tight=True),
                      bgcolor=TERRACOTTA_CLAIR, padding=10, border_radius=6, margin=marge(bottom=8)),
        *blocs_lignes,
        *([ft.Text("Vocabulaire nouveau :", size=11, weight=ft.FontWeight.BOLD, color=TERRACOTTA)] + construire_bloc_exemples(texte.get("vocabulaire_nouveau", [])) if texte.get("vocabulaire_nouveau") else []),
        ft.Row([
            ft.Button(ft.Text("✓ J'ai lu ce texte", size=11), bgcolor=VERT_SUCCES, color="white", height=32, on_click=lambda e: marquer(e, True)),
            ft.Button(ft.Text("🔁 À relire", size=11), bgcolor=AMBRE_ATTENTE, color="white", height=32, on_click=lambda e: marquer(e, False)),
        ], spacing=8),
        barre_pagination(etat.index_texte_lecture, len(textes), f"{etat.index_texte_lecture + 1} / {len(textes)} — {texte.get('titre','')}", naviguer(-1), naviguer(1)),
    ], spacing=6)


# =========================================================================
# ÉTAPE 6 : LA CARAVANE DU SAVOIR
# =========================================================================

def construire_etape_caravane(etape, etat, contenu_complet, rafraichir):
    progres_combine = dict(etat.progres)
    progres_combine.update(etat.progres_sciences)

    contenu_langue = contenu_complet.get("langue_arabe", {})
    contenu_sciences = contenu_complet.get("sciences_islamiques", {})
    nb_total = compter_points_a_revoir(progres_combine)
    session = construire_session_revision(progres_combine, contenu_langue, taille_max=10, contenu_sciences_islamiques=contenu_sciences)

    if not session:
        return ft.Container(
            content=ft.Column([
                ft.Text("🌱 Pas encore de quoi remplir une caravane", size=14, weight=ft.FontWeight.BOLD, color=OCRE),
                ft.Text("Parcourez l'alphabet, le vocabulaire, la conjugaison, la grammaire ou les sciences islamiques — la Caravane se remplira automatiquement.", size=11, color=TEXTE_FONCE),
            ], spacing=6),
            bgcolor=OCRE_CLAIR, padding=14, border_radius=6,
        )

    etat.index_caravane = min(etat.index_caravane, len(session) - 1)
    arret = session[etat.index_caravane]

    def marquer(e, connu):
        p = marquer_item(progres_combine, arret["cle_etape"], arret["identifiant"], connu)
        if arret["cle_etape"].startswith("sciences_"):
            etat.progres_sciences = {k: v for k, v in p.items() if k.startswith("sciences_")}
        else:
            etat.progres = {k: v for k, v in p.items() if not k.startswith("sciences_")}
        if etat.index_caravane < len(session) - 1:
            etat.index_caravane += 1
        rafraichir()

    def naviguer(delta):
        def handler(e):
            etat.index_caravane += delta
            rafraichir()
        return handler

    badge = "🔁 À consolider" if not arret.get("complement") else "✓ Déjà connu — petit rappel"
    return ft.Column([
        ft.Container(content=ft.Text(f"🧭 {nb_total} point(s) à revoir au total — {len(session)} étape(s) dans cette caravane", size=11, weight=ft.FontWeight.BOLD, color=TERRACOTTA),
                      bgcolor=OCRE_CLAIR, padding=10, border_radius=6, margin=marge(bottom=10)),
        ft.Container(
            content=ft.Column([
                ft.Text(f"{arret['module']}   ·   {badge}", size=10, weight=ft.FontWeight.BOLD, color=OCRE),
                ft.Text(arret.get("arabe", ""), size=22, weight=ft.FontWeight.BOLD, color=TERRACOTTA),
                ft.Text(" — ".join(filter(None, [arret.get("translitteration", ""), arret.get("sens", "")])), size=11, color=TEXTE_FONCE),
                ft.Row([
                    ft.Button(ft.Text("✓ Je la maîtrise", size=11), bgcolor=VERT_SUCCES, color="white", height=32, on_click=lambda e: marquer(e, True)),
                    ft.Button(ft.Text("🔁 Encore à revoir", size=11), bgcolor=AMBRE_ATTENTE, color="white", height=32, on_click=lambda e: marquer(e, False)),
                ], spacing=8),
            ], spacing=6, tight=True),
            bgcolor=GRIS_CLAIR, border=bordure_uniforme(TERRACOTTA, 2), border_radius=8, padding=16,
        ),
        barre_pagination(etat.index_caravane, len(session), f"Étape {etat.index_caravane + 1} / {len(session)}", naviguer(-1), naviguer(1)),
    ], spacing=6)


# =========================================================================
# ORCHESTRATION GÉNÉRALE
# =========================================================================

def construire_ecran(etat, contenu_complet, zone_contenu, rafraichir):
    langue_arabe = contenu_complet.get("langue_arabe", {})
    etapes = langue_arabe.get("etapes", [])
    if not etapes:
        zone_contenu.controls = [ft.Text("Contenu non disponible.", color=TEXTE_FONCE)]
        return

    def choisir_etape(idx, dispo):
        def handler(e):
            if not dispo:
                return
            etat.etape_active = idx
            rafraichir()
        return handler

    segments = [
        ft.Container(
            content=ft.Text(e.get("titre", "").split(" - ")[0][:14], size=11, weight=ft.FontWeight.BOLD if i == etat.etape_active else ft.FontWeight.NORMAL,
                             color="white" if i == etat.etape_active else (TEXTE_FONCE if e.get("disponible", False) else GRIS_TEXTE_CLAIR)),
            bgcolor=TERRACOTTA if i == etat.etape_active else (OCRE_CLAIR if e.get("disponible", False) else GRIS_CLAIR),
            padding=8, border_radius=6, on_click=choisir_etape(i, e.get("disponible", False)),
        )
        for i, e in enumerate(etapes)
    ]

    etape_courante = etapes[min(etat.etape_active, len(etapes) - 1)]
    corps = ft.Container()

    if etape_courante.get("type") == "caravane":
        corps = construire_etape_caravane(etape_courante, etat, contenu_complet, rafraichir)
    elif not etape_courante.get("disponible", False):
        corps = ft.Container(content=ft.Text(f"⏳ {etape_courante.get('titre','')} — bientôt disponible.", color=OCRE), bgcolor=OCRE_CLAIR, padding=14, border_radius=6)
    elif etape_courante.get("type") == "alphabet":
        corps = construire_etape_alphabet(etape_courante, etat, rafraichir)
    elif etape_courante.get("type") == "vocabulaire":
        corps = construire_etape_vocabulaire(etape_courante, etat, rafraichir)
    elif etape_courante.get("type") == "conjugaison":
        corps = construire_etape_conjugaison(etape_courante, etat, rafraichir)
    elif etape_courante.get("type") == "grammaire":
        corps = construire_etape_grammaire(etape_courante, etat, rafraichir)
    elif etape_courante.get("type") == "lecture":
        corps = construire_etape_lecture(etape_courante, etat, rafraichir)

    zone_contenu.controls = [ft.Row(segments, wrap=True, spacing=4), ft.Container(height=10), corps]


def main(page: ft.Page):
    page.title = "HAYAATI — Langue arabe (Flet)"
    page.bgcolor = "white"
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20

    contenu_complet = charger_json_complet()
    langue_arabe = contenu_complet.get("langue_arabe", {})
    etat = EtatApplication()

    titre = ft.Text(langue_arabe.get("titre", "🔤 Langue arabe"), size=20, weight=ft.FontWeight.BOLD, color=TERRACOTTA)
    zone_contenu = ft.Column([], spacing=4)

    def rafraichir():
        construire_ecran(etat, contenu_complet, zone_contenu, rafraichir)
        page.update()

    construire_ecran(etat, contenu_complet, zone_contenu, rafraichir)
    page.add(titre, ft.Container(height=10), zone_contenu)


if __name__ == "__main__":
    if hasattr(ft, "run"):
        ft.run(main)
    else:
        ft.app(target=main)
