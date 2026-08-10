"""
PAGE D'INSCRIPTION DE L'AUDITEUR (GUI/PAGES/PAGE_INSCRIPTION.PY)
Version Flet 0.86+ - Correction définitive de conformité globale pour APK Android & Python 3.14 (Partie 1/2)
"""
from __future__ import annotations
import uuid
import flet as ft
from gui.langues import DICTIONNAIRE_LANGUES

class PageInscription(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.page_flet = app_reference.page
        
        # 1. Déclaration des composants graphiques de l'IHM
        self.lbl_titre = ft.Text(size=18, weight=ft.FontWeight.BOLD, color="#064e3b", text_align=ft.TextAlign.CENTER)

        self.lbl_username = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#374151")
        self.entree_username = ft.TextField(
            width=280,
            height=45,
            text_size=14,
            content_padding=ft.Padding(left=10, right=10, top=10, bottom=10),
            border_radius=6,
            border_color=ft.Colors.GREY_400,
            bgcolor=ft.Colors.WHITE
        )

        self.lbl_email = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#374151")
        self.entree_email = ft.TextField(
            width=280,
            height=45,
            text_size=14,
            content_padding=ft.Padding(left=10, right=10, top=10, bottom=10),
            border_radius=6,
            border_color=ft.Colors.GREY_400,
            bgcolor=ft.Colors.WHITE,
            keyboard_type=ft.KeyboardType.EMAIL
        )

        self.lbl_password = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#374151")
        self.entree_password = ft.TextField(
            width=280,
            height=45,
            text_size=14,
            content_padding=ft.Padding(left=10, right=10, top=10, bottom=10),
            border_radius=6,
            border_color=ft.Colors.GREY_400,
            bgcolor=ft.Colors.WHITE,
            password=True,
            can_reveal_password=True
        )

        self.lbl_verdict = ft.Text(size=12, color="#b91c1c", italic=True, text_align=ft.TextAlign.CENTER)

        # 🎯 RECTIFICATION COMPATIBILITÉ SÉCURISÉE TEXTE PYTHON 3.14 : content=ft.Text()
        self.btn_valider = ft.ElevatedButton(
            content=ft.Text("Inscription", size=13, weight=ft.FontWeight.BOLD),
            width=280,
            bgcolor="#064e3b",
            color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
            on_click=lambda e: self.traiter_inscription_physique()
        )

        self.btn_retour = ft.TextButton(
            content=ft.Text("Connexion", size=12),
            style=ft.ButtonStyle(color="#0f766e"),
            on_click=lambda _: self.app.basculer_ecran("CONNEXION")
        )

        # 2. Structure et mise en page défilante et centrée
        self.c_centre = ft.Container(
            content=ft.Column(
                controls=[
                    self.lbl_titre,
                    ft.Column([self.lbl_username, self.entree_username], spacing=3),
                    ft.Column([self.lbl_email, self.entree_email], spacing=3),
                    ft.Column([self.lbl_password, self.entree_password], spacing=3),
                    self.lbl_verdict,
                    ft.Container(height=5),
                    self.btn_valider,
                    self.btn_retour
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                tight=True
            ),
            bgcolor=ft.Colors.WHITE,
            padding=25,
            border_radius=12,
            width=330,
            border=ft.Border.all(1, ft.Colors.GREY_100)
        )

        super().__init__(
            content=ft.Column([self.c_centre], scroll=ft.ScrollMode.AUTO, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True,
            bgcolor=ft.Colors.WHITE,
            padding=ft.Padding(left=20, right=20, top=20, bottom=20)
        )

        # 3. Branchement i18n et initialisation des chaînes de texte
        if hasattr(DICTIONNAIRE_LANGUES, "moteur_i18n"):
            DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_changement_langue)
        self.rafraichir_textes(DICTIONNAIRE_LANGUES.actif)

    def action_changement_langue(self, nouveau_dictionnaire: dict):
        """Met à jour les libellés lors du changement de langue."""
        self.rafraichir_textes(nouveau_dictionnaire)

    def rafraichir_textes(self, dic_actif: dict):
        """Injecte les données i18n dans les contrôles graphiques Flet en s'alignant sur vos clés JSON."""
        if not dic_actif:
            return
            
        txt_auth = dic_actif.get("auth", {})
        self.lbl_titre.value = txt_auth.get("titre_inscription", "Configuration Initiale de Hayaati")
        self.lbl_username.value = txt_auth.get("username_lbl", txt_auth.get("user_lbl", "Identifiant :"))
        self.lbl_email.value = txt_auth.get("email_lbl", "E-mail :")
        self.lbl_password.value = txt_auth.get("pass_lbl", "Mot de passe :")
        
        # 🎯 FIX TECHNIQUE TEXTE SÉCURISÉ : Extraction et mise à jour via .content.value
        if self.btn_valider.content:
            self.btn_valider.content.value = txt_auth.get("btn_soumettre", "Valider et installer")
        if self.btn_retour.content:
            self.btn_retour.content.value = txt_auth.get("deja_compte", "Se connecter")
        
        # 🎯 FIX TECHNIQUE ANCRAGE : Utilisation de self.page_flet pour contourner le RuntimeError
        if self.page_flet:
            try:
                self.update()
            except Exception:
                pass

    # --- SUITE ET FIN DU MODULE PAGE_INSCRIPTION (PARTIE 2/2) ---
    def traiter_inscription_physique(self):
        """Exécute la validation et initie l'inscription via le pontage d'authentification."""
        txt_auth = DICTIONNAIRE_LANGUES.actif.get("auth", {})
        username = self.entree_username.value.strip()
        email = self.entree_email.value.strip()
        password = self.entree_password.value.strip()

        if not username or not email or not password:
            self.lbl_verdict.value = txt_auth.get("err_champs_vides", "❌ Champs requis.")
            self.lbl_verdict.color = "#b91c1c"
            if self.page_flet:
                self.update()
            return

        if len(password) < 4:
            self.lbl_verdict.value = txt_auth.get("err_password_court", "❌ Mot de passe court (4 min).")
            self.lbl_verdict.color = "#b91c1c"
            if self.page_flet:
                self.update()
            return

        if hasattr(self.app, "controleur_auth") and self.app.controleur_auth:
            methode_inscription = getattr(self.app.controleur_auth, "enregistrer_nouvel_utilisateur", None)
            if not methode_inscription:
                methode_inscription = getattr(self.app.controleur_auth, "creer_compte_utilisateur", None)
                
            if methode_inscription:
                try:
                    succes, message = methode_inscription(username, email, password)
                except Exception as ex:
                    succes, message = False, str(ex)
            else:
                succes, message = False, "Service d'authentification dégradé."
            
            if succes:
                self.entree_username.value = ""
                self.entree_email.value = ""
                self.entree_password.value = ""
                self.lbl_verdict.value = ""
                
                # Redirection vers la page de Connexion
                self.app.basculer_ecran("CONNEXION")
                
                # Notification de succès injectée de façon réactive dans l'IHM cible
                ecran_connexion = self.app.layout_central.ecrans_instances.get("CONNEXION")
                if ecran_connexion and hasattr(ecran_connexion, "lbl_status"):
                    ecran_connexion.lbl_status.value = txt_auth.get("inscription_ok", "✓ Inscription réussie. Connectez-vous.")
                    ecran_connexion.lbl_status.color = "#064e3b"
                    try:
                        ecran_connexion.update()
                    except Exception:
                        pass
            else:
                self.lbl_verdict.value = f"❌ {message}"
                self.lbl_verdict.color = "#b91c1c"
                if self.page_flet:
                    self.update()
        else:
            self.lbl_verdict.value = txt_auth.get("err_champs_vides", "❌ Mode invité : Inscription impossible.")
            self.lbl_verdict.color = "#b91c1c"
            if self.page_flet:
                self.update()

    def changer_langue(self, n_lang: str):
        """Méthode invoquée par la propagation descendante du Layout central."""
        self.rafraichir_textes(DICTIONNAIRE_LANGUES.actif)

    def actualiser_donnees_affichage(self):
        """Cycle de vie : Purge les messages d'erreurs lors du retour ou de l'affichage de l'écran."""
        self.lbl_verdict.value = ""
        if self.page_flet:
            try:
                self.update()
            except Exception:
                pass

    def actualiser_contexte(self):
        """Alias pour le routeur central."""
        self.actualiser_donnees_affichage()
