"""
INTERFACE DU MODULE ZAKAT INTEGRÉE (GUI/INTERFACE_ZAKAT.PY)
"""
import tkinter as tk
from tkinter import messagebox
from gui.langues import DICTIONNAIRE_LANGUES
from core.zakat.finance import evaluer_zakat_financiere
from core.zakat.commerce import evaluer_zakat_commerciale
from core.zakat.agriculture import evaluer_zakat_agricole, evaluer_zakat_elevage_ovins
from core.certificate_engine import generer_certificat_pdf

class EcranZakat(tk.Frame):
    def __init__(self, parent, app_reference):
        super().__init__(parent, bg="#f9fafb")
        self.app = app_reference

        # Split 2 colonnes
        self.gauche = tk.Frame(self, bg="#f9fafb")
        self.gauche.pack(side="left", fill="both", expand=True, padx=15, pady=10)
        self.droite = tk.Frame(self, bg="#f9fafb")
        self.droite.pack(side="right", fill="both", expand=True, padx=15, pady=10)

        # En-tête de module
        self.lbl_entete = tk.Label(self.gauche, text="", font=("Helvetica", 12, "bold"), fg="#064e3b", bg="#f9fafb", justify="left", anchor="w")
        self.lbl_entete.pack(pady=5, anchor="w")

        self.cadre_form = tk.Frame(self.gauche, bg="#f9fafb")
        self.cadre_form.pack(fill="x", pady=5)

        self.structure_champs = [
            ("cours", "Cours de l'or (1g) :"), ("cash", "Argent liquide personnel :"),
            ("bijoux", "Valeur des bijoux personnels :"), ("stocks", "Valeur du stock marchand :"),
            ("pro_cash", "Liquidités de l'entreprise :"), ("dettes", "Dettes à court terme :"),
            ("recolte", "Récolte agricole (kg) :"), ("elevage", "Troupeau d'ovins (têtes) :"),
        ]

        self.champs = {}
        for i, (cle, libelle) in enumerate(self.structure_champs):
            lbl = tk.Label(self.cadre_form, text=libelle, font=("Helvetica", 9), fg="#374151", bg="#f9fafb", anchor="w")
            lbl.grid(row=i, column=0, sticky="w", pady=3)
            entree = tk.Entry(self.cadre_form, font=("Arial", 10), justify="center", width=15, bd=1, relief="solid")
            entree.grid(row=i, column=1, pady=3, padx=15)
            # 🚨 FIX : Insertion du cours par défaut à 68.50 au lieu de 0
            entree.insert(0, "68.50" if cle == "cours" else "0")
            self.champs[cle] = entree

        # Colonne droite
        self.lbl_res = tk.Label(self.droite, text="---", font=("Helvetica", 10, "bold"), fg="#1e3a8a", bg="#f3f4f6", height=8, width=46, bd=1, relief="solid", justify="left", anchor="nw", padx=10, pady=5)
        self.lbl_res.pack(pady=10)

        self.memoire_lignes = []
        self.memoire_intrants = {}

        cadre_actions = tk.Frame(self.droite, bg="#f9fafb")
        cadre_actions.pack(pady=10)

        self.btn_calc = tk.Button(cadre_actions, text="Calculer la Zakat 💰", font=("Helvetica", 10, "bold"), bg="#064e3b", fg="white", command=self.calculer_zakat_pro, width=16)
        self.btn_calc.grid(row=0, column=0, padx=5)

        self.btn_pdf = tk.Button(cadre_actions, text="🖨️ Certificat PDF", font=("Helvetica", 10, "bold"), bg="#d97706", fg="white", state="disabled", command=self.imprimer_certificat, width=16)
        self.btn_pdf.grid(row=0, column=1, padx=5)

        self.actualiser_contexte()

    def actualiser_contexte(self):
        lang = DICTIONNAIRE_LANGUES[self.app.langue_active]
        devise = self.app.devise_active
        madhhab = self.app.madhhab_actif
        self.lbl_entete.config(text=f"{lang['zk_titre']}\n[📜 {lang.get('selection_fiqh', 'Fiqh')} : {madhhab.upper()} | {devise}]")

    def calculer_zakat_pro(self):
        lang = DICTIONNAIRE_LANGUES[self.app.langue_active]
        devise = self.app.devise_active
        madhhab = self.app.madhhab_actif
        
        try:
            cours = float(self.champs["cours"].get().replace(",", "."))
            cash = float(self.champs["cash"].get().replace(",", "."))
            bijoux = float(self.champs["bijoux"].get().replace(",", "."))
            stocks = float(self.champs["stocks"].get().replace(",", "."))
            pro_cash = float(self.champs["pro_cash"].get().replace(",", "."))
            dettes = float(self.champs["dettes"].get().replace(",", "."))
            recolte = float(self.champs["recolte"].get().replace(",", "."))
            elevage = int(self.champs["elevage"].get())

            self.memoire_intrants = {lib: self.champs[c].get() for c, lib in self.structure_champs}

            bilan_com = evaluer_zakat_commerciale(stocks, pro_cash, dettes, 0.0, 0.0, 0.0, 0.0)
            masse_pro = bilan_com["assiette_globale_commerce_contribuee"]
            bilan_fin = evaluer_zakat_financiere(cash + masse_pro, 0.0, bijoux, 0.0, 0.0, cours, madhhab)
            bilan_agri = evaluer_zakat_agricole(recolte, "naturelle")
            bilan_ovins = evaluer_zakat_elevage_ovins(elevage)

            self.memoire_lignes = [f"{lang['zk_rep_titre']}"]
            if bilan_fin["eligible"]:
                self.memoire_lignes.append(f"  {lang['zk_rep_fin']}{bilan_fin['montant_zakat_du']:.2f} {devise}")
            else:
                self.memoire_lignes.append(f"  {lang['zk_rep_fin_non']}")
            if bilan_agri["eligible"]:
                self.memoire_lignes.append(f"  {lang['zk_rep_agri']}{bilan_agri['zakat_due_kg']:.1f}{lang['zk_unite_kg']}")
            if bilan_ovins["eligible"]:
                self.memoire_lignes.append(f"  {lang['zk_rep_el']}{bilan_ovins['moutons_dus']}{lang['zk_unite_tetes']}")

            self.lbl_res.config(text="\n".join(self.memoire_lignes), fg="#064e3b")
            self.btn_pdf.config(state="normal")

        except ValueError:
            messagebox.showerror(lang["err_titre"], lang["err_num"])

    def imprimer_certificat(self):
        # 🚨 FIX : On extrait le dictionnaire complet de l'identité, pas une simple chaîne
        identite_dict = self.app.obtenir_identite_saisie()
        if not identite_dict["nom"].strip():
            messagebox.showwarning("Hayaati", "Veuillez d'abord remplir le bloc de profil à gauche de l'écran.")
            return
        generer_certificat_pdf(identite_dict, "Zakat", self.app.madhhab_actif, self.app.devise_active, self.memoire_intrants, self.memoire_lignes)
