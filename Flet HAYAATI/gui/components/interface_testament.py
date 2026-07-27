"""
PANNEAU DE RÉDACTION ET DISPOSITIONS TESTAMENTAIRES (GUI/COMPONENTS/INTERFACE_TESTAMENT.PY)
Version Finale Intégrale Statique - Totalement compatible Flet 0.86.2, Python 3.14 & APK Android
"""
from __future__ import annotations
import flet as ft
from gui.langues import DICTIONNAIRE_LANGUES

class EcranTestament(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.page_flet = app_reference.page
        self.mode_mobile = None
        
        # --- 1. INSTANCIATION DES COMPOSANTS GRAPHIQUES MATERIAL 3 ---
        # Rappel canonique souverain sur le plafond du tiers (1/3)
        self.lbl_rappel_loi = ft.Text(size=11, italic=True, color="#991b1b")
        self.c_rappel = ft.Container(
            content=self.lbl_rappel_loi,
            bgcolor="#fee2e2", padding=ft.Padding(10, 8, 10, 8), border_radius=6
        )

        # Champ Bénéficiaire
        self.lbl_beneficiaire = ft.Text(size=11, weight=ft.FontWeight.BOLD, color="#4b5563")
        self.en_beneficiaire = ft.TextField(
            value="Association Dar es Salaam", height=40, text_size=13,
            border_radius=6, border_color=ft.Colors.GREY_400, bgcolor=ft.Colors.WHITE
        )

        # Champ Valeur financière du legs et symbole monétaire
        self.lbl_valeur = ft.Text(size=11, weight=ft.FontWeight.BOLD, color="#4b5563")
        self.en_valeur_legs = ft.TextField(
            value="0", width=150, height=40, text_size=13,
            border_radius=6, border_color=ft.Colors.GREY_400, bgcolor=ft.Colors.WHITE
        )
        self.lbl_devise_symbole = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#064e3b")

        # Cadre d'agencement du formulaire (Émule tk.LabelFrame)
        self.lbl_cadre_redaction = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.cadre_redaction = ft.Container(
            content=ft.Column([
                self.lbl_cadre_redaction,
                self.c_rappel,
                ft.Column([self.lbl_beneficiaire, self.en_beneficiaire], spacing=4),
                ft.Column([
                    self.lbl_valeur,
                    ft.Row([self.en_valeur_legs, self.lbl_devise_symbole], spacing=8, alignment=ft.MainAxisAlignment.START)
                ], spacing=4)
            ], spacing=12),
            bgcolor=ft.Colors.WHITE, padding=15, border_radius=8, border=ft.Border.all(1, "#064e3b")
        )

        # Bouton de validation de signature (Syntaxe sécurisée Python 3.14)
        self.btn_valider = ft.ElevatedButton(
            content=ft.Text("Valider", size=13, weight=ft.FontWeight.BOLD),
            bgcolor="#064e3b", color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
            on_click=lambda _: self.enregistrer_testament_db()
        )

        # Statut inférieur de confirmation et notification
        self.lbl_status = ft.Text(size=12, italic=True, color="#4b5563", text_align=ft.TextAlign.CENTER)
        self.c_notif = ft.Container(
            content=self.lbl_status, bgcolor="#f3f4f6", padding=10, border_radius=6, alignment=ft.Alignment(0, 0)
        )

        # Structure globale empilée défilante
        self.layout_testament = ft.Column([
            self.cadre_redaction,
            self.btn_valider,
            self.c_notif
        ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)

        super().__init__(
            content=self.layout_testament, expand=True, bgcolor="#f8fafc",
            padding=ft.Padding(left=15, right=15, top=15, bottom=15)
        )

        # Abonnement dynamique i18n
        if hasattr(DICTIONNAIRE_LANGUES, "moteur_i18n"):
            DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_langue)
        self.actualiser_donnees_affichage()

    def action_langue(self, dic: dict):
        """Met à jour l'interface lors d'une modification linguistique globale."""
        self.traduire_page(dic)

    def traduire_page(self, dic: dict):
        """Met à jour dynamiquement l'intégralité des textes du module de testament."""
        if not dic:
            return
        t = dic.get("testament", {})
        dev = getattr(self.app, "devise_active", "XOF")
        
        self.lbl_cadre_redaction.value = str(t.get("cadre_redaction", "Dispositions"))
        self.lbl_rappel_loi.value = str(t.get("limite_legale", "Rappel : Limite du tiers (1/3)."))
        self.lbl_beneficiaire.value = str(t.get("lbl_beneficiaire", "Bénéficiaire :"))
        self.lbl_valeur.value = str(t.get("lbl_valeur", "Montant du Legs :"))
        self.lbl_devise_symbole.value = str(dev)
        
        if self.btn_valider.content:
            self.btn_valider.content.value = str(t.get("btn_enregistrer", "Valider"))

        if self.page_flet:
            try: self.update()
            except Exception: pass

    def enregistrer_testament_db(self):
        """Sauvegarde les dispositions testamentaires dans l'espace via SyncEngine."""
        if not getattr(self.app, "est_mode_connecte", False):
            self.lbl_status.value = "❌ Espace privé déconnecté."
            self.c_notif.bgcolor = "#fee2e2"
            self.lbl_status.color = "#991b1b"
            self.update()
            return
            
        try:
            beneficiaire = self.en_beneficiaire.value.strip()
            valeur_legs = float(self.en_valeur_legs.value.strip() or 0.0)
            if valeur_legs < 0: 
                raise ValueError

            if hasattr(self.app, "sync_engine") and self.app.sync_engine:
                u_id = self.app.user_id_connecte
                
                # ALIGNEMENT DU MOTEUR : Sauvegarde synchrone pour le calcul de l'héritage live
                cache_fin = self.app.sync_engine.charger_donnees_module(u_id, "FINANCES") or {}
                cache_fin["wasiyya"] = valeur_legs
                self.app.sync_engine.executer_sauvegarde_module(u_id, "FINANCES", cache_fin)
                
                # Sauvegarde du document textuel spécifique du testament
                doc_testament = {"beneficiaire": beneficiaire, "valeur": valeur_legs}
                self.app.sync_engine.executer_sauvegarde_module(u_id, "TESTAMENT", doc_testament)
                
            self.lbl_status.value = "✓ Intentions testamentaires enregistrées avec succès."
            self.c_notif.bgcolor = "#d1fae5"
            self.lbl_status.color = "#064e3b"
            
            if hasattr(self.app, "declencher_changement_global"):
                self.app.declencher_changement_global()
            else:
                self.update()
                
        except ValueError:
            self.lbl_status.value = "❌ Erreur : Montant numérique positif requis."
            self.c_notif.bgcolor = "#fee2e2"
            self.lbl_status.color = "#991b1b"
            self.update()

    def injecter_donnees(self, data: dict | None):
        """Réinjecte la sauvegarde SQLite du legs au sein de l'interface."""
        if not data: 
            return
        self.en_beneficiaire.value = str(data.get("beneficiaire", "Association Dar es Salaam"))
        self.en_valeur_legs.value = f"{float(data.get('valeur', 0.0)):.2f}"
        if self.page_flet:
            try: self.update()
            except Exception: pass

    def changer_langue(self, n_lang: str):
        """Liaison avec la propagation descendante du Layout central."""
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)

    def actualiser_donnees_affichage(self):
        """Recharge les dispositions à l'apparition de l'écran."""
        self.lbl_status.value = ""
        self.c_notif.bgcolor = "#f3f4f6"
        self.lbl_status.color = "#4b5563"
        
        if getattr(self.app, "est_mode_connecte", False) and getattr(self.app, "sync_engine", None):
            testament_sauvegarde = self.app.sync_engine.charger_donnees_module(
                self.app.user_id_connecte, "TESTAMENT"
            )
            self.injecter_donnees(testament_sauvegarde)
            
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)

    def actualiser_contexte(self):
        """Alias pour le routeur central."""
        self.actualiser_donnees_affichage()
