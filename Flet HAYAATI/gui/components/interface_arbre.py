"""
INTERFACE DE SUIVI DE L'ARBRE GÉNÉALOGIQUE SUCCESSORAL INTERACTIF (GUI/COMPONENTS/INTERFACE_ARBRE.PY)
Version Finale Intégrale Statique - Totalement compatible Flet 0.86.2, Python 3.14 & APK Android
"""
from __future__ import annotations
import flet as ft
from gui.langues import DICTIONNAIRE_LANGUES

class EcranArbre(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.page_flet = app_reference.page
        self.mode_mobile = None
        
        # 🎯 EXHAUSTIVITÉ ET SÉPARATION CANONIQUE STRICTE DES 22 CONJOINTS ET PARENTS
        self.candidats = [
            "epoux", "epouse", "fils", "fille", "pere", "mere", "grand_pere", "grand_mere",
            "petit_fils", "petite_fille", "frere_germain", "soeur_germaine", "frere_paternel",
            "soeur_paternelle", "frere_uterin", "soeur_uterine", "fils_frere_germain",
            "fils_frere_paternel", "oncle_germain", "oncle_paternel", "cousin_germain", "cousin_paternel"
        ]
        self.labels: dict[str, ft.Text] = {}
        self.entries: dict[str, ft.TextField] = {}

        # 🎯 DICTIONNAIRES DE PERSISTANCE DES BOUTONS POUR VERROUILLAGE DYNAMIQUE
        self.boutons_famille_plus: dict[str, ft.IconButton] = {}
        self.boutons_famille_moins: dict[str, ft.IconButton] = {}

        # 📂 BLOC DE CONFIGURATION : Grille responsive émulant le LabelFrame
        self.lbl_cadre_form = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.grille_candidats = ft.ResponsiveRow(spacing=10, run_spacing=12)
        
        # 🎯 LOGIQUE MATÉRIELLE DU CHOIX DE SEXE AVEC VERROU DE CONJOINT DISCORDANT
        self.sexe_defunt_actif = "HOMME" 
        
        def selectionner_sexe(sexe_choisi):
            self.sexe_defunt_actif = sexe_choisi
            self.btn_homme.bgcolor = "#e0f2fe" if sexe_choisi == "HOMME" else "#f3f4f6"
            self.btn_homme.border = ft.Border.all(2, "#0284c7") if sexe_choisi == "HOMME" else None
            self.btn_femme.bgcolor = "#fce7f3" if sexe_choisi == "FEMME" else "#f3f4f6"
            self.btn_femme.border = ft.Border.all(2, "#db2777") if sexe_choisi == "FEMME" else None
            
            # Application synchrone des verrous à chaud
            if sexe_choisi == "HOMME":
                self.entries["epoux"].value = "0"
                if "epoux" in self.boutons_famille_plus:
                    self.boutons_famille_plus["epoux"].disabled = True
                    self.boutons_famille_moins["epoux"].disabled = True
                if "epouse" in self.boutons_famille_plus:
                    self.boutons_famille_plus["epouse"].disabled = False
                    self.boutons_famille_moins["epouse"].disabled = False
            else:
                self.entries["epouse"].value = "0"
                if "epouse" in self.boutons_famille_plus:
                    self.boutons_famille_plus["epouse"].disabled = True
                    self.boutons_famille_moins["epouse"].disabled = True
                if "epoux" in self.boutons_famille_plus:
                    self.boutons_famille_plus["epoux"].disabled = False
                    self.boutons_famille_moins["epoux"].disabled = False
            try: self.update()
            except Exception: pass

        # Composants visuels muets auto-adaptatifs (Homme / Femme)
        self.btn_homme = ft.Container(
            content=ft.Text("👨", size=20, text_align=ft.TextAlign.CENTER),
            bgcolor="#e0f2fe", border=ft.Border.all(2, "#0284c7"), border_radius=6,
            padding=ft.Padding(0, 4, 0, 0), width=50, height=38, on_click=lambda _: selectionner_sexe("HOMME")
        )
        self.btn_femme = ft.Container(
            content=ft.Text("👩", size=20, text_align=ft.TextAlign.CENTER),
            bgcolor="#f3f4f6", border_radius=6,
            padding=ft.Padding(0, 4, 0, 0), width=50, height=38, on_click=lambda _: selectionner_sexe("FEMME")
        )
        
        self.lbl_sexe_titre = ft.Text(value=" ", size=11, color="#4b5563")
        bloc_sexe_boutons = ft.Container(
            content=ft.Column([
                self.lbl_sexe_titre, 
                ft.Row([self.btn_homme, self.btn_femme], spacing=5)
            ], spacing=4), col={"xs": 12, "sm": 4, "md": 1.6}
        )

        # Insertion de la ligne de genre tout au début de la grille d'héritage connectée
        self.grille_candidats.controls.append(bloc_sexe_boutons)

        # Génération dynamique des compteurs (Spinbox émulés en Flet)
        for c in self.candidats:
            self.labels[c] = ft.Text(size=11, weight=ft.FontWeight.W_500, color="#4b5563")
            
            # Définition des plafonds doctrinaux par catégorie technique
            max_limite = 1 if c in ["epoux", "pere", "mere", "grand_pere", "grand_mere"] else 4 if c == "epouse" else 20
            
            self.entries[c] = ft.TextField(
                value="0", width=40, height=35, text_size=12, text_align=ft.TextAlign.CENTER,
                read_only=True, border_radius=4, border_color=ft.Colors.GREY_400, bgcolor=ft.Colors.WHITE,
                content_padding=ft.Padding(0, 0, 0, 0)
            )
            setattr(self, f"sb_{c}", self.entries[c])

            # Fonctions d'incrémentation sécurisées pour l'IHM
            def créer_ajusteur(champ_cible=self.entries[c], limite_max=max_limite):
                return lambda direction: self.ajuster_compteur_sharia(champ_cible, direction, limite_max)

            btn_moins = ft.IconButton(
                icon=ft.Icons.REMOVE, icon_size=14, icon_color="#b91c1c", width=28, height=28,
                on_click=lambda _, a=créer_ajusteur(): a(-1)
            )
            btn_plus = ft.IconButton(
                icon=ft.Icons.ADD, icon_size=14, icon_color="#166534", width=28, height=28,
                on_click=lambda _, a=créer_ajusteur(): a(1)
            )

            # Captation des instances pour le verrouillage dynamique à chaud
            self.boutons_famille_moins[c] = btn_moins
            self.boutons_famille_plus[c] = btn_plus

            # Cellule horizontale compacte pour chaque membre de l'arbre
            cellule_spinbox = ft.Container(
                content=ft.Column([
                    self.labels[c],
                    ft.Row([btn_moins, self.entries[c], btn_plus], spacing=2, alignment=ft.MainAxisAlignment.START)
                ], spacing=4),
                col={"xs": 12, "sm": 6, "md": 3}
            )
            self.grille_candidats.controls.append(cellule_spinbox)

        # Désactivation initiale réflexe de l'Époux (Sexe par défaut : HOMME)
        self.boutons_famille_plus["epoux"].disabled = True
        self.boutons_famille_moins["epoux"].disabled = True

        self.cadre_form = ft.Container(
            content=ft.Column([self.lbl_cadre_form, self.grille_candidats], spacing=8),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#064e3b")
        )

        # 🎯 FIX FIQH AVANCÉ : Variables d'états pour les scénarios d'extensions
        self.actif_khountha = False
        self.actif_zawil_arham = False

        def basculer_scénario_khountha(e):
            self.actif_khountha = not self.actif_khountha
            tile_khountha.bgcolor = "#fef3c7" if self.actif_khountha else "#f3f4f6"
            tile_khountha.border = ft.Border.all(2, "#d97706") if self.actif_khountha else None
            # Doctrinal : Si Khountha est actif, on peut désactiver temporairement les autres pour le test
            self.update()

        def basculer_scénario_arham(e):
            self.actif_zawil_arham = not self.actif_zawil_arham
            
            # 🎯 BLINDAGE ATTRIBUTE_ERROR : Gestion de l'état graphique de la tuile en arabe
            if hasattr(self, "tile_arham") and self.tile_arham:
                self.tile_arham.bgcolor = "#e0f2fe" if self.actif_zawil_arham else "#f3f4f6"
                self.tile_arham.border = ft.Border.all(2, "#0284c7") if self.actif_zawil_arham else None
            elif e and hasattr(e, "control") and e.control:
                e.control.bgcolor = "#e0f2fe" if self.actif_zawil_arham else "#f3f4f6"
                e.control.border = ft.Border.all(2, "#0284c7") if self.actif_zawil_arham else None
            
            # 🎯 VERROUILLAGE SÉLECTIF POUR LA BASE LIVE :
            # On gère l'accessibilité des boutons SANS écraser ni modifier la valeur textuelle affichée !
            for c in self.candidats:
                if self.actif_zawil_arham:
                    # Le frère utérin et la sœur utérine restent ouverts au clic
                    if c not in ["frere_uterin", "soeur_uterine"]:
                        # 🎯 RECTIFICATION RADICALE : Suppression de self.entries[c].value = "0" 
                        # pour ne pas détruire les saisies lors des autres simulations standards
                        if c in self.boutons_famille_plus:
                            self.boutons_famille_plus[c].disabled = True
                            self.boutons_famille_moins[c].disabled = True
                    else:
                        if c in self.boutons_famille_plus:
                            self.boutons_famille_plus[c].disabled = False
                            self.boutons_famille_moins[c].disabled = False
                else:
                    # En mode normal, on libère les boutons de l'arbre familial
                    if c in self.boutons_famille_plus:
                        # Préservation du verrou du genre sur le conjoint opposé
                        if c == "epoux" and getattr(self, "sexe_defunt_actif", "HOMME") == "HOMME":
                            continue
                        if c == "epouse" and getattr(self, "sexe_defunt_actif", "HOMME") == "FEMME":
                            continue
                        self.boutons_famille_plus[c].disabled = False
                        self.boutons_famille_moins[c].disabled = False
            try:
                self.update()
            except Exception:
                pass

        # Tuiles de prestige graphiques autonomes         
        tile_khountha = ft.Container(
            content=ft.Row([
                ft.Text("🧬", size=18),
                ft.Text("مسألة الخنثى المشكل", size=11, weight=ft.FontWeight.W_500, color="#1e293b")
            ], spacing=8),
            bgcolor="#f3f4f6", border_radius=6, padding=10, expand=True, on_click=basculer_scénario_khountha
        )

        tile_arham = ft.Container(
            content=ft.Row([
                ft.Text("🌿", size=18),
                ft.Text("مسألة ذوي الأرحام", size=11, weight=ft.FontWeight.W_500, color="#1e293b")
            ], spacing=8),
            bgcolor="#f3f4f6", border_radius=6, padding=10, expand=True, on_click=basculer_scénario_arham
        )

        # Grille responsive pour afficher les deux cas d'école côte à côte
        self.grille_extensions_fiqh = ft.ResponsiveRow([
            ft.Container(content=tile_khountha, col={"xs": 12, "md": 6}),
            ft.Container(content=tile_arham, col={"xs": 12, "md": 6})
        ], spacing=10)

        # Définition du widget de sécurité doctrinale 
        txt_onb = DICTIONNAIRE_LANGUES.actif.get("heritage", {})
        self.txt_indignite = ft.Text(
            value=str(txt_onb.get("lbl_alerte_indignite", "⚠️")),
            size=14, color="#b45309", italic=True, weight=ft.FontWeight.W_500
        )

        # Bouton d'action principal
        self.btn_sauver = ft.ElevatedButton(
            content=ft.Text("Enregistrer", size=13, weight=ft.FontWeight.BOLD),
            bgcolor="#064e3b", color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
            on_click=lambda _: self.enregistrer_arbre_db()
        )

        # Zone basse de notification et confirmation
        self.lbl_status = ft.Text(size=12, italic=True, color="#4b5563", text_align=ft.TextAlign.CENTER)
        self.c_notif = ft.Container(
            content=self.lbl_status, bgcolor="#f3f4f6", padding=10, border_radius=6, alignment=ft.Alignment(0, 0)
        )

        # 🎯 BOUTON RETOUR ÉMOJI UNIVERSEL VERS LE HUB INVENTAIRE
        self.btn_retour_hub = ft.IconButton(
            icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED, icon_color="#064e3b", icon_size=16, tooltip="↩️",
            on_click=lambda _: self.app.layout_central.basculer_vers_ecran("INVENTAIRE")
        )

        self.layout_arbre = ft.Column([
            self.btn_retour_hub, self.cadre_form, self.grille_extensions_fiqh, self.txt_indignite,
            self.btn_sauver, self.c_notif, self.btn_retour_hub
        ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)

        super().__init__(
            content=self.layout_arbre, expand=True, bgcolor="#f8fafc",
            padding=ft.Padding(left=15, right=15, top=15, bottom=15)
        )

        self.actualiser_donnees_affichage()

    def ajuster_compteur_sharia(self, champ_texte: ft.TextField, direction: int, limite_max: int):
        """Incrémente ou décrémente la valeur du champ en respectant les verrous du Fiqh."""
        valeur_actuelle = int(champ_texte.value or 0)
        nouvelle_valeur = valeur_actuelle + direction
        if 0 <= nouvelle_valeur <= limite_max:
            champ_texte.value = str(nouvelle_valeur)
            champ_texte.update()

    def action_langue(self, dic: dict):
        """Met à jour l'interface lors d'une modification linguistique globale."""
        self.traduire_page(dic)
        
    def traduire_page(self, dic: dict):
        """Met à jour dynamiquement l'intégralité des textes du module de l'arbre."""
        if not dic:
            return
        a = dic.get("arbre", {})
        h = dic.get("heritage", {})
        
        self.lbl_cadre_form.value = str(a.get("cadre_ajout", "Cellule Familiale"))
        if self.btn_sauver.content:
            self.btn_sauver.content.value = str(a.get("btn_ajouter_membre", "Enregistrer"))
        
        # Alignement des 21 bénéficiaires depuis le sous-bloc législatif
        candidats_json = h.get("candidats", {})
        for c in self.candidats:
            self.labels[c].value = f"{candidats_json.get(c, c)} :"

        if self.page_flet:
            try: self.update()
            except Exception: pass

    def enregistrer_arbre_db(self):
        """Compile la grille de l'arbre, valide la Sharia et sauvegarde en direct via SyncEngine."""
        if not getattr(self.app, "est_mode_connecte", False):
            self.lbl_status.value = "❌ Espace déconnecté."
            self.c_notif.bgcolor = "#fee2e2"
            self.lbl_status.color = "#991b1b"
            self.update()
            return
            
        try:
            arbre_compile = {}
            for c in self.candidats:
                valeur = int(self.entries[c].value or 0)
                if valeur > 0:
                    arbre_compile[c] = valeur

            # 🎯 GARDE-FOU CANONIQUE ABSOLU DU FIQH : Interdiction de double-conjoint
            if "epoux" in arbre_compile and "epouse" in arbre_compile:
                self.lbl_status.value = "❌ Erreur Conjoints : Double présence impossible selon la Sharia."
                self.c_notif.bgcolor = "#fee2e2"
                self.lbl_status.color = "#991b1b"
                self.update()
                return

            # 🎯 RÉRETABLISSEMENT STRICT : On lit uniquement la valeur réelle de la tuile cliquée (0% détection automatique erronée)
            is_arham_detecte = getattr(self, "actif_zawil_arham", False)

            # 🎯 CAPTURE ÉTANCHE DU FIQH AVANCÉ : Enregistrement des métadonnées rituelles
            # Blindage par getattr pour éliminer définitivement tout risque de transmission vide
            arbre_compile["sexe_defunt"] = getattr(self, "sexe_defunt_actif", "HOMME")
            arbre_compile["cas_khountha_actif"] = getattr(self, "actif_khountha", False)
            arbre_compile["cas_zawil_arham_actif"] = is_arham_detecte

            # Sauvegarde de la structure consolidée pour le HeritageEngine
            if hasattr(self.app, "sync_engine") and self.app.sync_engine:
                self.app.sync_engine.executer_sauvegarde_module(
                    self.app.user_id_connecte, "ARBRE_FAMILIAL", arbre_compile
                )
                
            self.lbl_status.value = "✓ Arbre familial et options du Fiqh synchronisés."
            self.c_notif.bgcolor = "#d1fae5"
            self.lbl_status.color = "#064e3b"
            
            if hasattr(self.app, "declencher_changement_global"):
                self.app.declencher_changement_global()
            else:
                self.update()
                
        except Exception as e:
            self.lbl_status.value = f"❌ Erreur de sauvegarde : {str(e)}"
            self.c_notif.bgcolor = "#fee2e2"
            self.lbl_status.color = "#b91c1c"
            self.update()

    def injecter_donnees(self, data: dict | None):
        """Réinjecte la sauvegarde de l'arbre au sein des compteurs d'interface et rafraîchit les icônes."""
        if not data: 
            return
            
        # 1. Hydratation des 21 compteurs de famille d'origine
        for c in self.candidats:
            self.entries[c].value = str(data.get(c, "0"))
            
        # 2. 🎯 RE-HYDRATATION DES ÉTATS ET VUES DES CONFIGURATIONS DE FIQH AVANCÉ
        self.sexe_defunt_actif = data.get("sexe_defunt", "HOMME")
        self.actif_khountha = bool(data.get("cas_khountha_actif", False))
        self.actif_zawil_arham = bool(data.get("cas_zawil_arham_actif", False))
        
        # Actualisation visuelle des tuiles Homme / Femme
        self.btn_homme.bgcolor = "#e0f2fe" if self.sexe_defunt_actif == "HOMME" else "#f3f4f6"
        self.btn_homme.border = ft.Border.all(2, "#0284c7") if self.sexe_defunt_actif == "HOMME" else None
        self.btn_femme.bgcolor = "#fce7f3" if self.sexe_defunt_actif == "FEMME" else "#f3f4f6"
        self.btn_femme.border = ft.Border.all(2, "#db2777") if self.sexe_defunt_actif == "FEMME" else None
        
        # Actualisation visuelle des boutons scénarios spéciaux (🧬 et 🌿)
        if hasattr(self, "tile_khountha") and self.tile_khountha:
            self.tile_khountha.bgcolor = "#fef3c7" if self.actif_khountha else "#f3f4f6"
            self.tile_khountha.border = ft.Border.all(2, "#d97706") if self.actif_khountha else None
            
        if hasattr(self, "tile_arham") and self.tile_arham:
            self.tile_arham.bgcolor = "#e0f2fe" if self.actif_zawil_arham else "#f3f4f6"
            self.tile_arham.border = ft.Border.all(2, "#0284c7") if self.actif_zawil_arham else None

        # Desactivation/Activation reflexe des boutons de conjoints selon le sexe chargé
        if "epoux" in self.boutons_famille_plus and "epouse" in self.boutons_famille_plus:
            if self.sexe_defunt_actif == "HOMME":
                self.boutons_famille_plus["epoux"].disabled = True
                self.boutons_famille_moins["epoux"].disabled = True
                self.boutons_famille_plus["epouse"].disabled = False
                self.boutons_famille_moins["epouse"].disabled = False
            else:
                self.boutons_famille_plus["epouse"].disabled = True
                self.boutons_famille_moins["epouse"].disabled = True
                self.boutons_famille_plus["epoux"].disabled = False
                self.boutons_famille_moins["epoux"].disabled = False

        if self.page_flet:
            try: 
                self.update()
            except Exception: 
                pass

    def changer_langue(self, n_lang: str):
        """Liaison avec la propagation descendante du Layout central."""
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)

    def actualiser_donnees_affichage(self):
        """Recharge l'arbre depuis la base de données à l'apparition de l'écran."""
        self.lbl_status.value = ""
        self.c_notif.bgcolor = "#f3f4f6"
        self.lbl_status.color = "#4b5563"
        
        if getattr(self.app, "est_mode_connecte", False) and getattr(self.app, "sync_engine", None):
            arbre_sauvegarde = self.app.sync_engine.charger_donnees_module(
                self.app.user_id_connecte, "ARBRE_FAMILIAL"
            )
            self.injecter_donnees(arbre_sauvegarde)
            
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)

    def actualiser_contexte(self):
        """Alias pour le routeur central."""
        self.actualiser_donnees_affichage()
