"""
PANNEAU D'ACCUEIL INTERACTIF CONNECTÉ (GUI/PAGES/PAGE_ONBOARDING.PY)
Version Finale Intégrale - Totalement compatible Flet 0.86.2, Python 3.14 & APK Android (Partie 1)
"""
from __future__ import annotations
import flet as ft
from gui.langues import DICTIONNAIRE_LANGUES
from gui.pages.page_onboarding_alerts import compiler_alertes_espace_prive

class PageOnboarding(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.page_flet = app_reference.page
        self.mode_smartphone_interne = None
        
        # --- 1. CONFIGURATION DES COMPOSANTS DE L'EN-TÊTE ---
        self.lbl_bienvenue = ft.Text(size=20, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.lbl_sous_titre = ft.Text(size=12, italic=True, color="#4b5563")
        
        # Grille responsive pour les trois cartes de métriques (Fortune, Zakat, Score)
        self.grille_metrics = ft.ResponsiveRow(spacing=15, run_spacing=12)
        
        # Boîtes de conteneurs pour la suite des alertes (Prieres, Agenda)
        self.c_prieres = ft.Column(spacing=5, tight=True)
        self.cadre_prieres = ft.Container(
            content=ft.Column([
                ft.Text(value="🕋 Prières Échues", size=12, weight=ft.FontWeight.BOLD, color="#b91c1c"),
                self.c_prieres
            ], spacing=6),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#b91c1c"),
            visible=False, expand=True
        )

        # 🎯 FIX TECHNIQUE GEOMÉTRIE : horizontal_alignment=STRETCH force TOUS les cadres à occuper 100% de la largeur
        self.layout_principal = ft.Column([
            self.lbl_bienvenue,
            self.lbl_sous_titre,
            ft.Container(height=5),
            self.grille_metrics,
            ft.Container(height=5),
            self.cadre_prieres
        ], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

        super().__init__(
            content=self.layout_principal,
            expand=True,
            bgcolor=ft.Colors.WHITE,
            padding=ft.Padding(left=20, right=20, top=15, bottom=15)
        )

        # Branchement direct et abonnement au gestionnaire linguistique i18n
        if hasattr(DICTIONNAIRE_LANGUES, "moteur_i18n"):
            DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_changement_langue)
        self.actualiser_donnees_affichage()

    def action_changement_langue(self, nuevo_dic: dict):
        """Met à jour l'interface lors d'une modification linguistique globale."""
        self.actualiser_contexte()

    def actualiser_contexte(self):
        """Ré-oriente l'affichage selon le type de session active (Visiteur ou Connecté Live)."""
        if getattr(self.app, "est_mode_connecte", False):
            self.rendre_tableau_de_bord_connecte()
        else:
            self.rendre_page_vitrine_visiteur()

    def rendre_tableau_de_bord_connecte(self):
        """Génère l'affichage complet des métriques financières et spirituelles SQLite."""
        u_id = self.app.user_id_connecte
        dev = getattr(self.app, "devise_active", "XOF")
        fiqh = getattr(self.app, "madhhab_actif", "Malikite")
        
        txt_onb = DICTIONNAIRE_LANGUES.actif.get("onboarding", {})
        txt_zk = DICTIONNAIRE_LANGUES.actif.get("zakat", {})

        # Extraction sécurisée des données du disque
        c_fin = self.app.sync_engine.charger_donnees_module(u_id, "FINANCES") or {}
        c_sp = self.app.sync_engine.charger_donnees_module(u_id, "MOUHASABAH") or {}
        c_arb = self.app.sync_engine.charger_donnees_module(u_id, "PROFIL") or {}
        c_pref = self.app.sync_engine.charger_donnees_module(u_id, "PREFERENCES") or {}

        ajust_hegiri = int(c_pref.get("ajustement_hegiri", 0))

        # Évaluation patrimoniale
        val_grain = float(c_fin.get("poids", 0.0)) * float(c_fin.get("grain_cours", 0.0))
        val_ovin = float(c_fin.get("ovins", 0)) * float(c_fin.get("ovin_cours", 0.0))
        val_bovin = float(c_fin.get("bovins", 0)) * float(c_fin.get("bovin_cours", 0.0))
        total_agro = val_grain + val_ovin + val_bovin

        brut = float(c_fin.get("immo", 0)) + float(c_fin.get("auto", 0)) + float(c_fin.get("liq", 0)) + float(c_fin.get("creances", 0)) + total_agro
        net = brut - float(c_fin.get("dettes", 0))
        score = c_sp.get("score_spirituel", 0)

        nom_c = f"{c_arb.get('prenom', '')} {c_arb.get('nom', '')}".strip()
        if not nom_c or nom_c == "- -": 
            nom_c = self.app.nom_utilisateur_connecte

        self.lbl_bienvenue.value = str(txt_onb.get("bienvenue", "Assalâmou Alaykoum, {} 🌟")).format(nom_c.upper())
        fiqh_traduit = DICTIONNAIRE_LANGUES.actif.get("barre_outils", {}).get("ecoles", {}).get(fiqh, fiqh)
        self.lbl_sous_titre.value = str(txt_onb.get("sous_titre", "Rapport de vigilance doctrinale — École {}")).format(str(fiqh_traduit).upper())

        # 🎯 CALCUL DU SEUIL LÉGAL DE LA ZAKAT SUR COMPTE LIVE
        cours_or_db = float(c_fin.get("or_cours", 45000.0))
        nisab_or_calcul_sec = 85.0 * cours_or_db
        if net >= nisab_or_calcul_sec:
            statut_zakat_traduit = txt_zk.get('statut_eligible', '🔴 IMPOSABLE')
            couleur_statut_zakat = "#b91c1c"
        else:
            statut_zakat_traduit = txt_zk.get('statut_non_eligible', '🟢 EXEMPTÉ')
            couleur_statut_zakat = "#166534"

        # Métriques structurées adaptées en cartes Material 3
        metrics_data = [
            (txt_onb.get("titre_fortune", "Fortune Nette"), f"{net:.2f} {dev}", "#f0fdf4", "#166534"),
            (txt_onb.get("titre_zakat", "Statut Zakat"), statut_zakat_traduit, "#fffbeb", couleur_statut_zakat),
            (txt_onb.get("titre_mouhasabah", "Indice Spirituel"), f"{score}%", "#f0f9ff", "#0369a1")
        ]
        
        self.grille_metrics.controls.clear()
        for titre, val, bg_c, fg_c in metrics_data:
            self.grille_metrics.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text(value=str(titre).strip(), size=11, color="#4b5563", weight=ft.FontWeight.W_500),
                        ft.Text(value=str(val), size=14, color=fg_c, weight=ft.FontWeight.BOLD),
                    ], spacing=4, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=bg_c,
                    padding=ft.Padding(10, 12, 10, 12),
                    border_radius=8,
                    alignment=ft.Alignment(0, 0),
                    col={"xs": 12, "md": 4}
                )
            )
            
        self.poursuivre_construction_alertes(c_fin, c_sp, net, dev, fiqh, u_id, ajust_hegiri, txt_onb)

    def poursuivre_construction_alertes(self, c_fin: dict, c_sp: dict, net: float, dev: str, fiqh: str, u_id: str, ajust_hegiri: int, txt_onb: dict):
        """Construit les volets d'alertes avec une typographie Material 3 aérée et lisible."""
        from gui.pages.page_onboarding_alerts import compiler_alertes_espace_prive
        
        # 1. Extraction et formatage des alertes rituelles du disque
        txt_pr, txt_cal_complet, bg_c, fg_c = compiler_alertes_espace_prive(c_fin, c_sp, net, dev, fiqh, user_id=u_id, ajustement_lune=ajust_hegiri)

        # 2. Remplissage du bloc Prières Échues
        self.c_prieres.controls.clear()
        if "⚠️" in txt_pr or "VIGILANCE" in txt_pr:
            self.cadre_prieres.visible = True
            self.c_prieres.controls.append(
                ft.Text(value=str(txt_pr).strip(), size=12, weight=ft.FontWeight.W_500, color=fg_c)
            )
        else:
            self.cadre_prieres.visible = False

        # 3. Remplissage du calendrier ligne par ligne pour conserver l'interligne aérée
        if not hasattr(self, "cadre_calendrier") or self.cadre_calendrier not in self.layout_principal.controls:
            self.c_agenda = ft.Column(spacing=6, tight=True)
            self.cadre_calendrier = ft.Container(
                content=ft.Column([
                    ft.Text(value="🌙 " + str(txt_onb.get("cadre_calendrier", "Chronologie Sacrée")).strip(), size=12, weight=ft.FontWeight.BOLD, color="#d97706"),
                    self.c_agenda
                ], spacing=6),
                bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#d97706"), expand=True
            )
        
        # On force sa ré-injection physique en s'assurant qu'il n'est pas dupliqué
        if self.cadre_calendrier not in self.layout_principal.controls:
            self.layout_principal.controls.append(self.cadre_calendrier)

        self.c_agenda.controls.clear()
        self.cadre_calendrier.visible = True
        
        lignes_agenda = txt_cal_complet.split("\n")
        for ligne in lignes_agenda:
            if ligne.strip():
                coloration_item = "#0f766e" if "📅" in ligne or "Date" in ligne else "#374151"
                self.c_agenda.controls.append(
                    ft.Text(value=str(ligne).strip(), size=12, weight=ft.FontWeight.W_500, color=coloration_item)
                )

        if self.page_flet:
            try: self.update()
            except Exception: pass

    def rendre_page_vitrine_visiteur(self):
        """Affiche le volet d'accueil premium Material 3 pour les utilisateurs anonymes invités."""
        txt_auth = DICTIONNAIRE_LANGUES.actif.get("auth", {})
        txt_onb = DICTIONNAIRE_LANGUES.actif.get("onboarding", {})

        # Réinitialisation visuelle des blocs connectés
        self.grille_metrics.controls.clear()
        self.cadre_prieres.visible = False
        if hasattr(self, "cadre_calendrier"):
            self.cadre_calendrier.visible = False

        # Boutons d'accès (Conformes Python 3.14 content=ft.Text)
        btn_login = ft.ElevatedButton(
            content=ft.Text(str(txt_auth.get("deja_compte", "Se connecter")), size=12, weight=ft.FontWeight.BOLD),
            bgcolor="#064e3b", color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
            on_click=lambda _: self.app.basculer_ecran("CONNEXION")
        )
        
        btn_register = ft.ElevatedButton(
            content=ft.Text(str(txt_auth.get("pas_compte", "S'inscrire")), size=12, weight=ft.FontWeight.BOLD),
            bgcolor="#0f766e", color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
            on_click=lambda _: self.app.basculer_ecran("INSCRIPTION")
        )

        # 🎯 GRAND LOGO SVG PREMIUM : Confiné uniquement ici pour une lecture parfaite de HAYAATI
        logo_vitrine_hayaati = ft.Image(
            src="images/Logo-Hayaati.svg",
            width=220,  # Agrandissement pour rendre la marque parfaitement visible
            height=220,
            fit="contain"
        )

        # Boîte centrée d'onboarding Visiteur
        boite_vitrine = ft.Container(
            content=ft.Column([
                logo_vitrine_hayaati,  # Le logo vectoriel remplace l'en-tête texte brut
                ft.Container(height=4),
                ft.Text(value=str(txt_onb.get("guide_visiteur_humain", "Mode Simulation Tiers actif.")), size=12, color="#374151", text_align=ft.TextAlign.CENTER),
                ft.Container(height=10),
                ft.Row([btn_login, btn_register], spacing=12, alignment=ft.MainAxisAlignment.CENTER, wrap=True)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8, tight=True),
            bgcolor=ft.Colors.WHITE,
            padding=30,
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.GREY_200),
            width=440
        )

        # Nettoyage et centrage absolu de la vitrine d'accueil
        self.layout_principal.controls.clear()
        self.layout_principal.controls.append(
            ft.Container(content=boite_vitrine, expand=True, alignment=ft.Alignment(0, 0))
        )

        if self.page_flet:
            try: self.update()
            except Exception: pass

    def actualiser_donnees_affichage(self):
        """Cycle de vie : Force la ré-évaluation du tableau de bord complet au chargement de la page."""
        if getattr(self.app, "est_mode_connecte", False):
            self.layout_principal.controls.clear()
            
            # 🎯 SÉCURISATION DU RENDU FLUIDE : Ré-injection des pointeurs d'en-têtes fixes
            self.layout_principal.controls.extend([
                self.lbl_bienvenue,
                self.lbl_sous_titre,
                ft.Container(height=5),
                self.grille_metrics,
                ft.Container(height=5),
                self.cadre_prieres
            ])
            # Forçage de l'alignement horizontal sur la coque récurrente
            self.layout_principal.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
            
            if hasattr(self, "cadre_calendrier"):
                self.layout_principal.controls.append(self.cadre_calendrier)
                
        self.actualiser_contexte()

    def actualiser_contexte(self):
        """Route le rendu vers le bon état de session."""
        if getattr(self.app, "est_mode_connecte", False):
            self.rendre_tableau_de_bord_connecte()
        else:
            self.rendre_page_vitrine_visiteur()
