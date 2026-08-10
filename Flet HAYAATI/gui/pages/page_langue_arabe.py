"""
PAGE LANGUE ARABE EN FLET (GUI/PAGES/PAGE_LANGUE_ARABE.PY)
Version 2.0 — Adapté pour routage via app_layout.py
"""
from __future__ import annotations
import json
import os
import flet as ft
from core.langue_arabe_engine import normaliser_progres, marquer_item, resume_etape, CLE_MODULE_LANGUE_ARABE
from core.caravane_savoir_engine import construire_session_revision, compter_points_a_revoir

CHEMIN_FR_JSON = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "locales", "fr.json")
# Clé de stockage dédiée aux Sciences islamiques (même moteur de progression que
# Langue arabe, mais un module distinct doit avoir sa propre ligne en base).
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

def bordure_uniforme(couleur, largeur=1):
    cote = ft.BorderSide(width=largeur, color=couleur)
    return ft.Border(top=cote, right=cote, bottom=cote, left=cote)

def marge(left=0, top=0, right=0, bottom=0):
    return ft.Margin(left=left, top=top, right=right, bottom=bottom)

def charger_json_complet():
    with open(CHEMIN_FR_JSON, encoding="utf-8") as f:
        return json.load(f)

class EtatApplication:
    def __init__(self):
        self.progres = normaliser_progres(None)
        self.progres_sciences = normaliser_progres(None)
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

class PageLangueArabe(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.etat = EtatApplication()
        self.contenu_complet = charger_json_complet()

        self.zone_contenu = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=0, expand=True)
        super().__init__(
            content=self.zone_contenu, expand=True,
            bgcolor="white", padding=ft.Padding(20, 20, 20, 20)
        )
        self._charger_progres_persistant()
        self.construire_ecran()

    def actualiser_donnees_affichage(self):
        # Raccourci venant du hub Madrassa : "Caravane du Savoir" doit ouvrir
        # directement le bon onglet plutôt que de retomber sur l'Alphabet.
        if getattr(self.app, "demande_ouverture_caravane", False):
            self.app.demande_ouverture_caravane = False
            etapes = self.contenu_complet.get("langue_arabe", {}).get("etapes", [])
            for i, e in enumerate(etapes):
                if e.get("cle") == "caravane":
                    self.etat.etape_active = i
                    break
        self.construire_ecran()

    def _rafraichir(self):
        self.construire_ecran()
        self.update()

    # --- Persistance sécurisée (coffre-fort chiffré via sync_engine) -------
    # Sans ce raccordement, la progression vit uniquement dans EtatApplication,
    # en mémoire vive : le bouclier de sécurité qui purge le cache d'écrans à
    # chaque mise en arrière-plan (voir app_visuelle.executer_deconnexion_session
    # et le verrou de minimisation dans main.py) effacerait alors le travail de
    # l'utilisateur à chaque fois que le téléphone se verrouille.
    def _charger_progres_persistant(self):
        u_id = getattr(self.app, "user_id_connecte", None)
        if not u_id or not hasattr(self.app, "sync_engine"):
            return
        donnees_langue = self.app.sync_engine.charger_donnees_module(u_id, CLE_MODULE_LANGUE_ARABE)
        donnees_sciences = self.app.sync_engine.charger_donnees_module(u_id, CLE_MODULE_SCIENCES_ISLAMIQUES)
        self.etat.progres = normaliser_progres(donnees_langue)
        self.etat.progres_sciences = normaliser_progres(donnees_sciences)

    def _sauvegarder_progres_langue(self):
        u_id = getattr(self.app, "user_id_connecte", None)
        if not u_id or not hasattr(self.app, "sync_engine"):
            return
        self.app.sync_engine.executer_sauvegarde_module(u_id, CLE_MODULE_LANGUE_ARABE, self.etat.progres)

    def _sauvegarder_progres_sciences(self):
        u_id = getattr(self.app, "user_id_connecte", None)
        if not u_id or not hasattr(self.app, "sync_engine"):
            return
        self.app.sync_engine.executer_sauvegarde_module(u_id, CLE_MODULE_SCIENCES_ISLAMIQUES, self.etat.progres_sciences)

    def construire_ecran(self):
        self.zone_contenu.controls.clear()
        
        # 🎯 BOUTON RETOUR SOUVERAIN VERS LE HUB MADRASSA
        btn_retour_madrassa = ft.IconButton(
            icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
            icon_color=TERRACOTTA,
            icon_size=16,
            tooltip="↩️",
            on_click=lambda _: self.app.layout_central.basculer_vers_ecran("MADRASSA")
        )
        self.zone_contenu.controls.append(btn_retour_madrassa)

        langue_arabe = self.app.txt_global.get("langue_arabe", {}) if hasattr(self.app, "txt_global") else self.contenu_complet.get("langue_arabe", {})
        etapes = langue_arabe.get("etapes", [])
        if not etapes:
            self.zone_contenu.controls.append(ft.Text("Contenu non disponible.", color=TEXTE_FONCE))
            return

        self.zone_contenu.controls.append(
            ft.Text(langue_arabe.get("titre", "🔤 Langue arabe"), size=20, weight=ft.FontWeight.BOLD, color=TERRACOTTA)
        )
        self.zone_contenu.controls.append(ft.Container(height=10))

        def choisir_etape(idx, dispo):
            def handler(e):
                if not dispo: return
                self.etat.etape_active = idx
                self._rafraichir()
            return handler

        segments = [
            ft.Container(
                content=ft.Text(e.get("titre", "").split(" - ")[0][:14], size=11,
                    weight=ft.FontWeight.BOLD if i == self.etat.etape_active else ft.FontWeight.NORMAL,
                    color="white" if i == self.etat.etape_active else (TEXTE_FONCE if e.get("disponible", False) else GRIS_TEXTE_CLAIR)),
                bgcolor=TERRACOTTA if i == self.etat.etape_active else (OCRE_CLAIR if e.get("disponible", False) else GRIS_CLAIR),
                padding=8, border_radius=6, on_click=choisir_etape(i, e.get("disponible", False)),
            )
            for i, e in enumerate(etapes)
        ]
        self.zone_contenu.controls.append(ft.Row(segments, wrap=True, spacing=4))
        self.zone_contenu.controls.append(ft.Container(height=10))

        etape_courante = etapes[min(self.etat.etape_active, len(etapes) - 1)]

        if etape_courante.get("type") == "caravane":
            corps = self._construire_etape_caravane(etape_courante)
        elif not etape_courante.get("disponible", False):
            corps = ft.Container(
                content=ft.Text(f"⏳ {etape_courante.get('titre','')} — bientôt disponible.", color=OCRE),
                bgcolor=OCRE_CLAIR, padding=14, border_radius=6
            )
        elif etape_courante.get("type") == "alphabet":
            corps = self._construire_etape_alphabet(etape_courante)
        elif etape_courante.get("type") == "vocabulaire":
            corps = self._construire_etape_vocabulaire(etape_courante)
        elif etape_courante.get("type") == "conjugaison":
            corps = self._construire_etape_conjugaison(etape_courante)
        elif etape_courante.get("type") == "grammaire":
            corps = self._construire_etape_grammaire(etape_courante)
        elif etape_courante.get("type") == "lecture":
            corps = self._construire_etape_lecture(etape_courante)
        else:
            corps = ft.Container()

        self.zone_contenu.controls.append(corps)

    def _construire_carte_flip(self, item, cle_etape):
        identifiant = item["id"]

        def couleur_bordure():
            e = self.etat.progres.get(cle_etape, {"connues": [], "a_revoir": []})
            if identifiant in e["connues"]: return VERT_SUCCES
            if identifiant in e["a_revoir"]: return AMBRE_ATTENTE
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
                self.etat.progres = marquer_item(self.etat.progres, cle_etape, identifiant, connu)
                self._sauvegarder_progres_langue()
                carte_container.content = contenu_recto
                carte_container.border = bordure_uniforme(couleur_bordure(), 2)
                self._rafraichir()

            lignes.append(ft.Row([
                ft.ElevatedButton("✅", bgcolor=VERT_SUCCES, color="white", height=32, width=48,
                                  style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
                                  tooltip="Je la connais", on_click=lambda e: marquer(e, True)),
                ft.ElevatedButton("❓❓", bgcolor=AMBRE_ATTENTE, color="white", height=32, width=48,
                                  style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
                                  tooltip="À revoir", on_click=lambda e: marquer(e, False)),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=8, tight=True))
            return ft.Column(lignes, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3, tight=True)

        def basculer(e):
            if carte_container.content == contenu_recto:
                carte_container.content = construire_verso()
            else:
                carte_container.content = contenu_recto
            carte_container.update()

        return ft.GestureDetector(content=carte_container, on_tap=basculer)

    def _construire_grille(self, items, cle_etape):
        return ft.Row([self._construire_carte_flip(it, cle_etape) for it in items], wrap=True, spacing=10, run_spacing=10)

    def _bandeau_resume(self, resume):
        return ft.Container(
            content=ft.Text(f"✓ {resume['connues']} connu(e)s   ·   🔁 {resume['a_revoir']} à revoir   ·   ⚪ {resume['non_vues']} pas encore vu(e)s",
                             size=12, weight=ft.FontWeight.BOLD, color=TEXTE_FONCE),
            bgcolor=OCRE_CLAIR, padding=10, border_radius=6, margin=marge(top=6, bottom=10),
        )

    def _barre_pagination(self, page_actuelle, nb_pages, libelle, on_precedent, on_suivant):
        # libelle : uniquement "x / y", sans mot ni titre — aucune traduction requise.
        return ft.Row([
            ft.ElevatedButton("◀", on_click=on_precedent, disabled=(page_actuelle == 0), width=44,
                              style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6))),
            ft.Text(libelle, size=12, weight=ft.FontWeight.BOLD, color=TEXTE_FONCE),
            ft.ElevatedButton("▶", on_click=on_suivant, disabled=(page_actuelle >= nb_pages - 1), width=44,
                              style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6))),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN) if nb_pages > 1 else ft.Container()

    PAR_PAGE_ALPHABET = 16

    def _construire_etape_alphabet(self, etape):
        lettres = etape.get("lettres", [])
        resume = resume_etape(self.etat.progres, "alphabet", len(lettres))
        nb_pages = max(1, (len(lettres) + self.PAR_PAGE_ALPHABET - 1) // self.PAR_PAGE_ALPHABET)
        self.etat.page_alphabet = min(self.etat.page_alphabet, nb_pages - 1)
        debut = self.etat.page_alphabet * self.PAR_PAGE_ALPHABET
        page_lettres = list(enumerate(lettres))[debut:debut + self.PAR_PAGE_ALPHABET]

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
                self.etat.page_alphabet += delta
                self._rafraichir()
            return handler

        return ft.Column([
            self._bandeau_resume(resume),
            self._construire_grille(items, "alphabet"),
            self._barre_pagination(self.etat.page_alphabet, nb_pages, f"{self.etat.page_alphabet + 1} / {nb_pages}", naviguer(-1), naviguer(1)),
        ], spacing=6)

    def _construire_etape_vocabulaire(self, etape):
        listes = etape.get("listes", [])
        if not listes:
            return ft.Text("Contenu non disponible.", color=TEXTE_FONCE)
        total_mots = sum(len(l.get("mots", [])) for l in listes)
        resume = resume_etape(self.etat.progres, "vocabulaire", total_mots)
        self.etat.index_liste_vocabulaire = min(self.etat.index_liste_vocabulaire, len(listes) - 1)
        i_liste = self.etat.index_liste_vocabulaire
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
                self.etat.index_liste_vocabulaire += delta
                self._rafraichir()
            return handler

        return ft.Column([
            self._bandeau_resume(resume),
            ft.Text(liste.get("titre", ""), size=15, weight=ft.FontWeight.BOLD, color=TERRACOTTA),
            self._construire_grille(items, "vocabulaire"),
            self._barre_pagination(i_liste, len(listes), f"{i_liste + 1} / {len(listes)}", naviguer(-1), naviguer(1)),
        ], spacing=6)

    PAR_PAGE_CONJUGAISON = 12

    def _construire_etape_conjugaison(self, etape):
        verbe = etape.get("verbe_modele", {})
        temps_liste = etape.get("temps", [])
        if not temps_liste:
            return ft.Text("Contenu non disponible.", color=TEXTE_FONCE)
        self.etat.onglet_temps_conjugaison = min(self.etat.onglet_temps_conjugaison, len(temps_liste) - 1)

        def choisir_temps(idx):
            def handler(e):
                self.etat.onglet_temps_conjugaison = idx
                self.etat.page_conjugaison = 0
                self._rafraichir()
            return handler

        segments = [
            ft.Container(
                content=ft.Text(t.get("titre", "").split(" - ")[-1], size=11,
                    weight=ft.FontWeight.BOLD if i == self.etat.onglet_temps_conjugaison else ft.FontWeight.NORMAL,
                    color="white" if i == self.etat.onglet_temps_conjugaison else TEXTE_FONCE),
                bgcolor=TERRACOTTA if i == self.etat.onglet_temps_conjugaison else GRIS_CLAIR,
                padding=8, border_radius=6, on_click=choisir_temps(i),
            )
            for i, t in enumerate(temps_liste)
        ]

        temps_actif = temps_liste[self.etat.onglet_temps_conjugaison]
        cle_progres = f"conjugaison_{temps_actif.get('cle', self.etat.onglet_temps_conjugaison)}"
        conjugaisons = temps_actif.get("conjugaisons", [])
        resume = resume_etape(self.etat.progres, cle_progres, len(conjugaisons))

        blocs_note = []
        note = temps_actif.get("note_pedagogique", "")
        if note:
            blocs_note.append(ft.Container(content=ft.Text(f"💡 {note}", size=10, color=TEXTE_FONCE), bgcolor=OCRE_CLAIR, padding=10, border_radius=6, margin=marge(bottom=8)))

        regles_verbe = temps_actif.get("regles_type_verbe", [])
        if regles_verbe:
            cartes_regles = []
            for r in regles_verbe:
                cartes_regles.append(ft.Container(
                    bgcolor="white", border=bordure_uniforme(TERRACOTTA), border_radius=8, padding=10,
                    margin=marge(bottom=6),
                    content=ft.Column([
                        ft.Text(r.get("type", ""), size=11, weight=ft.FontWeight.BOLD, color=TERRACOTTA),
                        ft.Text(r.get("regle", ""), size=10, color=TEXTE_FONCE),
                        ft.Row([
                            ft.Text(f"{r.get('madi','')} → {r.get('mudari','')} → {r.get('amr','')}", size=15, weight=ft.FontWeight.BOLD, color=TEXTE_FONCE),
                        ]),
                        ft.Text(f"{r.get('amr_translitteration','')} — {r.get('sens','')}", size=10, italic=True, color=TEXTE_FONCE),
                    ], spacing=3, tight=True),
                ))
            blocs_note.append(ft.Container(
                content=ft.Column([ft.Text("Trois profils vocaliques à distinguer :", size=11, weight=ft.FontWeight.BOLD, color=TERRACOTTA)] + cartes_regles, spacing=4, tight=True),
                margin=marge(bottom=8),
            ))

        note_temp = temps_actif.get("note_temporelle", "")
        exemples_temp = temps_actif.get("exemples_temporels", [])
        if note_temp:
            blocs_note.append(ft.Container(content=ft.Text(f"⏳ {note_temp}", size=10, color=TEXTE_FONCE), bgcolor=GRIS_CLAIR, padding=10, border_radius=6, margin=marge(bottom=6)))
        if exemples_temp:
            lignes_ex = [ft.Container(
                content=ft.Column([
                    ft.Text(ex.get("arabe", ""), size=14, weight=ft.FontWeight.BOLD, color=TEXTE_FONCE),
                    ft.Text(f"{ex.get('translitteration','')} — {ex.get('sens','')}", size=9, color=TEXTE_FONCE),
                ], spacing=1, tight=True), padding=6,
            ) for ex in exemples_temp]
            blocs_note.append(ft.Container(content=ft.Column(lignes_ex, spacing=2, tight=True), bgcolor=OCRE_CLAIR, border_radius=6, padding=6, margin=marge(bottom=8)))

        nb_pages = max(1, (len(conjugaisons) + self.PAR_PAGE_CONJUGAISON - 1) // self.PAR_PAGE_CONJUGAISON)
        self.etat.page_conjugaison = min(self.etat.page_conjugaison, nb_pages - 1)
        debut = self.etat.page_conjugaison * self.PAR_PAGE_CONJUGAISON
        page_items = list(enumerate(conjugaisons))[debut:debut + self.PAR_PAGE_CONJUGAISON]

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
                self.etat.page_conjugaison += delta
                self._rafraichir()
            return handler

        return ft.Column([
            ft.Container(content=ft.Text(f"Verbe modèle : {verbe.get('forme_base','')} · racine {verbe.get('racine','')} · « {verbe.get('sens','')} »", size=11, weight=ft.FontWeight.BOLD, color=TERRACOTTA),
                          bgcolor=TERRACOTTA_CLAIR, padding=10, border_radius=6, margin=marge(bottom=8)),
            ft.Row(segments, wrap=True, spacing=4),
            self._bandeau_resume(resume),
            *blocs_note,
            self._construire_grille(items, cle_progres),
            self._barre_pagination(self.etat.page_conjugaison, nb_pages, f"{self.etat.page_conjugaison + 1} / {nb_pages}", naviguer(-1), naviguer(1)),
        ], spacing=6)

    def _construire_bloc_exemples(self, exemples):
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

    def _construire_etape_grammaire(self, etape):
        babs = etape.get("babs", [])
        if not babs:
            return ft.Text("Contenu non disponible.", color=TEXTE_FONCE)
        self.etat.onglet_bab_grammaire = min(self.etat.onglet_bab_grammaire, len(babs) - 1)

        def choisir_bab(idx):
            def handler(e):
                self.etat.onglet_bab_grammaire = idx
                self.etat.onglet_sous_rubrique_grammaire = 0
                self.etat.index_lecon_grammaire = 0
                self._rafraichir()
            return handler

        segments_bab = [
            ft.Container(
                content=ft.Text(b.get("titre", f"Bab {i+1}"), size=11,
                    weight=ft.FontWeight.BOLD if i == self.etat.onglet_bab_grammaire else ft.FontWeight.NORMAL,
                    color="white" if i == self.etat.onglet_bab_grammaire else TEXTE_FONCE),
                bgcolor=TERRACOTTA if i == self.etat.onglet_bab_grammaire else GRIS_CLAIR, padding=8, border_radius=6, on_click=choisir_bab(i),
            )
            for i, b in enumerate(babs)
        ]

        bab_actif = babs[self.etat.onglet_bab_grammaire]
        contenu = [ft.Row(segments_bab, wrap=True, spacing=4),
                   ft.Text(bab_actif.get("sous_titre", ""), size=14, weight=ft.FontWeight.BOLD, color=TERRACOTTA, margin=marge(top=6, bottom=6))]

        sous_rubriques = bab_actif.get("sous_rubriques")
        cle_bab = bab_actif.get("cle", str(self.etat.onglet_bab_grammaire))

        if sous_rubriques:
            self.etat.onglet_sous_rubrique_grammaire = min(self.etat.onglet_sous_rubrique_grammaire, len(sous_rubriques) - 1)

            def choisir_sr(idx):
                def handler(e):
                    self.etat.onglet_sous_rubrique_grammaire = idx
                    self.etat.index_lecon_grammaire = 0
                    self._rafraichir()
                return handler

            segments_sr = [
                ft.Container(
                    content=ft.Text(sr.get("titre", ""), size=10,
                        weight=ft.FontWeight.BOLD if i == self.etat.onglet_sous_rubrique_grammaire else ft.FontWeight.NORMAL,
                        color="white" if i == self.etat.onglet_sous_rubrique_grammaire else TEXTE_FONCE),
                    bgcolor=OCRE if i == self.etat.onglet_sous_rubrique_grammaire else GRIS_CLAIR, padding=6, border_radius=6, on_click=choisir_sr(i),
                )
                for i, sr in enumerate(sous_rubriques)
            ]
            contenu.append(ft.Row(segments_sr, wrap=True, spacing=4))
            sr_active = sous_rubriques[self.etat.onglet_sous_rubrique_grammaire]
            lecons = sr_active.get("lecons", [])
            cle_progres = f"grammaire_{cle_bab}_{sr_active.get('cle', self.etat.onglet_sous_rubrique_grammaire)}"
        else:
            lecons = bab_actif.get("lecons", [])
            cle_progres = f"grammaire_{cle_bab}"

        if not lecons:
            contenu.append(ft.Text("Aucune leçon.", color=TEXTE_FONCE))
            return ft.Column(contenu, spacing=6)

        resume = resume_etape(self.etat.progres, cle_progres, len(lecons))
        contenu.append(self._bandeau_resume(resume))

        self.etat.index_lecon_grammaire = min(self.etat.index_lecon_grammaire, len(lecons) - 1)
        lecon = lecons[self.etat.index_lecon_grammaire]
        identifiant = str(self.etat.index_lecon_grammaire)

        def marquer(e, connu):
            self.etat.progres = marquer_item(self.etat.progres, cle_progres, identifiant, connu)
            self._sauvegarder_progres_langue()
            if self.etat.index_lecon_grammaire < len(lecons) - 1:
                self.etat.index_lecon_grammaire += 1
            self._rafraichir()

        def naviguer(delta):
            def handler(e):
                self.etat.index_lecon_grammaire += delta
                self._rafraichir()
            return handler

        carte = ft.Container(
            content=ft.Column(
                [ft.Text(lecon.get("titre", ""), size=15, weight=ft.FontWeight.BOLD, color=TERRACOTTA),
                 ft.Text(lecon.get("explication", ""), size=12, color=TEXTE_FONCE)]
                + self._construire_bloc_exemples(lecon.get("exemples", []))
                + [ft.Row([
                        ft.ElevatedButton("✅", bgcolor=VERT_SUCCES, color="white", height=36, width=52,
                                          style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
                                          tooltip="J'ai compris", on_click=lambda e: marquer(e, True)),
                        ft.ElevatedButton("❓❓", bgcolor=AMBRE_ATTENTE, color="white", height=36, width=52,
                                          style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
                                          tooltip="À revoir", on_click=lambda e: marquer(e, False)),
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)],
                spacing=6, tight=True,
            ),
            bgcolor=GRIS_CLAIR, border=bordure_uniforme(TERRACOTTA), border_radius=8, padding=16,
        )
        contenu.append(carte)
        contenu.append(self._barre_pagination(self.etat.index_lecon_grammaire, len(lecons), f"{self.etat.index_lecon_grammaire + 1} / {len(lecons)}", naviguer(-1), naviguer(1)))
        return ft.Column(contenu, spacing=6)

    def _construire_etape_lecture(self, etape):
        textes = etape.get("textes", [])
        if not textes:
            return ft.Text("Contenu non disponible.", color=TEXTE_FONCE)
        resume = resume_etape(self.etat.progres, "lecture", len(textes))
        self.etat.index_texte_lecture = min(self.etat.index_texte_lecture, len(textes) - 1)
        texte = textes[self.etat.index_texte_lecture]
        identifiant = str(self.etat.index_texte_lecture)

        blocs_lignes = []
        for ligne in texte.get("lignes", []):
            elements = []
            if ligne.get("locuteur"):
                elements.append(ft.Text(f"— {ligne['locuteur']} —", size=9, italic=True, weight=ft.FontWeight.BOLD, color=OCRE))
            elements.append(ft.Text(ligne.get("arabe", ""), size=16, weight=ft.FontWeight.BOLD, color=TEXTE_FONCE))
            elements.append(ft.Text(ligne.get("traduction", ""), size=10, italic=True, color=TEXTE_FONCE))
            blocs_lignes.append(ft.Container(content=ft.Column(elements, spacing=2, tight=True), bgcolor=GRIS_CLAIR, border=bordure_uniforme(OCRE), border_radius=6, padding=10, margin=marge(bottom=4)))

        def marquer(e, connu):
            self.etat.progres = marquer_item(self.etat.progres, "lecture", identifiant, connu)
            self._sauvegarder_progres_langue()
            if self.etat.index_texte_lecture < len(textes) - 1:
                self.etat.index_texte_lecture += 1
            self._rafraichir()

        def naviguer(delta):
            def handler(e):
                self.etat.index_texte_lecture += delta
                self._rafraichir()
            return handler

        vocab = []
        if texte.get("vocabulaire_nouveau"):
            vocab = [ft.Text("Vocabulaire nouveau :", size=11, weight=ft.FontWeight.BOLD, color=TERRACOTTA)] + self._construire_bloc_exemples(texte.get("vocabulaire_nouveau", []))

        return ft.Column([
            self._bandeau_resume(resume),
            ft.Container(content=ft.Column([ft.Text(texte.get("titre", ""), size=14, weight=ft.FontWeight.BOLD, color=TERRACOTTA),
                                              ft.Text(f"Niveau : {texte.get('niveau','')}", size=9, italic=True, color=TERRACOTTA)], spacing=2, tight=True),
                          bgcolor=TERRACOTTA_CLAIR, padding=10, border_radius=6, margin=marge(bottom=8)),
            *blocs_lignes,
            *vocab,
            ft.Row([
                ft.ElevatedButton("✅", bgcolor=VERT_SUCCES, color="white", height=36, width=52,
                                  style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
                                  tooltip="J'ai lu ce texte", on_click=lambda e: marquer(e, True)),
                ft.ElevatedButton("❓❓", bgcolor=AMBRE_ATTENTE, color="white", height=36, width=52,
                                  style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
                                  tooltip="À relire", on_click=lambda e: marquer(e, False)),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            self._barre_pagination(self.etat.index_texte_lecture, len(textes), f"{self.etat.index_texte_lecture + 1} / {len(textes)}", naviguer(-1), naviguer(1)),
        ], spacing=6)

    def _construire_etape_caravane(self, etape):
        progres_combine = dict(self.etat.progres)
        progres_combine.update(self.etat.progres_sciences)
        contenu_langue = self.contenu_complet.get("langue_arabe", {})
        contenu_sciences = self.contenu_complet.get("sciences_islamiques", {})
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

        self.etat.index_caravane = min(self.etat.index_caravane, len(session) - 1)
        arret = session[self.etat.index_caravane]

        def marquer(e, connu):
            p = marquer_item(progres_combine, arret["cle_etape"], arret["identifiant"], connu)
            if arret["cle_etape"].startswith("sciences_"):
                self.etat.progres_sciences = {k: v for k, v in p.items() if k.startswith("sciences_")}
                self._sauvegarder_progres_sciences()
            else:
                self.etat.progres = {k: v for k, v in p.items() if not k.startswith("sciences_")}
                self._sauvegarder_progres_langue()
            if self.etat.index_caravane < len(session) - 1:
                self.etat.index_caravane += 1
            self._rafraichir()

        def naviguer(delta):
            def handler(e):
                self.etat.index_caravane += delta
                self._rafraichir()
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
                        ft.ElevatedButton("✅", bgcolor=VERT_SUCCES, color="white", height=36, width=52,
                                          style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
                                          tooltip="Je la maîtrise", on_click=lambda e: marquer(e, True)),
                        ft.ElevatedButton("❓❓", bgcolor=AMBRE_ATTENTE, color="white", height=36, width=52,
                                          style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
                                          tooltip="Encore à revoir", on_click=lambda e: marquer(e, False)),
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                ], spacing=6, tight=True),
                bgcolor=GRIS_CLAIR, border=bordure_uniforme(TERRACOTTA, 2), border_radius=8, padding=16,
            ),
            self._barre_pagination(self.etat.index_caravane, len(session), f"{self.etat.index_caravane + 1} / {len(session)}", naviguer(-1), naviguer(1)),
        ], spacing=6)
