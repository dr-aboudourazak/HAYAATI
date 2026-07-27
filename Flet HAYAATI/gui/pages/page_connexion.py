"""
PAGE DE CONNEXION ET CERTIFICATION DOCTRINALE CINKASSÉ (GUI/PAGES/PAGE_CONNEXION.PY)
Version Finale Intégrale Statique - Totalement compatible Flet 0.86.2, Python 3.14 & APK Android
"""
from __future__ import annotations
import flet as ft
from gui.langues import DICTIONNAIRE_LANGUES

class PageConnexion(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.page_flet = app_reference.page
        
        # --- 1. INSTANCIATION DES COMPOSANTS GRAPHIQUES MATERIAL 3 ---
        self.lbl_titre = ft.Text(size=20, weight=ft.FontWeight.BOLD, color="#064e3b")

        # Panneau d'homologation doctrinale de Cinkassé (Togo)
        self.lbl_cadre_annonce = ft.Text(size=11, weight=ft.FontWeight.BOLD, color="#d97706")
        self.lbl_bienvenue_conseil = ft.Text(size=12, color="#374151", text_align=ft.TextAlign.CENTER)
        
        self.c_annonce_officielle = ft.Container(
            content=ft.Column([
                self.lbl_cadre_annonce,
                self.lbl_bienvenue_conseil
            ], spacing=6, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor="#f9fafb", padding=12, border_radius=8, border=ft.Border.all(1, "#d97706")
        )

        # Formulaire de saisie d'authentification
        self.lbl_user = ft.Text(size=11, weight=ft.FontWeight.BOLD, color="#4b5563")
        self.en_login = ft.TextField(
            height=40, text_size=13, border_radius=6,
            border_color=ft.Colors.GREY_400, bgcolor=ft.Colors.WHITE
        )

        self.lbl_pass = ft.Text(size=11, weight=ft.FontWeight.BOLD, color="#4b5563")
        self.en_password = ft.TextField(
            height=40, text_size=13, border_radius=6, password=True, can_reveal_password=True,
            border_color=ft.Colors.GREY_400, bgcolor=ft.Colors.WHITE
        )

        # Boutons d'accès d'identité (Conformes Python 3.14 content=ft.Text)
        self.btn_valider = ft.ElevatedButton(
            content=ft.Text("Se connecter", size=13, weight=ft.FontWeight.BOLD),
            bgcolor="#064e3b", color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
            on_click=lambda _: self.traiter_tentative_connexion()
        )

        self.btn_bascule = ft.TextButton(
            content=ft.Text("S'inscrire", size=12, style=ft.TextStyle(decoration=ft.TextDecoration.UNDERLINE)),
            style=ft.ButtonStyle(color="#0f766e"),
            on_click=lambda _: self.app.basculer_ecran("INSCRIPTION")
        )

        # Notification d'erreur ou statut de session
        self.lbl_status = ft.Text(size=12, weight=ft.FontWeight.W_500, color="#b91c1c", text_align=ft.TextAlign.CENTER)

        # Centrage absolu du conteneur de formulaire
        self.c_conteneur = ft.Container(
            content=ft.Column([
                self.lbl_titre,
                self.c_annonce_officielle,
                ft.Column([self.lbl_user, self.en_login], spacing=4),
                ft.Column([self.lbl_pass, self.en_password], spacing=4),
                ft.Container(height=5),
                self.btn_valider,
                self.btn_bascule,
                self.lbl_status
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10, tight=True),
            bgcolor=ft.Colors.WHITE,
            padding=25,
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.GREY_200),
            width=360
        )

        super().__init__(
            content=self.c_conteneur,
            expand=True,
            bgcolor=ft.Colors.WHITE,
            alignment=ft.Alignment(0, 0) #Centrage horizontal et vertical absolu sur l'écran
        )

        # Abonnement linguistique dynamique i18n
        if hasattr(DICTIONNAIRE_LANGUES, "moteur_i18n"):
            DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_changement_langue)
        self.actualiser_donnees_affichage()

    def action_changement_langue(self, nuevo_dic: dict):
        """Met à jour l'interface lors d'une modification linguistique globale."""
        self.traduire_page(nuevo_dic)

    def traduire_page(self, dic: dict):
        """Injecte l'ensemble des traductions d'authentification du fichier JSON."""
        if not dic:
            return
        txt_auth = dic.get("auth", {})
        
        self.lbl_cadre_annonce.value = str(txt_auth.get("cadre_legal", "📜 Homologation & Conseils"))
        self.lbl_titre.value = str(txt_auth.get("titre_connexion", "Connexion"))
        self.lbl_user.value = str(txt_auth.get("user_lbl", "Identifiant :"))
        self.lbl_pass.value = str(txt_auth.get("pass_lbl", "Mot de passe :"))
        self.lbl_bienvenue_conseil.value = str(txt_auth.get("message_bienvenue_doctrinal", ""))
        
        if self.btn_valider.content:
            self.btn_valider.content.value = str(txt_auth.get("btn_soumettre", "Se connecter"))
        if self.btn_bascule.content:
            self.btn_bascule.content.value = str(txt_auth.get("pas_compte", "S'inscrire"))

        if self.page_flet:
            try: self.update()
            except Exception: pass

    def traiter_tentative_connexion(self):
        """Orchestre la soumission de l'identité auprès du DatabaseManager de l'application."""
        txt_auth = DICTIONNAIRE_LANGUES.actif.get("auth", {})
        login = self.en_login.value.strip()
        password = self.en_password.value.strip()
        
        if not login or not password:
            self.lbl_status.value = str(txt_auth.get("err_champs_vides", "❌ Champs obligatoires manquants."))
            self.update()
            return
            
        if hasattr(self.app, "controleur_auth") and self.app.controleur_auth:
            succes, user_id, email = self.app.controleur_auth.verifier_connexion_utilisateur(login, password)
            if succes:
                self.en_login.value = ""
                self.en_password.value = ""
                self.lbl_status.value = ""
                
                # 1. Mise à jour de l'état de session global et reconstruction des menus
                self.app.executer_connexion_session(user_id, login, email)
                
                # 2. 🎯 CRITIQUE ANTI-FANTÔME : Purge explicite du cache d'instances du routeur avant redirection
                if hasattr(self.app, "layout_central") and self.app.layout_central:
                    self.app.layout_central.ecrans_instances.clear()  # Élimine le conteneur fantôme en mémoire vive
                    self.app.layout_central.basculer_vers_ecran("ONBOARDING")
            else:
                self.lbl_status.value = str(txt_auth.get("err_connexion", "❌ Identifiants incorrects."))
                self.update()

    def changer_langue(self, n_lang: str):
        """Liaison avec la propagation descendante du Layout central."""
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)

    def actualiser_donnees_affichage(self):
        """Cycle de vie : Efface les résidus d'erreurs au chargement de l'IHM."""
        self.lbl_status.value = ""
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)

    def actualiser_contexte(self):
        """Alias pour le routeur central."""
        self.actualiser_donnees_affichage()
