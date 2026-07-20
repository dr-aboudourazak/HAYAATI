"""
MODULE LANGUE ARABE (GUI/INTERFACE_LANGUE_ARABE.PY)
Version 2.0 - Navigation entre étapes repensée en "sentier" vertical (pastilles
numérotées reliées par un trait) plutôt qu'en onglets horizontaux : illisible
sur un écran de téléphone étroit, le sentier vertical se manipule au pouce
aussi bien qu'à la souris, sans logique séparée par plateforme.
Étape 2 (vocabulaire) ajoutée : listes thématiques, mêmes cartes retournables
que l'alphabet, progression indépendante par étape.
"""
import tkinter as tk
from tkinter import ttk
from gui.langues import DICTIONNAIRE_LANGUES
from gui.palette_hayaati import (
    TERRACOTTA, TERRACOTTA_CLAIR, TERRACOTTA_FONCE,
    OCRE, OCRE_CLAIR, OCRE_FONCE, SABLE, BLANC, GRIS_TEXTE, VERT_SUCCES, AMBRE_ATTENTE
)
from core.langue_arabe_engine import (
    CLE_MODULE_LANGUE_ARABE, normaliser_progres, marquer_item, resume_etape
)

GRIS_INACTIF = "#d1d5db"
GRIS_TEXTE_CLAIR = "#9ca3af"


class EcranLangueArabe(tk.Frame):
    def __init__(self, parent, app_reference):
        super().__init__(parent, bg=BLANC)
        self.app = app_reference
        self.etape_active = 0
        self.cartes_retournees = set()

        self.canevas = tk.Canvas(self, bg=BLANC, bd=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canevas.yview)
        self.zone_scrollable = tk.Frame(self.canevas, bg=BLANC)

        self.zone_scrollable.bind("<Configure>", lambda e: self.canevas.configure(scrollregion=self.canevas.bbox("all")))
        self.id_fenetre_scroll = self.canevas.create_window((0, 0), window=self.zone_scrollable, anchor="nw")
        self.canevas.configure(yscrollcommand=self.scrollbar.set)
        self.canevas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.canevas.bind("<Configure>", self._ajuster_largeur_contenu)
        self.canevas.bind_all("<MouseWheel>", lambda e: self.canevas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        self.canevas.bind_all("<Button-4>", lambda e: self.canevas.yview_scroll(-2, "units"))
        self.canevas.bind_all("<Button-5>", lambda e: self.canevas.yview_scroll(2, "units"))

        DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_changement_langue)
        self.construire_interface()

    def _ajuster_largeur_contenu(self, event):
        self.canevas.itemconfig(self.id_fenetre_scroll, width=event.width)

    def action_changement_langue(self, nouveau_dictionnaire):
        if self.winfo_exists():
            self.construire_interface()

    def actualiser_contexte(self):
        self.construire_interface()

    def actualiser_donnees_affichage(self):
        self.construire_interface()

    def _charger_progres(self):
        u_id = getattr(self.app, "user_id_connecte", None)
        if not u_id:
            return normaliser_progres(None)
        donnees = self.app.sync_engine.charger_donnees_module(u_id, CLE_MODULE_LANGUE_ARABE)
        return normaliser_progres(donnees)

    def _sauvegarder_progres(self, progres):
        u_id = getattr(self.app, "user_id_connecte", None)
        if not u_id:
            return
        self.app.sync_engine.executer_sauvegarde_module(u_id, CLE_MODULE_LANGUE_ARABE, progres)

    def construire_interface(self):
        for w in self.zone_scrollable.winfo_children():
            w.destroy()

        txt = DICTIONNAIRE_LANGUES.actif.get("langue_arabe", {})
        etapes = txt.get("etapes", [])

        tk.Label(
            self.zone_scrollable, text=txt.get("titre", "🔤 Langue arabe"),
            font=("Helvetica", 15, "bold"), fg=TERRACOTTA_FONCE, bg=BLANC, wraplength=640, justify="left"
        ).pack(anchor="w", padx=20, pady=(18, 4))

        tk.Label(
            self.zone_scrollable, text=txt.get("sous_titre", ""),
            font=("Helvetica", 9, "italic"), fg=GRIS_TEXTE, bg=BLANC, wraplength=640, justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 10))

        avertissement = txt.get("avertissement_audio", "")
        if avertissement:
            cadre_avert = tk.Frame(self.zone_scrollable, bg=OCRE_CLAIR)
            cadre_avert.pack(fill="x", padx=20, pady=(0, 14))
            tk.Label(
                cadre_avert, text=f"🔊 {avertissement}", font=("Helvetica", 8), fg=OCRE_FONCE, bg=OCRE_CLAIR,
                wraplength=600, justify="left"
            ).pack(anchor="w", padx=10, pady=6)

        if not etapes:
            tk.Label(self.zone_scrollable, text="Contenu non disponible.", bg=BLANC, fg=GRIS_TEXTE).pack(padx=20, pady=20)
            return

        self._construire_sentier_etapes(etapes)

        etape_courante = etapes[min(self.etape_active, len(etapes) - 1)]

        if not etape_courante.get("disponible", False):
            self._construire_message_attente(etape_courante)
        elif etape_courante.get("type") == "alphabet":
            self._construire_etape_alphabet(etape_courante)
        elif etape_courante.get("type") == "vocabulaire":
            self._construire_etape_vocabulaire(etape_courante)
        else:
            self._construire_message_attente(etape_courante)

        tk.Frame(self.zone_scrollable, bg=BLANC, height=30).pack()

    # --- Le "Sentier du Savoir" : navigation verticale entre étapes ---
    def _construire_sentier_etapes(self, etapes):
        conteneur = tk.Frame(self.zone_scrollable, bg=BLANC)
        conteneur.pack(fill="x", padx=20, pady=(0, 16))

        for i, etape in enumerate(etapes):
            active = (i == self.etape_active)
            disponible = etape.get("disponible", False)

            if active:
                couleur_puce, couleur_fond_ligne = TERRACOTTA, TERRACOTTA_CLAIR
            elif disponible:
                couleur_puce, couleur_fond_ligne = OCRE, BLANC
            else:
                couleur_puce, couleur_fond_ligne = GRIS_INACTIF, BLANC

            ligne = tk.Frame(conteneur, bg=couleur_fond_ligne, cursor="hand2")
            ligne.pack(fill="x")

            puce = tk.Canvas(ligne, width=34, height=42, bg=couleur_fond_ligne, highlightthickness=0)
            puce.pack(side="left")
            puce.create_oval(5, 9, 29, 33, fill=couleur_puce, outline="")
            texte_puce = "🔒" if not disponible else ("✎" if active else str(i + 1))
            puce.create_text(17, 21, text=texte_puce, fill=BLANC, font=("Helvetica", 9, "bold"))

            zone_txt = tk.Frame(ligne, bg=couleur_fond_ligne)
            zone_txt.pack(side="left", fill="both", expand=True, pady=7)
            couleur_titre = TERRACOTTA_FONCE if active else (OCRE_FONCE if disponible else GRIS_TEXTE_CLAIR)
            lbl_t = tk.Label(zone_txt, text=etape.get("titre", f"Étape {i+1}"), font=("Helvetica", 10, "bold" if active else "normal"), fg=couleur_titre, bg=couleur_fond_ligne, anchor="w")
            lbl_t.pack(anchor="w")
            statut = "Étape actuelle" if active else ("Disponible — touchez pour ouvrir" if disponible else "Bientôt disponible")
            lbl_s = tk.Label(zone_txt, text=statut, font=("Helvetica", 7), fg=GRIS_TEXTE_CLAIR, bg=couleur_fond_ligne, anchor="w")
            lbl_s.pack(anchor="w")

            lbl_chevron = tk.Label(ligne, text="▸" if disponible else "", font=("Helvetica", 10), fg=couleur_titre, bg=couleur_fond_ligne)
            lbl_chevron.pack(side="right", padx=14)

            gestionnaire = (lambda idx=i, dispo=disponible: self._choisir_etape(idx) if dispo else None)
            for w in (ligne, puce, zone_txt, lbl_t, lbl_s, lbl_chevron):
                w.bind("<Button-1>", lambda e, g=gestionnaire: g())

            if i < len(etapes) - 1:
                couleur_trait = OCRE if disponible else GRIS_INACTIF
                trait = tk.Canvas(conteneur, width=34, height=10, bg=BLANC, highlightthickness=0)
                trait.pack(anchor="w")
                trait.create_line(17, 0, 17, 10, fill=couleur_trait, width=2)

    def _choisir_etape(self, index):
        self.etape_active = index
        self.construire_interface()

    def _construire_message_attente(self, etape):
        cadre = tk.Frame(self.zone_scrollable, bg=SABLE, highlightbackground=OCRE, highlightthickness=1)
        cadre.pack(fill="x", padx=20, pady=10)
        tk.Label(
            cadre, text=f"⏳ {etape.get('titre', '')}", font=("Helvetica", 11, "bold"), fg=OCRE_FONCE, bg=SABLE
        ).pack(anchor="w", padx=14, pady=(12, 4))
        tk.Label(
            cadre, text="Cette étape n'a pas encore de contenu déposé. Elle apparaîtra ici dès qu'il sera prêt.",
            font=("Helvetica", 9), fg=GRIS_TEXTE, bg=SABLE, wraplength=560, justify="left"
        ).pack(anchor="w", padx=14, pady=(0, 12))

    # --- Grille de cartes générique (réutilisée par alphabet et vocabulaire) ---
    def _construire_grille_cartes(self, items, cle_etape, progres):
        largeur_placeholder = self.canevas.winfo_width()
        is_mobile = getattr(self.app, "mode_smartphone_actif", False)
        nb_colonnes = 2 if is_mobile else 4

        grille = tk.Frame(self.zone_scrollable, bg=BLANC)
        grille.pack(fill="x", padx=14)
        for c in range(nb_colonnes):
            grille.grid_columnconfigure(c, weight=1)

        for i, item in enumerate(items):
            ligne, colonne = divmod(i, nb_colonnes)
            self._construire_carte_item(grille, item, cle_etape, ligne, colonne, progres)

    def _construire_carte_item(self, parent, item, cle_etape, ligne, colonne, progres):
        identifiant = item["id"]
        retournee = identifiant in self.cartes_retournees
        etape_data = progres.get(cle_etape, {"connues": [], "a_revoir": []})
        est_connue = identifiant in etape_data["connues"]
        est_a_revoir = identifiant in etape_data["a_revoir"]
        couleur_bord = VERT_SUCCES if est_connue else (AMBRE_ATTENTE if est_a_revoir else TERRACOTTA)

        carte = tk.Frame(parent, bg=BLANC, highlightbackground=couleur_bord, highlightthickness=2, cursor="hand2")
        carte.grid(row=ligne, column=colonne, sticky="nsew", padx=6, pady=6)

        def rafraichir_carte():
            for w in carte.winfo_children():
                w.destroy()
            if identifiant in self.cartes_retournees:
                self._peupler_face_detail(carte, item, cle_etape, basculer)
            else:
                self._peupler_face_recto(carte, item, basculer)

        def basculer(event=None):
            if identifiant in self.cartes_retournees:
                self.cartes_retournees.discard(identifiant)
            else:
                self.cartes_retournees.add(identifiant)
            rafraichir_carte()

        carte.bind("<Button-1>", basculer)
        rafraichir_carte()

    def _peupler_face_recto(self, carte, item, basculer):
        lbl1 = tk.Label(carte, text=item.get("principal", "?"), font=("Helvetica", item.get("taille_police_recto", 20)), bg=BLANC, fg=TERRACOTTA_FONCE, wraplength=150, justify="center")
        lbl1.pack(pady=(14, 2))
        lbl2 = tk.Label(carte, text=item.get("sous_titre_recto", ""), font=("Helvetica", 9), bg=BLANC, fg=GRIS_TEXTE)
        lbl2.pack(pady=(0, 14))
        lbl1.bind("<Button-1>", basculer)
        lbl2.bind("<Button-1>", basculer)

    def _peupler_face_detail(self, carte, item, cle_etape, basculer):
        for texte, police, couleur, wrap in item.get("lignes_detail", []):
            kwargs = {"wraplength": wrap, "justify": "center"} if wrap else {}
            lbl = tk.Label(carte, text=texte, font=police, bg=BLANC, fg=couleur, **kwargs)
            lbl.pack(pady=(2, 2))
            lbl.bind("<Button-1>", basculer)

        pied = tk.Frame(carte, bg=BLANC)
        pied.pack(pady=(6, 10))

        def marquer(connu):
            p = self._charger_progres()
            p = marquer_item(p, cle_etape, item["id"], connu)
            self._sauvegarder_progres(p)
            self.construire_interface()

        tk.Button(pied, text="✓ Je la connais", font=("Helvetica", 7), bg=VERT_SUCCES, fg=BLANC, bd=0, padx=6, pady=3, command=lambda: marquer(True)).pack(side="left", padx=2)
        tk.Button(pied, text="🔁 À revoir", font=("Helvetica", 7), bg=AMBRE_ATTENTE, fg=BLANC, bd=0, padx=6, pady=3, command=lambda: marquer(False)).pack(side="left", padx=2)

    # --- Étape Alphabet ---
    def _construire_etape_alphabet(self, etape):
        lettres = etape.get("lettres", [])
        progres = self._charger_progres()
        resume = resume_etape(progres, "alphabet", len(lettres))
        self._construire_bandeau_resume(resume)

        items = []
        for i, l in enumerate(lettres):
            items.append({
                "id": str(i),
                "principal": l.get("lettre", "?"), "taille_police_recto": 28,
                "sous_titre_recto": l.get("nom", ""),
                "lignes_detail": [
                    (f"{l.get('lettre','')}  ·  {l.get('nom','')}", ("Helvetica", 12, "bold"), TERRACOTTA_FONCE, None),
                    (f"Translittération : {l.get('translitteration','')}", ("Helvetica", 8), GRIS_TEXTE, None),
                    (f"Connexion : {l.get('connexion','')}", ("Helvetica", 8), GRIS_TEXTE, 150),
                    (l.get("son", ""), ("Helvetica", 8), GRIS_TEXTE, 150),
                    (f"{l.get('exemple_mot','')} — {l.get('exemple_translitteration','')}\n« {l.get('exemple_sens','')} »", ("Helvetica", 9, "italic"), OCRE_FONCE, 150),
                ],
            })
        self._construire_grille_cartes(items, "alphabet", progres)

    # --- Étape Vocabulaire ---
    def _construire_etape_vocabulaire(self, etape):
        listes = etape.get("listes", [])
        progres = self._charger_progres()

        total_mots = sum(len(l.get("mots", [])) for l in listes)
        resume = resume_etape(progres, "vocabulaire", total_mots)
        self._construire_bandeau_resume(resume)

        for i_liste, liste in enumerate(listes):
            tk.Label(
                self.zone_scrollable, text=liste.get("titre", ""), font=("Helvetica", 11, "bold"),
                fg=TERRACOTTA_FONCE, bg=BLANC
            ).pack(anchor="w", padx=20, pady=(16, 6))

            items = []
            for i_mot, mot in enumerate(liste.get("mots", [])):
                identifiant = f"liste{i_liste}_mot{i_mot}"
                items.append({
                    "id": identifiant,
                    "principal": mot.get("arabe", "?"), "taille_police_recto": 16,
                    "sous_titre_recto": mot.get("sens", ""),
                    "lignes_detail": [
                        (mot.get("arabe", ""), ("Helvetica", 16, "bold"), TERRACOTTA_FONCE, None),
                        (mot.get("translitteration", ""), ("Helvetica", 9, "italic"), GRIS_TEXTE, 150),
                        (f"« {mot.get('sens','')} »", ("Helvetica", 9), OCRE_FONCE, 150),
                    ],
                })
            self._construire_grille_cartes(items, "vocabulaire", progres)

    def _construire_bandeau_resume(self, resume):
        bandeau = tk.Frame(self.zone_scrollable, bg=OCRE_CLAIR)
        bandeau.pack(fill="x", padx=20, pady=(0, 12))
        tk.Label(
            bandeau, text=f"✓ {resume['connues']} connu(e)s   ·   🔁 {resume['a_revoir']} à revoir   ·   ⚪ {resume['non_vues']} pas encore vu(e)s",
            font=("Helvetica", 9, "bold"), fg=TERRACOTTA_FONCE, bg=OCRE_CLAIR
        ).pack(anchor="w", padx=12, pady=8)
