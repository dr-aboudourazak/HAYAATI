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

        # 📂 BLOC DE CONFIGURATION : Grille responsive émulant le LabelFrame
        self.lbl_cadre_form = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.grille_candidats = ft.ResponsiveRow(spacing=10, run_spacing=12)
        
        self.cadre_form = ft.Container(
            content=ft.Column([
                self.lbl_cadre_form,
                self.grille_candidats
            ], spacing=8),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#064e3b")
        )

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
            def créer_ajusteur(champ_cible: ft.TextField, direction: int, limite_max: int):
                return lambda _: self.ajuster_compteur_sharia(champ_cible, direction, limite_max)

            btn_moins = ft.IconButton(
                icon=ft.Icons.REMOVE, icon_size=14, icon_color="#b91c1c", width=28, height=28,
                on_click=créer_ajusteur(self.entries[c], -1, max_limite)
            )
            btn_plus = ft.IconButton(
                icon=ft.Icons.ADD, icon_size=14, icon_color="#166534", width=28, height=28,
                on_click=créer_ajusteur(self.entries[c], 1, max_limite)
            )

            # Cellule horizontale compacte pour chaque membre de l'arbre
            cellule_spinbox = ft.Container(
                content=ft.Column([
                    self.labels[c],
                    ft.Row([btn_moins, self.entries[c], btn_plus], spacing=2, alignment=ft.MainAxisAlignment.START)
                ], spacing=4),
                col={"xs": 12, "sm": 6, "md": 3} # 🎯 GRID HARMONISÉE : 4 COLONNES PC / 1 MOBILE
            )
            self.grille_candidats.controls.append(cellule_spinbox)

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

        self.layout_arbre = ft.Column([
            self.cadre_form,
            self.btn_sauver,
            self.c_notif
        ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)

        super().__init__(
            content=self.layout_arbre, expand=True, bgcolor="#f8fafc",
            padding=ft.Padding(left=15, right=15, top=15, bottom=15)
        )

        if hasattr(DICTIONNAIRE_LANGUES, "moteur_i18n"):
            DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_langue)
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

            # Sauvegarde de la structure consolidée pour le HeritageEngine
            if hasattr(self.app, "sync_engine") and self.app.sync_engine:
                self.app.sync_engine.executer_sauvegarde_module(
                    self.app.user_id_connecte, "ARBRE_FAMILIAL", arbre_compile
                )
                
            self.lbl_status.value = "✓ Arbre familial synchronisé et mis à jour."
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
        """Réinjecte la sauvegarde de l'arbre au sein des compteurs d'interface."""
        if not data: 
            return
        for c in self.candidats:
            self.entries[c].value = str(data.get(c, "0"))
        if self.page_flet:
            try: self.update()
            except Exception: pass

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
