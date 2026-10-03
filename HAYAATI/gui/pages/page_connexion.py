"""
PAGE DE CONNEXION ET CERTIFICATION DOCTRINALE CINKASSÉ (GUI/PAGES/PAGE_CONNEXION.PY)
Version 4.1 — Retrait du doublon ecrans_instances.clear() + basculer_vers_ecran()
              après app.executer_connexion_session(), qui fait déjà tout ça en
              interne. Ce doublon, combiné à un doublon similaire dans
              executer_connexion_session() elle-même, provoquait la
              construction de plusieurs PageOnboarding en succession rapide
              au moment de la connexion, et des erreurs "session détruite"
              en cascade.
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

        self.lbl_cadre_annonce = ft.Text(size=11, weight=ft.FontWeight.BOLD, color="#d97706")
        self.lbl_bienvenue_conseil = ft.Text(size=12, color="#374151", text_align=ft.TextAlign.CENTER)

        self.c_annonce_officielle = ft.Container(
            content=ft.Column([
                self.lbl_cadre_annonce,
                self.lbl_bienvenue_conseil
            ], spacing=6, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor="#f9fafb", padding=12, border_radius=8, border=ft.Border.all(1, "#d97706")
        )

        self.lbl_user = ft.Text(size=11, weight=ft.FontWeight.BOLD, color="#4b5563")
        self.en_login = ft.TextField(
            height=40, text_size=13, border_radius=6,
            border_color=ft.Colors.GREY_400, bgcolor=ft.Colors.WHITE,
            on_focus=self._scroll_vers_champ  # Scroll auto quand le champ prend le focus
        )

        self.lbl_pass = ft.Text(size=11, weight=ft.FontWeight.BOLD, color="#4b5563")
        self.en_password = ft.TextField(
            height=40, text_size=13, border_radius=6, password=True, can_reveal_password=True,
            border_color=ft.Colors.GREY_400, bgcolor=ft.Colors.WHITE,
            on_focus=self._scroll_vers_champ  # Scroll auto quand le champ prend le focus
        )

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

        self.lbl_status = ft.Text(size=12, weight=ft.FontWeight.W_500, color="#b91c1c", text_align=ft.TextAlign.CENTER)

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

        # Column scrollable avec padding bottom généreux. Le scroll=AUTO
        # permet de remonter le contenu quand le clavier réduit la hauteur
        # disponible. Le padding bottom de 350px garantit que le champ
        # mot de passe peut toujours être amené au-dessus du clavier.
        self.layout_scrollable = ft.Column(
            controls=[
                ft.Container(height=60),      # Espaceur fixe en haut
                self.c_conteneur,             # Formulaire centré
                ft.Container(height=350),     # Padding bottom pour le clavier Android
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        super().__init__(
            content=self.layout_scrollable,
            expand=True,
            bgcolor=ft.Colors.WHITE,
            alignment=ft.Alignment(0, -1)
        )

        if hasattr(DICTIONNAIRE_LANGUES, "moteur_i18n"):
            DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_changement_langue)
        self.actualiser_donnees_affichage()

    def _scroll_vers_champ(self, e):
        """Scroll automatiquement vers le bas pour amener le champ actif au-dessus du clavier."""
        async def scroll():
            try:
                await self.layout_scrollable.scroll_to(offset=100000, duration=300)
            except Exception:
                pass
        if self.page_flet:
            self.page_flet.run_task(scroll)

    def action_changement_langue(self, nuevo_dic: dict):
        self.traduire_page(nuevo_dic)

    def traduire_page(self, dic: dict):
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

                # 🆕 04/09/2026 : le bloc qui suivait ici (vider
                # ecrans_instances puis rappeler basculer_vers_ecran)
                # a été retiré. executer_connexion_session() fait déjà
                # exactement ça en interne. Le doublon construisait deux
                # PageOnboarding en succession quasi immédiate, chacune
                # programmant sa propre tâche de fond, ce qui provoquait
                # des erreurs "session détruite" en boucle juste après
                # la connexion.
                self.app.executer_connexion_session(user_id, login, email)
            else:
                self.lbl_status.value = str(txt_auth.get("err_connexion", "❌ Identifiants incorrects."))
                self.update()

    def changer_langue(self, n_lang: str):
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)

    def actualiser_donnees_affichage(self):
        self.lbl_status.value = ""
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)

    def actualiser_contexte(self):
        self.actualiser_donnees_affichage()
