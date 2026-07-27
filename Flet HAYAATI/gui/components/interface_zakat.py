"""
INTERFACE DE LA ZAKAT LIVE AUTOMATIQUE (GUI/COMPONENTS/INTERFACE_ZAKAT.PY)
Version 6.2 - Initialisation, Cadres Responsives, Traduction Intégrale Flet 0.86.2 (Partie 1)
"""
from __future__ import annotations
import flet as ft
from datetime import datetime
from gui.langues import DICTIONNAIRE_LANGUES
from core.financial_engine import FinancialEngine
from core.certificate_engine import generer_certificat_pdf

class EcranZakat(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.page_flet = app_reference.page
        self.mode_mobile = None
        
        # Initialisation du moteur financier d'origine
        self.moteur_finance = FinancialEngine(
            sync_engine_reference=getattr(self.app, "sync_engine", None)
        )
        
        # Structure de stockage des résultats de calculs rituels
        self.fortune_calculee = {
            "liq": 0.0, "or": 0.0, "argent": 0.0, 
            "due": 0.0, "creances": 0.0, "dettes": 0.0
        }
        self.agri_calcule = {"poids": 0.0, "due": 0.0}
        self.pastoral_calcule = {
            "o": "Exempté", "b": "Exempté", "ovins": 0, "bovins": 0
        }
        self.intrants_mem = {}

        # --- 1. INSTANCIATION DES COMPOSANTS GRAPHIQUES MATERIAL 3 ---
        # Bandeau doctrinal supérieur
        self.lbl_info_fiqh = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.c_mode = ft.Container(
            content=self.lbl_info_fiqh,
            bgcolor="#d1fae5", padding=ft.Padding(10, 8, 10, 8),
            border_radius=6, border=ft.Border.all(1, "#064e3b"),
            alignment=ft.Alignment(0, 0)
        )

        # Cadre d'affichage des cours référentiels en direct
        self.lbl_cadre_cours = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.lbl_cours_or = ft.Text(size=11, weight=ft.FontWeight.W_500, color="#4b5563")
        self.lbl_cours_argent = ft.Text(size=11, weight=ft.FontWeight.W_500, color="#4b5563")
        
        self.cadre_cours_live = ft.Container(
            content=ft.Column([
                self.lbl_cadre_cours,
                self.lbl_cours_or,
                self.lbl_cours_argent
            ], spacing=4),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#e2e8f0")
        )

        # Cadre d'affichage du Grand Rapport de Bilan Élárgi
        self.lbl_cadre_res = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#064e3b")
        
        # 🎯 FIX TECHNIQUE RESPONSIVE : expand=True force le TextField à s'étendre sur toute la largeur
        self.text_rapport = ft.TextField(
            multiline=True, min_lines=8, max_lines=14, text_size=13, read_only=True,
            text_style=ft.TextStyle(font_family="Courier New"),
            border_color=ft.Colors.GREY_400, bgcolor="#f9fafb",
            expand=True
        )

        # 🎯 FIX HARMONISATION : expand=True sur la colonne et le Container supprime le blocage à gauche
        self.cadre_res = ft.Container(
            content=ft.Column([self.lbl_cadre_res, self.text_rapport], spacing=6, expand=True),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#064e3b"),
            expand=True
        )

        # Bouton d'exportation de certificat PDF Sharia-Compliant (🎯 FIX : Assignation de self.btn_pdf conforme)
        self.btn_pdf = ft.ElevatedButton(
            content=ft.Text(value="Générer PDF", size=13, weight=ft.FontWeight.BOLD),
            bgcolor="#064e3b", color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
            on_click=lambda _: self.imprimer_pdf_live_nominatif()
        )

        # Structure globale empilée défilante fluide
        self.layout_zakat = ft.Column([
            self.c_mode,
            self.cadre_cours_live,
            self.cadre_res,
            self.btn_pdf
        ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)

        super().__init__(
            content=self.layout_zakat, expand=True, bgcolor="#f8fafc",
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
        """Injecte les données i18n traduits dans les contrôles graphiques correspondants."""
        if not dic:
            return
            
        z = dic.get("zakat", {})
        b = dic.get("barre_outils", {})
        
        # Capture et traduction de l'école juridique active
        ecole_technique = getattr(self.app, 'madhhab_actif', 'Malikite')
        ecole_traduite = b.get("ecoles", {}).get(ecole_technique, ecole_technique)
        
        self.lbl_info_fiqh.value = f"🔄 {b.get('mode_live', 'Live / Visiteur')} | {b.get('label_fiqh', 'Fiqh :')} {ecole_traduite}"
        self.lbl_cadre_cours.value = str(z.get("cadre_cours", "Cours Référentiels"))
        self.lbl_cadre_res.value = str(z.get("cadre_analyse", "Rapport"))
        
        if self.btn_pdf.content:
            self.btn_pdf.content.value = str(z.get("btn_imprimer", "Générer PDF"))

        if self.page_flet:
            try:
                self.update()
            except Exception:
                pass

    # ============================================================
    # 🎯 PARTIE 2/2 : ALGORITHME SHARIA LIVE ET ACCÈS CERTIFICAT PDF
    # ============================================================

    def actualiser_contexte(self):
        """Calcule les quotas rituels de purification et dresse le bilan à l'écran."""
        u_id = getattr(self.app, "user_id_connecte", None)
        doctrine = getattr(self.app, "madhhab_actif", "Malikite")
        dev = getattr(self.app, "devise_active", "XOF")
        
        c_or, c_arg = 45000.0, 650.0
        agri_brut_kg = 0.0
        
        if getattr(self.app, "sync_engine", None) and u_id:
            cache_fin = self.app.sync_engine.charger_donnees_module(u_id, "FINANCES") or {}
            c_or = float(cache_fin.get("or_cours", 45000.0))
            c_arg = float(cache_fin.get("argent_cours", 650.0))
            agri_brut_kg = float(cache_fin.get("poids", 0.0))

        # 🌐 Extraction unifiée et dynamique des dictionnaires i18n actifs
        langue_active = DICTIONNAIRE_LANGUES.actif
        txt_zk = l_active.get("zakat", {}) if (l_active := langue_active) else {}
        txt_auth = l_active.get("auth", {}) if l_active else {}
        
        # 🎯 ALIGNEMENT DU FIQH TRADUIT (Évite l'apparition de la clé technique brute)
        ecole_traduite = langue_active.get("barre_outils", {}).get("ecoles", {}).get(doctrine, doctrine)

        self.lbl_cours_or.value = f"🔸 {txt_zk.get('lbl_cours_or', 'Cours Or')} : {c_or:.0f} {dev}/g"
        self.lbl_cours_argent.value = f"🔸 {txt_zk.get('lbl_cours_argent', 'Cours Argent')} : {c_arg:.0f} {dev}/g"

        try:
            res = self.moteur_finance.executer_audit_zakat_complet(
                mode_persistant=True, user_id=u_id, madhhab_actif=doctrine, cours_or_terrain=c_or
            )
            
            n_or = res.get("nissab_or_nominal", 85.0 * c_or)
            n_arg = res.get("nissab_argent_nominal", 595.0 * c_arg)
            net = res.get("assiette_financiere_nette", 0.0)
            z_due = res.get("zakat_monetaire_due", 0.0)

            self.fortune_calculee = {
                "liq": net, 
                "or": res.get("valeur_or_retenue_zakat", 0.0), 
                "argent": res.get("valeur_argent_retenue_zakat", 0.0), 
                "due": z_due, 
                "creances": res.get("creances_humaines_incluses", 0.0), 
                "dettes": res.get("dettes_humaines_deduites", 0.0)
            }
            
            self.agri_calcule = {"poids": agri_brut_kg, "due": res.get("zakat_agricole_due_kg", 0.0)}
            self.pastoral_calcule = {
                "o": res.get("obligation_ovins", "0"), 
                "b": res.get("obligation_bovins", "0"), 
                "ovins": res.get("brut_ovins", 0), 
                "bovins": res.get("brut_bovins", 0)
            }

            # 🎯 TRADUCTION DU SEUIL ET BAROMETRE SÉLECTIONNÉ DE MANIÈRE ÉTANCHE
            lbl_m_ref = res.get('metal_seuil_reference', 'OR')
            if "OR" in str(lbl_m_ref).upper():
                lbl_m_ref = txt_zk.get("options_nisab", {}).get("nisab_or", "Or (85g)")
            elif "ARGENT" in str(lbl_m_ref).upper():
                lbl_m_ref = txt_zk.get("options_nisab", {}).get("nisab_argent", "Argent (595g)")

            # 🎯 AJOUT DE SÉCURITÉ : On stocke le texte exact affiché à l'écran pour le PDF
            self.nisab_affiche_ecran = lbl_m_ref

            p_or_poids = res.get('or_imposable_poids', 0.0)
            p_ag_poids = res.get('argent_imposable_poids', 0.0)
            
            self.intrants_mem = {
                "LIQUIDE": f"{net:.2f} {dev}",
                "OR": f"{self.fortune_calculee['or']:.2f} {dev} ({p_or_poids:.1f}g)",
                "ARGENT": f"{self.fortune_calculee['argent']:.2f} {dev} ({p_ag_poids:.1f}g)",
                "DETTES": f"-{self.fortune_calculee['dettes']:.2f} {dev}",
                "CREANCES": f"{self.fortune_calculee['creances']:.2f} {dev}",
                "AGRO": f"{agri_brut_kg:.1f} kg"
            }

            titre_traduit = txt_zk.get("rapport_titre", "BILAN DE ZAKAT")

            # 🎯 RECONSTRUCTION DU RAPPORT TEXTUEL MULTILINGUE SÉCURISÉ POUR L'ÉCRAN
            v = f" 🕋 {titre_traduit} ({ecole_traduite.upper()}) :\n"
            v += " ==================================================\n\n"
            v += f"   • {txt_zk.get('options_nisab', {}).get('nisab_or', 'Or')} : {n_or:.2f} {dev}\n"
            v += f"   • {txt_zk.get('options_nisab', {}).get('nisab_argent', 'Argent')}  : {n_arg:.2f} {dev}\n"
            v += f"   • {txt_zk.get('lbl_guide_nisab', 'Baromètre')} : {lbl_m_ref}\n"
            v += f"   • {txt_zk.get('nisab_applique', 'Nisab')} : {res.get('statut_doctrine_or', '')}\n"
            v += f"   • {txt_zk.get('assiette_imposable', 'Assiette')}   : {net:.2f} {dev}\n\n"
            v += " --------------------------------------------------\n"
            v += f"   ▶ {txt_zk.get('montant_du', 'Zakat')} (2.5%)  : {z_due:.2f} {dev}\n"
            v += f"   ▶ {txt_zk.get('zakat_grain', 'Agricole')}          : {self.agri_calcule['due']:.2f} kg\n"
            v += f"   ▶ {txt_zk.get('zakat_moutons', 'Ovins')}   -> {self.pastoral_calcule['o']}\n"
            v += f"   ▶ {txt_zk.get('zakat_bovins', 'Bovins')}  -> {self.pastoral_calcule['b']}\n"
            v += " ==================================================\n"
            
            self.text_rapport.value = v
        except Exception:
            self.text_rapport.value = f"⚠️ {txt_auth.get('err_champs_vides', 'Erreur de calcul ou données manquantes.')}"

        if self.page_flet:
            try:
                self.update()
            except Exception:
                pass

    def imprimer_pdf_live_nominatif(self):
        """Compile les quotas et génère le certificat PDF Sharia-Compliant."""
        if not self.intrants_mem: 
            return
        dev = getattr(self.app, "devise_active", "XOF")
        langue_active = DICTIONNAIRE_LANGUES.actif
        txt_zk = l_active.get("zakat", {}) if (l_active := langue_active) else {}
        
        identite = {
            "nom": getattr(self.app, "nom_utilisateur_connecte", "Inconnu"), 
            "prenom": "", 
            "ville": getattr(self.app, "ville_utilisateur", "Espace"), 
            "pays": getattr(self.app, "pays_utilisateur", "Privé"), 
            "telephone": getattr(self.app, "telephone_utilisateur", "-")
        }
        
        self.lignes_mem = [
            [f"{txt_zk.get('assiette_imposable', 'Assiette')} : {self.fortune_calculee['liq']:.2f} {dev}"],
            [f"{txt_zk.get('montant_du', 'Zakat monétaire due')} (2.5%) : {self.fortune_calculee['due']:.2f} {dev}"],
            [f"{txt_zk.get('zakat_grain', 'Zakat Agricole')} : {self.agri_calcule['due']:.2f} kg"],
            [f"{txt_zk.get('zakat_moutons', 'Zakat Ovins')} : {self.pastoral_calcule['o']}"],
            [f"{txt_zk.get('zakat_bovins', 'Zakat Bovins')} : {self.pastoral_calcule['b']}"]
        ]
        
        nisab_live_texte = getattr(self, "nisab_affiche_ecran", txt_zk.get("options_nisab", {}).get("nisab_plus_bas", "Baromètre Prudent"))

        # Envoi au compilateur PDF avec la valeur textuelle validée à l'écran
        generer_certificat_pdf(
            identite, 
            "ZAKAT", 
            self.app.madhhab_actif, 
            dev, 
            self.intrants_mem, 
            self.lignes_mem, 
            nisab_label=nisab_live_texte
        )

    def changer_langue(self, n_lang: str): 
        """Méthode invoquée par la propagation descendante du Layout central."""
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)
        
    def actualiser_donnees_affichage(self): 
        """Cycle de vie : Déclenche le re-calcul et force l'affichage i18n différé."""
        # 1. Calculer d'abord les avoirs, métaux et bétails (Synchrone)
        self.actualiser_contexte()
        
        # 2. 🎯 FORÇAGE ASYNCHRONE DIFFÉRÉ : Laisse 60ms à Flutter pour ancrer le bouton 
        # avant d'y injecter de force le texte traduit du dictionnaire JSON
        async def executer_traduction_zakat_differee(*args):
            import asyncio
            await asyncio.sleep(0.06)
            self.traduire_page(DICTIONNAIRE_LANGUES.actif)
            
        if self.page_flet:
            self.page_flet.run_task(executer_traduction_zakat_differee)
