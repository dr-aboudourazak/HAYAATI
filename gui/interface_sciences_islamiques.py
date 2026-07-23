"""
MODULE SCIENCES ISLAMIQUES (GUI/INTERFACE_SCIENCES_ISLAMIQUES.PY)
Version 1.0 - Coran, Hadith, Sîra, Tawhid, Fiqh. Même sentier vertical et
même mécanique de leçon (titre + explication + exemples, "J'ai compris" /
"À revoir" qui avance automatiquement) que le module Langue arabe, dont ce
module réutilise le moteur de progression générique.
"""
import tkinter as tk
from tkinter import ttk
from gui.langues import DICTIONNAIRE_LANGUES
from gui.palette_hayaati import (
    TERRACOTTA, TERRACOTTA_CLAIR, TERRACOTTA_FONCE,
    OCRE, OCRE_CLAIR, OCRE_FONCE, SABLE, BLANC, GRIS_TEXTE, VERT_SUCCES, AMBRE_ATTENTE,
    TEXTE_FONCE
)
from core.langue_arabe_engine import normaliser_progres, marquer_item, resume_etape

GRIS_INACTIF = "#d1d5db"
GRIS_TEXTE_CLAIR = "#6b7280"
CLE_MODULE_SCIENCES_ISLAMIQUES = "SCIENCES_ISLAMIQUES_PROGRES"


class EcranSciencesIslamiques(tk.Frame):
    def __init__(self, parent, app_reference):
        super().__init__(parent, bg=BLANC)
        self.app = app_reference
        self.etape_active = 0
        self.index_lecon = 0
        self.sentier_reduit = False
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
        donnees = self.app.sync_engine.charger_donnees_module(u_id, CLE_MODULE_SCIENCES_ISLAMIQUES)
        return normaliser_progres(donnees)

    def _sauvegarder_progres(self, progres):
        u_id = getattr(self.app, "user_id_connecte", None)
        if not u_id:
            return
        self.app.sync_engine.executer_sauvegarde_module(u_id, CLE_MODULE_SCIENCES_ISLAMIQUES, progres)

    def _construire_encart(self, texte, couleur_accent, icone="", police=("Helvetica", 9), pady_ext=(0, 10)):
        conteneur = tk.Frame(self.zone_scrollable, bg=BLANC)
        conteneur.pack(fill="x", padx=20, pady=pady_ext)
        tk.Frame(conteneur, bg=couleur_accent, width=4).pack(side="left", fill="y")
        corps = tk.Frame(conteneur, bg=SABLE)
        corps.pack(side="left", fill="both", expand=True)
        tk.Label(
            corps, text=f"{icone} {texte}".strip(), font=police, fg=TEXTE_FONCE, bg=SABLE,
            wraplength=self._largeur_disponible() - 70, justify="left"
        ).pack(anchor="w", padx=12, pady=8)

    def construire_interface(self):
        for w in self.zone_scrollable.winfo_children():
            w.destroy()

        txt = DICTIONNAIRE_LANGUES.actif.get("sciences_islamiques", {})
        etapes = txt.get("etapes", [])

        tk.Label(
            self.zone_scrollable, text=txt.get("titre", "🕌 Sciences islamiques"),
            font=("Helvetica", 16, "bold"), fg=TERRACOTTA_FONCE, bg=BLANC, wraplength=640, justify="left"
        ).pack(anchor="w", padx=20, pady=(18, 4))
        tk.Label(
            self.zone_scrollable, text=txt.get("sous_titre", ""),
            font=("Helvetica", 10, "italic"), fg=TEXTE_FONCE, bg=BLANC, wraplength=640, justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 10))

        avertissement = txt.get("avertissement", "")
        if avertissement:
            self._construire_encart(avertissement, OCRE, icone="ℹ️", police=("Helvetica", 8, "italic"))

        if not etapes:
            tk.Label(self.zone_scrollable, text="Contenu non disponible.", bg=BLANC, fg=TEXTE_FONCE).pack(padx=20, pady=20)
            return

        self._construire_sentier(etapes)
        etape_courante = etapes[min(self.etape_active, len(etapes) - 1)]

        if not etape_courante.get("disponible", False):
            self._construire_message_attente(etape_courante)
        else:
            self._construire_lecons(etape_courante)

        tk.Frame(self.zone_scrollable, bg=BLANC, height=30).pack()

    def _construire_sentier(self, etapes):
        etape_courante = etapes[min(self.etape_active, len(etapes) - 1)]
        entete = tk.Frame(self.zone_scrollable, bg=SABLE, cursor="hand2")
        entete.pack(fill="x", padx=20, pady=(0, 4))
        icone_repli = "▾" if not self.sentier_reduit else "▸"
        texte_entete = "🧭 Domaines" if not self.sentier_reduit else f"🧭 {etape_courante.get('titre','')}"
        lbl = tk.Label(entete, text=f"{icone_repli}  {texte_entete}", font=("Helvetica", 9, "bold"), fg=TERRACOTTA_FONCE, bg=SABLE, wraplength=self._largeur_disponible() - 60, justify="left")
        lbl.pack(anchor="w", padx=12, pady=8)
        for w in (entete, lbl):
            w.bind("<Button-1>", lambda e: self._basculer_sentier())

        if self.sentier_reduit:
            return

        conteneur = tk.Frame(self.zone_scrollable, bg=BLANC)
        conteneur.pack(fill="x", padx=20, pady=(0, 16))
        for i, etape in enumerate(etapes):
            active = (i == self.etape_active)
            disponible = etape.get("disponible", False)
            couleur_puce, couleur_fond = (TERRACOTTA, TERRACOTTA_CLAIR) if active else ((OCRE, BLANC) if disponible else (GRIS_INACTIF, BLANC))

            ligne = tk.Frame(conteneur, bg=couleur_fond, cursor="hand2")
            ligne.pack(fill="x")
            puce = tk.Canvas(ligne, width=34, height=42, bg=couleur_fond, highlightthickness=0)
            puce.pack(side="left")
            puce.create_oval(5, 9, 29, 33, fill=couleur_puce, outline="")
            puce.create_text(17, 21, text=("🔒" if not disponible else ("✎" if active else str(i + 1))), fill=BLANC, font=("Helvetica", 9, "bold"))

            zone_txt = tk.Frame(ligne, bg=couleur_fond)
            zone_txt.pack(side="left", fill="both", expand=True, pady=7)
            couleur_titre = TERRACOTTA_FONCE if active else (TEXTE_FONCE if disponible else GRIS_TEXTE_CLAIR)
            lbl_t = tk.Label(zone_txt, text=etape.get("titre", f"Domaine {i+1}"), font=("Helvetica", 10, "bold" if active else "normal"), fg=couleur_titre, bg=couleur_fond, anchor="w")
            lbl_t.pack(anchor="w")
            statut = "Domaine actuel" if active else ("Disponible — touchez pour ouvrir" if disponible else "Bientôt disponible")
            lbl_s = tk.Label(zone_txt, text=statut, font=("Helvetica", 8), fg=GRIS_TEXTE_CLAIR, bg=couleur_fond, anchor="w")
            lbl_s.pack(anchor="w")
            lbl_chevron = tk.Label(ligne, text="▸" if disponible else "", font=("Helvetica", 10), fg=couleur_titre, bg=couleur_fond)
            lbl_chevron.pack(side="right", padx=14)

            gestionnaire = (lambda idx=i, dispo=disponible: self._choisir_etape(idx) if dispo else None)
            for w in (ligne, puce, zone_txt, lbl_t, lbl_s, lbl_chevron):
                w.bind("<Button-1>", lambda e, g=gestionnaire: g())

            if i < len(etapes) - 1:
                trait = tk.Canvas(conteneur, width=34, height=10, bg=BLANC, highlightthickness=0)
                trait.pack(anchor="w")
                trait.create_line(17, 0, 17, 10, fill=(OCRE if disponible else GRIS_INACTIF), width=2)

    def _basculer_sentier(self):
        self.sentier_reduit = not self.sentier_reduit
        self.construire_interface()

    def _choisir_etape(self, index):
        self.etape_active = index
        self.index_lecon = 0
        self.sentier_reduit = True
        self.construire_interface()

    def _construire_message_attente(self, etape):
        cadre = tk.Frame(self.zone_scrollable, bg=SABLE, highlightbackground=OCRE, highlightthickness=1)
        cadre.pack(fill="x", padx=20, pady=10)
        tk.Label(cadre, text=f"⏳ {etape.get('titre', '')}", font=("Helvetica", 12, "bold"), fg=OCRE_FONCE, bg=SABLE).pack(anchor="w", padx=14, pady=(12, 4))
        tk.Label(
            cadre, text="Ce domaine n'a pas encore de contenu déposé. Il arrive bientôt.",
            font=("Helvetica", 10), fg=TEXTE_FONCE, bg=SABLE, wraplength=560, justify="left"
        ).pack(anchor="w", padx=14, pady=(0, 12))

    def _construire_chaine_isnad(self, parent, maillons, wraplength):
        if not maillons:
            return
        conteneur = tk.Frame(parent, bg=BLANC, highlightbackground=TERRACOTTA, highlightthickness=1)
        conteneur.pack(fill="x", padx=16, pady=(4, 10))
        tk.Label(
            conteneur, text="🔗 De la source jusqu'au recueil, maillon par maillon :", font=("Helvetica", 9, "italic"),
            fg=OCRE_FONCE, bg=BLANC
        ).pack(anchor="w", padx=10, pady=(8, 4))

        for i, maillon in enumerate(maillons):
            ligne = tk.Frame(conteneur, bg=BLANC)
            ligne.pack(fill="x", padx=10, pady=2)

            puce = tk.Canvas(ligne, width=30, height=36, bg=BLANC, highlightthickness=0)
            puce.pack(side="left")
            puce.create_oval(3, 6, 27, 30, fill=(TERRACOTTA if i == 0 else OCRE), outline="")
            puce.create_text(15, 18, text=str(i + 1), fill=BLANC, font=("Helvetica", 9, "bold"))

            zone_txt = tk.Frame(ligne, bg=BLANC)
            zone_txt.pack(side="left", fill="x", expand=True, padx=(6, 0))
            tk.Label(zone_txt, text=maillon.get("role", ""), font=("Helvetica", 8, "italic"), fg=GRIS_TEXTE_CLAIR, bg=BLANC).pack(anchor="w")
            tk.Label(zone_txt, text=maillon.get("nom", ""), font=("Helvetica", 13, "bold"), fg=TERRACOTTA_FONCE, bg=BLANC, wraplength=wraplength - 60, justify="left").pack(anchor="w")
            tk.Label(zone_txt, text=maillon.get("note", ""), font=("Helvetica", 8), fg=TEXTE_FONCE, bg=BLANC, wraplength=wraplength - 60, justify="left").pack(anchor="w")

            if i < len(maillons) - 1:
                trait = tk.Canvas(conteneur, width=30, height=14, bg=BLANC, highlightthickness=0)
                trait.pack(anchor="w", padx=10)
                trait.create_line(15, 0, 15, 10, fill=OCRE, width=2)
                trait.create_polygon(15, 14, 10, 6, 20, 6, fill=OCRE, outline="")

        tk.Frame(conteneur, bg=BLANC, height=8).pack()

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

    def _construire_lecons(self, etape):
        lecons = etape.get("lecons", [])
        if not lecons:
            self._construire_message_attente(etape)
            return

        cle_progres = f"sciences_{etape.get('cle', self.etape_active)}"
        progres = self._charger_progres()
        resume = resume_etape(progres, cle_progres, len(lecons))

        bandeau = tk.Frame(self.zone_scrollable, bg=BLANC)
        bandeau.pack(fill="x", padx=20, pady=(0, 12))
        tk.Frame(bandeau, bg=OCRE, width=4).pack(side="left", fill="y")
        corps = tk.Frame(bandeau, bg=OCRE_CLAIR)
        corps.pack(side="left", fill="both", expand=True)
        tk.Label(
            corps, text=f"✓ {resume['connues']} compris(es)   ·   🔁 {resume['a_revoir']} à revoir   ·   ⚪ {resume['non_vues']} pas encore vu(e)s",
            font=("Helvetica", 10, "bold"), fg=TEXTE_FONCE, bg=OCRE_CLAIR
        ).pack(anchor="w", padx=12, pady=8)

        self.index_lecon = min(self.index_lecon, len(lecons) - 1)
        lecon = lecons[self.index_lecon]
        identifiant = str(self.index_lecon)
        wraplength = self._largeur_disponible() - 60

        carte = tk.Frame(self.zone_scrollable, bg=SABLE, highlightbackground=TERRACOTTA, highlightthickness=1)
        carte.pack(fill="x", padx=20, pady=(0, 10))
        tk.Label(carte, text=lecon.get("titre", ""), font=("Helvetica", 13, "bold"), fg=TERRACOTTA_FONCE, bg=SABLE, wraplength=wraplength, justify="left").pack(anchor="w", padx=16, pady=(14, 8))
        tk.Label(carte, text=lecon.get("explication", ""), font=("Helvetica", 11), fg=TEXTE_FONCE, bg=SABLE, wraplength=wraplength, justify="left").pack(anchor="w", padx=16, pady=(0, 10))

        if lecon.get("type_visuel") == "chaine_isnad":
            self._construire_chaine_isnad(carte, lecon.get("chaine_isnad", []), wraplength)

        for ex in lecon.get("exemples", []):
            ligne_ex = tk.Frame(carte, bg=BLANC, highlightbackground=OCRE, highlightthickness=1)
            ligne_ex.pack(fill="x", padx=16, pady=3)
            tk.Label(ligne_ex, text=ex.get("arabe", ""), font=("Helvetica", 18, "bold"), fg=TEXTE_FONCE, bg=BLANC, wraplength=wraplength - 20, justify="left").pack(anchor="w", padx=10, pady=(8, 0))
            tk.Label(ligne_ex, text=f"{ex.get('translitteration','')} — {ex.get('sens','')}", font=("Helvetica", 10), fg=TEXTE_FONCE, bg=BLANC, wraplength=wraplength - 20, justify="left").pack(anchor="w", padx=10, pady=(0, 8))

        pied = tk.Frame(carte, bg=SABLE)
        pied.pack(fill="x", padx=16, pady=(4, 14))

        def marquer_et_avancer(connu):
            p = self._charger_progres()
            p = marquer_item(p, cle_progres, identifiant, connu)
            self._sauvegarder_progres(p)
            if self.index_lecon < len(lecons) - 1:
                self.index_lecon += 1
            self.construire_interface()

        tk.Button(pied, text="✓ J'ai compris", font=("Helvetica", 9), bg=VERT_SUCCES, fg=BLANC, bd=0, padx=9, pady=5, cursor="hand2", command=lambda: marquer_et_avancer(True)).pack(side="left", padx=(0, 6))
        tk.Button(pied, text="🔁 À revoir", font=("Helvetica", 9), bg=AMBRE_ATTENTE, fg=BLANC, bd=0, padx=9, pady=5, cursor="hand2", command=lambda: marquer_et_avancer(False)).pack(side="left")

        libelles = [l.get("titre", f"Leçon {i+1}") for i, l in enumerate(lecons)]
        self._construire_barre_pagination(
            self.index_lecon, len(lecons), f"{self.index_lecon + 1} / {len(lecons)} — {libelles[self.index_lecon]}",
            lambda: self._changer_lecon(-1), lambda: self._changer_lecon(1)
        )

    def _changer_lecon(self, delta):
        self.index_lecon += delta
        self.construire_interface()
