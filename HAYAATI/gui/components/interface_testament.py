"""
PANNEAU DE RÉDACTION ET DISPOSITIONS TESTAMENTAIRES (GUI/COMPONENTS/INTERFACE_TESTAMENT.PY)
Version Finale Intégrale - Totalement compatible Flet 0.86.2, Python 3.14 & APK Android
Intégration du Fiqh Avancé : Dettes Spirituelles (Kaffâra, Hajj) et Dernières Consignes.
"""
from __future__ import annotations
import flet as ft
from gui.langues import DICTIONNAIRE_LANGUES

class EcranTestament(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.page_flet = app_reference.page
        self.mode_mobile = None
        
        # 🎯 SÉCURITÉ FIQH AVANCÉ : Si l'utilisateur n'est pas connecté, l'IHM affiche un écran de verrouillage étanche
        if not getattr(self.app, "est_mode_connecte", False):
            self.layout_verrouille = ft.Column([
                ft.Icon(ft.icons.LOCK_OUTLINED, size=50, color="#b91c1c"),
                ft.Text("Espace Réservé (Mode Connecté)", size=18, weight=ft.FontWeight.BOLD, color="#b91c1c"),
                ft.Text("Veuillez vous connecter pour enregistrer vos dettes spirituelles, legs et consignes morales de manière persistante sur le disque.", text_align=ft.TextAlign.CENTER, color="#64748b")
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            
            super().__init__(
                content=self.layout_verrouille, expand=True, bgcolor="#f8fafc",
                padding=ft.Padding(left=15, right=15, top=15, bottom=15)
            )
            return

        # --- 1. INSTANCIATION DES COMPOSANTS GRAPHIQUES MATERIAL 3 ---
        self.lbl_rappel_loi = ft.Text(size=11, italic=True, color="#991b1b")
        self.c_rappel = ft.Container(
            content=self.lbl_rappel_loi,
            bgcolor="#fee2e2", padding=ft.Padding(10, 8, 10, 8), border_radius=6
        )

        # A. Champ Bénéficiaire Historique
        self.lbl_beneficiaire = ft.Text(size=11, weight=ft.FontWeight.BOLD, color="#4b5563")
        self.en_beneficiaire = ft.TextField(
            value="Association Dar es Salaam", height=40, text_size=13,
            border_radius=6, border_color=ft.Colors.GREY_400, bgcolor=ft.Colors.WHITE
        )

        # B. Champ Valeur Financière du legs
        self.lbl_valeur = ft.Text(size=11, weight=ft.FontWeight.BOLD, color="#4b5563")
        self.en_valeur_legs = ft.TextField(
            value="0", width=150, height=40, text_size=13,
            border_radius=6, border_color=ft.Colors.GREY_400, bgcolor=ft.Colors.WHITE
        )
        self.lbl_devise_symbole = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#064e3b")

        # C. NOUVEAUX CHAMPS : Dettes envers Allah (Diyoun Allah)
        self.lbl_kaffara = ft.Text("Expiations rituelles impayées (Kaffârât / An-Noudhour) :", size=11, weight=ft.FontWeight.BOLD, color="#4b5563")
        self.en_kaffara = ft.TextField(
            value="0", height=40, text_size=13, keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=6, border_color=ft.Colors.GREY_400, bgcolor=ft.Colors.WHITE
        )

        self.lbl_hajj = ft.Text("Coût estimé du Hajj obligatoire non accompli :", size=11, weight=ft.FontWeight.BOLD, color="#4b5563")
        self.en_hajj = ft.TextField(
            value="0", height=40, text_size=13, keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=6, border_color=ft.Colors.GREY_400, bgcolor=ft.Colors.WHITE
        )

        # D. NOUVEAU CHAMP : Dernières Consignes et Recommandations Morales
        self.lbl_consignes = ft.Text("Dernières consignes spirituelles et messages vertueux à la famille :", size=11, weight=ft.FontWeight.BOLD, color="#4b5563")
        self.en_consignes = ft.TextField(
            value="", hint_text="Écrivez ici vos conseils sur la foi, enterrement sunnah, messages de paix...",
            multiline=True, min_lines=3, max_lines=6, text_size=13,
            border_radius=6, border_color=ft.Colors.GREY_400, bgcolor=ft.Colors.WHITE
        )

        # Cadre d'agencement du formulaire global
        self.lbl_cadre_redaction = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.cadre_redaction = ft.Container(
            content=ft.Column([
                self.lbl_cadre_redaction,
                self.c_rappel,
                ft.Column([self.lbl_beneficiaire, self.en_beneficiaire], spacing=4),
                ft.Column([
                    self.lbl_valeur,
                    ft.Row([self.en_valeur_legs, self.lbl_devise_symbole], spacing=8, alignment=ft.MainAxisAlignment.START)
                ], spacing=4),
                ft.Divider(height=10, color=ft.Colors.GREY_200),
                ft.Column([self.lbl_kaffara, self.en_kaffara], spacing=4),
                ft.Column([self.lbl_hajj, self.en_hajj], spacing=4),
                ft.Column([self.lbl_consignes, self.en_consignes], spacing=4),
            ], spacing=12),
            bgcolor=ft.Colors.WHITE, padding=15, border_radius=8, border=ft.Border.all(1, "#064e3b")
        )

        # Bouton de validation de signature
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

        # 🎯 BOUTON RETOUR ÉMOJI UNIVERSEL VERS LE HUB INVENTAIRE
        self.btn_retour_hub = ft.IconButton(
            icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
            icon_color="#064e3b",
            icon_size=16,
            tooltip="↩️",
            on_click=lambda _: self.app.layout_central.basculer_vers_ecran("INVENTAIRE")
        )

        # Injection physique du bouton au sommet absolu de la colonne
        self.layout_testament = ft.Column([
            self.btn_retour_hub,
            self.cadre_redaction,
            self.btn_valider,
            self.c_notif,
            self.btn_retour_hub
        ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)

        super().__init__(
            content=self.layout_testament, expand=True, bgcolor="#f8fafc",
            padding=ft.Padding(left=15, right=15, top=15, bottom=15)
        )
        
        self.actualiser_donnees_affichage()

    def action_langue(self, dic: dict):
        """Met à jour l'interface lors d'une modification linguistique globale."""
        self.traduire_page(dic)

    def traduire_page(self, dic: dict):
        """Met à jour dynamiquement l'intégralité des textes du module de testament en multilingue."""
        if not dic:
            return
        t = dic.get("testament", {})
        dev = getattr(self.app, "devise_active", "XOF")
        
        # 1. Mise à jour des libellés historiques
        self.lbl_cadre_redaction.value = str(t.get("cadre_redaction", "Dispositions"))
        self.lbl_rappel_loi.value = str(t.get("limite_legale", "Rappel : Limite du tiers (1/3)."))
        self.lbl_beneficiaire.value = str(t.get("lbl_beneficiaire", "Bénéficiaire :"))
        self.lbl_valeur.value = str(t.get("lbl_valeur", "Montant du Legs :"))
        self.lbl_devise_symbole.value = str(dev)
        
        # 2. 🎯 MULTILINGUE DYNAMIQUE DES NOUVEAUX PASSIFS RITUELS & CONSIGNES
        self.lbl_kaffara.value = str(t.get("lbl_kaffara", "Expiations rituelles impayées (Kaffârât / An-Noudhour) :"))
        self.lbl_hajj.value = str(t.get("lbl_hajj", "Coût estimé du Hajj obligatoire non accompli :"))
        self.lbl_consignes.value = str(t.get("lbl_consignes", "Dernières consignes spirituelles et messages vertueux à la famille :"))
        
        # Mise à jour dynamique du texte d'indication (Hint) sans écraser la saisie en cours
        if hasattr(self.en_consignes, "hint_text"):
            self.en_consignes.hint_text = str(t.get("hint_consignes", "Écrivez ici vos conseils sur la foi, enterrement sunnah, messages de paix..."))

        if self.btn_valider.content:
            self.btn_valider.content.value = str(t.get("btn_enregistrer", "Valider"))

        # Rafraîchissement réactif de l'IHM Flet
        if self.page_flet:
            try: 
                self.update()
            except Exception: 
                pass

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
            valeur_kaffara = float(self.en_kaffara.value.strip() or 0.0)
            valeur_hajj = float(self.en_hajj.value.strip() or 0.0)
            consignes_morales = self.en_consignes.value.strip()

            if valeur_legs < 0 or valeur_kaffara < 0 or valeur_hajj < 0: 
                raise ValueError

            if hasattr(self.app, "sync_engine") and self.app.sync_engine:
                u_id = self.app.user_id_connecte
                
                # 🎯 ALIGNEMENT MOTEURS ATOMIQUES : Sauvegarde centralisée dans le module FINANCES
                cache_fin = self.app.sync_engine.charger_donnees_module(u_id, "FINANCES") or {}
                cache_fin["wasiyya"] = valeur_legs
                cache_fin["kaffara_expiation"] = valeur_kaffara
                cache_fin["cout_hajj_obligatoire"] = valeur_hajj
                
                # Le moteur HeritageEngine attend la somme totale sous la clé technique 'dettes_spirituelles'
                cache_fin["dettes_spirituelles"] = valeur_kaffara + valeur_hajj
                self.app.sync_engine.executer_sauvegarde_module(u_id, "FINANCES", cache_fin)
                
                # Sauvegarde du document textuel d'accompagnement spécifique du Testament
                doc_testament = {
                    "beneficiaire": beneficiaire, 
                    "valeur": valeur_legs,
                    "kaffara_expiation": valeur_kaffara,
                    "cout_hajj_obligatoire": valeur_hajj,
                    "dernieres_consignes_morales": consignes_morales
                }
                self.app.sync_engine.executer_sauvegarde_module(u_id, "TESTAMENT", doc_testament)
                
            self.lbl_status.value = "✓ Volontés de fin de vie, passifs rituels et consignes enregistrés."
            self.c_notif.bgcolor = "#d1fae5"
            self.lbl_status.color = "#064e3b"
            
            if hasattr(self.app, "declencher_changement_global"):
                self.app.declencher_changement_global()
            else:
                self.update()
                
        except ValueError:
            self.lbl_status.value = "❌ Erreur : Montants numériques positifs requis."
            self.c_notif.bgcolor = "#fee2e2"
            self.lbl_status.color = "#991b1b"
            self.update()

    def injecter_donnees(self, data: dict | None):
        """Réinjecte la sauvegarde SQLite des dispositions au sein de l'interface."""
        if not data: 
            return
        self.en_beneficiaire.value = str(data.get("beneficiaire", "Association Dar es Salaam"))
        self.en_valeur_legs.value = f"{float(data.get('valeur', 0.0)):.2f}"
        self.en_kaffara.value = f"{float(data.get('kaffara_expiation', 0.0)):.2f}"
        self.en_hajj.value = f"{float(data.get('cout_hajj_obligatoire', 0.0)):.2f}"
        self.en_consignes.value = str(data.get("dernieres_consignes_morales", ""))
        
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
