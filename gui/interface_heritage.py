"""
INTERFACE DES SUCCESSIONS INTEGRÉE ET UNIFIÉE (GUI/INTERFACE_HERITAGE.PY)
"""
import tkinter as tk
from tkinter import messagebox, ttk
from gui.langues import DICTIONNAIRE_LANGUES
from core.heritage.exclusions import appliquer_moteur_exclusions
from core.heritage.fractions import distribuer_parts_completes
from core.certificate_engine import generer_certificat_pdf

class EcranHeritage(tk.Frame):
    def __init__(self, parent, app_reference):
        super().__init__(parent, bg="#f9fafb")
        self.app = app_reference

        self.colonne_gauche = tk.Frame(self, bg="#f9fafb")
        self.colonne_gauche.pack(side="left", fill="both", expand=True, padx=20, pady=10)
        self.colonne_droite = tk.Frame(self, bg="#f9fafb")
        self.colonne_droite.pack(side="right", fill="both", expand=True, padx=20, pady=10)

        # Masse successorale
        cadre_cap = tk.Frame(self.colonne_gauche, bg="#f9fafb")
        cadre_cap.pack(pady=5, fill="x")
        self.lbl_capital = tk.Label(cadre_cap, text="Masse successorale :", font=("Helvetica", 11, "bold"), bg="#f9fafb", fg="#b45309")
        self.lbl_capital.pack(side="left")
        self.entree_capital = tk.Entry(cadre_cap, font=("Arial", 11), justify="center", width=12, bd=1, relief="solid")
        self.entree_capital.pack(side="left", padx=10)
        self.entree_capital.insert(0, "24000")

        self.var_hors_mariage = tk.BooleanVar()
        self.chk_hm = tk.Checkbutton(self.colonne_gauche, text="⚖️ Filiation : Enfant né hors mariage (Arbre maternel)", variable=self.var_hors_mariage, bg="#f9fafb", fg="#4b5563", font=("Helvetica", 9))
        self.chk_hm.pack(anchor="w", pady=5)

        self.lbl_famille_titre = tk.Label(self.colonne_gauche, text="Membres de la famille vivants :", font=("Helvetica", 11, "bold"), fg="#374151", bg="#f9fafb")
        self.lbl_famille_titre.pack(pady=5, anchor="w")

        self.cadre_grille = tk.Frame(self.colonne_gauche, bg="#f9fafb")
        self.cadre_grille.pack(fill="x", pady=5)

        self.categories = [
            ("epouse", "Épouse(s) [Max 4]", 4), ("epoux", "Époux [Max 1]", 1),
            ("fils", "Nombre de Fils", 20), ("fille", "Nombre de Filles", 20),
            ("pere", "Père Vivant (0/1)", 1), ("mere", "Mère Vivante (0/1)", 1),
            ("grand_pere", "Grand-père paternel (0/1)", 1),
            ("frere_germain", "Frères Germains", 20),
            ("frere_uterin", "Frères/Sœurs utérins", 20), ("oncle", "Oncles paternels", 20)
        ]

        self.champs_nombres = {}
        for i, (cle, libelle, max_v) in enumerate(self.categories):
            tk.Label(self.cadre_grille, text=libelle, font=("Helvetica", 9), bg="#f9fafb", anchor="w").grid(row=i, column=0, sticky="w", pady=2)
            spn = ttk.Spinbox(self.cadre_grille, from_=0, to=max_v, width=5, justify="center")
            spn.set(0)
            spn.grid(row=i, column=1, padx=15, pady=2)
            self.champs_nombres[cle] = spn

        # Colonne Droite
        self.liste_indignes_globale = []
        self.btn_exceptions = tk.Button(self.colonne_droite, text="⚠️ Exceptions / Indignités", bg="#fee2e2", fg="#991b1b", font=("Helvetica", 9), command=self.ouvrir_popup_exceptions, width=25)
        self.btn_exceptions.pack(pady=5)

        self.lbl_res = tk.Label(self.colonne_droite, text="---", font=("Courier", 9, "bold"), fg="#111827", bg="#f3f4f6", height=15, width=48, bd=1, relief="solid", justify="left", anchor="nw", padx=8, pady=5)
        self.lbl_res.pack(pady=5)

        self.memoire_rapport_lignes = []
        self.memoire_intrants_bruts = {}

        cadre_actions = tk.Frame(self.colonne_droite, bg="#f9fafb")
        cadre_actions.pack(pady=10)

        self.btn_partage = tk.Button(cadre_actions, text="Calculer le Partage ⚖️", font=("Helvetica", 10, "bold"), bg="#b45309", fg="#ffffff", command=self.executer_partage_heritage, width=18)
        self.btn_partage.grid(row=0, column=0, padx=5)

        self.btn_pdf = tk.Button(cadre_actions, text="🖨️ Certificat PDF", font=("Helvetica", 10, "bold"), bg="#d97706", fg="#ffffff", state="disabled", command=self.declencher_impression_heritage, width=18)
        self.btn_pdf.grid(row=0, column=1, padx=5)

    # 🚨 FIX : Ajout de la fonction manquante demandée par l'accueil lors des rafraîchissements
    def actualiser_contexte(self):
        self.executer_partage_heritage()

    def ouvrir_popup_exceptions(self):
        lang = DICTIONNAIRE_LANGUES[self.app.langue_active]
        membres_presents = [c for c, spn in self.champs_nombres.items() if int(spn.get()) > 0]
        if not membres_presents:
            messagebox.showwarning("Hayaati", "Veuillez d'abord déclarer des membres vivants.")
            return

        pop = tk.Toplevel(self)
        pop.title(lang.get("her_pop_exceptions_titre", "Exceptions"))
        pop.geometry("350x300")
        pop.configure(bg="#fef2f2")
        pop.grab_set()

        chks_indignes = {}
        for m in membres_presents:
            var_ind = tk.BooleanVar()
            if m in self.liste_indignes_globale: var_ind.set(True)
            chk = tk.Checkbutton(pop, text=f"{m.upper()} -> Exclu", variable=var_ind, bg="#fef2f2", fg="#7f1d1d")
            chk.pack(anchor="w", padx=20, pady=3)
            chks_indignes[m] = var_ind

        def valider_exceptions():
            self.liste_indignes_globale = [cle for cle, var in chks_indignes.items() if var.get()]
            pop.destroy()
            self.executer_partage_heritage()

        tk.Button(pop, text="Valider ✅", bg="#991b1b", fg="white", command=valider_exceptions).pack(pady=15)

    def executer_partage_heritage(self):
        lang = DICTIONNAIRE_LANGUES[self.app.langue_active]
        devise = self.app.devise_active
        madhhab = self.app.madhhab_actif

        try:
            capital = float(self.entree_capital.get().replace(",", "."))
            config_nombres = {c: int(spn.get()) for c, spn in self.champs_nombres.items()}
            famille_brute = [c for c, v in config_nombres.items() if v > 0]
            exceptions = [i for i in self.liste_indignes_globale if i in famille_brute]

            if self.var_hors_mariage.get():
                for cpt in ["pere", "grand_pere", "frere_germain", "oncle"]:
                    if cpt in famille_brute and cpt not in exceptions: exceptions.append(cpt)

            bilan_ex = appliquer_moteur_exclusions(famille_brute, cas_indignite=exceptions)
            retenus = bilan_ex["heritiers_valides"]
            exclus = bilan_ex["personnes_exclues"]

            self.memoire_intrants = {f"NB_{c.upper()}": str(v) for c, v in config_nombres.items() if v > 0}

            bilan_parts = distribuer_parts_completes(retenus, config_nombres)
            ventilation = bilan_parts["ventilation_fractions"]

            self.memoire_rapport_lignes = [f"=== {lang['her_res_titre']} ==="]
            self.memoire_rapport_lignes.append(f" [{lang['selection_fiqh']} {madhhab.upper()}]")
            
            for heritier, fraction in ventilation.items():
                part_totale = capital * fraction
                nb_p = config_nombres[heritier]
                if nb_p > 1:
                    self.memoire_rapport_lignes.append(f"  • {heritier.upper()} (x{nb_p}) : {fraction*100:.1f}% -> {part_totale:.2f} {devise}")
                else:
                    self.memoire_rapport_lignes.append(f"  • {heritier.upper()} : {fraction*100:.1f}% -> {part_totale:.2f} {devise}")
            
            if exclus:
                self.memoire_rapport_lignes.append(f"\n{lang['her_lbl_exclus']}")
                for e in list(set(exclus)):
                    self.memoire_rapport_lignes.append(f"  • {e.upper()}")

            self.lbl_res.config(text="\n".join(self.memoire_rapport_lignes))
            self.btn_pdf.config(state="normal")

        except ValueError:
            pass

    def declencher_impression_heritage(self):
        identite = self.app.obtenir_identite_saisie()
        if not identite["nom"].strip():
            messagebox.showwarning("Hayaati", "Veuillez remplir le bloc d'identité.")
            return
        generer_certificat_pdf(identite, "Heritage", self.app.madhhab_actif, self.app.devise_active, self.memoire_intrants, self.memoire_rapport_lignes)
