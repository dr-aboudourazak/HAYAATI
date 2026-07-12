"""
INTERFACE DE L'ESPACE D'AUDIT COMPACTE VIA COMPILATION JSON (GUI/INTERFACE_AUDIT.PY)
Version 1.2 - Correction du traitement de l'index de sélection (Tuple Fix).
"""
import tkinter as tk
import os
import json

class EcranAudit(tk.Frame):
    def __init__(self, parent, app_reference):
        super().__init__(parent, bg="#f9fafb")
        self.app = app_reference
        self.data_complete = {}

        # Chargement sécurisé du fichier de données JSON
        chemin_json = os.path.join("gui", "dictionnaires", "audit_data.json")
        if os.path.exists(chemin_json):
            try:
                with open(chemin_json, "r", encoding="utf-8") as f:
                    self.data_complete = json.load(f)
            except Exception:
                pass

        # Éléments graphiques de l'interface
        self.lbl_titre = tk.Label(self, text="", font=("Helvetica", 13, "bold"), fg="#064e3b", bg="#f9fafb")
        self.lbl_titre.pack(pady=10)
        
        self.lbl_consigne = tk.Label(self, text="", font=("Helvetica", 9), fg="#4b5563", bg="#f9fafb")
        self.lbl_consigne.pack(pady=2)

        self.liste_categories = tk.Listbox(self, font=("Helvetica", 10), width=75, height=4, bd=1, relief="solid", bg="white", selectbackground="#064e3b", selectforeground="white")
        self.liste_categories.pack(pady=10, padx=25, fill="x")
        self.liste_categories.bind("<<ListboxSelect>>", self.afficher_texte_categorie)

        self.txt_reponse = tk.Text(self, font=("Helvetica", 10), bg="#f3f4f6", fg="#111827", wrap="word", bd=1, relief="solid", padx=12, pady=10, state="disabled")
        self.txt_reponse.pack(pady=10, padx=25, fill="both", expand=True)

        self.actualiser_contexte()

    def actualiser_contexte(self):
        """Lit la langue active et recharge dynamiquement la liste depuis le JSON."""
        langue = self.app.langue_active
        ctx = self.data_complete.get(langue, self.data_complete.get("FR", {"titre": "Audit", "consigne": "", "categories": []}))

        self.lbl_titre.config(text=ctx["titre"])
        self.lbl_consigne.config(text=ctx["consigne"])

        self.liste_categories.delete(0, tk.END)
        for cat in ctx["categories"]:
            self.liste_categories.insert(tk.END, f"  {cat['titre']}")
            
        self.txt_reponse.config(state="normal")
        self.txt_reponse.delete("1.0", tk.END)
        self.txt_reponse.config(state="disabled")

    def afficher_texte_categorie(self, event=None):
        selection = self.liste_categories.curselection()
        if not selection: 
            return
        
        # 🚨 CORRECTION CRUCIALE : Extraction du premier entier du tuple renvoyé par Tkinter
        index = selection[0]
        
        langue = self.app.langue_active
        ctx = self.data_complete.get(langue, self.data_complete.get("FR", {"categories": []}))
        
        # Injection propre du texte sacré et doctrinal dans le rectangle du bas
        self.txt_reponse.config(state="normal")
        self.txt_reponse.delete("1.0", tk.END)
        self.txt_reponse.insert(tk.END, ctx["categories"][index]["texte"])
        self.txt_reponse.config(state="disabled")
