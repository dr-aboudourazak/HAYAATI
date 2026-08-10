"""
ÉCRAN DE DIAGNOSTIC SUCCESSION TIERS (GUI/COMPONENTS/INTERFACE_HERITAGE_TIERS.PY)
Version Finale Intégrale Statique - Totalement compatible Flet 0.86.2, Python 3.14 & APK Android (Partie 1)
"""
from __future__ import annotations
import flet as ft
import re
from gui.langues import DICTIONNAIRE_LANGUES
from core.certificate_engine import generer_certificat_pdf
from core.heritage_engine import HeritageEngine

class EcranHeritageTiers(ft.Container):

    def __init__(self, app_reference):
        self.app = app_reference
        self.page_flet = app_reference.page
        self.mode_mobile = None
        self.moteur_succession = HeritageEngine()
        
        # Liste complète des 22 candidats canoniques d'héritiers
        self.famille = [
            "epoux", "epouse", "fils", "fille", "pere", "mere", 
            "grand_pere", "grand_mere", "petit_fils", "petite_fille", 
            "frere_germain", "soeur_germaine", "frere_paternel",
            "soeur_paternelle", "frere_uterin", "soeur_uterine", 
            "fils_frere_germain", "fils_frere_paternel", 
            "oncle_germain", "oncle_paternel", "cousin_germain", 
            "cousin_paternel"
        ]
        self.cles_caps = ["en_masse", "en_creances", "en_dettes", "en_legs"]
        self.labels: dict[str, ft.Text] = {}
        self.entries: dict[str, ft.TextField] = {}
        self.intrants_mem: dict[str, str] = {}
        self.lignes_mem: list[str] = []
        self.lignes_exclus_mem: list[str] = []
        self.dernier_resultat_succession: dict = {}

        # Dictionnaires requis pour désactiver les spinbox à chaud
        self.boutons_famille_plus: dict[str, ft.IconButton] = {}
        self.boutons_famille_moins: dict[str, ft.IconButton] = {}

        # 🎯 INITIALISATION PRÉVENTIVE DU FIQH AVANCÉ POUR L'INTERFACE TIERS
        self.sexe_defunt_actif = "HOMME" 
        self.actif_khountha = False
        self.actif_zawil_arham = False

        # --- 1. CONFIGURATION DU PATRIMOINE TIERS ---
        self.lbl_cadre_tiers = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#d97706")
        self.lbl_defunt = ft.Text(size=11, weight=ft.FontWeight.BOLD, color="#4b5563")
        self.entree_nom = ft.TextField(
            value="Amina Diallo", height=38, text_size=12,
            border_radius=6, border_color=ft.Colors.GREY_400, bgcolor=ft.Colors.WHITE
        )
        
        def selectionner_sexe(sexe_choisi):
            self.sexe_defunt_actif = sexe_choisi
            self.btn_homme.bgcolor = "#e0f2fe" if sexe_choisi == "HOMME" else "#f3f4f6"
            self.btn_homme.border = ft.Border.all(2, "#0284c7") if sexe_choisi == "HOMME" else None
            self.btn_femme.bgcolor = "#fce7f3" if sexe_choisi == "FEMME" else "#f3f4f6"
            self.btn_femme.border = ft.Border.all(2, "#db2777") if sexe_choisi == "FEMME" else None
            
            # Application instantanée des verrous Sharia
            if sexe_choisi == "HOMME":
                self.entries["epoux"].value = "0"
                if "epoux" in self.boutons_famille_plus:
                    self.boutons_famille_plus["epoux"].disabled = True
                    self.boutons_famille_moins["epoux"].disabled = True
                if "epouse" in self.boutons_famille_plus:
                    self.boutons_famille_plus["epouse"].disabled = False
                    self.boutons_famille_moins["epouse"].disabled = False
            else:
                self.entries["epouse"].value = "0"
                if "epouse" in self.boutons_famille_plus:
                    self.boutons_famille_plus["epouse"].disabled = True
                    self.boutons_famille_moins["epouse"].disabled = True
                if "epoux" in self.boutons_famille_plus:
                    self.boutons_famille_plus["epoux"].disabled = False
                    self.boutons_famille_moins["epoux"].disabled = False
            try: self.update()
            except Exception: pass

        # Tuiles cliquables des genres (👨 / 👩)
        self.btn_homme = ft.Container(
            content=ft.Text("👨", size=20, text_align=ft.TextAlign.CENTER),
            bgcolor="#e0f2fe", border=ft.Border.all(2, "#0284c7"), border_radius=6,
            padding=ft.Padding(0, 4, 0, 0), width=50, height=38, on_click=lambda _: selectionner_sexe("HOMME")
        )
        self.btn_femme = ft.Container(
            content=ft.Text("👩", size=20, text_align=ft.TextAlign.CENTER),
            bgcolor="#f3f4f6", border_radius=6,
            padding=ft.Padding(0, 4, 0, 0), width=50, height=38, on_click=lambda _: selectionner_sexe("FEMME")
        )
        
        self.lbl_sexe_titre = ft.Text(value=" ", size=11, color="#4b5563")
        bloc_sexe_boutons = ft.Container(
            content=ft.Column([
                self.lbl_sexe_titre, 
                ft.Row([self.btn_homme, self.btn_femme], spacing=5)
            ], spacing=4), col={"xs": 12, "sm": 4, "md": 1.6}
        )

        self.grille_patrimoine_tiers = ft.ResponsiveRow(spacing=8, run_spacing=8)
        self.grille_patrimoine_tiers.controls.append(
            ft.Container(content=ft.Column([self.lbl_defunt, self.entree_nom], spacing=4), col={"xs": 12, "sm": 4, "md": 2.4})
        )
        self.grille_patrimoine_tiers.controls.append(bloc_sexe_boutons)

        for k in self.cles_caps:
            self.labels[k] = ft.Text(size=11, weight=ft.FontWeight.W_500, color="#4b5563")
            self.entries[k] = ft.TextField(
                value="0", height=38, text_size=12,
                border_radius=6, border_color=ft.Colors.GREY_400, bgcolor=ft.Colors.WHITE
            )
            setattr(self, k, self.entries[k])
            self.grille_patrimoine_tiers.controls.append(
                ft.Container(content=ft.Column([self.labels[k], self.entries[k]], spacing=4), col={"xs": 12, "sm": 4, "md": 2.0})
            )

        self.c_tiers = ft.Container(
            content=ft.Column([self.lbl_cadre_tiers, self.grille_patrimoine_tiers], spacing=8),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#d97706")
        )

        # 📂 BLOC DE CONFIGURATION MEMBRES DE FAMILLE
        self.lbl_cadre_famille = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.grille_famille = ft.ResponsiveRow(spacing=8, run_spacing=8)
        
        for c in self.famille:
            self.labels[c] = ft.Text(size=11, weight=ft.FontWeight.W_500, color="#4b5563")
            max_l = 1 if c in ["epoux", "pere", "mere", "grand_pere", "grand_mere"] else 4 if c == "epouse" else 20
            
            self.entries[c] = ft.TextField(
                value="0", width=40, height=35, text_size=12, text_align=ft.TextAlign.CENTER,
                read_only=True, border_radius=4, border_color=ft.Colors.GREY_400, bgcolor=ft.Colors.WHITE,
                content_padding=ft.Padding(0, 0, 0, 0)
            )
            
            def créer_ajusteur_tiers(champ_cible=self.entries[c], limite_max=max_l):
                return lambda direction: self.ajuster_compteur_tiers(champ_cible, direction, limite_max)

            btn_moins = ft.IconButton(icon=ft.Icons.REMOVE, icon_size=14, icon_color="#b91c1c", width=26, height=28, on_click=lambda _, a=créer_ajusteur_tiers(): a(-1))
            btn_plus = ft.IconButton(icon=ft.Icons.ADD, icon_size=14, icon_color="#166534", width=26, height=28, on_click=lambda _, a=créer_ajusteur_tiers(): a(1))

            self.boutons_famille_moins[c] = btn_moins
            self.boutons_famille_plus[c] = btn_plus

            cellule_spinbox = ft.Container(
                content=ft.Column([
                    self.labels[c],
                    ft.Row([btn_moins, self.entries[c], btn_plus], spacing=1)
                ], spacing=4), col={"xs": 12, "sm": 6, "md": 3} 
            )
            self.grille_famille.controls.append(cellule_spinbox)

        # Désactivation initiale réflexe de l'Époux (Sexe par défaut : HOMME)
        self.boutons_famille_plus["epoux"].disabled = True
        self.boutons_famille_moins["epoux"].disabled = True

        self.c_famille = ft.Container(
            content=ft.Column([self.lbl_cadre_famille, self.grille_famille], spacing=8),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#064e3b")
        )

        # 🎯 LOGIQUE DES TUILES COMPACTES DU FIQH AVANCÉ SANS TRADUCTION COMPLEXE
        def basculer_scénario_khountha(e):
            self.actif_khountha = not self.actif_khountha
            self.tile_khountha.bgcolor = "#fef3c7" if self.actif_khountha else "#f3f4f6"
            self.tile_khountha.border = ft.Border.all(2, "#d97706") if self.actif_khountha else None
            self.update()

        def basculer_scénario_arham(e):
            self.actif_zawil_arham = not self.actif_zawil_arham
            self.tile_arham.bgcolor = "#e0f2fe" if self.actif_zawil_arham else "#f3f4f6"
            self.tile_arham.border = ft.Border.all(2, "#0284c7") if self.actif_zawil_arham else None
            self.update()

        self.tile_khountha = ft.Container(
            content=ft.Row([
                ft.Text("🧬", size=18),
                ft.Text("مسألة الخنثى المشكل", size=11, weight=ft.FontWeight.W_500, color="#1e293b")
            ], spacing=8),
            bgcolor="#f3f4f6", border_radius=6, padding=10, expand=True, on_click=basculer_scénario_khountha
        )

        self.tile_arham = ft.Container(
            content=ft.Row([
                ft.Text("🌿", size=18),
                ft.Text("مسألة ذوي الأرحام", size=11, weight=ft.FontWeight.W_500, color="#1e293b")
            ], spacing=8),
            bgcolor="#f3f4f6", border_radius=6, padding=10, expand=True, on_click=basculer_scénario_arham
        )

        self.grille_extensions_fiqh = ft.ResponsiveRow([
            ft.Container(content=self.tile_khountha, col={"xs": 12, "md": 6}),
            ft.Container(content=self.tile_arham, col={"xs": 12, "md": 6})
        ], spacing=10)

        txt_onb = DICTIONNAIRE_LANGUES.actif.get("heritage", {}) 
        self.txt_indignite = ft.Text(
            value=str(txt_onb.get("lbl_alerte_indignite", "⚠️")),
            size=14, color="#b45309", italic=True, weight=ft.FontWeight.W_500
        )

        self.btn_calc = ft.ElevatedButton(
            content=ft.Text("Calculer", size=13, weight=ft.FontWeight.BOLD),
            bgcolor="#064e3b", color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
            on_click=lambda _: self.calculer()
        )

        self.btn_pdf = ft.ElevatedButton(
            content=ft.Text("Générer PDF", size=13, weight=ft.FontWeight.BOLD),
            bgcolor="#0f766e", color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
            on_click=lambda _: self.imprimer()
        )

        self.lbl_cadre_res = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.text_rapport = ft.TextField(
            multiline=True, min_lines=8, max_lines=14, text_size=14, read_only=True,
            text_style=ft.TextStyle(font_family="Courier New", weight=ft.FontWeight.BOLD, color="#064e3b"),
            border_color=ft.Colors.GREY_400, bgcolor="#f9fafb", expand=True
        )
        self.c_res = ft.Container(
            content=ft.Column([self.lbl_cadre_res, self.text_rapport], spacing=6, expand=True),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#064e3b"),
            alignment=ft.Alignment(0, -1), expand=True
        )

        # 🎯 ASSEMBLAGE DU LAYOUT INCLUANT LES EXTENSIONS DU FIQH AVANCÉ
        self.layout_heritage_tiers = ft.Column([
            self.c_tiers, 
            self.c_famille, 
            self.grille_extensions_fiqh,
            self.txt_indignite,
            ft.Row([self.btn_calc, self.btn_pdf], spacing=15, wrap=True), 
            self.c_res
        ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)

        super().__init__(
            content=self.layout_heritage_tiers, expand=True, bgcolor="#f8fafc",
            padding=ft.Padding(left=15, right=15, top=15, bottom=15)
        )

        # Initialisation préventive pour détruire les AttributeError
        self.titre_traduit = "RAPPORT DE SUCCESSION"
        self.ecole_traduite = "Malikite"

        if hasattr(DICTIONNAIRE_LANGUES, "moteur_i18n"):
            DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_langue)
        self.actualiser_donnees_affichage()

    def ajuster_compteur_tiers(self, champ_cible: ft.TextField, direction: int, limite_max: int):
        """Ajuste de manière synchrone et sécurisée la valeur numérique de la cellule familiale."""
        valeur_actuelle = int(champ_cible.value or 0)
        nouvelle_valeur = valeur_actuelle + direction
        if 0 <= nouvelle_valeur <= limite_max:
            champ_cible.value = str(nouvelle_valeur)
            champ_cible.update()

    def action_langue(self, dic: dict):
        """Met à jour l'interface lors d'une modification linguistique globale."""
        self.traduire(dic)

    def traduire(self, dic: dict):
        """Met à jour dynamiquement tous les labels du formulaire depuis le JSON."""
        if not dic:
            return
        h = dic.get("heritage", {})
        p = dic.get("pdf", {})
        
        self.lbl_cadre_tiers.value = str(h.get("cadre_defunt", "Défunt"))
        self.lbl_defunt.value = str(h.get("genre_lbl", "Genre :"))
        
        self.labels["en_masse"].value = h.get("masse_successorale_nette", "Masse :") + " :"
        self.labels["en_creances"].value = h.get("creances_actives_incluses", "Créances :") + " :"
        self.labels["en_dettes"].value = h.get("dettes_humaines_purgées", "Dettes :") + " :"
        self.labels["en_legs"].value = h.get("wasiyya_retenue", "Legs :") + " :"
        
        self.lbl_cadre_famille.value = str(h.get("cadre_ayants_droit", "Composition de la Cellule Familiale"))
        self.lbl_cadre_res.value = str(p.get("rapport_succession_titre", "Bilan Législatif des Droits Successoraux"))
        
        if self.btn_calc.content:
            self.btn_calc.content.value = str(h.get("btn_simuler", "Calculer"))
        if self.btn_pdf.content:
            self.btn_pdf.content.value = str(h.get("btn_imprimer_succession", "Générer PDF"))
        
        candidats_json = h.get("candidats", {})
        for c in self.famille:
            # 🎯 SÉCURITÉ DOCTRINALE ÉTANCHE : On ignore les métadonnées pour éviter les crashs à l'écran
            if c not in ["cle_extra_khountha", "cle_extra_arham", "cas_khountha_actif", "cas_zawil_arham_actif", "sexe_defunt"]:
                self.labels[c].value = f"{candidats_json.get(c, c)} :"

        # 🎯 EXIGENCE DE CONCEPTION : Affichage en arabe littéraire pur en permanence à l'IHM
        # (S'applique sur vos libellés de titres ou de checkboxes du Khountha / Arham présents dans l'interface)
        if hasattr(self, "lbl_titre_khountha"):
            self.lbl_titre_khountha.value = "مسألة الخنثى المشكل"
        if hasattr(self, "chk_khountha") and self.chk_khountha:
            self.chk_khountha.label = "مسألة الخنثى المشكل"

        if self.page_flet:
            try: self.update()
            except Exception: pass

    def calculer(self):
        """Exécute l'audit algorithmique successoral et dresse la synthèse comptable."""
        try:
            b = float(self.en_masse.value.strip() or 0)
            c = float(self.en_creances.value.strip() or 0)
            d = float(self.en_dettes.value.strip() or 0)
            l = float(self.en_legs.value.strip() or 0)
            
            dev = getattr(self.app, "devise_active", "XOF")
            doc = getattr(self.app, "madhhab_actif", "Malikite")
            
            langue_active = DICTIONNAIRE_LANGUES.actif
            txt_her = langue_active.get("heritage", {})
            txt_pdf = langue_active.get("pdf", {})
            
            # 🎯 FILTRAGE SHARIA ET HARMONISATION LIVE : On n'injecte que les compteurs strictement supérieurs à 0
            # Cela élimine les clés fantômes à 0 pour que "in" ne soit pas faussé dans fractions.py
            saisi = {}
            for comp in self.famille:
                valeur_compteur = int(self.entries[comp].value or 0)
                if valeur_compteur > 0:
                    saisi[comp] = valeur_compteur
            
            # 🎯 VÉRIFICATION ET SÉCURITÉ CONJOINTS AVANT CALCUL
            if saisi.get("epoux", 0) > 0 and saisi.get("epouse", 0) > 0:
                self.text_rapport.value = str(txt_her.get("err_doublon", "❌ Erreur Conjoints : Double présence impossible."))
                self.update()
                return

            # Construction étanche du paquet d'intrants manuels
            intrants_tiers = {
                "brut": b, "creances_humains": c, "dettes_humains": d, "legs": l, "arbre_saisi": saisi,
                "sexe_defunt": self.sexe_defunt_actif,
                "cas_khountha_actif": self.actif_khountha,
                "cas_zawil_arham_actif": self.actif_zawil_arham
            }

            res = self.moteur_succession.executer_audit_successoral_complet(
                False, None, doc, intrants_tiers
            )
            self.dernier_resultat_succession = res
    
            self.titre_traduit = txt_her.get("rapport_succession", "RAPPORT DE SUCCESSION")
            b_outils = langue_active.get("barre_outils", {})
            self.ecole_traduite = b_outils.get("ecoles", {}).get(doc, doc)

            self.lignes_exclus_mem = [
                str(ex) for ex in res.get("personnes_exclues", [])
                if saisi.get(str(ex).lower(), 0) > 0
            ]
            
            self.m_nette = float(res.get("masse_successorale_nette", 0.0))
            self.wasiyya_retenue = float(res.get("wasiyya_retenue", 0.0))
            self.creances_inc = float(res.get("creances_actives_incluses", 0.0))
            self.dettes_purg = float(res.get("dettes_humaines_purgées", 0.0))
            self.ventilation = res.get("ventilation_fractions", {})

            self.lbl_ms_nette = txt_her.get("masse_successorale_nette", "Masse successorale nette à distribuer")
            self.lbl_creances_inc = txt_her.get("creances_actives_incluses", "Créances actives incluses")
            self.lbl_dettes_purg = txt_her.get("dettes_humaines_purgées", "Dettes et passif purgés")
            self.lbl_wasiyya = txt_her.get("wasiyya_retenue", "Legs testamentaires retenus (Max 1/3)")

            self.intrants_mem = {
                self.lbl_ms_nette: f"{self.m_nette:.2f} {dev}",
                self.lbl_creances_inc: f"{self.creances_inc:.2f} {dev}",
                self.lbl_dettes_purg: f"-{self.dettes_purg:.2f} {dev}",
                self.lbl_wasiyya: f"{self.wasiyya_retenue:.2f} {dev}"
            }

            self.lignes_mem.clear()
            
            # Reconstruction rigoureuse et transparente de la chaîne textuelle du verdict
            texte_verdict = f"📜 {self.titre_traduit} ({self.ecole_traduite.upper()}) :\n"
            texte_verdict += "=" * 45 + "\n"
            for k_lbl, v_val in self.intrants_mem.items():
                texte_verdict += f"{k_lbl:<32} : {v_val}\n"
            
            texte_verdict += "-" * 45 + "\n"
            for heritier, fraction in self.ventilation.items():
                valeur_fraction = float(fraction)
                
                # 🎯 CORRECTION SHARIA : On élimine strictement de l'affichage tout héritier à quota nul (0.0)
                if valeur_fraction > 0.00001 and heritier not in ["cas_khountha_actif", "cas_zawil_arham_actif", "sexe_defunt"]:
                    montant_heritier = self.m_nette * valeur_fraction
                    
                    # 🎯 INTERCEPTION TIERS BAS : Harmonisation en arabe littéraire pour le Khountha
                    nom_final = str(heritier).upper()
                    if str(heritier).lower() == "khountha":
                        nom_final = "الخنثى المشكل"
                    
                    # 🎯 RETOUR AUX DÉCIMALES STRICTES : Formatage à 4 décimales canoniques (ex: 0.3333) au lieu du %
                    texte_verdict += f"• {nom_final:<24} ({valeur_fraction:.4f}) : {montant_heritier:.2f} {dev}\n"
                
            self.text_rapport.value = texte_verdict
            self.lignes_mem = texte_verdict.split("\n")
            
            if self.page_flet:
                self.update()
                
        except Exception as e:
            # Plus de masquage : on lève l'exception pour bloquer et déboguer proprement en console
            raise e

        # ============================================================
        # 🎯 PARTIE 3/4 : HARMONISATION DU RAPPORT ÉCRAN ET SYSTÈME INTRANTS PDF
        # ============================================================
        try:
            # 🎯 HARMONISATION TEXTUELLE DE LA SECTION 1 SUR L'ÉCRAN PRINCIPAL (Flet Text Value)
            v = f"📜 {self.titre_traduit} ({self.ecole_traduite.upper()}) :\n"
            v += " ==================================================\n"
            v += f"   ▶ {self.lbl_ms_nette} : {self.m_nette:.2f} {dev}\n"
            v += f"   ▶ {self.lbl_creances_inc} : {self.creances_inc:.2f} {dev}\n"
            v += f"   ▶ {self.lbl_dettes_purg} : -{self.dettes_purg:.2f} {dev}\n"
            v += f"   ▶ {self.lbl_wasiyya} : {self.wasiyya_retenue:.2f} {dev}\n"
            v += " ==================================================\n\n"

            # 🎯 SECTION 2 : Ventilation des héritiers à l'écran
            if self.ventilation:
                candidats_json = txt_her.get("candidats", {})
                for heritier, fraction in self.ventilation.items():
                    # 🎯 RECTIFICATION DIRECTE : Correction de la faute de frappe sur 'nom_heritier_traduit' [🎰]
                    nom_heritier_traduit = candidats_json.get(heritier.lower(), heritier.upper())
                    ligne = f"     - {nom_heritier_traduit} : {fraction:.4f} ({(self.m_nette * fraction):.2f} {dev})"
                    v += f"{ligne}\n"
                    self.lignes_mem.append(ligne)
            else:
                v += f"   {txt_her.get('succession_sans_heritier', '❌ Aucun héritier éligible.')}\n"
                    
            # 🎯 SECTION 3 : Affichage épuré des exclus (Hajb) à l'écran Tiers
            # 🎯 L'ALIGNEMENT SOUVERAIN ASSAINI : Récupération du titre officiel du PDF
            label_bloques = txt_pdf.get("sec_3_titre_exclus", "3. Candidates Bloqués ou Écartés de la Succession (Hajb) :")
            label_bloques_clean = label_bloques.replace("<b>", "").replace("</b>", "").replace("3. ", "").replace(":", "").strip()
            
            exclus_text_tiers = ""
            candidats_json = txt_her.get("candidats", {})
            
            # Extraction propre sous forme de liste en minuscules de tous les bénéficiaires actifs du Tiers
            liste_beneficiaires_tiers = [str(k).lower().strip() for k in self.ventilation.keys()]
            
            # A. Traitement initial exclusif des exclus physiques issus du moteur d'exclusions absolues
            if self.lignes_exclus_mem:
                for ex in self.lignes_exclus_mem:
                    # 🎯 SÉCURISATION ET EXTRACTION DE L'INDEX TEXTUEL [0] APRÈS LE SPLIT
                    ligne_brute = str(ex).strip()
                    if ":" in ligne_brute:
                        cle_brute = str(ligne_brute.split(":", 1)[0]).strip().upper()
                    else:
                        cle_brute = str(ligne_brute).strip().upper()
                        
                    cle_json = str(cle_brute.lower().replace("-", "_")).strip()
                    
                    # 🎯 CORRECTIF TEXTE : Isolation stricte de l'index [0] pour éviter l'injection de type List
                    if "_" in cle_json and any(str(i) in cle_json for i in range(10)):
                        cle_json_base = str(cle_json.split("_")[0]).strip()
                    else:
                        cle_json_base = str(cle_json).strip()
                    
                    # 🎯 LE SHIELD ANTI-DOUBLON UNIVERSEL TIERS GÉNÉRIQUE
                    if cle_json in liste_beneficiaires_tiers or cle_json_base in liste_beneficiaires_tiers:
                        continue
                        
                    exclus_text_tiers += f"     - {candidats_json.get(cle_json, candidats_json.get(cle_json_base, cle_brute.capitalize()))}\n"

            # C. On injecte le bloc complet à l'écran uniquement si des exclus réels subsistent après filtrage
            if exclus_text_tiers.strip():
                v += f"\n   ▶ {label_bloques_clean} :\n" + exclus_text_tiers
                        
            # Assignation de la chaîne compilée de manière réactive
            self.text_rapport.value = v
                    
        except Exception as e:
            self.text_rapport.value = f"❌ : {str(e)}"

        if self.page_flet:
            try: self.update()
            except Exception: pass

    def imprimer(self):
        """Compile et génère le certificat d'hérédité PDF officiel pour la simulation tiers."""
        if not self.lignes_mem: 
            return
            
        n = self.entree_nom.value.strip() or "Tiers"
        dev = getattr(self.app, "devise_active", "XOF")
        doc = getattr(self.app, "madhhab_actif", "Malikite")
        
        langue_active = DICTIONNAIRE_LANGUES.actif
        txt_her = langue_active.get("heritage", {})
        b_candidats = txt_her.get("candidats", {})

        # Extraction en temps réel des valeurs numériques de l'écran Tiers Flet TextField
        brut = float(self.en_masse.value.strip() or 0.0)
        creances = float(self.en_creances.value.strip() or 0.0)
        dettes = float(self.en_dettes.value.strip() or 0.0)
        legs_demande = float(self.en_legs.value.strip() or 0.0)

        # Re-compilation de la composition de l'arbre familial saisi à l'écran
        saisi = {comp: int(self.entries[comp].value or 0) for comp in self.famille}

        # 🎯 RECTIFICATION DIRECTE : Remplacement de max_initiale par masse_initiale pour éviter tout crash
        masse_initiale = brut + creances
        safe_mass = max(0.0, masse_initiale - dettes)
        wasiyya_retenue = min(legs_demande, safe_mass / 3.0)
        masse_nette = max(0.0, safe_mass - wasiyya_retenue)

        # Traduction forcée et étanche des 4 paramètres d'inventaire
        label_net = txt_her.get("masse_successorale_nette", "Masse successorale nette à distribuer")
        label_creances = txt_her.get("creances_actives_incluses", "Créances actives incluses")
        label_dettes = txt_her.get("dettes_humaines_purgées", "Dettes et passif purgés")
        label_legs = txt_her.get("wasiyya_retenue", "Legs testamentaires retenus (Max 1/3)")

        self.intrants_ordonnes_i18n_tiers = {
            label_net: f"{masse_nette:.2f} {dev}",
            label_creances: f"{creances:.2f} {dev}",
            label_dettes: f"-{dettes:.2f} {dev}",
            label_legs: f"{wasiyya_retenue:.2f} {dev}"
        }

        # 🎯 SECTION 3 VERROUILLÉE : ÉLARGISSEMENT DE L'ESPACE ENTRE HÉRITIER ET COMMENTAIRE
        langue_est_arabe = any('\u0600' <= char <= '\u06FF' for char in str(txt_her.get('rapport_succession', '')))
        lignes_exclus_traduites = []
        
        for ex in getattr(self, "lignes_exclus_mem", []):
            txt_ex = str(ex).strip()
            
            # Isolement de la clé et du commentaire s'il y a un ":"
            if ":" in txt_ex:
                cle_brute, commentaire_brut = txt_ex.split(":", 1)
                cle_brute = cle_brute.strip().upper()
                commentaire_final = commentaire_brut.strip()
            else:
                cle_brute = txt_ex.upper()
                commentaire_final = ""
            
            # Normalisation vers la clé minuscule du JSON candidats
            cle_json = cle_brute.lower().replace("-", "_")
            nom_traduit = b_candidats.get(cle_json, cle_brute.capitalize())
            
            if commentaire_final:
                # 🎯 INJECTION D'UN SÉPARATEUR ÉLARGIS ET SÉCURISÉ BiDi
                if langue_est_arabe:
                    separateur_espace = "  \u200E◄\u200E  "
                    lignes_exclus_traduites.append(f"• {nom_traduit}{separateur_espace}{commentaire_final}")
                else:
                    separateur_espace = "  \u200E►\u200E  "
                    lignes_exclus_traduites.append(f"• {nom_traduit}{separateur_espace}{commentaire_final}")
            else:
                lignes_exclus_traduites.append(f"• {nom_traduit}")

    # ============================================================================
    # 🎯 PARTIE 4/4 : HARMONISATION DU RAPPORT ÉCRAN ET SYSTÈME INTRANTS PDF (FIXÉ)
    # ============================================================================

        id_t = {
            "nom": n, 
            "prenom": "", 
            "ville": "Saisie Manuelle", 
            "pays": "Diagnostic", 
            "telephone": "-", 
            "personnes_exclues": lignes_exclus_traduites
        }
        
        # 🎯 SECTION 2 VERROUILLÉE : STRUCTURE UNIVERSELLE (Fraction ➔ Héritier ➔ Montant)
        from fractions import Fraction
        import math
        import re

        # Étape 1 : Analyser toutes les parts décimales calculées pour en extraire le Dénominateur Commun (Asl)
        liste_fractions = []
        for ligne in self.lignes_mem:
            txt_ligne = " ".join(ligne) if isinstance(ligne, list) else str(ligne)
            motifs_decimaux = re.findall(r"\b0[\.,]\d+\b", txt_ligne)
            for dec_str in motifs_decimaux:
                try:
                    val_float = float(dec_str.replace(",", "."))
                    liste_fractions.append(Fraction(val_float).limit_denominator(96))
                except Exception: pass

        # Calcul du PPCM (LCM) des dénominateurs
        denomination_commune = 1
        for frac in liste_fractions:
            denomination_commune = abs(denomination_commune * frac.denominator) // math.gcd(denomination_commune, frac.denominator)

        # Étape 2 : Reconstruction universelle : Fraction (Ratio) ➔ Héritier ➔ Montant
        lignes_pdf_fractions = []
        candidats_json = txt_her.get("candidats", {})
        
        # 🎯 CONTEXTE D'ARBRE PUR POUR REPORTLAB (Évite la collision et protège le Père)
        arbre_propre_pdf = {}
        if hasattr(self, "famille") and self.famille:
            for heritier_saisi in self.famille:
                try:
                    # On filtre les métadonnées pour ne garder que les effectifs réels de la famille
                    if heritier_saisi not in ["cas_khountha_actif", "cas_zawil_arham_actif", "sexe_defunt", "cle_extra_khountha", "cle_extra_arham"]:
                        val_champ = self.entries.get(heritier_saisi)
                        if val_champ and val_champ.value and int(val_champ.value) > 0:
                            arbre_propre_pdf[str(heritier_saisi).lower().strip()] = int(val_champ.value)
                except Exception:
                    pass

        # 🌟 INJECTION DES CAS EXTRAORDINAIRES SANS TOUCHER AU PÈRE
        # Ces clés techniques étanches empêchent ReportLab de supprimer le Père du cadre vert supérieur
        if self.chk_khountha.value if hasattr(self, "chk_khountha") else False:
            arbre_propre_pdf["cle_extra_khountha"] = 1
            
        if self.chk_arham.value if hasattr(self, "chk_arham") else False:
            arbre_propre_pdf["cle_extra_arham"] = 1

        if self.ventilation:
            for heritier, fraction in self.ventilation.items():
                # On conserve la chaîne brute pour tester l'arabe natif, et la version nettoyée pour les clés techniques
                heritier_brut = str(heritier).strip()
                heritier_cle = heritier_brut.lower()
                
                # 🎯 EXIGENCE DE CONCEPTION IMMUABLE À LA RACINE :
                # Interception totale de toutes les variantes de clés (arabe, minuscules ou clés extra du moteur)
                if heritier_cle in ["khountha", "cle_extra_khountha"] or "الخنثى" in heritier_brut:
                    nom_heritier_traduit = "الخنثى المشكل"
                elif heritier_cle in ["zawil", "cle_extra_arham"] or "الأرحام" in heritier_brut:
                    nom_heritier_traduit = "مسألة ذوي الأرحام"
                else:
                    nom_heritier_traduit = candidats_json.get(heritier_cle, heritier_brut.upper())
                    
                parts_entieres = int(round(fraction * denomination_commune))
                montant_calcule = self.m_nette * fraction
                
                # 🎯 RECTIFICATION RADICALE : Utilisation du séparateur symétrique ":" pour toutes les langues
                label_parts = f"\u200E[{parts_entieres} : {denomination_commune}]\u200E"
                ligne_restructuree = f"{label_parts}  -  {nom_heritier_traduit}  :  {montant_calcule:.2f} {dev}"
                
                lignes_pdf_fractions.append(ligne_restructuree)
        else:
            lignes_pdf_fractions.append(txt_her.get('succession_sans_heritier', '❌ Aucun héritier éligible.'))

        # ------------------------------------------------------------
        # 🎯 FIX TECHNIQUE CRITIQUE (PONT DE DONNÉES RETOUR HOUSTAZ)
        # ------------------------------------------------------------
        # Clonage de sécurité pour l'impression
        saisi_pdf = saisi.copy()
        
        if getattr(self, "actif_khountha", False):
            saisi_pdf["مسألة الخنثى المشكل"] = 1
            
        # 🌟 FORCE INJECTION ZAWIL : Même si 'saisi' est vide, on injecte la clé 
        # pour forcer ReportLab à dessiner le tableau vert supérieur
        if getattr(self, "actif_zawil_arham", False):
            saisi_pdf["cas_zawil_arham_actif"] = True
            saisi_pdf["مسألة ذوي الأرحام"] = 1

        # Attribution du dictionnaire enrichi au tracé de la boîte verte quantitative ReportLab
        self.intrants_ordonnes_i18n_tiers["arbre_saisi"] = saisi_pdf

        # Transmission au PDF ReportLab sans aucune perte de données
        generer_certificat_pdf(id_t, "HERITAGE", doc, dev, self.intrants_ordonnes_i18n_tiers, lignes_pdf_fractions)

    def changer_langue(self, n_lang: str): 
        """Propagation descendante linguistique."""
        self.traduire(DICTIONNAIRE_LANGUES.actif)
        
    def actualiser_contexte(self): 
        """Réinitialise la zone textuelle du rapport de simulation."""
        self.text_rapport.value = ""
        if self.page_flet:
            try: self.update()
            except Exception: pass
        
    def actualiser_donnees_affichage(self): 
        """Cycle de vie : Remet à zéro les simulations."""
        self.entree_nom.value = "Amina Diallo"
        for k in self.cles_caps:
            self.entries[k].value = "0"
        for c in self.famille:
            self.entries[c].value = "0"
            
        self.actualiser_contexte()
        self.traduire(DICTIONNAIRE_LANGUES.actif)
