"""
MODULE ÉDUCATIF : ENCYCLOPÉDIE DOCTRINALE (GUI/INTERFACE_ENCYCLOPEDIE.PY)
Version 1.0 - Consomme le contenu déjà rédigé dans gui/dictionnaires/*.json
(clé "encyclopedie"). Suivi de lecture non punitif : on affiche la progression,
sans série à préserver ni compte à rebours.
"""
import tkinter as tk
from tkinter import ttk
from gui.langues import DICTIONNAIRE_LANGUES
from gui.palette_hayaati import (
    TERRACOTTA, TERRACOTTA_CLAIR, TERRACOTTA_FONCE,
    OCRE, OCRE_CLAIR, OCRE_FONCE, SABLE, BLANC, GRIS_TEXTE, VERT_SUCCES
)

CLE_MODULE_PROGRES = "ENCYCLOPEDIE_PROGRES"


class EcranEncyclopedie(tk.Frame):
    def __init__(self, parent, app_reference):
        super().__init__(parent, bg=BLANC)
        self.app = app_reference
        self.categories_ouvertes = set()
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

    def _charger_progres(self):
        u_id = getattr(self.app, "user_id_connecte", None)
        if not u_id:
            return set()
        donnees = self.app.sync_engine.charger_donnees_module(u_id, CLE_MODULE_PROGRES)
        return set(donnees.get("lus", []))

    def _sauvegarder_progres(self, indices_lus):
        u_id = getattr(self.app, "user_id_connecte", None)
        if not u_id:
            return
        self.app.sync_engine.executer_sauvegarde_module(u_id, CLE_MODULE_PROGRES, {"lus": sorted(indices_lus)})

    def construire_interface(self):
        for w in self.zone_scrollable.winfo_children():
            w.destroy()
        self.widgets_categories = []

        txt = DICTIONNAIRE_LANGUES.actif.get("encyclopedie", {})
        categories = txt.get("categories", [])
        indices_lus = self._charger_progres()

        # --- En-tête ---
        tk.Label(
            self.zone_scrollable, text=txt.get("titre", "📚 Encyclopédie"),
            font=("Helvetica", 15, "bold"), fg=TERRACOTTA_FONCE, bg=BLANC, wraplength=640, justify="left"
        ).pack(anchor="w", padx=20, pady=(18, 4))

        tk.Label(
            self.zone_scrollable, text=txt.get("consigne", ""),
            font=("Helvetica", 9, "italic"), fg=GRIS_TEXTE, bg=BLANC, wraplength=640, justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 4))

        total = len(categories)
        lu_n = len([i for i in indices_lus if i < total])
        lbl_progres = txt.get("progres_lecture", "{} sur {} thèmes parcourus").format(lu_n, total) if total else ""
        self.lbl_compteur = tk.Label(
            self.zone_scrollable, text=lbl_progres, font=("Helvetica", 9, "bold"),
            fg=OCRE_FONCE, bg=BLANC
        )
        self.lbl_compteur.pack(anchor="w", padx=20, pady=(4, 14))

        # --- Frise décorative simple (zigzag terracotta / ocre) ---
        frise = tk.Canvas(self.zone_scrollable, height=8, bg=BLANC, bd=0, highlightthickness=0)
        frise.pack(fill="x", padx=20, pady=(0, 14))
        frise.bind("<Configure>", lambda e, c=frise: self._dessiner_frise(c))

        # --- Cartes de catégories ---
        for i, categorie in enumerate(categories):
            self._construire_carte_categorie(i, categorie, i in indices_lus)

        tk.Frame(self.zone_scrollable, bg=BLANC, height=30).pack()

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

    def _construire_carte_categorie(self, index, categorie, deja_lu):
        couleur_accent = TERRACOTTA if index % 2 == 0 else OCRE
        couleur_fond_titre = TERRACOTTA_CLAIR if index % 2 == 0 else OCRE_CLAIR
        couleur_texte_titre = TERRACOTTA_FONCE if index % 2 == 0 else OCRE_FONCE

        carte = tk.Frame(self.zone_scrollable, bg=BLANC, highlightbackground=couleur_accent, highlightthickness=1, bd=0)
        carte.pack(fill="x", padx=20, pady=6)

        entete = tk.Frame(carte, bg=couleur_fond_titre, cursor="hand2")
        entete.pack(fill="x")

        badge = "✓ " if deja_lu else ""
        lbl_titre = tk.Label(
            entete, text=f"{badge}{categorie.get('titre', '')}", font=("Helvetica", 10, "bold"),
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
        pied.pack(fill="x", padx=14, pady=(0, 10))

        var_lu = tk.BooleanVar(value=deja_lu)

        def basculer_lu():
            indices = self._charger_progres()
            if var_lu.get():
                indices.add(index)
            else:
                indices.discard(index)
            self._sauvegarder_progres(indices)
            total = len(DICTIONNAIRE_LANGUES.actif.get("encyclopedie", {}).get("categories", []))
            txt = DICTIONNAIRE_LANGUES.actif.get("encyclopedie", {})
            lbl = txt.get("progres_lecture", "{} sur {} thèmes parcourus").format(len(indices), total)
            if hasattr(self, "lbl_compteur") and self.lbl_compteur.winfo_exists():
                self.lbl_compteur.config(text=lbl)
            lbl_titre.config(text=f"{'✓ ' if var_lu.get() else ''}{categorie.get('titre', '')}")

        txt_reglages = DICTIONNAIRE_LANGUES.actif.get("reglages", {})
        chk = tk.Checkbutton(
            pied, text=txt_reglages.get("lbl_marquer_lu", "Marquer comme parcouru"),
            variable=var_lu, onvalue=True, offvalue=False, bg=SABLE, fg=GRIS_TEXTE,
            activebackground=SABLE, font=("Helvetica", 9), command=basculer_lu, selectcolor=BLANC
        )
        chk.pack(side="left")

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
