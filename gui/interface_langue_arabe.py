"""
MODULE LANGUE ARABE (GUI/INTERFACE_LANGUE_ARABE.PY)
Version 3.0
- Les cartes de la grille se redimensionnent réellement avec la fenêtre :
  nombre de colonnes ET repli du texte (wraplength) recalculés à chaque
  redimensionnement (avec anti-rebond), au lieu d'une valeur fixe qui
  débordait sur petit écran.
- Navigation par "page" plutôt que défilement long : l'alphabet se feuillette
  par lots calés sur la taille d'écran, le vocabulaire se feuillette liste
  par liste. Un défilement vertical résiduel reste possible si une page
  dépasse malgré tout la hauteur visible, en filet de sécurité.
- Chaque lettre montre désormais sa graphie en début, milieu et fin de mot,
  avec exemple à chaque position (sauf pour les lettres non connectantes,
  qui n'ont pas de forme médiane distincte — expliqué à l'écran).
- Le vocabulaire s'illustre : pastilles de couleur réelles pour la liste
  "couleurs", icône pour les autres.
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
LARGEUR_MIN_CARTE = 145   # en dessous, une carte n'a plus la place d'être lisible
LIGNES_PAR_PAGE = 3       # nombre de rangées de cartes visées par page


class EcranLangueArabe(tk.Frame):
    def __init__(self, parent, app_reference):
        super().__init__(parent, bg=BLANC)
        self.app = app_reference
        self.etape_active = 0
        self.cartes_retournees = set()
        self.page_alphabet = 0
        self.index_liste_vocabulaire = 0
        self._derniere_largeur_connue = 0
        self._id_redimensionnement = None

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

    # --- Redimensionnement réactif, avec anti-rebond pour ne pas reconstruire
    # l'écran à chaque pixel glissé pendant un drag de fenêtre ---
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
        largeur = self._largeur_disponible() - 28  # marge intérieure
        nb_colonnes = max(1, min(6, largeur // LARGEUR_MIN_CARTE))
        largeur_carte = largeur // nb_colonnes
        wraplength = max(90, largeur_carte - 24)
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
        self.page_alphabet = 0
        self.index_liste_vocabulaire = 0
        self.cartes_retournees.clear()
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

    # --- Barre de pagination générique ("changement de page") ---
    def _construire_barre_pagination(self, page_actuelle, nb_pages, libelle, action_precedent, action_suivant):
        if nb_pages <= 1:
            return
        barre = tk.Frame(self.zone_scrollable, bg=BLANC)
        barre.pack(fill="x", padx=20, pady=(4, 16))
        b_prec = tk.Button(barre, text="◂ Précédent", font=("Helvetica", 9), bg=SABLE, fg=TERRACOTTA_FONCE, bd=0, padx=10, pady=5, cursor="hand2", command=action_precedent)
        b_prec.pack(side="left")
        if page_actuelle == 0:
            b_prec.config(state=tk.DISABLED, fg=GRIS_TEXTE_CLAIR)
        tk.Label(barre, text=libelle, font=("Helvetica", 9, "bold"), fg=GRIS_TEXTE, bg=BLANC).pack(side="left", expand=True)
        b_suiv = tk.Button(barre, text="Suivant ▸", font=("Helvetica", 9), bg=SABLE, fg=TERRACOTTA_FONCE, bd=0, padx=10, pady=5, cursor="hand2", command=action_suivant)
        b_suiv.pack(side="right")
        if page_actuelle >= nb_pages - 1:
            b_suiv.config(state=tk.DISABLED, fg=GRIS_TEXTE_CLAIR)

    # --- Grille de cartes générique (réutilisée par alphabet et vocabulaire) ---
    def _construire_grille_cartes(self, items, cle_etape, progres, nb_colonnes, wraplength):
        grille = tk.Frame(self.zone_scrollable, bg=BLANC)
        grille.pack(fill="x", padx=14)
        for c in range(nb_colonnes):
            grille.grid_columnconfigure(c, weight=1)

        for i, item in enumerate(items):
            ligne, colonne = divmod(i, nb_colonnes)
            self._construire_carte_item(grille, item, cle_etape, ligne, colonne, progres, wraplength)

    def _construire_carte_item(self, parent, item, cle_etape, ligne, colonne, progres, wraplength):
        identifiant = item["id"]
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
                self._peupler_face_detail(carte, item, cle_etape, basculer, wraplength)
            else:
                self._peupler_face_recto(carte, item, basculer, wraplength)

        def basculer(event=None):
            if identifiant in self.cartes_retournees:
                self.cartes_retournees.discard(identifiant)
            else:
                self.cartes_retournees.add(identifiant)
            rafraichir_carte()

        carte.bind("<Button-1>", basculer)
        rafraichir_carte()

    def _peupler_face_recto(self, carte, item, basculer, wraplength):
        widgets = []

        if item.get("couleur_hex"):
            zone_swatch = tk.Canvas(carte, width=44, height=44, bg=BLANC, highlightthickness=0)
            zone_swatch.pack(pady=(14, 4))
            zone_swatch.create_oval(2, 2, 42, 42, fill=item["couleur_hex"], outline=GRIS_TEXTE)
            widgets.append(zone_swatch)
        elif item.get("icone"):
            lbl_icone = tk.Label(carte, text=item["icone"], font=("Helvetica", 22), bg=BLANC)
            lbl_icone.pack(pady=(12, 0))
            widgets.append(lbl_icone)

        lbl1 = tk.Label(carte, text=item.get("principal", "?"), font=("Helvetica", item.get("taille_police_recto", 18)), bg=BLANC, fg=TERRACOTTA_FONCE, wraplength=wraplength, justify="center")
        lbl1.pack(pady=(8 if widgets else 14, 2))
        lbl2 = tk.Label(carte, text=item.get("sous_titre_recto", ""), font=("Helvetica", 9), bg=BLANC, fg=GRIS_TEXTE, wraplength=wraplength, justify="center")
        lbl2.pack(pady=(0, 14))
        widgets += [lbl1, lbl2]
        for w in widgets:
            w.bind("<Button-1>", basculer)

    def _peupler_face_detail(self, carte, item, cle_etape, basculer, wraplength):
        for texte, police, couleur in item.get("lignes_detail", []):
            lbl = tk.Label(carte, text=texte, font=police, bg=BLANC, fg=couleur, wraplength=wraplength, justify="center")
            lbl.pack(pady=(3, 3))
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

    # --- Étape Alphabet, paginée ---
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
            lignes = [(f"{l.get('lettre','')}  ·  {l.get('nom','')}", ("Helvetica", 12, "bold"), TERRACOTTA_FONCE),
                      (f"Translittération : {l.get('translitteration','')}", ("Helvetica", 8), GRIS_TEXTE),
                      (f"Connexion : {l.get('connexion','')}", ("Helvetica", 8), GRIS_TEXTE),
                      (l.get("son", ""), ("Helvetica", 8), GRIS_TEXTE)]

            occurrences = l.get("occurrences", [])
            positions_presentes = {o["position"] for o in occurrences}
            if "milieu" not in positions_presentes:
                lignes.append(("(lettre non connectante : pas de forme médiane distincte)", ("Helvetica", 7, "italic"), GRIS_TEXTE_CLAIR))
            for occ in occurrences:
                lignes.append((f"{occ['position'].capitalize()} : {occ['mot']} ({occ['translitteration']}) — {occ['sens']}", ("Helvetica", 8), OCRE_FONCE))

            items.append({"id": str(i), "principal": l.get("lettre", "?"), "taille_police_recto": 26, "sous_titre_recto": l.get("nom", ""), "lignes_detail": lignes})

        self._construire_grille_cartes(items, "alphabet", progres, nb_colonnes, wraplength)
        self._construire_barre_pagination(
            self.page_alphabet, nb_pages, f"Page {self.page_alphabet + 1} / {nb_pages}",
            lambda: self._changer_page_alphabet(-1), lambda: self._changer_page_alphabet(1)
        )

    def _changer_page_alphabet(self, delta):
        self.page_alphabet += delta
        self.cartes_retournees.clear()
        self.construire_interface()

    # --- Étape Vocabulaire, paginée liste par liste ---
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
            self.zone_scrollable, text=liste.get("titre", ""), font=("Helvetica", 12, "bold"),
            fg=TERRACOTTA_FONCE, bg=BLANC
        ).pack(anchor="w", padx=20, pady=(6, 10))

        nb_colonnes, wraplength = self._colonnes_et_wraplength()
        items = []
        for i_mot, mot in enumerate(liste.get("mots", [])):
            identifiant = f"liste{i_liste}_mot{i_mot}"
            items.append({
                "id": identifiant,
                "principal": mot.get("arabe", "?"), "taille_police_recto": 15,
                "sous_titre_recto": mot.get("sens", ""),
                "icone": mot.get("icone"), "couleur_hex": mot.get("couleur_hex"),
                "lignes_detail": [
                    (mot.get("arabe", ""), ("Helvetica", 15, "bold"), TERRACOTTA_FONCE),
                    (mot.get("translitteration", ""), ("Helvetica", 9, "italic"), GRIS_TEXTE),
                    (f"« {mot.get('sens','')} »", ("Helvetica", 9), OCRE_FONCE),
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

    def _construire_bandeau_resume(self, resume):
        bandeau = tk.Frame(self.zone_scrollable, bg=OCRE_CLAIR)
        bandeau.pack(fill="x", padx=20, pady=(0, 12))
        tk.Label(
            bandeau, text=f"✓ {resume['connues']} connu(e)s   ·   🔁 {resume['a_revoir']} à revoir   ·   ⚪ {resume['non_vues']} pas encore vu(e)s",
            font=("Helvetica", 9, "bold"), fg=TERRACOTTA_FONCE, bg=OCRE_CLAIR
        ).pack(anchor="w", padx=12, pady=8)
