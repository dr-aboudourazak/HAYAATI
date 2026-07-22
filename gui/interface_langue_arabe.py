"""
MODULE LANGUE ARABE (GUI/INTERFACE_LANGUE_ARABE.PY)
Version 4.0 - Retours d'usage concrets pris en compte :
- Sentier des étapes repliable : ne mange plus l'espace vertical une fois
  une étape choisie.
- Contraste et taille de police revus : le texte de corps utilise désormais
  TEXTE_FONCE (quasi-noir) plutôt que des teintes de marque colorées, et les
  tailles de police sont globalement augmentées. Les encarts (avertissements,
  bandeau de progression, verbe modèle) passent d'un fond saturé plein à un
  fond clair + liseré coloré, bien plus lisible sur de longs textes.
- "J'ai compris" / "À revoir" n'entraîne plus de saut en haut de page :
  pour les grilles de cartes (alphabet/vocabulaire/conjugaison), la carte
  suivante s'ouvre directement en place, sans reconstruction complète de
  l'écran. Pour la Grammaire (une leçon = un plein écran), le clic avance
  logiquement à la leçon suivante.
- Grammaire réorganisée en sous-rubriques (comme Conjugaison), chacune avec
  ses propres leçons : Notions de base, Types de phrases, Parties de la
  phrase, Classification des noms, Awzan (10 formes verbales).
"""
import tkinter as tk
from tkinter import ttk
from gui.langues import DICTIONNAIRE_LANGUES
from gui.palette_hayaati import (
    TERRACOTTA, TERRACOTTA_CLAIR, TERRACOTTA_FONCE,
    OCRE, OCRE_CLAIR, OCRE_FONCE, SABLE, BLANC, GRIS_TEXTE, VERT_SUCCES, AMBRE_ATTENTE,
    TEXTE_FONCE
)
from core.langue_arabe_engine import (
    CLE_MODULE_LANGUE_ARABE, normaliser_progres, marquer_item, resume_etape
)
from core.caravane_savoir_engine import construire_session_revision, compter_points_a_revoir

GRIS_INACTIF = "#d1d5db"
GRIS_TEXTE_CLAIR = "#6b7280"      # assombri par rapport à la V3 : meilleur contraste sur fond clair
LARGEUR_MIN_CARTE = 150
LIGNES_PAR_PAGE = 3


class EcranLangueArabe(tk.Frame):
    def __init__(self, parent, app_reference):
        super().__init__(parent, bg=BLANC)
        self.app = app_reference
        self.etape_active = 0
        self.cartes_retournees = set()
        self.page_alphabet = 0
        self.page_conjugaison = 0
        self.onglet_temps_conjugaison = 0
        self.index_liste_vocabulaire = 0
        self.index_lecon_grammaire = 0
        self.onglet_bab_grammaire = 0
        self.onglet_sous_rubrique_grammaire = 0
        self.index_texte_lecture = 0
        self.index_caravane = 0
        self.sentier_reduit = False
        self._derniere_largeur_connue = 0
        self._id_redimensionnement = None
        self._cartes_ordre = []          # [(identifiant, carte_frame, rafraichir_fn)] de la grille visible
        self._lbl_resume = None          # référence pour mise à jour en place, sans reconstruire l'écran
        self._total_pour_bandeau = 0

        self.canevas = tk.Canvas(self, bg=BLANC, bd=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canevas.yview)
        self.zone_scrollable = tk.Frame(self.canevas, bg=BLANC)

        self.zone_scrollable.bind("<Configure>", lambda e: self.canevas.configure(scrollregion=self.canevas.bbox("all")))
        self.id_fenetre_scroll = self.canevas.create_window((0, 0), window=self.zone_scrollable, anchor="nw")
        self.canevas.configure(yscrollcommand=self.scrollbar.set)
        self.canevas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.canevas.bind("<Configure>", self._sur_redimensionnement)
        self.canevas.bind_all("<MouseWheel>", lambda e: self.canevas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        self.canevas.bind_all("<Button-4>", lambda e: self.canevas.yview_scroll(-2, "units"))
        self.canevas.bind_all("<Button-5>", lambda e: self.canevas.yview_scroll(2, "units"))

        DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_changement_langue)
        self.construire_interface()

    # --- Redimensionnement réactif, avec anti-rebond ---
    def _sur_redimensionnement(self, event):
        self.canevas.itemconfig(self.id_fenetre_scroll, width=event.width)
        if abs(event.width - self._derniere_largeur_connue) < 15:
            return
        self._derniere_largeur_connue = event.width
        if self._id_redimensionnement:
            self.after_cancel(self._id_redimensionnement)
        self._id_redimensionnement = self.after(150, self._reconstruire_apres_redimensionnement)

    def _reconstruire_apres_redimensionnement(self):
        self._id_redimensionnement = None
        if self.winfo_exists():
            self.construire_interface()

    def _largeur_disponible(self):
        largeur = self.canevas.winfo_width()
        return largeur if largeur > 1 else (self.winfo_width() or 700)

    def _colonnes_et_wraplength(self):
        largeur = self._largeur_disponible() - 28
        nb_colonnes = max(1, min(6, largeur // LARGEUR_MIN_CARTE))
        largeur_carte = largeur // nb_colonnes
        wraplength = max(100, largeur_carte - 24)
        return nb_colonnes, wraplength

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

    # --- Petit encart utilitaire : fond clair + liseré coloré + texte à fort contraste,
    # remplace les anciens encarts à fond saturé, difficiles à lire sur un long texte. ---
    def _construire_encart(self, texte, couleur_accent, icone="", police=("Helvetica", 9), pady_ext=(0, 10)):
        conteneur = tk.Frame(self.zone_scrollable, bg=BLANC)
        conteneur.pack(fill="x", padx=20, pady=pady_ext)
        liseret = tk.Frame(conteneur, bg=couleur_accent, width=4)
        liseret.pack(side="left", fill="y")
        corps = tk.Frame(conteneur, bg=SABLE)
        corps.pack(side="left", fill="both", expand=True)
        tk.Label(
            corps, text=f"{icone} {texte}".strip(), font=police, fg=TEXTE_FONCE, bg=SABLE,
            wraplength=self._largeur_disponible() - 70, justify="left"
        ).pack(anchor="w", padx=12, pady=8)
        return conteneur

    def construire_interface(self):
        for w in self.zone_scrollable.winfo_children():
            w.destroy()
        self._cartes_ordre = []
        self._lbl_resume = None

        txt = DICTIONNAIRE_LANGUES.actif.get("langue_arabe", {})
        etapes = txt.get("etapes", [])

        tk.Label(
            self.zone_scrollable, text=txt.get("titre", "🔤 Langue arabe"),
            font=("Helvetica", 16, "bold"), fg=TERRACOTTA_FONCE, bg=BLANC, wraplength=640, justify="left"
        ).pack(anchor="w", padx=20, pady=(18, 4))

        tk.Label(
            self.zone_scrollable, text=txt.get("sous_titre", ""),
            font=("Helvetica", 10, "italic"), fg=TEXTE_FONCE, bg=BLANC, wraplength=640, justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 10))

        avertissement = txt.get("avertissement_audio", "")
        if avertissement:
            self._construire_encart(avertissement, OCRE, icone="🔊", police=("Helvetica", 9))

        if not etapes:
            tk.Label(self.zone_scrollable, text="Contenu non disponible.", bg=BLANC, fg=TEXTE_FONCE).pack(padx=20, pady=20)
            return

        self._construire_sentier_etapes(etapes)

        etape_courante = etapes[min(self.etape_active, len(etapes) - 1)]

        if not etape_courante.get("disponible", False):
            self._construire_message_attente(etape_courante)
        elif etape_courante.get("type") == "alphabet":
            self._construire_etape_alphabet(etape_courante)
        elif etape_courante.get("type") == "vocabulaire":
            self._construire_etape_vocabulaire(etape_courante)
        elif etape_courante.get("type") == "conjugaison":
            self._construire_etape_conjugaison(etape_courante)
        elif etape_courante.get("type") == "grammaire":
            self._construire_etape_grammaire(etape_courante)
        elif etape_courante.get("type") == "lecture":
            self._construire_etape_lecture(etape_courante)
        elif etape_courante.get("type") == "caravane":
            self._construire_etape_caravane(etape_courante)
        else:
            self._construire_message_attente(etape_courante)

        tk.Frame(self.zone_scrollable, bg=BLANC, height=30).pack()

    # --- Le "Sentier du Savoir" : repliable, pour ne pas manger l'espace utile ---
    def _construire_sentier_etapes(self, etapes):
        etape_courante = etapes[min(self.etape_active, len(etapes) - 1)]

        entete = tk.Frame(self.zone_scrollable, bg=SABLE, cursor="hand2")
        entete.pack(fill="x", padx=20, pady=(0, 4))
        icone_repli = "▾" if not self.sentier_reduit else "▸"
        texte_entete = "🧭 Sentier des étapes" if not self.sentier_reduit else f"🧭 Étape {self.etape_active + 1}/{len(etapes)} — {etape_courante.get('titre','')}"
        lbl_entete = tk.Label(entete, text=f"{icone_repli}  {texte_entete}", font=("Helvetica", 9, "bold"), fg=TERRACOTTA_FONCE, bg=SABLE, wraplength=self._largeur_disponible() - 60, justify="left")
        lbl_entete.pack(anchor="w", padx=12, pady=8)
        for w in (entete, lbl_entete):
            w.bind("<Button-1>", lambda e: self._basculer_sentier())

        if self.sentier_reduit:
            return

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
            couleur_titre = TERRACOTTA_FONCE if active else (TEXTE_FONCE if disponible else GRIS_TEXTE_CLAIR)
            lbl_t = tk.Label(zone_txt, text=etape.get("titre", f"Étape {i+1}"), font=("Helvetica", 10, "bold" if active else "normal"), fg=couleur_titre, bg=couleur_fond_ligne, anchor="w")
            lbl_t.pack(anchor="w")
            statut = "Étape actuelle" if active else ("Disponible — touchez pour ouvrir" if disponible else "Bientôt disponible")
            lbl_s = tk.Label(zone_txt, text=statut, font=("Helvetica", 8), fg=GRIS_TEXTE_CLAIR, bg=couleur_fond_ligne, anchor="w")
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

    def _basculer_sentier(self):
        self.sentier_reduit = not self.sentier_reduit
        self.construire_interface()

    def _choisir_etape(self, index):
        self.etape_active = index
        self.page_alphabet = 0
        self.page_conjugaison = 0
        self.onglet_temps_conjugaison = 0
        self.index_liste_vocabulaire = 0
        self.index_lecon_grammaire = 0
        self.onglet_bab_grammaire = 0
        self.onglet_sous_rubrique_grammaire = 0
        self.index_texte_lecture = 0
        self.index_caravane = 0
        self.cartes_retournees.clear()
        self.sentier_reduit = True   # une fois l'étape choisie, on rend l'espace au contenu
        self.construire_interface()

    def _construire_message_attente(self, etape):
        cadre = tk.Frame(self.zone_scrollable, bg=SABLE, highlightbackground=OCRE, highlightthickness=1)
        cadre.pack(fill="x", padx=20, pady=10)
        tk.Label(
            cadre, text=f"⏳ {etape.get('titre', '')}", font=("Helvetica", 12, "bold"), fg=OCRE_FONCE, bg=SABLE
        ).pack(anchor="w", padx=14, pady=(12, 4))
        tk.Label(
            cadre, text="Cette étape n'a pas encore de contenu déposé. Elle apparaîtra ici dès qu'il sera prêt.",
            font=("Helvetica", 10), fg=TEXTE_FONCE, bg=SABLE, wraplength=560, justify="left"
        ).pack(anchor="w", padx=14, pady=(0, 12))

    # --- Barre de pagination générique ---
    def _construire_barre_pagination(self, page_actuelle, nb_pages, libelle, action_precedent, action_suivant):
        if nb_pages <= 1:
            return
        barre = tk.Frame(self.zone_scrollable, bg=BLANC)
        barre.pack(fill="x", padx=20, pady=(4, 16))
        b_prec = tk.Button(barre, text="◂ Précédent", font=("Helvetica", 10), bg=SABLE, fg=TERRACOTTA_FONCE, bd=0, padx=10, pady=6, cursor="hand2", command=action_precedent)
        b_prec.pack(side="left")
        if page_actuelle == 0:
            b_prec.config(state=tk.DISABLED, fg=GRIS_TEXTE_CLAIR)
        tk.Label(barre, text=libelle, font=("Helvetica", 10, "bold"), fg=TEXTE_FONCE, bg=BLANC, wraplength=300).pack(side="left", expand=True)
        b_suiv = tk.Button(barre, text="Suivant ▸", font=("Helvetica", 10), bg=SABLE, fg=TERRACOTTA_FONCE, bd=0, padx=10, pady=6, cursor="hand2", command=action_suivant)
        b_suiv.pack(side="right")
        if page_actuelle >= nb_pages - 1:
            b_suiv.config(state=tk.DISABLED, fg=GRIS_TEXTE_CLAIR)

    # --- Grille de cartes générique (alphabet / vocabulaire / conjugaison) ---
    def _construire_grille_cartes(self, items, cle_etape, progres, nb_colonnes, wraplength):
        grille = tk.Frame(self.zone_scrollable, bg=BLANC)
        grille.pack(fill="x", padx=14)
        for c in range(nb_colonnes):
            grille.grid_columnconfigure(c, weight=1)

        self._cartes_ordre = []
        for i, item in enumerate(items):
            ligne, colonne = divmod(i, nb_colonnes)
            self._construire_carte_item(grille, item, cle_etape, ligne, colonne, progres, wraplength)

    def _construire_carte_item(self, parent, item, cle_etape, ligne, colonne, progres, wraplength):
        identifiant = item["id"]
        etape_data = progres.get(cle_etape, {"connues": [], "a_revoir": []})

        carte = tk.Frame(parent, bg=BLANC, highlightthickness=2, cursor="hand2")
        carte.grid(row=ligne, column=colonne, sticky="nsew", padx=6, pady=6)

        def couleur_bordure_actuelle():
            p = self._charger_progres()
            e = p.get(cle_etape, {"connues": [], "a_revoir": []})
            if identifiant in e["connues"]:
                return VERT_SUCCES
            if identifiant in e["a_revoir"]:
                return AMBRE_ATTENTE
            return TERRACOTTA

        def rafraichir_carte():
            carte.config(highlightbackground=couleur_bordure_actuelle())
            for w in carte.winfo_children():
                w.destroy()
            if identifiant in self.cartes_retournees:
                self._peupler_face_detail(carte, item, cle_etape, basculer, wraplength)
            else:
                self._peupler_face_recto(carte, item, basculer, wraplength)

        def basculer(event=None):
            if identifiant in self.cartes_retournees:
                self.cartes_retournees.discard(identifiant)
            else:
                self.cartes_retournees.add(identifiant)
            rafraichir_carte()

        carte.config(highlightbackground=couleur_bordure_actuelle())
        carte.bind("<Button-1>", basculer)
        rafraichir_carte()
        self._cartes_ordre.append((identifiant, carte, rafraichir_carte))

    def _mettre_a_jour_bandeau_resume_en_place(self, cle_etape):
        if self._lbl_resume and self._lbl_resume.winfo_exists():
            progres = self._charger_progres()
            resume = resume_etape(progres, cle_etape, self._total_pour_bandeau)
            self._lbl_resume.config(text=self._texte_resume(resume))

    def _texte_resume(self, resume):
        return f"✓ {resume['connues']} connu(e)s   ·   🔁 {resume['a_revoir']} à revoir   ·   ⚪ {resume['non_vues']} pas encore vu(e)s"

    def _ouvrir_carte_suivante(self, identifiant_actuel):
        """Après avoir marqué une carte, ouvre directement la suivante dans l'ordre
        de la grille — sans reconstruire tout l'écran, donc sans sauter en haut de page."""
        ids = [i for i, _c, _r in self._cartes_ordre]
        if identifiant_actuel not in ids:
            return
        pos = ids.index(identifiant_actuel)
        if pos + 1 < len(self._cartes_ordre):
            identifiant_suivant, carte_suivante, rafraichir_suivante = self._cartes_ordre[pos + 1]
            self.cartes_retournees.discard(identifiant_actuel)
            self.cartes_retournees.add(identifiant_suivant)
            for i2, c2, r2 in self._cartes_ordre:
                r2()
            self.canevas.update_idletasks()
            try:
                y_carte = carte_suivante.winfo_y()
                hauteur_totale = max(self.zone_scrollable.winfo_height(), 1)
                self.canevas.yview_moveto(max(0.0, (y_carte - 40) / hauteur_totale))
            except tk.TclError:
                pass
        else:
            self.cartes_retournees.discard(identifiant_actuel)
            for i2, c2, r2 in self._cartes_ordre:
                r2()

    def _peupler_face_recto(self, carte, item, basculer, wraplength):
        widgets = []
        if item.get("couleur_hex"):
            zone_swatch = tk.Canvas(carte, width=44, height=44, bg=BLANC, highlightthickness=0)
            zone_swatch.pack(pady=(14, 4))
            zone_swatch.create_oval(2, 2, 42, 42, fill=item["couleur_hex"], outline=TEXTE_FONCE)
            widgets.append(zone_swatch)
        elif item.get("icone"):
            lbl_icone = tk.Label(carte, text=item["icone"], font=("Helvetica", 24), bg=BLANC)
            lbl_icone.pack(pady=(12, 0))
            widgets.append(lbl_icone)

        lbl1 = tk.Label(carte, text=item.get("principal", "?"), font=("Helvetica", item.get("taille_police_recto", 19)), bg=BLANC, fg=TERRACOTTA_FONCE, wraplength=wraplength, justify="center")
        lbl1.pack(pady=(8 if widgets else 14, 2))
        lbl2 = tk.Label(carte, text=item.get("sous_titre_recto", ""), font=("Helvetica", 10), bg=BLANC, fg=TEXTE_FONCE, wraplength=wraplength, justify="center")
        lbl2.pack(pady=(0, 14))
        widgets += [lbl1, lbl2]
        for w in widgets:
            w.bind("<Button-1>", basculer)

    def _peupler_face_detail(self, carte, item, cle_etape, basculer, wraplength):
        for texte, police, _couleur_marque in item.get("lignes_detail", []):
            lbl = tk.Label(carte, text=texte, font=police, bg=BLANC, fg=TEXTE_FONCE, wraplength=wraplength, justify="center")
            lbl.pack(pady=(3, 3))
            lbl.bind("<Button-1>", basculer)

        pied = tk.Frame(carte, bg=BLANC)
        pied.pack(pady=(6, 10))

        def marquer(connu):
            identifiant = item["id"]
            p = self._charger_progres()
            p = marquer_item(p, cle_etape, identifiant, connu)
            self._sauvegarder_progres(p)
            self._ouvrir_carte_suivante(identifiant)
            self._mettre_a_jour_bandeau_resume_en_place(cle_etape)

        tk.Button(pied, text="✓ Je la connais", font=("Helvetica", 8), bg=VERT_SUCCES, fg=BLANC, bd=0, padx=7, pady=4, command=lambda: marquer(True)).pack(side="left", padx=2)
        tk.Button(pied, text="🔁 À revoir", font=("Helvetica", 8), bg=AMBRE_ATTENTE, fg=BLANC, bd=0, padx=7, pady=4, command=lambda: marquer(False)).pack(side="left", padx=2)

    # --- Étape Alphabet ---
    def _construire_etape_alphabet(self, etape):
        lettres = etape.get("lettres", [])
        progres = self._charger_progres()
        resume = resume_etape(progres, "alphabet", len(lettres))
        self._construire_bandeau_resume(resume)

        nb_colonnes, wraplength = self._colonnes_et_wraplength()
        par_page = max(nb_colonnes * LIGNES_PAR_PAGE, nb_colonnes)
        nb_pages = max(1, (len(lettres) + par_page - 1) // par_page)
        self.page_alphabet = min(self.page_alphabet, nb_pages - 1)
        debut = self.page_alphabet * par_page
        lettres_page = list(enumerate(lettres))[debut:debut + par_page]

        items = []
        for i, l in lettres_page:
            lignes = [(f"{l.get('lettre','')}  ·  {l.get('nom','')}", ("Helvetica", 16, "bold"), TERRACOTTA_FONCE),
                      (f"Translittération : {l.get('translitteration','')}", ("Helvetica", 9), TEXTE_FONCE),
                      (f"Connexion : {l.get('connexion','')}", ("Helvetica", 9), TEXTE_FONCE),
                      (l.get("son", ""), ("Helvetica", 9), TEXTE_FONCE)]

            occurrences = l.get("occurrences", [])
            positions_presentes = {o["position"] for o in occurrences}
            if "milieu" not in positions_presentes:
                lignes.append(("(lettre non connectante : pas de forme médiane distincte)", ("Helvetica", 8, "italic"), GRIS_TEXTE_CLAIR))
            for occ in occurrences:
                lignes.append((f"{occ['position'].capitalize()} :", ("Helvetica", 8, "italic"), GRIS_TEXTE_CLAIR))
                lignes.append((occ["mot"], ("Helvetica", 19, "bold"), TEXTE_FONCE))
                lignes.append((f"{occ['translitteration']} — {occ['sens']}", ("Helvetica", 9), TEXTE_FONCE))

            items.append({"id": str(i), "principal": l.get("lettre", "?"), "taille_police_recto": 28, "sous_titre_recto": l.get("nom", ""), "lignes_detail": lignes})

        self._construire_grille_cartes(items, "alphabet", progres, nb_colonnes, wraplength)
        self._construire_barre_pagination(
            self.page_alphabet, nb_pages, f"Page {self.page_alphabet + 1} / {nb_pages}",
            lambda: self._changer_page_alphabet(-1), lambda: self._changer_page_alphabet(1)
        )

    def _changer_page_alphabet(self, delta):
        self.page_alphabet += delta
        self.cartes_retournees.clear()
        self.construire_interface()

    # --- Étape Vocabulaire ---
    def _construire_etape_vocabulaire(self, etape):
        listes = etape.get("listes", [])
        if not listes:
            self._construire_message_attente(etape)
            return
        progres = self._charger_progres()
        total_mots = sum(len(l.get("mots", [])) for l in listes)
        resume = resume_etape(progres, "vocabulaire", total_mots)
        self._construire_bandeau_resume(resume)

        self.index_liste_vocabulaire = min(self.index_liste_vocabulaire, len(listes) - 1)
        i_liste = self.index_liste_vocabulaire
        liste = listes[i_liste]

        tk.Label(
            self.zone_scrollable, text=liste.get("titre", ""), font=("Helvetica", 13, "bold"),
            fg=TERRACOTTA_FONCE, bg=BLANC
        ).pack(anchor="w", padx=20, pady=(6, 10))

        nb_colonnes, wraplength = self._colonnes_et_wraplength()
        items = []
        for i_mot, mot in enumerate(liste.get("mots", [])):
            identifiant = f"liste{i_liste}_mot{i_mot}"
            items.append({
                "id": identifiant,
                "principal": mot.get("arabe", "?"), "taille_police_recto": 22,
                "sous_titre_recto": mot.get("sens", ""),
                "icone": mot.get("icone"), "couleur_hex": mot.get("couleur_hex"),
                "lignes_detail": [
                    (mot.get("arabe", ""), ("Helvetica", 22, "bold"), TERRACOTTA_FONCE),
                    (mot.get("translitteration", ""), ("Helvetica", 10, "italic"), TEXTE_FONCE),
                    (f"« {mot.get('sens','')} »", ("Helvetica", 10), TEXTE_FONCE),
                ],
            })
        self._construire_grille_cartes(items, "vocabulaire", progres, nb_colonnes, wraplength)

        libelles_listes = [l.get("titre", f"Liste {i+1}") for i, l in enumerate(listes)]
        self._construire_barre_pagination(
            i_liste, len(listes), f"{i_liste + 1} / {len(listes)} — {libelles_listes[i_liste]}",
            lambda: self._changer_liste_vocabulaire(-1), lambda: self._changer_liste_vocabulaire(1)
        )

    def _changer_liste_vocabulaire(self, delta):
        self.index_liste_vocabulaire += delta
        self.cartes_retournees.clear()
        self.construire_interface()

    # --- Étape Conjugaison : sélecteur à 3 segments (Passé/Présent/Futur) ---
    def _construire_etape_conjugaison(self, etape):
        verbe = etape.get("verbe_modele", {})
        temps_liste = etape.get("temps", [])
        if not temps_liste:
            self._construire_message_attente(etape)
            return

        self._construire_encart(
            f"Verbe modèle : {verbe.get('forme_base','')}  ·  racine {verbe.get('racine','')}  ·  « {verbe.get('sens','')} »",
            TERRACOTTA, police=("Helvetica", 10, "bold")
        )

        segments = tk.Frame(self.zone_scrollable, bg=BLANC)
        segments.pack(fill="x", padx=20, pady=(0, 12))
        nb_col_temps = 3 if getattr(self.app, "mode_smartphone_actif", False) else len(temps_liste)
        for c in range(nb_col_temps):
            segments.grid_columnconfigure(c, weight=1)
        self.onglet_temps_conjugaison = min(self.onglet_temps_conjugaison, len(temps_liste) - 1)
        for i, temps in enumerate(temps_liste):
            actif = (i == self.onglet_temps_conjugaison)
            b = tk.Button(
                segments, text=temps.get("titre", f"Temps {i+1}"), font=("Helvetica", 10, "bold" if actif else "normal"),
                bg=TERRACOTTA if actif else SABLE, fg=BLANC if actif else TEXTE_FONCE, bd=0, pady=9, cursor="hand2",
                wraplength=140, justify="center",
                command=lambda idx=i: self._choisir_temps_conjugaison(idx)
            )
            l_t, c_t = divmod(i, nb_col_temps)
            b.grid(row=l_t, column=c_t, sticky="ew", padx=2, pady=2)

        temps_actif = temps_liste[self.onglet_temps_conjugaison]
        cle_progres = f"conjugaison_{temps_actif.get('cle', self.onglet_temps_conjugaison)}"
        conjugaisons = temps_actif.get("conjugaisons", [])
        progres = self._charger_progres()
        resume = resume_etape(progres, cle_progres, len(conjugaisons))
        self._construire_bandeau_resume(resume)

        note = temps_actif.get("note_pedagogique", "")
        if note:
            self._construire_encart(note, OCRE, icone="💡", police=("Helvetica", 9, "italic"))

        regles_type_verbe = temps_actif.get("regles_type_verbe", [])
        if regles_type_verbe:
            tk.Label(
                self.zone_scrollable, text="Le timbre de la hamza dépend du verbe :", font=("Helvetica", 10, "bold"),
                fg=TERRACOTTA_FONCE, bg=BLANC
            ).pack(anchor="w", padx=20, pady=(2, 6))
            for regle in regles_type_verbe:
                cadre_regle = tk.Frame(self.zone_scrollable, bg=SABLE, highlightbackground=TERRACOTTA, highlightthickness=1)
                cadre_regle.pack(fill="x", padx=20, pady=4)
                tk.Label(
                    cadre_regle, text=f"{regle['type']} — {regle['regle']}", font=("Helvetica", 9, "italic"), fg=TEXTE_FONCE, bg=SABLE,
                    wraplength=self._largeur_disponible() - 60, justify="left"
                ).pack(anchor="w", padx=12, pady=(8, 4))
                tk.Label(
                    cadre_regle, text=f"{regle['madi']}  →  {regle['mudari']} ({regle['mudari_translitteration']})  →  {regle['amr']} ({regle['amr_translitteration']})",
                    font=("Helvetica", 15, "bold"), fg=TERRACOTTA_FONCE, bg=SABLE, wraplength=self._largeur_disponible() - 60, justify="left"
                ).pack(anchor="w", padx=12, pady=(0, 4))
                tk.Label(
                    cadre_regle, text=regle["sens"], font=("Helvetica", 9), fg=TEXTE_FONCE, bg=SABLE
                ).pack(anchor="w", padx=12, pady=(0, 8))

        note_temporelle = temps_actif.get("note_temporelle", "")
        if note_temporelle:
            tk.Label(
                self.zone_scrollable, text="Et pour parler d'un ordre au passé ou au futur ?", font=("Helvetica", 10, "bold"),
                fg=TERRACOTTA_FONCE, bg=BLANC
            ).pack(anchor="w", padx=20, pady=(10, 6))
            self._construire_encart(note_temporelle, TERRACOTTA, icone="⏳", police=("Helvetica", 9))
            self._construire_bloc_exemples(temps_actif.get("exemples_temporels", []))
            tk.Frame(self.zone_scrollable, bg=BLANC, height=8).pack()

        source = etape.get("source", "")
        if source:
            tk.Label(
                self.zone_scrollable, text=f"📚 Source : {source}", font=("Helvetica", 8), fg=GRIS_TEXTE_CLAIR, bg=BLANC,
                wraplength=600, justify="left"
            ).pack(anchor="w", padx=20, pady=(0, 10))

        nb_colonnes, wraplength = self._colonnes_et_wraplength()
        par_page = max(nb_colonnes * LIGNES_PAR_PAGE, nb_colonnes)
        nb_pages = max(1, (len(conjugaisons) + par_page - 1) // par_page)
        self.page_conjugaison = min(self.page_conjugaison, nb_pages - 1)
        debut = self.page_conjugaison * par_page
        page_items = list(enumerate(conjugaisons))[debut:debut + par_page]

        items = []
        for i, c in page_items:
            items.append({
                "id": f"{cle_progres}_{i}",
                "principal": c.get("forme", "?"), "taille_police_recto": 20,
                "sous_titre_recto": c.get("pronom", ""),
                "lignes_detail": [
                    (f"{c.get('pronom','')} ({c.get('pronom_translitteration','')})", ("Helvetica", 11, "bold"), TERRACOTTA_FONCE),
                    (c.get("personne", ""), ("Helvetica", 8, "italic"), GRIS_TEXTE_CLAIR),
                    (f"{c.get('forme','')}", ("Helvetica", 20, "bold"), TERRACOTTA_FONCE),
                    (c.get("translitteration", ""), ("Helvetica", 10, "italic"), TEXTE_FONCE),
                    (f"« {c.get('sens','')} »", ("Helvetica", 10), TEXTE_FONCE),
                ],
            })
        self._construire_grille_cartes(items, cle_progres, progres, nb_colonnes, wraplength)
        self._construire_barre_pagination(
            self.page_conjugaison, nb_pages, f"Page {self.page_conjugaison + 1} / {nb_pages}",
            lambda: self._changer_page_conjugaison(-1), lambda: self._changer_page_conjugaison(1)
        )

    def _choisir_temps_conjugaison(self, index):
        self.onglet_temps_conjugaison = index
        self.page_conjugaison = 0
        self.cartes_retournees.clear()
        self.construire_interface()

    def _changer_page_conjugaison(self, delta):
        self.page_conjugaison += delta
        self.cartes_retournees.clear()
        self.construire_interface()

    # --- Étape Grammaire : Bab 1-5 (labels courts et uniformes), certains avec
    # sous-rubriques (Nom, Phrase), d'autres directement en leçons (bases, Verbe, Particule) ---
    def _construire_etape_grammaire(self, etape):
        babs = etape.get("babs", [])
        if not babs:
            self._construire_message_attente(etape)
            return

        avertissement = etape.get("avertissement_source", "")
        if avertissement:
            self._construire_encart(avertissement, OCRE, icone="ℹ️", police=("Helvetica", 8, "italic"))

        self.onglet_bab_grammaire = min(getattr(self, "onglet_bab_grammaire", 0), len(babs) - 1)
        segments = tk.Frame(self.zone_scrollable, bg=BLANC)
        segments.pack(fill="x", padx=20, pady=(0, 4))
        for c in range(len(babs)):
            segments.grid_columnconfigure(c, weight=1)
        for i, bab in enumerate(babs):
            actif = (i == self.onglet_bab_grammaire)
            b = tk.Button(
                segments, text=bab.get("titre", f"Bab {i+1}"), font=("Helvetica", 10, "bold" if actif else "normal"),
                bg=TERRACOTTA if actif else SABLE, fg=BLANC if actif else TEXTE_FONCE, bd=0, pady=9, cursor="hand2",
                command=lambda idx=i: self._choisir_bab_grammaire(idx)
            )
            b.grid(row=0, column=i, sticky="ew", padx=2)

        bab_actif = babs[self.onglet_bab_grammaire]
        tk.Label(
            self.zone_scrollable, text=bab_actif.get("sous_titre", ""), font=("Helvetica", 12, "bold"),
            fg=TERRACOTTA_FONCE, bg=BLANC, wraplength=self._largeur_disponible() - 40, justify="left"
        ).pack(anchor="w", padx=20, pady=(8, 12))

        sous_rubriques = bab_actif.get("sous_rubriques")
        cle_bab = bab_actif.get("cle", str(self.onglet_bab_grammaire))

        if sous_rubriques:
            self.onglet_sous_rubrique_grammaire = min(getattr(self, "onglet_sous_rubrique_grammaire", 0), len(sous_rubriques) - 1)
            segments2 = tk.Frame(self.zone_scrollable, bg=BLANC)
            segments2.pack(fill="x", padx=20, pady=(0, 10))
            nb_col_seg2 = 2 if getattr(self.app, "mode_smartphone_actif", False) else len(sous_rubriques)
            for c in range(nb_col_seg2):
                segments2.grid_columnconfigure(c, weight=1)
            for i, sr in enumerate(sous_rubriques):
                actif = (i == self.onglet_sous_rubrique_grammaire)
                b = tk.Button(
                    segments2, text=sr.get("titre", f"{i+1}"), font=("Helvetica", 9, "bold" if actif else "normal"),
                    bg=OCRE if actif else SABLE, fg=BLANC if actif else TEXTE_FONCE, bd=0, pady=7, cursor="hand2",
                    wraplength=170, justify="center",
                    command=lambda idx=i: self._choisir_sous_rubrique_grammaire(idx)
                )
                l_s, c_s = divmod(i, nb_col_seg2)
                b.grid(row=l_s, column=c_s, sticky="ew", padx=2, pady=2)
            sous_rubrique_active = sous_rubriques[self.onglet_sous_rubrique_grammaire]
            lecons = sous_rubrique_active.get("lecons", [])
            cle_progres = f"grammaire_{cle_bab}_{sous_rubrique_active.get('cle', self.onglet_sous_rubrique_grammaire)}"
        else:
            lecons = bab_actif.get("lecons", [])
            cle_progres = f"grammaire_{cle_bab}"

        if not lecons:
            self._construire_message_attente(bab_actif)
            return

        progres = self._charger_progres()
        resume = resume_etape(progres, cle_progres, len(lecons))
        self._construire_bandeau_resume(resume)

        self.index_lecon_grammaire = min(self.index_lecon_grammaire, len(lecons) - 1)
        lecon = lecons[self.index_lecon_grammaire]
        identifiant_lecon = str(self.index_lecon_grammaire)
        wraplength_lecon = self._largeur_disponible() - 60

        carte = tk.Frame(self.zone_scrollable, bg=SABLE, highlightbackground=TERRACOTTA, highlightthickness=1)
        carte.pack(fill="x", padx=20, pady=(0, 10))

        tk.Label(
            carte, text=lecon.get("titre", ""), font=("Helvetica", 13, "bold"), fg=TERRACOTTA_FONCE, bg=SABLE,
            wraplength=wraplength_lecon, justify="left"
        ).pack(anchor="w", padx=16, pady=(14, 8))

        tk.Label(
            carte, text=lecon.get("explication", ""), font=("Helvetica", 11), fg=TEXTE_FONCE, bg=SABLE,
            wraplength=wraplength_lecon, justify="left"
        ).pack(anchor="w", padx=16, pady=(0, 10))

        for ex in lecon.get("exemples", []):
            ligne_ex = tk.Frame(carte, bg=BLANC, highlightbackground=OCRE, highlightthickness=1)
            ligne_ex.pack(fill="x", padx=16, pady=3)
            tk.Label(
                ligne_ex, text=ex.get("arabe", ""), font=("Helvetica", 20, "bold"), fg=TEXTE_FONCE, bg=BLANC,
                wraplength=wraplength_lecon - 20, justify="left"
            ).pack(anchor="w", padx=10, pady=(8, 0))
            tk.Label(
                ligne_ex, text=f"{ex.get('translitteration','')} — {ex.get('sens','')}",
                font=("Helvetica", 10), fg=TEXTE_FONCE, bg=BLANC, wraplength=wraplength_lecon - 20, justify="left"
            ).pack(anchor="w", padx=10, pady=(0, 8))
        # NB : bloc conservé en logique équivalente à _construire_bloc_exemples, mais imbriqué
        # dans la carte (fond SABLE) plutôt que dans zone_scrollable directement — la variante
        # générique est utilisée pour les blocs hors carte (Conjugaison : règles, notes temporelles).

        pied = tk.Frame(carte, bg=SABLE)
        pied.pack(fill="x", padx=16, pady=(4, 14))

        def marquer_et_avancer(connu):
            p = self._charger_progres()
            p = marquer_item(p, cle_progres, identifiant_lecon, connu)
            self._sauvegarder_progres(p)
            if self.index_lecon_grammaire < len(lecons) - 1:
                self.index_lecon_grammaire += 1
            self.construire_interface()

        tk.Button(pied, text="✓ J'ai compris", font=("Helvetica", 9), bg=VERT_SUCCES, fg=BLANC, bd=0, padx=9, pady=5, cursor="hand2", command=lambda: marquer_et_avancer(True)).pack(side="left", padx=(0, 6))
        tk.Button(pied, text="🔁 À revoir", font=("Helvetica", 9), bg=AMBRE_ATTENTE, fg=BLANC, bd=0, padx=9, pady=5, cursor="hand2", command=lambda: marquer_et_avancer(False)).pack(side="left")

        source = etape.get("source", "")
        if source:
            tk.Label(
                self.zone_scrollable, text=f"📚 Source : {source}", font=("Helvetica", 8), fg=GRIS_TEXTE_CLAIR, bg=BLANC,
                wraplength=600, justify="left"
            ).pack(anchor="w", padx=20, pady=(0, 10))

        libelles = [l.get("titre", f"Leçon {i+1}") for i, l in enumerate(lecons)]
        self._construire_barre_pagination(
            self.index_lecon_grammaire, len(lecons), f"{self.index_lecon_grammaire + 1} / {len(lecons)} — {libelles[self.index_lecon_grammaire]}",
            lambda: self._changer_lecon_grammaire(-1), lambda: self._changer_lecon_grammaire(1)
        )

    def _choisir_bab_grammaire(self, index):
        self.onglet_bab_grammaire = index
        self.onglet_sous_rubrique_grammaire = 0
        self.index_lecon_grammaire = 0
        self.construire_interface()

    def _choisir_sous_rubrique_grammaire(self, index):
        self.onglet_sous_rubrique_grammaire = index
        self.index_lecon_grammaire = 0
        self.construire_interface()

    def _changer_lecon_grammaire(self, delta):
        self.index_lecon_grammaire += delta
        self.construire_interface()

    def _construire_bloc_exemples(self, exemples, wraplength=None):
        if wraplength is None:
            wraplength = self._largeur_disponible() - 76
        for ex in exemples:
            ligne_ex = tk.Frame(self.zone_scrollable, bg=BLANC, highlightbackground=OCRE, highlightthickness=1)
            ligne_ex.pack(fill="x", padx=20, pady=3)
            tk.Label(
                ligne_ex, text=ex.get("arabe", ""), font=("Helvetica", 20, "bold"), fg=TEXTE_FONCE, bg=BLANC,
                wraplength=wraplength, justify="left"
            ).pack(anchor="w", padx=10, pady=(8, 0))
            tk.Label(
                ligne_ex, text=f"{ex.get('translitteration','')} — {ex.get('sens','')}",
                font=("Helvetica", 10), fg=TEXTE_FONCE, bg=BLANC, wraplength=wraplength, justify="left"
            ).pack(anchor="w", padx=10, pady=(0, 8))

    # --- Étape Lecture : un texte/dialogue à la fois, vocabulaire nouveau en bas ---
    def _construire_etape_lecture(self, etape):
        textes = etape.get("textes", [])
        if not textes:
            self._construire_message_attente(etape)
            return

        consigne = etape.get("consigne", "")
        if consigne:
            tk.Label(
                self.zone_scrollable, text=consigne, font=("Helvetica", 10, "italic"), fg=TEXTE_FONCE, bg=BLANC,
                wraplength=self._largeur_disponible() - 40, justify="left"
            ).pack(anchor="w", padx=20, pady=(0, 12))

        progres = self._charger_progres()
        resume = resume_etape(progres, "lecture", len(textes))
        self._construire_bandeau_resume(resume)

        self.index_texte_lecture = min(self.index_texte_lecture, len(textes) - 1)
        texte = textes[self.index_texte_lecture]
        identifiant_texte = str(self.index_texte_lecture)

        entete = tk.Frame(self.zone_scrollable, bg=TERRACOTTA_CLAIR)
        entete.pack(fill="x", padx=20, pady=(0, 10))
        tk.Label(
            entete, text=texte.get("titre", ""), font=("Helvetica", 13, "bold"), fg=TERRACOTTA_FONCE, bg=TERRACOTTA_CLAIR,
            wraplength=self._largeur_disponible() - 60, justify="left"
        ).pack(anchor="w", padx=12, pady=(10, 2))
        tk.Label(
            entete, text=f"Niveau : {texte.get('niveau','')}", font=("Helvetica", 9, "italic"), fg=TERRACOTTA_FONCE, bg=TERRACOTTA_CLAIR
        ).pack(anchor="w", padx=12, pady=(0, 10))

        wraplength_lecture = self._largeur_disponible() - 76
        for ligne in texte.get("lignes", []):
            bloc = tk.Frame(self.zone_scrollable, bg=SABLE, highlightbackground=OCRE, highlightthickness=1)
            bloc.pack(fill="x", padx=20, pady=4)
            if ligne.get("locuteur"):
                tk.Label(
                    bloc, text=f"— {ligne['locuteur']} —", font=("Helvetica", 8, "bold italic"), fg=OCRE_FONCE, bg=SABLE
                ).pack(anchor="w", padx=12, pady=(8, 0))
            tk.Label(
                bloc, text=ligne.get("arabe", ""), font=("Helvetica", 17, "bold"), fg=TEXTE_FONCE, bg=SABLE,
                wraplength=wraplength_lecture, justify="right" if not ligne.get("locuteur") else "left"
            ).pack(anchor="w", padx=12, pady=(4, 2))
            tk.Label(
                bloc, text=ligne.get("traduction", ""), font=("Helvetica", 10, "italic"), fg=TEXTE_FONCE, bg=SABLE,
                wraplength=wraplength_lecture, justify="left"
            ).pack(anchor="w", padx=12, pady=(0, 8))

        vocab_nouveau = texte.get("vocabulaire_nouveau", [])
        if vocab_nouveau:
            tk.Label(
                self.zone_scrollable, text="Vocabulaire nouveau dans ce texte :", font=("Helvetica", 10, "bold"),
                fg=TERRACOTTA_FONCE, bg=BLANC
            ).pack(anchor="w", padx=20, pady=(10, 4))
            self._construire_bloc_exemples(vocab_nouveau, wraplength=wraplength_lecture)

        pied = tk.Frame(self.zone_scrollable, bg=BLANC)
        pied.pack(fill="x", padx=20, pady=(10, 4))

        def marquer_et_avancer(connu):
            p = self._charger_progres()
            p = marquer_item(p, "lecture", identifiant_texte, connu)
            self._sauvegarder_progres(p)
            if self.index_texte_lecture < len(textes) - 1:
                self.index_texte_lecture += 1
            self.construire_interface()

        tk.Button(pied, text="✓ J'ai lu ce texte", font=("Helvetica", 9), bg=VERT_SUCCES, fg=BLANC, bd=0, padx=9, pady=5, cursor="hand2", command=lambda: marquer_et_avancer(True)).pack(side="left", padx=(0, 6))
        tk.Button(pied, text="🔁 À relire", font=("Helvetica", 9), bg=AMBRE_ATTENTE, fg=BLANC, bd=0, padx=9, pady=5, cursor="hand2", command=lambda: marquer_et_avancer(False)).pack(side="left")

        libelles = [t.get("titre", f"Texte {i+1}") for i, t in enumerate(textes)]
        self._construire_barre_pagination(
            self.index_texte_lecture, len(textes), f"{self.index_texte_lecture + 1} / {len(textes)} — {libelles[self.index_texte_lecture]}",
            lambda: self._changer_texte_lecture(-1), lambda: self._changer_texte_lecture(1)
        )

    def _changer_texte_lecture(self, delta):
        self.index_texte_lecture += delta
        self.construire_interface()

    # --- Étape Caravane du Savoir : révision transversale de tous les modules ---
    def _construire_etape_caravane(self, etape):
        progres = self._charger_progres()
        contenu = DICTIONNAIRE_LANGUES.actif.get("langue_arabe", {})
        nb_a_revoir_total = compter_points_a_revoir(progres)
        session = construire_session_revision(progres, contenu, taille_max=10)

        tk.Label(
            self.zone_scrollable, text="Une halte de révision qui pioche dans tout ce que vous avez déjà rencontré — alphabet, vocabulaire, conjugaison, grammaire et lecture confondus.",
            font=("Helvetica", 10, "italic"), fg=TEXTE_FONCE, bg=BLANC, wraplength=self._largeur_disponible() - 40, justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 14))

        if not session:
            cadre_vide = tk.Frame(self.zone_scrollable, bg=SABLE, highlightbackground=OCRE, highlightthickness=1)
            cadre_vide.pack(fill="x", padx=20, pady=10)
            tk.Label(
                cadre_vide, text="🌱 Pas encore de quoi remplir une caravane", font=("Helvetica", 12, "bold"), fg=OCRE_FONCE, bg=SABLE
            ).pack(anchor="w", padx=14, pady=(12, 4))
            tk.Label(
                cadre_vide, text="Parcourez un peu l'alphabet, le vocabulaire, la conjugaison ou la grammaire — la Caravane se remplira automatiquement avec ce que vous avez vu, en particulier ce qui reste « à revoir ».",
                font=("Helvetica", 10), fg=TEXTE_FONCE, bg=SABLE, wraplength=560, justify="left"
            ).pack(anchor="w", padx=14, pady=(0, 12))
            return

        bandeau = tk.Frame(self.zone_scrollable, bg=OCRE_CLAIR)
        bandeau.pack(fill="x", padx=20, pady=(0, 14))
        tk.Label(
            bandeau, text=f"🧭 {nb_a_revoir_total} point(s) à revoir au total dans tout le parcours — {len(session)} étape(s) dans cette caravane",
            font=("Helvetica", 10, "bold"), fg=TERRACOTTA_FONCE, bg=OCRE_CLAIR
        ).pack(anchor="w", padx=12, pady=8)

        self.index_caravane = min(self.index_caravane, len(session) - 1)
        arret = session[self.index_caravane]

        carte = tk.Frame(self.zone_scrollable, bg=SABLE, highlightbackground=TERRACOTTA, highlightthickness=2)
        carte.pack(fill="x", padx=20, pady=(0, 10))

        badge_texte = "🔁 À consolider" if not arret.get("complement") else "✓ Déjà connu — petit rappel"
        tk.Label(
            carte, text=f"{arret.get('module','')}   ·   {badge_texte}", font=("Helvetica", 9, "bold"),
            fg=OCRE_FONCE, bg=SABLE
        ).pack(anchor="w", padx=16, pady=(14, 6))

        tk.Label(
            carte, text=arret.get("arabe", ""), font=("Helvetica", 26, "bold"), fg=TERRACOTTA_FONCE, bg=SABLE,
            wraplength=self._largeur_disponible() - 76, justify="left"
        ).pack(anchor="w", padx=16, pady=(0, 4))

        meta = " — ".join(filter(None, [arret.get("translitteration", ""), arret.get("sens", "")]))
        tk.Label(
            carte, text=meta, font=("Helvetica", 11), fg=TEXTE_FONCE, bg=SABLE,
            wraplength=self._largeur_disponible() - 76, justify="left"
        ).pack(anchor="w", padx=16, pady=(0, 12))

        pied = tk.Frame(carte, bg=SABLE)
        pied.pack(fill="x", padx=16, pady=(0, 14))

        def marquer_et_avancer(connu):
            p = self._charger_progres()
            p = marquer_item(p, arret["cle_etape"], arret["identifiant"], connu)
            self._sauvegarder_progres(p)
            if self.index_caravane < len(session) - 1:
                self.index_caravane += 1
            self.construire_interface()

        tk.Button(pied, text="✓ Je la maîtrise maintenant", font=("Helvetica", 9), bg=VERT_SUCCES, fg=BLANC, bd=0, padx=9, pady=5, cursor="hand2", command=lambda: marquer_et_avancer(True)).pack(side="left", padx=(0, 6))
        tk.Button(pied, text="🔁 Encore à revoir", font=("Helvetica", 9), bg=AMBRE_ATTENTE, fg=BLANC, bd=0, padx=9, pady=5, cursor="hand2", command=lambda: marquer_et_avancer(False)).pack(side="left")

        if self.index_caravane == len(session) - 1:
            tk.Label(
                self.zone_scrollable, text="🏁 Dernière étape de cette caravane — une nouvelle vous attendra la prochaine fois, reflétant vos progrès du moment.",
                font=("Helvetica", 9, "italic"), fg=GRIS_TEXTE_CLAIR, bg=BLANC, wraplength=560, justify="left"
            ).pack(anchor="w", padx=20, pady=(0, 10))

        self._construire_barre_pagination(
            self.index_caravane, len(session), f"Étape {self.index_caravane + 1} / {len(session)}",
            lambda: self._changer_arret_caravane(-1), lambda: self._changer_arret_caravane(1)
        )

    def _changer_arret_caravane(self, delta):
        self.index_caravane += delta
        self.construire_interface()

    def _construire_bandeau_resume(self, resume):
        self._total_pour_bandeau = resume["total"]
        bandeau = tk.Frame(self.zone_scrollable, bg=BLANC)
        bandeau.pack(fill="x", padx=20, pady=(0, 12))
        liseret = tk.Frame(bandeau, bg=OCRE, width=4)
        liseret.pack(side="left", fill="y")
        corps = tk.Frame(bandeau, bg=OCRE_CLAIR)
        corps.pack(side="left", fill="both", expand=True)
        lbl = tk.Label(
            corps, text=self._texte_resume(resume), font=("Helvetica", 10, "bold"), fg=TEXTE_FONCE, bg=OCRE_CLAIR
        )
        lbl.pack(anchor="w", padx=12, pady=8)
        self._lbl_resume = lbl
