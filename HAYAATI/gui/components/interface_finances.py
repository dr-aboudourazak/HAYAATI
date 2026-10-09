"""
INTERFACE MATRICE DU PATRIMOINE GLOBAL LIVE (PARTIE 1)
Version 6.4 Stabilisée - Initialisation, "stock" commercial réintégré et grilles Material 3
"""
from __future__ import annotations
from datetime import datetime
import flet as ft
from gui.langues import DICTIONNAIRE_LANGUES
from gui.components.zakat_affichage import (
    MODES_IRRIGATION, libelle_irrigation, creer_menu_irrigation, creer_cellule_irrigation, actualiser_cours_en_ligne,
)

class EcranFinances(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.page_flet = app_reference.page
        
        # 🎯 FIX TECHNIQUE ET DOCTRINAL : Réintégration de "stock" de manière étanche dans les clés
        self.cles = [
            "immo", "auto", "stock", "liq", "creances", "dettes", "dettes_long_terme",
            "or_refuge_poids", "or_parure_poids", "or_cours", 
            "argent_refuge_poids", "argent_parure_poids", "argent_cours",
            "poids", "grain_cours", "ovins", "ovin_cours", "bovins", "bovin_cours", "chameaux", "chameau_cours"
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
            elif c in ["poids", "grain_cours", "ovins", "ovin_cours", "bovins", "bovin_cours", "chameaux", "chameau_cours"]:
                self.grille_agro.controls.append(cellule_formulaire)
            else:
                self.grille_avoirs.controls.append(cellule_formulaire)

        # 🌙 Hawl : date a laquelle le nisab a ete atteint (annee lunaire ~ 354 jours). Vide = non precisee.
        self.lbl_date_hawl = ft.Text(size=11, weight=ft.FontWeight.W_500, color="#4b5563")
        self.en_date_hawl = ft.TextField(
            value="", hint_text="AAAA-MM-JJ", height=40, text_size=13,
            border_radius=6, border_color=ft.Colors.GREY_400, bgcolor=ft.Colors.WHITE
        )
        self.grille_avoirs.controls.append(ft.Container(
            content=ft.Column([self.lbl_date_hawl, self.en_date_hawl], spacing=4), col={"xs": 12, "md": 6}))

        # 🌾 Mode d'irrigation (pluie 10 %, artificielle 5 %, mixte 7,5 %) : meme gabarit et memes couleurs
        # que les champs de saisie voisins ; l'aide est dans une cellule a part (plus de chevauchement).
        self.lbl_irrigation = ft.Text(size=11, weight=ft.FontWeight.W_500, color="#4b5563")
        self.cb_irrigation = creer_menu_irrigation(40, 13)
        (_cell_menu,) = creer_cellule_irrigation(self.lbl_irrigation, self.cb_irrigation, None, {"xs": 12, "md": 6})
        self.grille_agro.controls.insert(1, _cell_menu)

        # 🔄 Cours de l'or et de l'argent en ligne (la saisie manuelle reste toujours possible)
        self.btn_cours = ft.OutlinedButton(content=ft.Text("🔄", size=12), on_click=lambda _: self._lancer_actualisation_cours())
        self.lbl_cours_etat = ft.Text(size=10, italic=True, color="#6b7280")
        self.grille_metaux.controls.append(ft.Container(
            content=ft.Column([self.btn_cours, self.lbl_cours_etat], spacing=4), col={"xs": 12}))

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

        # 🎯 BOUTON RETOUR ÉMOJI UNIVERSEL VERS LE HUB INVENTAIRE
        self.btn_retour_hub = ft.IconButton(
            icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
            icon_color="#064e3b",
            icon_size=16,
            tooltip="↩️",
            on_click=lambda _: self.app.layout_central.basculer_vers_ecran("INVENTAIRE")
        )

        # Injection physique du bouton au sommet absolu de la colonne
        self.zone_defilement = ft.Column(
            controls=[self.btn_retour_hub, self.c_avoirs, self.c_metaux, self.c_agro, self.btn_sauver, self.c_res, self.btn_retour_hub],
            scroll=ft.ScrollMode.AUTO, spacing=15, expand=True
        )

        super().__init__(
            content=self.zone_defilement, expand=True, bgcolor="#f8fafc",
            padding=ft.Padding(left=15, right=15, top=15, bottom=15)
        )
        
        self.actualiser_donnees_affichage()

    def action_langue_finances(self, dic: dict):
        """Met à jour l'interface lors d'une modification linguistique globale."""
        self.traduire(dic)

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

        # 🎯 COUPLAGE INTERNATIONAUX DES STOCKS COMMERCIAUX POUR L'UTILISATEUR CONNECTÉ
        # On va lire la clé de stock officielle, avec repli intelligent s'il n'est pas encore présent.
        dict_labels = {
            "immo": f.get("immo_lbl", "Immobilisations / Terrains :"), 
            "auto": f.get("auto_lbl", "Actifs Mobiliers / Véhicules :"), 
            "stock": f.get("stock_lbl", "Stocks de Marchandises Commerciales :"), 
            "liq": f.get("liq_lbl", "Disponibilités Cash / Comptes :"), 
            "creances": f.get("creances_lbl", "Créances Actives Recouvrables :"), 
            "dettes": f.get("dettes_lbl", "Passif Exigible / Dettes :")
        }
        for k in ["immo", "auto", "stock", "liq", "creances", "dettes"]:
            if k in self.labels:
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
        self.labels["chameaux"].value = str(f.get("lbl_chameaux", "Chameaux :"))
        self.labels["dettes_long_terme"].value = str(f.get("lbl_dettes_long_terme", "Dont dettes à long terme (> 1 an) :"))
        self.lbl_date_hawl.value = str(f.get("lbl_date_hawl", "Date où le nisab a été atteint (AAAA-MM-JJ) :"))
        self.labels["bovin_cours"].value = str(f.get("valeur_bovins", "Cours :"))
        self.labels["chameau_cours"].value = str(f.get("valeur_chameaux", "Valeur d'un chameau (par tête) :"))

        # Mode d'irrigation : libelles traduits, selection conservee
        cle_irrigation = self.cb_irrigation.value if self.cb_irrigation.value in MODES_IRRIGATION else "pluie"
        self.lbl_irrigation.value = str(f.get("lbl_irrigation", "Irrigation des cultures :"))
        self.cb_irrigation.options.clear()
        for m in MODES_IRRIGATION:
            self.cb_irrigation.options.append(ft.dropdown.Option(key=m, text=libelle_irrigation(m, f)))
        self.cb_irrigation.value = cle_irrigation
        self._txt_finances = f
        if self.btn_cours.content:
            self.btn_cours.content.value = str(f.get("btn_cours_en_ligne", "🔄 Cours en ligne"))

        if self.page_flet:
            try:
                self.update()
            except Exception:
                pass

    def _lancer_actualisation_cours(self):
        """Bouton « Cours en ligne » : remplit les champs or / argent (modifiables ensuite)."""
        if self.page_flet:
            self.page_flet.run_task(self._actualiser_cours)

    async def _actualiser_cours(self):
        dev = str(getattr(self.app, "devise_active", "XOF") or "XOF")
        await actualiser_cours_en_ligne(self, self.entries["or_cours"], self.entries["argent_cours"],
                                        self.lbl_cours_etat, getattr(self, "_txt_finances", {}), dev)

    def sauvegarder(self):
        """Calcule les masses et exporte le dictionnaire d'inventaire vers le SyncEngine."""
        try:
            # Extraction et conversion sécurisée des saisies TextField Flet
            v = {c: float(self.entries[c].value.strip() or 0) for c in self.cles}
            v["irrigation_mode"] = self.cb_irrigation.value if self.cb_irrigation.value in MODES_IRRIGATION else "pluie"
            v["date_hawl"] = self.en_date_hawl.value.strip()
            
            v["or_poids"] = v["or_refuge_poids"] + v["or_parure_poids"]
            v["argent_poids"] = v["argent_refuge_poids"] + v["argent_parure_poids"]
            
            val_or = v["or_poids"] * v["or_cours"]
            val_arg = v["argent_poids"] * v["argent_cours"]
            v["or"] = val_or
            
            val_grain = v["poids"] * v["grain_cours"]
            val_ovin = v["ovins"] * v["ovin_cours"]
            val_bovin = v["bovins"] * v["bovin_cours"]
            # 08/10/2026 : valeur monétaire des chameaux. Sans effet sur la zakat
            # (qui se calcule sur le nombre de têtes), mais nécessaire au patrimoine
            # net et donc à la masse successorale.
            val_chameau = v["chameaux"] * v["chameau_cours"]
            total_agro = val_grain + val_ovin + val_bovin + val_chameau
            
            # 🎯 CALCUL DU PATRIMOINE GLOBAL SUCCESSORAL (HERITAGE) INCLUANT TOUT : IMMO + AUTO + STOCK
            brut = v["immo"] + v["auto"] + v["stock"] + v["liq"] + val_or + val_arg + v["creances"] + total_agro
            net_calcule = brut - v["dettes"]
            dev = getattr(self.app, "devise_active", "XOF")

            # 🌟 BLINDAGE DE SÉCURITÉ : Stockage sous forme de float et de chaîne pour parer à tout caprice SQLite/Flet
            v["net"] = float(net_calcule)
            
            # Concaténation de l'historique au sommet (Simule l'insertion 1.0 Tkinter)
            nouvelle_ligne = f"📅 [{datetime.now().strftime('%d/%m/%Y %H:%M')}] - Net: {net_calcule:.2f} {dev}\n"
            historique_existant = str(self.text_hist.value or "")
            self.text_hist.value = nouvelle_ligne + historique_existant
            v["historique"] = str(self.text_hist.value)
            
            if self.page_flet:
                self.update()

            # Persistance disque via le SyncEngine si session connectée
            if getattr(self.app, "est_mode_connecte", False) and getattr(self.app, "sync_engine", None):
                u_id = self.app.user_id_connecte
                
                # Sauvegarde dupliquée et étanche avec clé "net" validée dans les deux tables
                self.app.sync_engine.executer_sauvegarde_module(u_id, "FINANCES", v)
                self.app.sync_engine.executer_sauvegarde_module(u_id, "ZAKAT", v)
                
                # Optionnel : Forcer la mise à jour immédiate du dictionnaire en cache de l'app de l'Onboarding
                if hasattr(self.app, "txt_global"):
                    # Permet de rafraîchir à chaud sans déconnexion
                    pass
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

        mode_irr = data.get("irrigation_mode") or ("artificielle" if data.get("irrigation_artificielle_active") else "pluie")
        self.cb_irrigation.value = mode_irr if mode_irr in MODES_IRRIGATION else "pluie"
        self.en_date_hawl.value = str(data.get("date_hawl", "") or "")

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
        self.traduire(DICTIONNAIRE_LANGUES.actif)
        
        if getattr(self.app, "est_mode_connecte", False) and getattr(self.app, "sync_engine", None):
            u_id = self.app.user_id_connecte
            donnees_chargees = self.app.sync_engine.charger_donnees_module(u_id, "FINANCES")
            if donnees_chargees:
                self.injecter_donnees(donnees_chargees)
