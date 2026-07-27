"""
INTERFACE MATRICE DU PATRIMOINE GLOBAL LIVE (PARTIE 1)
Version 6.3 - Initialisation, agencement des cadres et grille responsive sécurisée Flet 0.86.2
"""
from __future__ import annotations
from datetime import datetime  # 🎯 FIX PYLANCE : Importation requise pour l'historique de calculs
import flet as ft
from gui.langues import DICTIONNAIRE_LANGUES

class EcranFinances(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.page_flet = app_reference.page
        
        # Clés techniques indispensables au moteur de calcul
        self.cles = [
            "immo", "auto", "liq", "creances", "dettes",
            "or_refuge_poids", "or_parure_poids", "or_cours", 
            "argent_refuge_poids", "argent_parure_poids", "argent_cours",
            "poids", "grain_cours", "ovins", "ovin_cours", "bovins", "bovin_cours"
        ]
        self.labels: dict[str, ft.Text] = {}
        self.entries: dict[str, ft.TextField] = {}

        # 📂 INITIALISATION DES CONTENEURS COMPACTS ET GRILLES RESPONSIVES
        self.lbl_cadre_avoirs = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.grille_avoirs = ft.ResponsiveRow(spacing=15, run_spacing=10)
        self.c_avoirs = ft.Container(
            content=ft.Column([self.lbl_cadre_avoirs, self.grille_avoirs], spacing=8),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#064e3b")
        )

        self.lbl_cadre_metaux = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.grille_metaux = ft.ResponsiveRow(spacing=15, run_spacing=10)
        self.c_metaux = ft.Container(
            content=ft.Column([self.lbl_cadre_metaux, self.grille_metaux], spacing=8),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#064e3b")
        )

        self.lbl_cadre_agro = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.grille_agro = ft.ResponsiveRow(spacing=15, run_spacing=10)
        self.c_agro = ft.Container(
            content=ft.Column([self.lbl_cadre_agro, self.grille_agro], spacing=8),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#064e3b")
        )

        # Génération dynamique des entrées de formulaire et étiquettes associées
        for c in self.cles:
            self.labels[c] = ft.Text(size=11, weight=ft.FontWeight.W_500, color="#4b5563")
            self.entries[c] = ft.TextField(
                width=None, height=40, text_size=13, value="0",
                border_radius=6, border_color=ft.Colors.GREY_400, bgcolor=ft.Colors.WHITE
            )
            setattr(self, f"en_{c}", self.entries[c])

            # Routage chirurgical des composants dans la grille de répartition
            cellule_formulaire = ft.Container(content=ft.Column([self.labels[c], self.entries[c]], spacing=4), col={"xs": 12, "md": 6})
            
            if "or" in c or "argent" in c:
                self.grille_metaux.controls.append(cellule_formulaire)
            elif c in ["poids", "grain_cours", "ovins", "ovin_cours", "bovins", "bovin_cours"]:
                self.grille_agro.controls.append(cellule_formulaire)
            else:
                self.grille_avoirs.controls.append(cellule_formulaire)

        # Bouton d'action maître (Syntaxe immunisée Python 3.14)
        self.btn_sauver = ft.ElevatedButton(
            content=ft.Text("Enregistrer", size=13, weight=ft.FontWeight.BOLD),
            bgcolor="#064e3b", color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
            on_click=lambda _: self.sauvegarder()
        )

        # Zone d'affichage du bilan et historique des purifications (Simule le widget Text Tkinter)
        self.lbl_cadre_res = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.text_hist = ft.TextField(
            multiline=True, min_lines=4, max_lines=6, text_size=12, read_only=True,
            border_color=ft.Colors.GREY_400, bgcolor="#f9fafb"
        )
        self.c_res = ft.Container(
            content=ft.Column([self.lbl_cadre_res, self.text_hist], spacing=6),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#064e3b")
        )

        # Structure de défilement principale de l'IHM connectée
        self.zone_defilement = ft.Column(
            controls=[self.c_avoirs, self.c_metaux, self.c_agro, self.btn_sauver, self.c_res],
            scroll=ft.ScrollMode.AUTO, spacing=15, expand=True
        )

        super().__init__(
            content=self.zone_defilement, expand=True, bgcolor="#f8fafc",
            padding=ft.Padding(left=15, right=15, top=15, bottom=15)
        )

        # Branchement direct et abonnement au gestionnaire linguistique i18n
        if hasattr(DICTIONNAIRE_LANGUES, "moteur_i18n"):
            DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_langue_finances)
        self.actualiser_donnees_affichage()

    def action_langue_finances(self, dic: dict):
        """Met à jour l'interface lors d'une modification linguistique globale."""
        self.traduire(dic)

    # ============================================================
    # 🎯 PARTIE 2/2 : TRADUCTION, ALGORITHME ET SAUVEGARDE SQLITE/SYNC
    # ============================================================

    def traduire(self, dic: dict):
        """Met à jour dynamiquement tous les libellés et structures i18n de la matrice de patrimoine."""
        if not dic:
            return
            
        f = dic.get("finances", {})
        z = dic.get("zakat", {})
        
        # Traduction des titres de cadres émulés
        self.lbl_cadre_avoirs.value = str(f.get("cadre_liquide", "Patrimoine"))
        self.lbl_cadre_metaux.value = str(f.get("cadre_metaux", "Métaux"))
        self.lbl_cadre_agro.value = str(f.get("cadre_agropastoral", "Élevage"))
        self.lbl_cadre_res.value = str(dic.get("audit", {}).get("titre_graphique_evolution", "History"))
        
        # Mise à jour sécurisée du bouton d'action principal (Python 3.14)
        if self.btn_sauver.content:
            self.btn_sauver.content.value = str(f.get("btn_sauvegarder", "Enregistrer"))
        
        # Mappage strict des clés i18n d'actifs liquides et dettes
        dict_labels = {
            "immo": f.get("immo_lbl", "Immobilisations / Terrains :"), 
            "auto": f.get("auto_lbl", "Actifs Mobiliers / Véhicules :"), 
            "liq": f.get("liq_lbl", "Disponibilités Cash / Comptes :"), 
            "creances": f.get("creances_lbl", "Créances Actives Recouvrables :"), 
            "dettes": f.get("dettes_lbl", "Passif Exigible / Dettes :")
        }
        for k in ["immo", "auto", "liq", "creances", "dettes"]:
            self.labels[k].value = str(dict_labels[k])
        
        # Mappage de la matrice des métaux précieux
        self.labels["or_refuge_poids"].value = str(f.get("lbl_or_refuge", "Or Refuge (g) :"))
        self.labels["or_parure_poids"].value = str(f.get("lbl_or_parures", "Or Parure (g) :"))
        self.labels["or_cours"].value = str(z.get("lbl_cours_or", "Cours Or :"))
        self.labels["argent_refuge_poids"].value = str(f.get("lbl_argent_refuge", "Argent Refuge (g) :"))
        self.labels["argent_parure_poids"].value = str(f.get("lbl_argent_parures", "Argent Parure (g) :"))
        self.labels["argent_cours"].value = str(z.get("lbl_cours_argent", "Cours Argent :"))
        
        # Mappage du secteur Agro-Pastoral et Élevage
        self.labels["poids"].value = str(f.get("lbl_grain", "Grain (Kg) :"))
        self.labels["grain_cours"].value = str(f.get("valeur_grain", "Cours :"))
        self.labels["ovins"].value = str(f.get("lbl_moutons", "Moutons :"))
        self.labels["ovin_cours"].value = str(f.get("valeur_moutons", "Cours :"))
        self.labels["bovins"].value = str(f.get("lbl_bovins", "Bovins :"))
        self.labels["bovin_cours"].value = str(f.get("valeur_bovins", "Cours :"))

        if self.page_flet:
            try:
                self.update()
            except Exception:
                pass

    def sauvegarder(self):
        """Calcule les masses et exporte le dictionnaire d'inventaire vers le SyncEngine."""
        try:
            # Extraction et conversion sécurisée des saisiesTextField Flet
            v = {c: float(self.entries[c].value.strip() or 0) for c in self.cles}
            
            v["or_poids"] = v["or_refuge_poids"] + v["or_parure_poids"]
            v["argent_poids"] = v["argent_refuge_poids"] + v["argent_parure_poids"]
            
            val_or = v["or_poids"] * v["or_cours"]
            val_arg = v["argent_poids"] * v["argent_cours"]
            v["or"] = val_or
            
            val_grain = v["poids"] * v["grain_cours"]
            val_ovin = v["ovins"] * v["ovin_cours"]
            val_bovin = v["bovins"] * v["bovin_cours"]
            total_agro = val_grain + val_ovin + val_bovin
            
            brut = v["immo"] + v["auto"] + v["liq"] + val_or + val_arg + v["creances"] + total_agro
            net = brut - v["dettes"]
            dev = getattr(self.app, "devise_active", "XOF")
            
            # Concaténation de l'historique au sommet (Simule l'insertion 1.0 Tkinter)
            nouvelle_ligne = f"📅 [{datetime.now().strftime('%d/%m/%Y %H:%M')}] - Net: {net:.2f} {dev}\n"
            historique_existant = str(self.text_hist.value or "")
            self.text_hist.value = nouvelle_ligne + historique_existant
            
            if self.page_flet:
                self.update()

            # Persistance disque via le SyncEngine si session connectée
            if getattr(self.app, "est_mode_connecte", False) and getattr(self.app, "sync_engine", None):
                v["historique"] = str(self.text_hist.value)
                u_id = self.app.user_id_connecte
                self.app.sync_engine.executer_sauvegarde_module(u_id, "FINANCES", v)
                self.app.sync_engine.executer_sauvegarde_module(u_id, "ZAKAT", v)
        except Exception:
            pass

    def injecter_donnees(self, data: dict | None):
        """Hydrate réactivement les boîtes de dialogue à partir d'un dictionnaire de données."""
        if not data:
            return
            
        for c in self.cles:
            if c in data:
                self.entries[c].value = str(data.get(c, "0"))
        
        # Sécurité d'arbitrage de garde fou pour le Nisab par défaut
        try:
            if float(self.entries["or_refuge_poids"].value or 0) == 85.0:
                if "or_refuge_poids" not in data:
                    self.entries["or_refuge_poids"].value = "0"
        except Exception:
            pass

        self.text_hist.value = str(data.get("historique", ""))
        if self.page_flet:
            try:
                self.update()
            except Exception:
                pass

    def changer_langue(self, n_lang: str): 
        """Méthode invoquée par la propagation descendante du Layout central."""
        self.traduire(DICTIONNAIRE_LANGUES.actif)
        
    def actualiser_donnees_affichage(self):
        """Cycle de vie : Force la traduction instantanée et charge l'historique de l'auditeur."""
        # 🎯 FIX QUANTIQUE : On applique d'abord les étiquettes linguistiques pour éviter les champs anonymes
        self.traduire(DICTIONNAIRE_LANGUES.actif)
        
        if getattr(self.app, "est_mode_connecte", False) and getattr(self.app, "sync_engine", None):
            u_id = self.app.user_id_connecte
            donnees_chargees = self.app.sync_engine.charger_donnees_module(u_id, "FINANCES")
            if donnees_chargees:
                self.injecter_donnees(donnees_chargees)
