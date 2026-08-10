"""
PAGE ENCYCLOPÉDIE EN FLET (GUI/PAGES/PAGE_ENCYCLOPEDIE.PY)
Version 4.0 — Refonte "catalogue de modules" pour mobile.

Pourquoi cette refonte : l'ancienne version empilait les 10 modules en
accordéon sur un seul écran, ce qui noyait le contenu sous des rubriques
encore fermées et donnait une impression d'écran surchargé. Ici, l'écran
d'accueil ne montre qu'une grille compacte de tuiles (façon catalogue de
cours) ; on n'entre dans le détail d'un module — texte + quiz — qu'après
un tap. Deux vues, une seule à la fois, beaucoup plus aéré sur petit écran.

Correction du bug historique du quiz : toutes les interactions (ouvrir un
module, répondre à une question, changer de question) reconstruisent
entièrement l'écran via construire_interface() + update(), au lieu de
muter des contrôles déjà affichés puis d'appeler update() en espérant
qu'ils soient encore attachés à l'arbre — le pattern fragile qui rendait
le quiz invisible en usage réel.
"""
from __future__ import annotations
import flet as ft
from gui.langues import DICTIONNAIRE_LANGUES
from gui.palette_hayaati import (
    TERRACOTTA, TERRACOTTA_CLAIR, TERRACOTTA_FONCE,
    OCRE, OCRE_CLAIR, OCRE_FONCE, SABLE, BLANC, GRIS_TEXTE, GRIS_CLAIR, VERT_SUCCES, ROUGE_ERREUR
)
from core.jeu_educatif_engine import (
    CLE_MODULE_JEU, normaliser_progres, compter_perles, badge_actuel,
    prochain_palier, enregistrer_reponse, questions_maitrisees_categorie
)


def _couleurs_index(index):
    if index % 2 == 0:
        return TERRACOTTA, TERRACOTTA_CLAIR, TERRACOTTA_FONCE
    return OCRE, OCRE_CLAIR, OCRE_FONCE


def _emoji_et_libelle(titre_brut):
    """Sépare l'emoji de tête (toujours le tout premier caractère/segment du
    titre brut, avant même 'MODULE :') du libellé affichable sur la tuile.
    Bug corrigé : l'ancienne version retirait d'abord le préfixe 'MODULE : ',
    ce qui supprimait l'emoji avec lui — le premier MOT restant (« Le », « Une »)
    était alors pris à tort pour l'emoji et affiché en grand."""
    parts = titre_brut.split(" ", 1)
    emoji = parts[0] if parts and parts[0] else "📖"
    reste = parts[1] if len(parts) > 1 else ""
    if "MODULE : " in reste:
        reste = reste.split("MODULE : ", 1)[1]
    elif "MODULE :" in reste:
        reste = reste.split("MODULE :", 1)[1].strip()
    return emoji, reste.strip() or titre_brut


class PageEncyclopedie(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.vue = "catalogue"           # "catalogue" | "detail"
        self.categorie_active = None
        self.index_question_courante = {}
        self.quiz_visible = set()

        self.zone_contenu = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=0, expand=True)
        super().__init__(
            content=self.zone_contenu, expand=True,
            bgcolor=BLANC, padding=ft.Padding(20, 20, 20, 20)
        )
        self.construire_interface()

    def actualiser_donnees_affichage(self):
        self.construire_interface()

    def _rafraichir(self):
        self.construire_interface()
        self.update()

    def _charger_progres(self):
        u_id = getattr(self.app, "user_id_connecte", None)
        if not u_id:
            return normaliser_progres(None)
        donnees = self.app.sync_engine.charger_donnees_module(u_id, CLE_MODULE_JEU)
        return normaliser_progres(donnees)

    def _sauvegarder_progres(self, progres):
        u_id = getattr(self.app, "user_id_connecte", None)
        if not u_id:
            return
        self.app.sync_engine.executer_sauvegarde_module(u_id, CLE_MODULE_JEU, progres)

    # -------------------------------------------------------------------
    # ORCHESTRATION
    # -------------------------------------------------------------------
    def construire_interface(self):
        self.zone_contenu.controls.clear()

        txt = DICTIONNAIRE_LANGUES.actif.get("encyclopedie", {})
        categories = txt.get("categories", [])

        if self.vue == "detail" and self.categorie_active is not None and 0 <= self.categorie_active < len(categories):
            self._construire_vue_detail(txt, categories, self.categorie_active)
        else:
            self.vue = "catalogue"
            self._construire_vue_catalogue(txt, categories)

    # -------------------------------------------------------------------
    # VUE 1 : CATALOGUE (grille de tuiles, aérée)
    # -------------------------------------------------------------------
    def _construire_vue_catalogue(self, txt, categories):
        progres = self._charger_progres()

        btn_retour_madrassa = ft.IconButton(
            icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED, icon_color=TERRACOTTA_FONCE, icon_size=16,
            tooltip="↩️", on_click=lambda _: self.app.layout_central.basculer_vers_ecran("MADRASSA")
        )
        self.zone_contenu.controls.append(btn_retour_madrassa)
        self.zone_contenu.controls.append(ft.Text(txt.get("titre", "📚 Encyclopédie"), size=20, weight=ft.FontWeight.BOLD, color=TERRACOTTA_FONCE))
        self.zone_contenu.controls.append(ft.Text(txt.get("consigne", ""), size=11, italic=True, color=GRIS_TEXTE))
        self.zone_contenu.controls.append(ft.Container(height=12))

        self._construire_bandeau_progression(categories, progres)
        self.zone_contenu.controls.append(ft.Container(height=16))

        grille = ft.ResponsiveRow(spacing=12, run_spacing=12)
        for i, categorie in enumerate(categories):
            grille.controls.append(self._construire_tuile_module(i, categorie, progres))
        self.zone_contenu.controls.append(grille)
        self.zone_contenu.controls.append(ft.Container(height=30))

    def _construire_bandeau_progression(self, categories, progres):
        total_lecture = len(categories)
        lu_n = len([i for i in progres["lus"] if i < total_lecture])
        total_questions = sum(len(c.get("quiz", [])) for c in categories)
        perles = compter_perles(progres)
        _cle_badge, libelle_badge = badge_actuel(perles)

        lbl_lecture = DICTIONNAIRE_LANGUES.actif.get("encyclopedie", {}).get("progres_lecture", "{} sur {} thèmes parcourus")
        lbl_lecture = lbl_lecture.format(lu_n, total_lecture) if total_lecture else ""

        bandeau = ft.Container(
            bgcolor=OCRE_CLAIR, border_radius=10, padding=12,
            content=ft.Column([
                ft.Row([
                    ft.Text(f"📖 {lbl_lecture}", size=11, weight=ft.FontWeight.BOLD, color=OCRE_FONCE),
                    ft.Text(f"✨ {perles}/{total_questions}  ·  {libelle_badge}", size=11, weight=ft.FontWeight.BOLD, color=TERRACOTTA_FONCE),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=4)
        )
        self.zone_contenu.controls.append(bandeau)

        suite = prochain_palier(perles)
        if suite:
            manquantes, prochain_libelle = suite
            self.zone_contenu.controls.append(ft.Container(
                content=ft.Text(f"Encore {manquantes} bonne(s) réponse(s) avant « {prochain_libelle} »", size=10, color=GRIS_TEXTE),
                margin=ft.Margin(left=2, top=4, right=0, bottom=0),
            ))

    def _construire_tuile_module(self, index, categorie, progres):
        accent, fond_clair, texte_accent = _couleurs_index(index)
        deja_lu = index in progres["lus"]
        nb_questions = len(categorie.get("quiz", []))
        nb_maitrisees = len(questions_maitrisees_categorie(progres, index))

        emoji, libelle = _emoji_et_libelle(categorie.get("titre", ""))

        puces = []
        if deja_lu:
            puces.append(ft.Text("✅", size=13))
        if nb_questions:
            puces.append(ft.Container(
                content=ft.Text(f"🎯 {nb_maitrisees}/{nb_questions}", size=10, weight=ft.FontWeight.BOLD, color=texte_accent),
                bgcolor=BLANC, border_radius=20, padding=ft.Padding(left=8, right=8, top=2, bottom=2),
            ))

        return ft.Container(
            content=ft.Column([
                ft.Text(emoji, size=26),
                ft.Text(libelle, size=12, weight=ft.FontWeight.BOLD, color=texte_accent,
                        text_align=ft.TextAlign.CENTER, max_lines=3),
                ft.Row(puces, alignment=ft.MainAxisAlignment.CENTER, spacing=6) if puces else ft.Container(height=4),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
            bgcolor=fond_clair, border_radius=14, padding=14, height=140,
            border=ft.Border.all(1, accent),
            alignment=ft.Alignment(0, 0),
            on_click=lambda e, i=index: self._ouvrir_module(i),
            col={"xs": 6, "sm": 4, "md": 3},
        )

    def _ouvrir_module(self, index):
        self.categorie_active = index
        self.vue = "detail"
        self._rafraichir()

    def _retour_catalogue(self, _e=None):
        self.categorie_active = None
        self.vue = "catalogue"
        self._rafraichir()

    # -------------------------------------------------------------------
    # VUE 2 : DÉTAIL D'UN MODULE (texte + quiz)
    # -------------------------------------------------------------------
    def _construire_vue_detail(self, txt, categories, index):
        categorie = categories[index]
        progres = self._charger_progres()
        deja_lu = index in progres["lus"]
        accent, fond_clair, texte_accent = _couleurs_index(index)

        entete = ft.Row([
            ft.IconButton(icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED, icon_color=texte_accent, icon_size=16,
                          tooltip="↩️", on_click=self._retour_catalogue),
            ft.Text(categorie.get("titre", ""), size=14, weight=ft.FontWeight.BOLD, color=texte_accent, expand=True),
        ])
        self.zone_contenu.controls.append(entete)
        self.zone_contenu.controls.append(ft.Container(height=8))

        carte_texte = ft.Container(
            content=ft.Text(categorie.get("texte", ""), size=12, color=GRIS_TEXTE, selectable=True),
            bgcolor=SABLE, border_radius=12, padding=16, border=ft.Border.all(1, accent),
        )
        self.zone_contenu.controls.append(carte_texte)
        self.zone_contenu.controls.append(ft.Container(height=12))

        self.zone_contenu.controls.append(ft.Container(
            bgcolor=fond_clair, border_radius=10, padding=8,
            content=ft.Checkbox(
                label=DICTIONNAIRE_LANGUES.actif.get("reglages", {}).get("lbl_marquer_lu", "Marquer comme parcouru"),
                value=deja_lu, on_change=lambda e: self._basculer_lu(index, e.control.value),
            ),
        ))
        self.zone_contenu.controls.append(ft.Container(height=12))

        nb_questions = len(categorie.get("quiz", []))
        if nb_questions:
            if index in self.quiz_visible:
                self.zone_contenu.controls.append(ft.ElevatedButton(
                    "🎯 Masquer le quiz", bgcolor=accent, color=BLANC,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=lambda e: self._basculer_quiz(index),
                ))
                self.zone_contenu.controls.append(ft.Container(height=10))
                self._construire_zone_quiz(index, categorie, progres, accent)
            else:
                self.zone_contenu.controls.append(ft.ElevatedButton(
                    f"🎯 Quiz ({nb_questions})", bgcolor=accent, color=BLANC,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=lambda e: self._basculer_quiz(index),
                ))

        self.zone_contenu.controls.append(ft.Container(height=30))

    def _basculer_lu(self, index, valeur):
        p = self._charger_progres()
        indices = set(p["lus"])
        if valeur:
            indices.add(index)
        else:
            indices.discard(index)
        p["lus"] = sorted(indices)
        self._sauvegarder_progres(p)
        self._rafraichir()

    def _basculer_quiz(self, index):
        if index in self.quiz_visible:
            self.quiz_visible.discard(index)
        else:
            self.quiz_visible.add(index)
            self.index_question_courante.setdefault(index, 0)
        self._rafraichir()

    def _construire_zone_quiz(self, index_categorie, categorie, progres, accent):
        questions = categorie.get("quiz", [])
        if not questions:
            return

        i_question = self.index_question_courante.get(index_categorie, 0) % len(questions)
        question = questions[i_question]
        deja_maitrisee = i_question in questions_maitrisees_categorie(progres, index_categorie)

        conteneur = ft.Container(
            bgcolor=BLANC, border=ft.Border.all(1, accent), border_radius=10, padding=14,
        )
        colonne = ft.Column(spacing=8)

        # Pied de page réduit au strict "x / y" + une coche discrète si déjà maîtrisée —
        # aucun mot nécessitant une traduction.
        colonne.controls.append(ft.Row([
            ft.Text(f"{i_question + 1} / {len(questions)}", size=11, weight=ft.FontWeight.BOLD,
                     color=VERT_SUCCES if deja_maitrisee else GRIS_TEXTE),
            ft.Text("✅", size=12) if deja_maitrisee else ft.Container(),
        ], spacing=6))
        colonne.controls.append(ft.Text(question["question"], size=13, weight=ft.FontWeight.BOLD, color=GRIS_TEXTE))

        lbl_feedback = ft.Text("", size=11)
        colonne.controls.append(lbl_feedback)

        boutons_choix = []

        def choisir(i_choix):
            correcte = (i_choix == question["reponse"])
            for j, b in enumerate(boutons_choix):
                b.disabled = True
                if j == i_choix:
                    b.bgcolor = VERT_SUCCES if correcte else ROUGE_ERREUR
                    b.color = BLANC
                elif j == question["reponse"] and not correcte:
                    b.bgcolor = VERT_SUCCES
                    b.color = BLANC
            if correcte:
                lbl_feedback.value = f"✓ {question.get('explication', '')}"
                lbl_feedback.color = VERT_SUCCES
            else:
                lbl_feedback.value = f"« {question['choix'][question['reponse']]} » — {question.get('explication', '')}"
                lbl_feedback.color = ROUGE_ERREUR

            p = self._charger_progres()
            p2 = enregistrer_reponse(p, index_categorie, i_question, correcte)
            self._sauvegarder_progres(p2)
            self.update()

        for i_choix, libelle_choix in enumerate(question["choix"]):
            b = ft.ElevatedButton(
                libelle_choix, bgcolor=SABLE, color=GRIS_TEXTE,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                on_click=lambda e, i=i_choix: choisir(i)
            )
            boutons_choix.append(b)
            colonne.controls.append(b)

        nav = ft.Row([
            ft.ElevatedButton("◀", bgcolor=BLANC, color=GRIS_TEXTE, width=44,
                              style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                              on_click=lambda e: self._naviguer_question(index_categorie, -1)),
            ft.ElevatedButton("▶", bgcolor=BLANC, color=GRIS_TEXTE, width=44,
                              style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                              on_click=lambda e: self._naviguer_question(index_categorie, 1)),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=16)
        colonne.controls.append(nav)

        conteneur.content = colonne
        self.zone_contenu.controls.append(conteneur)

    def _naviguer_question(self, index_categorie, delta):
        txt = DICTIONNAIRE_LANGUES.actif.get("encyclopedie", {})
        categories = txt.get("categories", [])
        questions = categories[index_categorie].get("quiz", []) if index_categorie < len(categories) else []
        if not questions:
            return
        self.index_question_courante[index_categorie] = (self.index_question_courante.get(index_categorie, 0) + delta) % len(questions)
        self._rafraichir()
