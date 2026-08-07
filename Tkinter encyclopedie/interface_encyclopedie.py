"""
MODULE ÉDUCATIF : ENCYCLOPÉDIE & JEU DU SAVOIR (GUI/INTERFACE_ENCYCLOPEDIE.PY)
Version 2.0 - Ajout du "Sentier du Savoir" : un mini-quiz sourcé par thème,
propre à HAYAATI. Progression mesurée à la maîtrise réelle, sans série à
préserver ni classement comparatif entre utilisateurs.
"""
import tkinter as tk
from tkinter import ttk
from gui.langues import DICTIONNAIRE_LANGUES
from gui.palette_hayaati import (
    TERRACOTTA, TERRACOTTA_CLAIR, TERRACOTTA_FONCE,
    OCRE, OCRE_CLAIR, OCRE_FONCE, SABLE, BLANC, GRIS_TEXTE, VERT_SUCCES, ROUGE_ERREUR
)
from core.jeu_educatif_engine import (
    CLE_MODULE_JEU, normaliser_progres, compter_perles, badge_actuel,
    prochain_palier, enregistrer_reponse, questions_maitrisees_categorie
)


class EcranEncyclopedie(tk.Frame):
    def __init__(self, parent, app_reference):
        super().__init__(parent, bg=BLANC)
        self.app = app_reference
        self.categories_ouvertes = set()
        self.quiz_ouverts = set()
        self.index_question_courante = {}  # {categorie: index_question}
        self.widgets_categories = []

        self.canevas = tk.Canvas(self, bg=BLANC, bd=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canevas.yview)
        self.zone_scrollable = tk.Frame(self.canevas, bg=BLANC)

        self.zone_scrollable.bind(
            "<Configure>",
            lambda e: self.canevas.configure(scrollregion=self.canevas.bbox("all"))
        )
        self.id_fenetre_scroll = self.canevas.create_window((0, 0), window=self.zone_scrollable, anchor="nw")
        self.canevas.configure(yscrollcommand=self.scrollbar.set)

        self.canevas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canevas.bind("<Configure>", self._ajuster_largeur_contenu)
        self.canevas.bind_all("<MouseWheel>", self._defilement_molette)
        self.canevas.bind_all("<Button-4>", lambda e: self.canevas.yview_scroll(-2, "units"))
        self.canevas.bind_all("<Button-5>", lambda e: self.canevas.yview_scroll(2, "units"))

        DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_changement_langue)
        self.construire_interface()

    def _ajuster_largeur_contenu(self, event):
        self.canevas.itemconfig(self.id_fenetre_scroll, width=event.width)

    def _defilement_molette(self, event):
        self.canevas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def action_changement_langue(self, nouveau_dictionnaire):
        if self.winfo_exists():
            self.construire_interface()

    def actualiser_contexte(self):
        self.construire_interface()

    def actualiser_donnees_affichage(self):
        self.construire_interface()

    # --- Persistance (une seule clé de module regroupe lecture + quiz) ---
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
        for w in self.zone_scrollable.winfo_children():
            w.destroy()
        self.widgets_categories = []

        txt = DICTIONNAIRE_LANGUES.actif.get("encyclopedie", {})
        categories = txt.get("categories", [])
        progres = self._charger_progres()

        # --- En-tête ---
        tk.Label(
            self.zone_scrollable, text=txt.get("titre", "📚 Encyclopédie"),
            font=("Helvetica", 15, "bold"), fg=TERRACOTTA_FONCE, bg=BLANC, wraplength=640, justify="left"
        ).pack(anchor="w", padx=20, pady=(18, 4))

        tk.Label(
            self.zone_scrollable, text=txt.get("consigne", ""),
            font=("Helvetica", 9, "italic"), fg=GRIS_TEXTE, bg=BLANC, wraplength=640, justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 10))

        self._construire_bandeau_progression(categories, progres)

        # --- Frise décorative simple (zigzag terracotta / ocre) ---
        frise = tk.Canvas(self.zone_scrollable, height=8, bg=BLANC, bd=0, highlightthickness=0)
        frise.pack(fill="x", padx=20, pady=(0, 14))
        frise.bind("<Configure>", lambda e, c=frise: self._dessiner_frise(c))

        # --- Cartes de catégories ---
        for i, categorie in enumerate(categories):
            self._construire_carte_categorie(i, categorie, progres)

        tk.Frame(self.zone_scrollable, bg=BLANC, height=30).pack()

    def _construire_bandeau_progression(self, categories, progres):
        total_lecture = len(categories)
        lu_n = len([i for i in progres["lus"] if i < total_lecture])
        total_questions = sum(len(c.get("quiz", [])) for c in categories)
        perles = compter_perles(progres)
        _cle_badge, libelle_badge = badge_actuel(perles)

        bandeau = tk.Frame(self.zone_scrollable, bg=OCRE_CLAIR)
        bandeau.pack(fill="x", padx=20, pady=(0, 4))

        txt_encyclo = DICTIONNAIRE_LANGUES.actif.get("encyclopedie", {})
        lbl_lecture = txt_encyclo.get("progres_lecture", "{} sur {} thèmes parcourus").format(lu_n, total_lecture) if total_lecture else ""

        tk.Label(bandeau, text=f"📖 {lbl_lecture}", font=("Helvetica", 9, "bold"), fg=OCRE_FONCE, bg=OCRE_CLAIR).pack(side="left", padx=12, pady=8)
        tk.Label(
            bandeau, text=f"✨ {perles} sur {total_questions} perles de savoir  ·  {libelle_badge}",
            font=("Helvetica", 9, "bold"), fg=TERRACOTTA_FONCE, bg=OCRE_CLAIR
        ).pack(side="right", padx=12, pady=8)

        suite = prochain_palier(perles)
        if suite:
            manquantes, prochain_libelle = suite
            tk.Label(
                self.zone_scrollable, text=f"Encore {manquantes} bonne(s) réponse(s) avant \"{prochain_libelle}\"",
                font=("Helvetica", 8), fg=GRIS_TEXTE, bg=BLANC
            ).pack(anchor="w", padx=22, pady=(2, 10))
        else:
            tk.Frame(self.zone_scrollable, bg=BLANC, height=10).pack()

    def _dessiner_frise(self, canevas):
        canevas.delete("all")
        largeur = canevas.winfo_width()
        if largeur <= 1:
            return
        pas = 20
        couleurs = [TERRACOTTA, OCRE]
        x = 0
        i = 0
        while x < largeur:
            canevas.create_polygon(x, 0, x + pas, 8, x + 2 * pas, 0, fill=couleurs[i % 2], outline="")
            x += 2 * pas
            i += 1

    # --- Carte d'un thème (lecture + quiz) ---
    def _construire_carte_categorie(self, index, categorie, progres):
        deja_lu = index in progres["lus"]
        couleur_accent = TERRACOTTA if index % 2 == 0 else OCRE
        couleur_fond_titre = TERRACOTTA_CLAIR if index % 2 == 0 else OCRE_CLAIR
        couleur_texte_titre = TERRACOTTA_FONCE if index % 2 == 0 else OCRE_FONCE

        carte = tk.Frame(self.zone_scrollable, bg=BLANC, highlightbackground=couleur_accent, highlightthickness=1, bd=0)
        carte.pack(fill="x", padx=20, pady=6)

        entete = tk.Frame(carte, bg=couleur_fond_titre, cursor="hand2")
        entete.pack(fill="x")

        nb_questions = len(categorie.get("quiz", []))
        nb_maitrisees = len(questions_maitrisees_categorie(progres, index))
        badge_lecture = "✓ " if deja_lu else ""
        suffixe_quiz = f"  ({nb_maitrisees}/{nb_questions} 🎯)" if nb_questions else ""

        lbl_titre = tk.Label(
            entete, text=f"{badge_lecture}{categorie.get('titre', '')}{suffixe_quiz}", font=("Helvetica", 10, "bold"),
            fg=couleur_texte_titre, bg=couleur_fond_titre, wraplength=560, justify="left", anchor="w"
        )
        lbl_titre.pack(side="left", fill="x", expand=True, padx=12, pady=8)

        icone_var = tk.StringVar(value="▾" if index in self.categories_ouvertes else "▸")
        lbl_icone = tk.Label(entete, textvariable=icone_var, font=("Helvetica", 10, "bold"), fg=couleur_texte_titre, bg=couleur_fond_titre)
        lbl_icone.pack(side="right", padx=12)

        corps = tk.Frame(carte, bg=SABLE)

        zone_texte = tk.Text(
            corps, font=("Helvetica", 10), bg=SABLE, fg=GRIS_TEXTE,
            bd=0, highlightthickness=0, wrap=tk.WORD, height=1, padx=14, pady=10, spacing3=6
        )
        zone_texte.insert("1.0", categorie.get("texte", ""))
        zone_texte.config(state=tk.DISABLED)
        zone_texte.pack(fill="both", expand=True)

        def ajuster_hauteur_texte():
            zone_texte.update_idletasks()
            nb_lignes = int(zone_texte.index("end-1c").split(".")[0])
            zone_texte.config(height=min(max(nb_lignes, 4), 30))

        pied = tk.Frame(corps, bg=SABLE)
        pied.pack(fill="x", padx=14, pady=(0, 6))

        var_lu = tk.BooleanVar(value=deja_lu)

        def basculer_lu():
            p = self._charger_progres()
            indices = set(p["lus"])
            if var_lu.get():
                indices.add(index)
            else:
                indices.discard(index)
            p["lus"] = sorted(indices)
            self._sauvegarder_progres(p)
            self.construire_interface()

        txt_reglages = DICTIONNAIRE_LANGUES.actif.get("reglages", {})
        chk = tk.Checkbutton(
            pied, text=txt_reglages.get("lbl_marquer_lu", "Marquer comme parcouru"),
            variable=var_lu, onvalue=True, offvalue=False, bg=SABLE, fg=GRIS_TEXTE,
            activebackground=SABLE, font=("Helvetica", 9), command=basculer_lu, selectcolor=BLANC
        )
        chk.pack(side="left")

        zone_quiz_conteneur = tk.Frame(corps, bg=BLANC, highlightbackground=couleur_accent, highlightthickness=1)

        if nb_questions:
            def basculer_quiz():
                if index in self.quiz_ouverts:
                    self.quiz_ouverts.discard(index)
                    zone_quiz_conteneur.pack_forget()
                    btn_quiz.config(text=f"🎯 Tester mes connaissances ({nb_questions} questions)")
                else:
                    self.quiz_ouverts.add(index)
                    self.index_question_courante.setdefault(index, 0)
                    self._rafraichir_zone_quiz(zone_quiz_conteneur, index, categorie)
                    zone_quiz_conteneur.pack(fill="x", padx=14, pady=(6, 12))
                    btn_quiz.config(text="🎯 Masquer le quiz")

            btn_quiz = tk.Button(
                pied, text=f"🎯 Tester mes connaissances ({nb_questions} questions)",
                font=("Helvetica", 9, "bold"), fg=BLANC, bg=couleur_accent, bd=0, padx=10, pady=4,
                cursor="hand2", command=basculer_quiz
            )
            btn_quiz.pack(side="right")

            if index in self.quiz_ouverts:
                self._rafraichir_zone_quiz(zone_quiz_conteneur, index, categorie)
                zone_quiz_conteneur.pack(fill="x", padx=14, pady=(6, 12))

        def basculer_ouverture(event=None):
            if index in self.categories_ouvertes:
                self.categories_ouvertes.discard(index)
                corps.pack_forget()
                icone_var.set("▸")
            else:
                self.categories_ouvertes.add(index)
                ajuster_hauteur_texte()
                corps.pack(fill="both", expand=True)
                icone_var.set("▾")

        entete.bind("<Button-1>", basculer_ouverture)
        lbl_titre.bind("<Button-1>", basculer_ouverture)
        lbl_icone.bind("<Button-1>", basculer_ouverture)

        if index in self.categories_ouvertes:
            ajuster_hauteur_texte()
            corps.pack(fill="both", expand=True)

        self.widgets_categories.append(carte)

    # --- Panneau de quiz d'un thème ---
    def _rafraichir_zone_quiz(self, conteneur, index_categorie, categorie):
        for w in conteneur.winfo_children():
            w.destroy()

        questions = categorie.get("quiz", [])
        if not questions:
            return

        i_question = self.index_question_courante.get(index_categorie, 0) % len(questions)
        question = questions[i_question]
        progres = self._charger_progres()
        deja_maitrisee = i_question in questions_maitrisees_categorie(progres, index_categorie)

        entete_q = tk.Frame(conteneur, bg=BLANC)
        entete_q.pack(fill="x", padx=10, pady=(10, 4))
        tk.Label(
            entete_q, text=f"Question {i_question + 1} / {len(questions)}" + ("  ✓ déjà maîtrisée" if deja_maitrisee else ""),
            font=("Helvetica", 8, "bold"), fg=VERT_SUCCES if deja_maitrisee else GRIS_TEXTE, bg=BLANC
        ).pack(anchor="w")

        tk.Label(
            conteneur, text=question["question"], font=("Helvetica", 10), fg=GRIS_TEXTE, bg=BLANC,
            wraplength=560, justify="left"
        ).pack(anchor="w", padx=10, pady=(0, 8))

        zone_boutons = tk.Frame(conteneur, bg=BLANC)
        zone_boutons.pack(fill="x", padx=10)

        lbl_feedback = tk.Label(conteneur, text="", font=("Helvetica", 9), bg=BLANC, wraplength=560, justify="left")
        lbl_feedback.pack(anchor="w", padx=10, pady=(4, 4))

        boutons_choix = []

        def choisir(i_choix):
            for b in boutons_choix:
                b.config(state=tk.DISABLED)
            correcte = (i_choix == question["reponse"])
            if correcte:
                boutons_choix[i_choix].config(bg=VERT_SUCCES, fg=BLANC)
                lbl_feedback.config(text=f"✓ Exact. {question.get('explication', '')}", fg=VERT_SUCCES)
            else:
                boutons_choix[i_choix].config(bg=ROUGE_ERREUR, fg=BLANC)
                boutons_choix[question["reponse"]].config(bg=VERT_SUCCES, fg=BLANC)
                lbl_feedback.config(text=f"La bonne réponse était : « {question['choix'][question['reponse']]} ». {question.get('explication', '')}", fg=ROUGE_ERREUR)

            p = self._charger_progres()
            p2 = enregistrer_reponse(p, index_categorie, i_question, correcte)
            self._sauvegarder_progres(p2)

        for i_choix, libelle_choix in enumerate(question["choix"]):
            b = tk.Button(
                zone_boutons, text=libelle_choix, font=("Helvetica", 9), anchor="w", justify="left",
                bg=SABLE, fg=GRIS_TEXTE, bd=1, relief="solid", padx=8, pady=5, cursor="hand2",
                command=lambda i=i_choix: choisir(i)
            )
            b.pack(fill="x", pady=2)
            boutons_choix.append(b)

        nav = tk.Frame(conteneur, bg=BLANC)
        nav.pack(fill="x", padx=10, pady=(6, 10))

        def question_suivante():
            self.index_question_courante[index_categorie] = (i_question + 1) % len(questions)
            self._rafraichir_zone_quiz(conteneur, index_categorie, categorie)

        def question_precedente():
            self.index_question_courante[index_categorie] = (i_question - 1) % len(questions)
            self._rafraichir_zone_quiz(conteneur, index_categorie, categorie)

        tk.Button(nav, text="◂ Précédente", font=("Helvetica", 8), bg=BLANC, fg=GRIS_TEXTE, bd=0, cursor="hand2", command=question_precedente).pack(side="left")
        tk.Button(nav, text="Suivante ▸", font=("Helvetica", 8), bg=BLANC, fg=GRIS_TEXTE, bd=0, cursor="hand2", command=question_suivante).pack(side="right")
