"""
PANNEAU DE GESTION DE L'IDENTITÉ ET DU PROFIL UTILISATEUR (GUI/PAGES/PAGE_PROFIL.PY)
Version Finale Intégrale Statique - Totalement compatible Flet 0.86.2, Python 3.14 & APK Android (Partie 1)
"""
from __future__ import annotations
import flet as ft
from gui.langues import DICTIONNAIRE_LANGUES
from core import pays_devises
from gui.components.selecteur_recherche import SelecteurRecherche

class PageProfil(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.page_flet = app_reference.page
        self.mode_mobile = None
        
        # Liste des clés techniques du formulaire d'identité
        self.cles_champs = [
            "prenom", "nom", "username", "email", 
            "password", "confirm_password", "birth", 
            "tel", "pays", "ville", "profession"
        ]
        self.labels: dict[str, ft.Text] = {}
        self.entries: dict[str, ft.TextField] = {}
        
        # --- 1. INSTANCIATION DES COMPOSANTS GRAPHIQUES MATERIAL 3 ---
        # 📂 BLOC STATUS DE SESSION
        self.lbl_info_id = ft.Text(size=11, color="#4b5563")
        self.lbl_info_sec = ft.Text(size=11, weight=ft.FontWeight.BOLD, color="#166534")
        self.lbl_cadre_status = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#064e3b")
        
        self.c_status = ft.Container(
            content=ft.Column([
                self.lbl_cadre_status,
                self.lbl_info_id,
                self.lbl_info_sec
            ], spacing=4),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#064e3b")
        )

        # 📂 BLOC IDENTITÉ ET SÉCURITÉ NUMÉRIQUE
        self.lbl_cadre_identite = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.grille_profil = ft.ResponsiveRow(spacing=12, run_spacing=12)
        
        self.c_identite = ft.Container(
            content=ft.Column([
                self.lbl_cadre_identite,
                self.grille_profil
            ], spacing=8),
            bgcolor=ft.Colors.WHITE, padding=15, border_radius=8, border=ft.Border.all(1, "#064e3b")
        )

        # Génération dynamique des zones de saisie responsive
        for c in self.cles_champs:
            self.labels[c] = ft.Text(size=11, weight=ft.FontWeight.BOLD, color="#4b5563")
            
            if c == "birth":
                # ⚠️ CORRECTION 09/09/2026 : sans content_padding explicite,
                # le padding Material par défaut de Flet est plus généreux
                # sur Android que sur PC. Combiné à une largeur fixe étroite
                # (82/95px), il grignotait l'espace horizontal disponible
                # pour le texte, coupant les derniers chiffres de l'année
                # (ex. "2005" affiché "200"). content_padding resserré +
                # largeur/hauteur légèrement augmentées pour garder une
                # marge de sécurité sur toutes les densités d'écran.
                pad_date = ft.Padding(left=6, top=0, right=0, bottom=0)
                self.cb_jour = ft.Dropdown(
                    options=[ft.dropdown.Option(f"{i:02d}") for i in range(1, 32)],
                    width=88, height=42, text_size=12, value="07", dense=True,
                    bgcolor=ft.Colors.WHITE, content_padding=pad_date
                )
                self.cb_mois = ft.Dropdown(
                    options=[ft.dropdown.Option(f"{i:02d}") for i in range(1, 13)],
                    width=88, height=42, text_size=12, value="04", dense=True,
                    bgcolor=ft.Colors.WHITE, content_padding=pad_date
                )
                self.cb_annee = ft.Dropdown(
                    options=[ft.dropdown.Option(str(i)) for i in range(1930, 2027)],
                    width=104, height=42, text_size=12, value="1988", dense=True,
                    bgcolor=ft.Colors.WHITE, content_padding=pad_date
                )
                
                self.c_date_triple = ft.Row([self.cb_jour, self.cb_mois, self.cb_annee], spacing=3, alignment=ft.MainAxisAlignment.START)
                
                cellule_formulaire = ft.Container(
                    content=ft.Column([self.labels[c], self.c_date_triple], spacing=6), col={"xs": 12, "md": 6}
                )
                self.grille_profil.controls.append(cellule_formulaire)
            elif c == "pays":
                # 15/10/2026 : sélecteur avec suggestions pendant la saisie (tous les pays du monde).
                # entries["pays"] reste le TextField du sélecteur : le reste du code lit toujours .value.
                self.selecteur_pays = SelecteurRecherche(
                    rechercher=lambda q: [p["c"] for p in pays_devises.chercher_pays(q, self._lang())],
                    libelle_de=lambda code: pays_devises.nom_pays(code, self._lang()),
                    exact=pays_devises.deviner_pays,
                    on_select=lambda code: self._maj_devise_associee(),
                    rtl=(self._lang() == "ar"),
                )
                self.entries[c] = self.selecteur_pays.champ
                setattr(self, f"en_{c}", self.entries[c])
                self.lbl_devise_pays = ft.Text("", size=11, color="#4b5563", italic=True)
                cellule_formulaire = ft.Container(
                    content=ft.Column([self.labels[c], self.selecteur_pays, self.lbl_devise_pays], spacing=6),
                    col={"xs": 12, "md": 6},
                )
                self.grille_profil.controls.append(cellule_formulaire)
            else:
                est_masque = c in ["password", "confirm_password"]
                # ⚠️ CORRECTION 09/09/2026 : content_padding explicite et
                # hauteur légèrement augmentée (40→44), même raison que les
                # dropdowns de date ci-dessus — le padding par défaut
                # d'Android déborde de la hauteur fixée sans lui, ce qui
                # écrasait visuellement le label juste au-dessus.
                self.entries[c] = ft.TextField(
                    value="-", height=44, text_size=13, password=est_masque, can_reveal_password=est_masque,
                    border_radius=6, border_color=ft.Colors.GREY_400, bgcolor=ft.Colors.WHITE,
                    content_padding=ft.Padding(left=10, top=6, right=10, bottom=6)
                )
                setattr(self, f"en_{c}", self.entries[c])
                
                cellule_formulaire = ft.Container(
                    content=ft.Column([self.labels[c], self.entries[c]], spacing=6), col={"xs": 12, "md": 6}
                )
                self.grille_profil.controls.append(cellule_formulaire)

        # Boutons d'actions réactifs (Syntaxe immunisée Python 3.14 content=ft.Text)
        self.btn_sauver = ft.ElevatedButton(
            content=ft.Text("Enregistrer", size=13, weight=ft.FontWeight.BOLD),
            bgcolor="#064e3b", color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
            on_click=lambda _: self.sauvegarder_profil_disque()
        )

        self.btn_purger = ft.ElevatedButton(
            content=ft.Text("Purger les données", size=12, weight=ft.FontWeight.BOLD),
            bgcolor="#b91c1c", color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
            on_click=lambda _: self.purger_donnees_locales()
        )

        # Zone de notification basse
        self.lbl_status = ft.Text(size=12, italic=True, color="#4b5563", text_align=ft.TextAlign.CENTER)
        self.c_notif = ft.Container(
            content=self.lbl_status, bgcolor="#f3f4f6", padding=10, border_radius=6, alignment=ft.Alignment(0, 0)
        )

        # 🎯 BOUTON RETOUR ÉMOJI INVARIANT (Désenclave la page Profil)
        self.btn_retour_reglages = ft.IconButton(
            icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
            icon_color="#064e3b",
            icon_size=16,
            tooltip="↩️",
            on_click=lambda _: self.app.layout_central.basculer_vers_ecran("REGLAGES") # 🌟 Fait demi-tour vers les Réglages !
        )

        # 🌟 Réorganisation : Le bouton retour s'ancre au sommet absolu de la colonne
        self.layout_profil = ft.Column([
            self.btn_retour_reglages, # ➔ Première position
            self.c_status,
            self.c_identite,
            ft.Row([self.btn_sauver, self.btn_purger], spacing=15, alignment=ft.MainAxisAlignment.START, wrap=True),
            self.c_notif
        ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)

        super().__init__(
            content=self.layout_profil, expand=True, bgcolor="#f8fafc",
            padding=ft.Padding(left=15, right=15, top=15, bottom=15)
        )

        # Liaison i18n
        if hasattr(DICTIONNAIRE_LANGUES, "moteur_i18n"):
            DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_langue)
        self.actualiser_donnees_affichage()

    def action_langue(self, dic: dict):
        """Met à jour l'interface lors d'une modification linguistique globale."""
        self.traduire_page(dic)

    # ============================================================
    # 🎯 PARTIE 2/2 : TRADUCTION, PERSISTANCE SQLITE ET PURGE LOCALE
    # ============================================================

    def traduire_page(self, dic: dict):
        """Met à jour dynamiquement tous les labels du formulaire depuis le JSON."""
        if not dic:
            return
        p = dic.get("profil", {})
        self._actualiser_selecteur_pays(p)
        
        self.lbl_cadre_status.value = str(p.get("titre_vue", "Profil"))
        self.lbl_info_id.value = f"{p.get('lbl_identifiant', 'ID :')} {getattr(self.app, 'user_id_connecte', '-')}"
        self.lbl_info_sec.value = f"🛡️ {p.get('statut_connecte', 'Sécurisé')}"
        
        self.lbl_cadre_identite.value = str(p.get("lbl_statut_compte", "Formulaire d'Identité"))
        
        if self.btn_sauver.content:
            self.btn_sauver.content.value = str(p.get("btn_sauvegarder", "Enregistrer"))
        if self.btn_purger.content:
            self.btn_purger.content.value = str(p.get("btn_purger", "Purger les données"))

        mapping_labels_ihm = {
            "prenom": p.get("lbl_prenom", "Prénom :"),
            "nom": p.get("lbl_nom", "Nom :"),
            "username": p.get("lbl_username", "Utilisateur :"),
            "email": p.get("lbl_email", "Email :"),
            "password": p.get("lbl_password", "Mot de passe :"),
            "confirm_password": p.get("lbl_confirm_password", "Confirmation :"),
            "birth": p.get("lbl_birth", "Naissance :"),
            "tel": p.get("lbl_tel", "Téléphone :"),
            "pays": p.get("lbl_pays", "Pays :"),
            "ville": p.get("lbl_ville", "Ville :"),
            "profession": p.get("lbl_profession", "Profession :")
        }

        for k, text_traduit in mapping_labels_ihm.items():
            if k in self.labels:
                self.labels[k].value = str(text_traduit)

        if self.page_flet:
            try: self.update()
            except Exception: pass

    # ------------------------------------------------------------------
    # 15/10/2026 : PAYS (sélecteur avec suggestions) et DEVISE automatique
    # ------------------------------------------------------------------
    def _lang(self) -> str:
        return str(getattr(self.app, "langue_actuelle", "FR")).lower()

    def _maj_ctrl(self, *controles):
        for c in controles:
            try:
                c.update()
            except Exception:
                pass

    def _actualiser_selecteur_pays(self, p: dict):
        """Changement de langue : réécrit le nom du pays choisi et l'invite de saisie."""
        sel = getattr(self, "selecteur_pays", None)
        if sel is None:
            return
        sel.actualiser_langue(hint=str(p.get("pays_recherche", "Tapez le nom du pays…")), rtl=(self._lang() == "ar"))
        self._maj_devise_associee()

    def _maj_devise_associee(self):
        """« Devise associée : XOF - franc CFA » sous le champ (information ; appliquée à l'enregistrement)."""
        if not hasattr(self, "lbl_devise_pays"):
            return
        devise = pays_devises.devise_du_pays(self.selecteur_pays.value)
        modele = DICTIONNAIRE_LANGUES.actif.get("profil", {}).get("pays_devise_associee", "Devise associée : {devise}")
        self.lbl_devise_pays.value = (
            modele.replace("{devise}", pays_devises.libelle_devise(devise, self._lang())) if devise else "")
        self._maj_ctrl(self.lbl_devise_pays)

    def _charger_pays(self, donnees_profil: dict):
        brut = str(donnees_profil.get("pays", "") or "")
        texte = "" if brut.strip() in ("", "-") else brut
        code = donnees_profil.get("pays_code") or pays_devises.deviner_pays(texte)
        if code:
            self.selecteur_pays.definir(code)
        else:
            self.selecteur_pays.definir_texte_libre(texte)
        self._maj_devise_associee()

    def _appliquer_devise_pays(self, u_id, code_pays):
        """Applique la devise du pays (réglage, application et base). Retourne le code de la devise
        appliquée, ou None : pas de pays, devise choisie à la main dans les Réglages (conservée), ou
        déjà à jour."""
        devise = pays_devises.devise_du_pays(code_pays)
        sync = getattr(self.app, "sync_engine", None)
        if not devise or not sync:
            return None
        try:
            profil = sync.charger_donnees_module(u_id, "PROFIL") or {}
            if profil.get("devise_manuelle"):
                return None
            pref = sync.charger_donnees_module(u_id, "PREFERENCES") or {}
            if str(pref.get("devise_defaut", "")).upper() == devise and getattr(self.app, "devise_active", None) == devise:
                return None
            pref["devise_defaut"] = devise
            sync.executer_sauvegarde_module("INVITE", "PREFERENCES", pref)
            sync.executer_sauvegarde_module(u_id, "PREFERENCES", pref)
            self.app.devise_active = devise
            try:
                import sqlite3
                from gui.pages.page_onboarding_alerts import obtenir_chemin_base_donnees
                conn = sqlite3.connect(obtenir_chemin_base_donnees())
                conn.execute("UPDATE comptes_utilisateurs SET devise_defaut = ? WHERE user_id = ?", (devise, str(u_id)))
                conn.commit()
                conn.close()
            except Exception as exc:
                print(f"[PROFIL] Devise du pays non enregistrée en base : {exc}")
            return devise
        except Exception as exc:
            print(f"[PROFIL] Application de la devise du pays impossible : {exc}")
            return None

    def sauvegarder_profil_disque(self):
        """Enregistre l'ensemble des données d'identité dans l'espace chiffré et synchronise l'âge."""
        if not getattr(self.app, "est_mode_connecte", False):
            self.lbl_status.value = "❌ Action impossible hors connexion."
            self.c_notif.bgcolor = "#fee2e2"
            self.lbl_status.color = "#991b1b"
            self.update()
            return
            
        try:
            u_id = self.app.user_id_connecte
            p = DICTIONNAIRE_LANGUES.actif.get("profil", {})
            
            # 1. Compilation des champs textes standard depuis les TextField Flet
            profil_dict = {c: self.entries[c].value.strip() for c in self.cles_champs if c in self.entries}
            # 15/10/2026 : le pays est mémorisé par son CODE ISO ; le nom est écrit dans la langue courante
            # (il sert aux certificats PDF). devise_manuelle (posée par la page Réglages) est conservée.
            code_pays = self.selecteur_pays.value or pays_devises.deviner_pays(profil_dict.get("pays", ""))
            profil_dict["pays_code"] = code_pays or ""
            if code_pays:
                profil_dict["pays"] = pays_devises.nom_pays(code_pays, self._lang())
            try:
                ancien_profil = self.app.sync_engine.charger_donnees_module(u_id, "PROFIL") or {}
                profil_dict["devise_manuelle"] = bool(ancien_profil.get("devise_manuelle", False))
            except Exception:
                profil_dict["devise_manuelle"] = False
            
            # 2. Reconstitution de la date sécurisée depuis les 3 Dropdowns (Format AAAA-MM-DD)
            date_formatee = f"{self.cb_annee.value}-{self.cb_mois.value}-{self.cb_jour.value}"
            profil_dict["birth"] = date_formatee
            
            # 3. Sauvegarde dans le SyncEngine pour le cache PROFIL
            if hasattr(self.app, "sync_engine") and self.app.sync_engine:
                self.app.sync_engine.executer_sauvegarde_module(u_id, "PROFIL", profil_dict)
            
            # =====================================================================
            # 🎯 4. EXÉCUTION DU CORRECTIF SQL DIRECT SUR LA TABLE NATIVE COMMPTES
            # =====================================================================
            import sqlite3
            from gui.pages.page_onboarding_alerts import obtenir_chemin_base_donnees
            
            conn = sqlite3.connect(obtenir_chemin_base_donnees())
            cur = conn.cursor()
            
            cur.execute("""
                UPDATE comptes_utilisateurs 
                SET date_naissance = ?, date_naissance_definie = 1
                WHERE user_id = ?
            """, (date_formatee, str(u_id)))
            
            conn.commit()
            conn.close()
            # =====================================================================
                
            devise_appliquee = self._appliquer_devise_pays(u_id, profil_dict.get("pays_code"))
            self.lbl_status.value = str(p.get("status_ok_profil", "✓ Profil mis à jour."))
            if devise_appliquee:
                self.lbl_status.value += "  " + str(p.get("pays_devise_appliquee", "Devise ajustée : {devise}")).replace(
                    "{devise}", pays_devises.libelle_devise(devise_appliquee, self._lang()))
            self.c_notif.bgcolor = "#d1fae5"
            self.lbl_status.color = "#064e3b"
            
            # Mise à jour des pointeurs de session globaux de l'app maîtresse
            if "ville" in profil_dict: self.app.ville_utilisateur = profil_dict["ville"]
            if "pays" in profil_dict: self.app.pays_utilisateur = profil_dict["pays"]
            if "tel" in profil_dict: self.app.telephone_utilisateur = profil_dict["tel"]
            
            # Force l'application à recharger l'accueil et à recalculer l'âge hégirien
            if hasattr(self.app, "declencher_changement_global"):
                self.app.declencher_changement_global()
            else:
                self.update()
                
        except Exception as e:
            self.lbl_status.value = f"❌ Erreur : {str(e)}"
            self.c_notif.bgcolor = "#fee2e2"
            self.lbl_status.color = "#991b1b"
            self.update()

    def purger_donnees_locales(self):
        """Purge la session de l'auditeur en exécutant une déconnexion synchrone."""
        if hasattr(self.app, "executer_deconnexion_session"):
            self.app.executer_deconnexion_session()

    def changer_langue(self, n_lang: str):
        """Liaison avec la propagation descendante du Layout central."""
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)

    def actualiser_donnees_affichage(self):
        """Recharge les informations de l'auditeur et synchronise le sélecteur de date."""
        self.lbl_status.value = ""
        self.c_notif.bgcolor = "#f3f4f6"
        self.lbl_status.color = "#4b5563"
        
        if getattr(self.app, "est_mode_connecte", False) and getattr(self.app, "sync_engine", None):
            donnees_profil = self.app.sync_engine.charger_donnees_module(self.app.user_id_connecte, "PROFIL") or {}
            
            # Injection dans les champs textes standard
            for c in self.cles_champs:
                if c != "birth" and c in donnees_profil and c in self.entries:
                    self.entries[c].value = str(donnees_profil.get(c, "-"))
            
            self._charger_pays(donnees_profil)      # 15/10/2026 : pays = sélecteur (code ISO)
            # Découpage et réinjection de la date mémorisée dans les Dropdowns Flet
            date_sauvegardee = donnees_profil.get("birth", "2000-01-01")
            if "-" in date_sauvegardee and len(date_sauvegardee.split("-")) == 3:
                aaaa, mm, jj = date_sauvegardee.split("-")
                
                # Alignement sécurisé des valeurs sélectionnées dans les listes déroulantes
                self.cb_annee.value = str(aaaa)
                self.cb_mois.value = str(mm)
                self.cb_jour.value = str(jj)
                    
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)

    def actualiser_contexte(self):
        """Alias pour le routeur central."""
        self.actualiser_donnees_affichage()
