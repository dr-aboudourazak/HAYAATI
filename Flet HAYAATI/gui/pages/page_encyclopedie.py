"""
PAGE ENCYCLOPÉDIE EN FLET (GUI/PAGES/PAGE_ENCYCLOPEDIE.PY)
Version 3.0 — Migration complète depuis Tkinter vers Flet 0.86.2
"""
from __future__ import annotations
import flet as ft
from gui.langues import DICTIONNAIRE_LANGUES
from gui.palette_hayaati import (
    TERRACOTTA, TERRACOTTA_CLAIR, TERRACOTTA_FONCE,
    OCRE, OCRE_CLAIR, OCRE_FONCE, SABLE, BLANC, GRIS_TEXTE, VERT_SUCCES, ROUGE_ERREUR
)
from core.jeu_educatif_engine import (
    CLE_MODULE_JEU, normaliser_progres, compter_perles, badge_actuel,
    prochain_palier, enregistrer_reponse, questions_maitrisees_categorie
)

class PageEncyclopedie(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.categories_ouvertes: set[int] = set()
        self.quiz_ouverts: set[int] = set()
        self.index_question_courante: dict[int, int] = {}

        self.zone_contenu = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=0, expand=True)
        super().__init__(
            content=self.zone_contenu, expand=True,
            bgcolor=BLANC, padding=ft.Padding(20, 20, 20, 20)
        )
        self.construire_interface()

    def actualiser_donnees_affichage(self):
        self.construire_interface()

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

    def construire_interface(self):
        self.zone_contenu.controls.clear()
        
        # 🎯 BOUTON RETOUR SOUVERAIN VERS LE HUB MADRASSA
        btn_retour_madrassa = ft.IconButton(
            icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
            icon_color=TERRACOTTA_FONCE,
            icon_size=16,
            tooltip="↩️",
            on_click=lambda _: self.app.layout_central.basculer_vers_ecran("MADRASSA")
        )
        self.zone_contenu.controls.append(btn_retour_madrassa)

        txt = DICTIONNAIRE_LANGUES.actif.get("encyclopedie", {})
        categories = txt.get("categories", [])
        progres = self._charger_progres()

        self.zone_contenu.controls.append(
            ft.Text(txt.get("titre", "📚 Encyclopédie"), size=20, weight=ft.FontWeight.BOLD, color=TERRACOTTA_FONCE)
        )
        self.zone_contenu.controls.append(
            ft.Text(txt.get("consigne", ""), size=11, italic=True, color=GRIS_TEXTE)
        )
        self.zone_contenu.controls.append(ft.Container(height=10))

        self._construire_bandeau_progression(categories, progres)
        self.zone_contenu.controls.append(ft.Container(height=14))

        for i, categorie in enumerate(categories):
            self.zone_contenu.controls.append(self._construire_carte_categorie(i, categorie, progres))

        self.zone_contenu.controls.append(ft.Container(height=30))

    def _construire_bandeau_progression(self, categories, progres):
        total_lecture = len(categories)
        lu_n = len([i for i in progres["lus"] if i < total_lecture])
        total_questions = sum(len(c.get("quiz", [])) for c in categories)
        perles = compter_perles(progres)
        _cle_badge, libelle_badge = badge_actuel(perles)

        txt_encyclo = DICTIONNAIRE_LANGUES.actif.get("encyclopedie", {})
        lbl_lecture = txt_encyclo.get("progres_lecture", "{} sur {} thèmes parcourus").format(lu_n, total_lecture) if total_lecture else ""

        bandeau = ft.Container(
            bgcolor=OCRE_CLAIR, border_radius=6, padding=10,
            content=ft.Row([
                ft.Text(f"📖 {lbl_lecture}", size=11, weight=ft.FontWeight.BOLD, color=OCRE_FONCE),
                ft.Text(f"✨ {perles} sur {total_questions} perles  ·  {libelle_badge}", size=11, weight=ft.FontWeight.BOLD, color=TERRACOTTA_FONCE),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        )
        self.zone_contenu.controls.append(bandeau)

        suite = prochain_palier(perles)
        if suite:
            manquantes, prochain_libelle = suite
            self.zone_contenu.controls.append(
                ft.Text(f"Encore {manquantes} bonne(s) réponse(s) avant \"{prochain_libelle}\"",
                        size=10, color=GRIS_TEXTE)
            )

    def _construire_carte_categorie(self, index, categorie, progres):
        deja_lu = index in progres["lus"]
        couleur_accent = TERRACOTTA if index % 2 == 0 else OCRE
        couleur_fond_titre = TERRACOTTA_CLAIR if index % 2 == 0 else OCRE_CLAIR
        couleur_texte_titre = TERRACOTTA_FONCE if index % 2 == 0 else OCRE_FONCE

        nb_questions = len(categorie.get("quiz", []))
        nb_maitrisees = len(questions_maitrisees_categorie(progres, index))
        badge_lecture = "✓ " if deja_lu else ""
        suffixe_quiz = f"  ({nb_maitrisees}/{nb_questions} 🎯)" if nb_questions else ""

        corps = ft.Column(spacing=0)
        zone_texte = ft.Text(categorie.get("texte", ""), size=11, color=GRIS_TEXTE, selectable=True)
        corps.controls.append(ft.Container(content=zone_texte, padding=ft.Padding(14, 10, 14, 6), bgcolor=SABLE))

        zone_quiz = ft.Container(visible=False, bgcolor=BLANC, border=ft.Border(
            top=ft.BorderSide(1, couleur_accent), bottom=ft.BorderSide(1, couleur_accent),
            left=ft.BorderSide(1, couleur_accent), right=ft.BorderSide(1, couleur_accent)
        ), border_radius=6, margin=ft.Margin(14, 6, 14, 12))

        btn_quiz = ft.ElevatedButton(
            f"🎯 Tester mes connaissances ({nb_questions} questions)" if nb_questions else "",
            bgcolor=couleur_accent, color=BLANC,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
            on_click=lambda e: self._basculer_quiz(index, categorie, corps, btn_quiz, zone_quiz)
        )

        pied = ft.Container(
            bgcolor=SABLE, padding=ft.Padding(14, 0, 14, 6),
            content=ft.Row([
                ft.Checkbox(
                    label=DICTIONNAIRE_LANGUES.actif.get("reglages", {}).get("lbl_marquer_lu", "Marquer comme parcouru"),
                    value=deja_lu,
                    on_change=lambda e: self._basculer_lu(index, e.control.value)
                ),
                ft.Container(expand=True),
                btn_quiz if nb_questions else ft.Container()
            ])
        )
        corps.controls.append(pied)
        corps.controls.append(zone_quiz)

        if index in self.categories_ouvertes:
            corps.visible = True
            icone = "▾"
        else:
            corps.visible = False
            icone = "▸"

        if index in self.quiz_ouverts:
            zone_quiz.visible = True
            self._rafraichir_zone_quiz(zone_quiz, index, categorie)
            btn_quiz.text = "🎯 Masquer le quiz"

        entete = ft.Container(
            bgcolor=couleur_fond_titre, border_radius=6, padding=10,
            content=ft.Row([
                ft.Text(f"{badge_lecture}{categorie.get('titre', '')}{suffixe_quiz}",
                        size=12, weight=ft.FontWeight.BOLD, color=couleur_texte_titre, expand=True),
                ft.Text(icone, size=14, weight=ft.FontWeight.BOLD, color=couleur_texte_titre)
            ]),
            on_click=lambda e: self._basculer_ouverture(index, corps, entete)
        )

        return ft.Column([entete, corps], spacing=0)

    def _basculer_ouverture(self, index, corps, entete):
        if index in self.categories_ouvertes:
            self.categories_ouvertes.discard(index)
            corps.visible = False
            entete.content.controls[1].value = "▸"
        else:
            self.categories_ouvertes.add(index)
            corps.visible = True
            entete.content.controls[1].value = "▾"
        self.update()

    def _basculer_lu(self, index, valeur):
        p = self._charger_progres()
        indices = set(p["lus"])
        if valeur:
            indices.add(index)
        else:
            indices.discard(index)
        p["lus"] = sorted(indices)
        self._sauvegarder_progres(p)
        self.construire_interface()
        self.update()

    def _basculer_quiz(self, index, categorie, corps, btn_quiz, zone_quiz):
        if index in self.quiz_ouverts:
            self.quiz_ouverts.discard(index)
            zone_quiz.visible = False
            btn_quiz.text = f"🎯 Tester mes connaissances ({len(categorie.get('quiz', []))} questions)"
        else:
            self.quiz_ouverts.add(index)
            self.index_question_courante.setdefault(index, 0)
            self._rafraichir_zone_quiz(zone_quiz, index, categorie)
            zone_quiz.visible = True
            btn_quiz.text = "🎯 Masquer le quiz"
        self.update()

    def _rafraichir_zone_quiz(self, conteneur, index_categorie, categorie):
        conteneur.content = None
        questions = categorie.get("quiz", [])
        if not questions:
            return

        i_question = self.index_question_courante.get(index_categorie, 0) % len(questions)
        question = questions[i_question]
        progres = self._charger_progres()
        deja_maitrisee = i_question in questions_maitrisees_categorie(progres, index_categorie)

        colonne = ft.Column(spacing=6, padding=10)
        colonne.controls.append(ft.Text(
            f"Question {i_question + 1} / {len(questions)}" + ("  ✓ déjà maîtrisée" if deja_maitrisee else ""),
            size=10, weight=ft.FontWeight.BOLD, color=VERT_SUCCES if deja_maitrisee else GRIS_TEXTE
        ))
        colonne.controls.append(ft.Text(question["question"], size=12, color=GRIS_TEXTE))

        lbl_feedback = ft.Text("", size=11)
        colonne.controls.append(lbl_feedback)

        boutons_choix = []

        def choisir(i_choix):
            correcte = (i_choix == question["reponse"])
            for b in boutons_choix:
                b.disabled = True
                if boutons_choix.index(b) == i_choix:
                    b.bgcolor = VERT_SUCCES if correcte else ROUGE_ERREUR
                    b.color = BLANC
                elif boutons_choix.index(b) == question["reponse"] and not correcte:
                    b.bgcolor = VERT_SUCCES
                    b.color = BLANC
            if correcte:
                lbl_feedback.value = f"✓ Exact. {question.get('explication', '')}"
                lbl_feedback.color = VERT_SUCCES
            else:
                lbl_feedback.value = f"La bonne réponse était : « {question['choix'][question['reponse']]} ». {question.get('explication', '')}"
                lbl_feedback.color = ROUGE_ERREUR

            p = self._charger_progres()
            p2 = enregistrer_reponse(p, index_categorie, i_question, correcte)
            self._sauvegarder_progres(p2)
            self.update()

        for i_choix, libelle_choix in enumerate(question["choix"]):
            b = ft.ElevatedButton(
                libelle_choix, bgcolor=SABLE, color=GRIS_TEXTE,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4)),
                on_click=lambda e, i=i_choix: choisir(i)
            )
            boutons_choix.append(b)
            colonne.controls.append(b)

        nav = ft.Row([
            ft.ElevatedButton("◂ Précédente", bgcolor=BLANC, color=GRIS_TEXTE,
                              style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4)),
                              on_click=lambda e: self._naviguer_question(index_categorie, -1, conteneur, categorie)),
            ft.Container(expand=True),
            ft.ElevatedButton("Suivante ▸", bgcolor=BLANC, color=GRIS_TEXTE,
                              style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4)),
                              on_click=lambda e: self._naviguer_question(index_categorie, 1, conteneur, categorie))
        ])
        colonne.controls.append(nav)
        conteneur.content = colonne

    def _naviguer_question(self, index_categorie, delta, conteneur, categorie):
        questions = categorie.get("quiz", [])
        if not questions:
            return
        self.index_question_courante[index_categorie] = (self.index_question_courante.get(index_categorie, 0) + delta) % len(questions)
        self._rafraichir_zone_quiz(conteneur, index_categorie, categorie)
        self.update()
