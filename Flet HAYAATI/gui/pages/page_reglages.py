"""
PAGE DE RÉGLAGES ET CONFIGURATION DE SESSION (GUI/PAGES/PAGE_REGLAGES.PY)
Version Finale Intégrale Statique Épurée - Totalement compatible Flet 0.86.2, Python 3.14 & APK Android (Partie 1)
"""
from __future__ import annotations
import flet as ft
from gui.langues import DICTIONNAIRE_LANGUES

class PageReglages(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.page_flet = app_reference.page
        self.mode_mobile = None
        
        # Mappages locaux statiques du dictionnaire
        self.map_fiqh_trad_vers_cle: dict[str, str] = {}
        self.map_nisab_trad_vers_cle: dict[str, str] = {}
        self.map_nisab_cle_vers_trad: dict[str, str] = {}

        # 📂 BLOC DE PRÉFÉRENCES DOCTRINALES ET GÉOGRAPHIQUES
        self.lbl_cadre_pref = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.grille_pref = ft.ResponsiveRow(spacing=15, run_spacing=12)
        
        self.c_pref = ft.Container(
            content=ft.Column([
                self.lbl_cadre_pref,
                self.grille_pref
            ], spacing=10),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#064e3b")
        )

        # Initialisation sécurisée des sélecteurs de préférences
        devise_init = getattr(self.app, "devise_active", "XOF")
        self.lbl_guide_devise = ft.Text(size=11, color="#4b5563")
        self.cb_devise = ft.Dropdown(
            options=[ft.dropdown.Option(d) for d in ["XOF", "GHS", "NGN", "USD", "EUR", "GNF", "MAD", "DZD", "TND", "MRU", "LYD", "SAR", "AED", "QAR", "ILS", "JOD", "INR"]],
            height=40, text_size=13, bgcolor=ft.Colors.WHITE, value=str(devise_init)
        )
        
        self.lbl_guide_langue = ft.Text(size=11, color="#4b5563")
        m_index = DICTIONNAIRE_LANGUES.moteur_i18n.langues_disponibles_index if hasattr(DICTIONNAIRE_LANGUES, "moteur_i18n") else {}
        
        self.cb_langue = ft.Dropdown(
            options=[ft.dropdown.Option(nom) for nom in m_index.values()],
            height=40, text_size=13, bgcolor=ft.Colors.WHITE
        )
        self.cb_langue.on_change = lambda e: self.changer_langue(DICTIONNAIRE_LANGUES.moteur_i18n.langue_courante)
        
        langue_init = getattr(self.app, "langue_actuelle", "FR")
        code_courant = str(langue_init).upper()
        self.cb_langue.value = m_index.get(code_courant, code_courant)

        self.lbl_guide_fiqh = ft.Text(size=11, color="#4b5563")
        self.cb_fiqh = ft.Dropdown(height=40, text_size=13, bgcolor=ft.Colors.WHITE)
        
        self.lbl_guide_nisab = ft.Text(size=11, color="#4b5563")
        self.cb_nisab = ft.Dropdown(height=40, text_size=13, bgcolor=ft.Colors.WHITE)

        # Curseur gradué pour l'ajustement lunaire (-2 à 2)
        self.lbl_ajust = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#d97706")
        self.sc_ajustement = ft.Slider(
            min=-2, max=2, divisions=4, label="{value}",
            active_color="#064e3b", inactive_color="#f3f4f6", value=0
        )
        self.c_lunaire = ft.Column([self.lbl_ajust, self.sc_ajustement], spacing=3)

        # Récupération persistante via le SyncEngine
        ajust_pref = 0
        nisab_pref = "PLUS_BAS"
        if hasattr(self.app, "sync_engine") and self.app.sync_engine:
            u_id = getattr(self.app, "user_id_connecte", "INVITE")
            c_p = self.app.sync_engine.charger_donnees_module(u_id, "PREFERENCES") or {}
            ajust_pref = int(c_p.get("ajustement_hegiri", 0))
            nisab_pref = str(c_p.get("arbitrage_nisab", "PLUS_BAS")).upper()
            
        self.sc_ajustement.value = ajust_pref
        self.cle_nisab_active_memoire = nisab_pref

        # Bouton d'enregistrement des préférences doctrinales
        self.btn_sauver_pref = ft.ElevatedButton(
            content=ft.Text("Sauvegarder", size=13, weight=ft.FontWeight.BOLD),
            bgcolor="#064e3b", color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
            on_click=lambda e: self.sauvegarder_preferences_disque()
        )

        # Assemblage de la grille responsive des préférences
        composants_pref = [
            (self.lbl_guide_devise, self.cb_devise), (self.lbl_guide_langue, self.cb_langue),
            (self.lbl_guide_fiqh, self.cb_fiqh), (self.lbl_guide_nisab, self.cb_nisab)
        ]
        for lbl, combo in composants_pref:
            self.grille_pref.controls.append(ft.Container(content=ft.Column([lbl, combo], spacing=3), col={"xs": 12, "md": 6}))
        
        self.grille_pref.controls.extend([
            ft.Container(content=self.c_lunaire, col={"xs": 12}),
            ft.Container(content=self.btn_sauver_pref, col={"xs": 12}, padding=ft.Padding(left=0, right=0, top=5, bottom=0))
        ])

        # 📂 BLOC FEEDBACK UTILISATEUR ET ASSISTANCE WHATSAPP DIRECTE
        self.lbl_cadre_feed = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.lbl_note = ft.Text(size=11, color="#4b5563")
        self.combo_etoiles = ft.Dropdown(
            options=[ft.dropdown.Option(f"{i} ★") for i in range(5, 0, -1)],
            height=40, text_size=13, bgcolor=ft.Colors.WHITE, value="5 ★", width=100
        )
        
        self.lbl_suggestions = ft.Text(size=11, color="#4b5563")
        self.txt_commentaire = ft.TextField(
            multiline=True, min_lines=2, max_lines=3, text_size=13,
            border_color=ft.Colors.GREY_400, bgcolor=ft.Colors.WHITE
        )
        
        # Planification asynchrone de la tâche WhatsApp via run_task
        self.btn_send_feed = ft.ElevatedButton(
            content=ft.Text("Envoyer", size=13, weight=ft.FontWeight.BOLD),
            bgcolor="#0f766e", color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
            on_click=lambda _: self.page_flet.run_task(self.traiter_envoi_feedback)
        )

        self.c_feed = ft.Container(
            content=ft.Column([
                self.lbl_cadre_feed,
                ft.Row([self.lbl_note, self.combo_etoiles], alignment=ft.MainAxisAlignment.START, spacing=10, wrap=True),
                self.lbl_suggestions,
                self.txt_commentaire,
                self.btn_send_feed
            ], spacing=10),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#064e3b")
        )

        # 📂 BLOC DE DECONNEXION DE SESSION
        self.btn_deconnexion = ft.ElevatedButton(
            content=ft.Text("Déconnexion", size=13, weight=ft.FontWeight.BOLD),
            bgcolor="#b91c1c", color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
            on_click=lambda _: self.app.executer_deconnexion_session()
        )
        self.c_deconnexion = ft.Container(content=self.btn_deconnexion, padding=ft.Padding(left=0, right=0, top=5, bottom=5))

        # Zone de notification basse
        self.lbl_status = ft.Text(size=12, italic=True, color="#4b5563", text_align=ft.TextAlign.CENTER)
        self.c_notif = ft.Container(content=self.lbl_status, bgcolor="#f3f4f6", padding=10, border_radius=6, alignment=ft.Alignment(0, 0))

        # 🎯 SÉCURISATION DU BOUTON PROFIL : Déclaration neutre et propre.
        # C'est la méthode de traduction de la page qui va lui injecter sa valeur depuis les JSON.
        self.lbl_bouton_profil = ft.Text(size=13, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.lbl_bouton_profil.key = "profil"

        self.btn_ouvrir_profil = ft.Container(
            content=ft.Row([
                ft.Text("👤", size=16),
                self.lbl_bouton_profil, 
                ft.Text("➡️", size=12),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            bgcolor="#f0fdf4", 
            padding=12,
            border_radius=8,
            border=ft.Border.all(1, "#d1fae5"),
            on_click=lambda _: self.app.layout_central.basculer_vers_ecran("PROFIL")
        )

        # 🌟 On insère ce bouton de profil tout en haut de la liste de vos réglages existants
        self.zone_defilement = ft.Column(
            controls=[self.btn_ouvrir_profil, ft.Container(height=5), self.c_pref, self.c_feed, self.c_deconnexion, self.c_notif],
            scroll=ft.ScrollMode.AUTO, spacing=15, expand=True
        )

        super().__init__(
            content=self.zone_defilement, expand=True, bgcolor=ft.Colors.WHITE,
            padding=ft.Padding(left=15, right=15, top=15, bottom=15)
        )

        if hasattr(DICTIONNAIRE_LANGUES, "moteur_i18n"):
            DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_langue_reglages)
        self.actualiser_donnees_affichage()

    def action_langue_reglages(self, dic: dict):
        """Met à jour l'interface lors d'une modification linguistique globale."""
        self.traduire_page(dic)

    def traduire_page(self, dic: dict):
        """Met à jour dynamiquement tous les libellés et structures i18n de la page."""
        if not dic:
            return
        r = dic.get("reglages", {})
        b_j = dic.get("barre_outils", {})
        
        self.lbl_cadre_pref.value = r.get("cadre_pref", "Préférences")
        self.lbl_ajust.value = r.get("lunaire_lbl", "Ajustement Lune (Jours) :")
        
        if self.btn_sauver_pref.content:
            self.btn_sauver_pref.content.value = r.get("btn_sauver_pref", "Enregistrer")
        if self.btn_deconnexion.content:
            self.btn_deconnexion.content.value = b_j.get("btn_deconnexion", "🚪 Déconnexion")
        if self.btn_send_feed.content:
            self.btn_send_feed.content.value = r.get("btn_soumettre", "Soumettre")
            
        self.lbl_cadre_feed.value = r.get("cadre_feed", "Feedback")
        self.lbl_guide_devise.value = r.get("lbl_guide_devise", "Devise :")
        self.lbl_guide_langue.value = r.get("lbl_guide_langue", "Langue :")
        self.lbl_guide_fiqh.value = r.get("lbl_guide_fiqh", "Fiqh :")
        self.lbl_guide_nisab.value = r.get("lbl_guide_nisab", "Nisab :")
        self.lbl_note.value = r.get("note_lbl", "Note :")
        self.lbl_suggestions.value = r.get("lbl_commentaires", "Suggestions :")

        self.btn_deconnexion.visible = getattr(self.app, "est_mode_connecte", False)

        # 🌟 TRADUCTION DYNAMIQUE IMMÉDIATE : Utilise le dictionnaire déjà passé en argument
        if hasattr(self, "lbl_bouton_profil") and self.lbl_bouton_profil:
            m_json = dic.get("menu", {}) if dic else {}
            libelle_profil_traduit = str(m_json.get("profil", "Profil")).replace("👤", "").strip()
            self.lbl_bouton_profil.value = libelle_profil_traduit

        # Mappage du Fiqh Jurisprudentiel
        ecoles_trad = b_j.get("ecoles", {})
        options_fiqh = ["Malikite", "Hanafite", "Chafiite", "Hanbalite"]
        map_fiqh = {c: ecoles_trad.get(c, c) for c in options_fiqh}
        self.map_fiqh_trad_vers_cle = {str(v).strip().upper(): k for k, v in map_fiqh.items()}
        self.cb_fiqh.options = [ft.dropdown.Option(nom) for nom in map_fiqh.values()]
        
        fiqh_pur = getattr(self.app, "madhhab_actif", "Malikite")
        if fiqh_pur == "Chafi'ite": 
            fiqh_pur = "Chafiite"
        self.cb_fiqh.value = map_fiqh.get(fiqh_pur, fiqh_pur)

        # Mappage de l'arbitrage du Nisab
        self.map_nisab_trad_vers_cle.clear()
        self.map_nisab_cle_vers_trad.clear()
        opt_nisab = dic.get("zakat", {}).get("options_nisab", r.get("options_nisab", {}))
        trads_nisab = {
            "PLUS_BAS": opt_nisab.get("nisab_plus_bas", "Baromètre Prudent (Plus Bas)"),
            "OR": opt_nisab.get("nisab_or", "Seuil de l'Or (85g)"),
            "ARGENT": opt_nisab.get("nisab_argent", "Seuil de l'Argent (595g)")
        }
        
        liste_valeurs_traduites = []
        self.cb_nisab.options.clear()
        for c in ["PLUS_BAS", "OR", "ARGENT"]:
            txt_t = trads_nisab[c]
            self.map_nisab_trad_vers_cle[str(txt_t).strip().upper()] = c
            self.map_nisab_cle_vers_trad[c] = txt_t
            liste_valeurs_traduites.append(txt_t)
            self.cb_nisab.options.append(ft.dropdown.Option(txt_t))

        cle_pure = getattr(self.app, "cle_nisab_active_memoire", "PLUS_BAS")
        self.cb_nisab.value = self.map_nisab_cle_vers_trad.get(cle_pure, liste_valeurs_traduites[0])

        if self.page_flet:
            try: self.update()
            except Exception: pass

    def sauvegarder_preferences_disque(self):
        """Enregistre les arbitrages et préférences de l'auditeur de façon permanente et unifiée."""
        est_co = getattr(self.app, "est_mode_connecte", False)
        u = self.app.user_id_connecte if est_co else "INVITE"
        
        d = self.cb_devise.value
        nom_langue_choisi = self.cb_langue.value
        m_index = DICTIONNAIRE_LANGUES.moteur_i18n.langues_disponibles_index
        
        l = "FR"
        for code, nom in m_index.items():
            if str(nom).strip() == str(nom_langue_choisi).strip():
                l = code
                break
                
        trad_f = self.cb_fiqh.value
        f = self.map_fiqh_trad_vers_cle.get(str(trad_f).strip().upper(), "Malikite")
        
        trad_n = self.cb_nisab.value
        cle_nisab = self.map_nisab_trad_vers_cle.get(str(trad_n).strip().upper(), "PLUS_BAS")
        ajust = int(self.sc_ajustement.value)
        
        # 📂 1. PERSISTANCE CACHE SYNC_ENGINE
        if hasattr(self.app, "sync_engine") and self.app.sync_engine:
            pref = self.app.sync_engine.charger_donnees_module(u, "PREFERENCES") or {}
            pref["devise_defaut"] = d
            pref["langue_actuelle"] = l
            pref["fiqh_defaut"] = f
            pref["arbitrage_nisab"] = cle_nisab
            pref["ajustement_hegiri"] = ajust
            
            if est_co:
                self.app.sync_engine.executer_sauvegarde_module("INVITE", "PREFERENCES", pref)
            self.app.sync_engine.executer_sauvegarde_module(u, "PREFERENCES", pref)

        # Affectation immédiate en mémoire vive de session
        self.app.devise_active = d
        self.app.langue_actuelle = l
        self.app.madhhab_actif = f
        self.app.cle_nisab_active_memoire = cle_nisab
        self.cle_nisab_active_memoire = cle_nisab

        # 📂 2. PERSISTANCE LOURDE DIRECTE SQLITE UTILISATEUR
        if est_co and hasattr(self.app, "controleur_auth") and self.app.controleur_auth:
            dt_naiss = "2000-01-01"
            try:
                import sqlite3
                from gui.pages.page_onboarding_alerts import obtenir_chemin_base_donnees
                conn = sqlite3.connect(obtenir_chemin_base_donnees())
                cur = conn.cursor()
                cur.execute("SELECT date_naissance FROM comptes_utilisateurs WHERE user_id = ?", (str(u),))
                row = cur.fetchone()
                conn.close()
                if row and row[0]: dt_naiss = row[0]
            except Exception: pass

            self.app.controleur_auth.sauvegarder_preferences_reglages(u, dt_naiss, d, l, f)

        if hasattr(self.app, "changer_langue_globale"):
            self.app.changer_langue_globale(l)
            
        r_t = DICTIONNAIRE_LANGUES.actif.get("reglages", {})
        self.lbl_status.value = r_t.get("status_ok_pref", "✓ Configuration sauvegardée localement.")
        self.c_notif.bgcolor = "#d1fae5"
        self.lbl_status.color = "#064e3b"
        self.update()

    async def traiter_envoi_feedback(self):
        """Transmet l'avis de manière persistante et bascule de façon infaillible vers WhatsApp Togo."""
        if not getattr(self.app, "est_mode_connecte", False): 
            return
            
        com = self.txt_commentaire.value.strip()
        r = DICTIONNAIRE_LANGUES.actif.get("reglages", {})
        
        if not com:
            self.lbl_status.value = r.get("err_feed_vide", "❌ Les commentaires ne peuvent pas être vides.")
            self.c_notif.bgcolor = "#fee2e2"
            self.lbl_status.color = "#991b1b"
            self.update()
            return
            
        if hasattr(self.app, "controleur_auth") and self.app.controleur_auth:
            try:
                valeur_combo = str(self.combo_etoiles.value or "5").strip()
                note_entiere = int(valeur_combo.split(" ")[0])
                
                succes, message = self.app.controleur_auth.enregistrer_feedback_utilisateur(
                    self.app.user_id_connecte, note_entiere, com
                )
                
                if {succes: True}.get(succes, False):
                    self.lbl_status.value = r.get("status_ok_feed", "✓ Avis enregistré.")
                    self.c_notif.bgcolor = "#d1fae5"
                    self.lbl_status.color = "#064e3b"
                    
                    # 🎯 URL ÉPURÉE INFAILLIBLE SANS PARAMÈTRE DE TEXTE INTÉGRÉ CONTRE ERREUR 404
                    lien_whatsapp_direct = "https://wa.me/22891836881"
                    
                    if self.page_flet:
                        try: await self.page_flet.launch_url(lien_whatsapp_direct)
                        except Exception: pass
                    
                    self.txt_commentaire.value = ""
                    self.update()
                else:
                    self.lbl_status.value = f"❌ {message}"
                    self.c_notif.bgcolor = "#fee2e2"
                    self.lbl_status.color = "#b91c1c"
                    self.update()
            except Exception as e:
                self.lbl_status.value = f"❌ Erreur : {str(e)}"
                self.c_notif.bgcolor = "#fee2e2"
                self.lbl_status.color = "#b91c1c"
                self.update()

    def changer_langue(self, n_lang: str): 
        """Propagation descendante linguistique."""
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)

    def actualiser_donnees_affichage(self):
        """Cycle de vie : Synchronise les listes au focus de la page."""
        self.cb_devise.value = self.app.devise_active
        
        m_index = DICTIONNAIRE_LANGUES.moteur_i18n.langues_disponibles_index
        code_courant = getattr(self.app, "langue_actuelle", "FR").upper()
        self.cb_langue.value = m_index.get(code_courant, code_courant)
        
        if hasattr(self.app, "sync_engine") and self.app.sync_engine:
            u_id = getattr(self.app, "user_id_connecte", "INVITE")
            c_p = self.app.sync_engine.charger_donnees_module(u_id, "PREFERENCES") or {}
            self.sc_ajustement.value = int(c_p.get("ajustement_hegiri", 0))
            
            cle_chargee = str(c_p.get("arbitrage_nisab", "PLUS_BAS")).upper()
            self.cle_nisab_active_memoire = cle_chargee
            self.app.cle_nisab_active_memoire = cle_chargee
        
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)

    def actualiser_contexte(self): 
        """Alias pour le routeur."""
        self.actualiser_donnees_affichage()
