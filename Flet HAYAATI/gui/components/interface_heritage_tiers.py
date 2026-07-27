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
        
        # 🎯 SÉPARATION CANONIQUE STRICTE : Époux et Épouse disposent de deux compteurs distincts
        self.famille = [
            "epoux", "epouse", "fils", "fille", "pere", "mere", "grand_pere", "grand_mere",
            "petit_fils", "petite_fille", "frere_germain", "soeur_germaine", "frere_paternel",
            "soeur_paternelle", "frere_uterin", "soeur_uterine", "fils_frere_germain",
            "fils_frere_paternel", "oncle_germain", "oncle_paternel", "cousin_germain", "cousin_paternel"
        ]
        self.cles_caps = ["en_masse", "en_creances", "en_dettes", "en_legs"]
        self.labels: dict[str, ft.Text] = {}
        self.entries: dict[str, ft.TextField] = {}
        self.intrants_mem: dict[str, str] = {}
        self.lignes_mem: list[str] = []
        self.lignes_exclus_mem: list[str] = []
        
        # Mémorisation du dictionnaire brut du moteur pour le bouton imprimer
        self.dernier_resultat_succession: dict = {}

        # --- 1. INSTANCIATION DES COMPOSANTS GRAPHIQUES MATERIAL 3 ---
        # 📂 BLOC DE CONFIGURATION PATRIMOINE TIERS (Émule le premier LabelFrame)
        self.lbl_cadre_tiers = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#d97706")
        self.lbl_defunt = ft.Text(size=11, weight=ft.FontWeight.BOLD, color="#4b5563")
        self.entree_nom = ft.TextField(
            value="Amina Diallo", height=38, text_size=12,
            border_radius=6, border_color=ft.Colors.GREY_400, bgcolor=ft.Colors.WHITE
        )
        
        self.grille_patrimoine_tiers = ft.ResponsiveRow(spacing=8, run_spacing=8)
        self.grille_patrimoine_tiers.controls.append(
            ft.Container(content=ft.Column([self.lbl_defunt, self.entree_nom], spacing=4), col={"xs": 12, "sm": 4, "md": 2.4})
        )

        for k in self.cles_caps:
            self.labels[k] = ft.Text(size=11, weight=ft.FontWeight.W_500, color="#4b5563")
            self.entries[k] = ft.TextField(
                value="0", height=38, text_size=12,
                border_radius=6, border_color=ft.Colors.GREY_400, bgcolor=ft.Colors.WHITE
            )
            setattr(self, k, self.entries[k])
            self.grille_patrimoine_tiers.controls.append(
                ft.Container(content=ft.Column([self.labels[k], self.entries[k]], spacing=4), col={"xs": 12, "sm": 4, "md": 2.4})
            )

        self.c_tiers = ft.Container(
            content=ft.Column([self.lbl_cadre_tiers, self.grille_patrimoine_tiers], spacing=8),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#d97706")
        )

        # 📂 BLOC DE CONFIGURATION MEMBRES DE FAMILLE (Émule le second LabelFrame)
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

            cellule_spinbox = ft.Container(
                content=ft.Column([
                    self.labels[c],
                    ft.Row([btn_moins, self.entries[c], btn_plus], spacing=1, alignment=ft.MainAxisAlignment.START)
                ], spacing=4), col={"xs": 12, "sm": 6, "md": 3} # 🎯 AGENCEMENT HARMONISÉ 4 COLONNES PC
            )
            self.grille_famille.controls.append(cellule_spinbox)

        self.c_famille = ft.Container(
            content=ft.Column([self.lbl_cadre_famille, self.grille_famille], spacing=8),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#064e3b")
        )

        # Boutons d'action maîtres (Conformes Python 3.14 content=ft.Text)
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

        # 🎯 RECTIFICATION RESPONSIVE DU CADRE DU VERDICT EXTÉRIEUR FLUIDE ÉTIRÉ
        self.lbl_cadre_res = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.text_rapport = ft.TextField(
            multiline=True, min_lines=8, max_lines=14, text_size=13, read_only=True,
            text_style=ft.TextStyle(font_family="Courier New"),
            border_color=ft.Colors.GREY_400, bgcolor="#f9fafb", expand=True
        )
        self.c_res = ft.Container(
            content=ft.Column([self.lbl_cadre_res, self.text_rapport], spacing=6, expand=True),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#064e3b"),
            alignment=ft.Alignment(0, -1), expand=True
        )

        # Structure globale défilante
        self.layout_heritage_tiers = ft.Column([
            self.c_tiers,
            self.c_famille,
            ft.Row([self.btn_calc, self.btn_pdf], spacing=15, alignment=ft.MainAxisAlignment.START, wrap=True),
            self.c_res
        ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)

        super().__init__(
            content=self.layout_heritage_tiers, expand=True, bgcolor="#f8fafc",
            padding=ft.Padding(left=15, right=15, top=15, bottom=15)
        )

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

    # ============================================================
    # 🎯 PARTIE 2/4 : TRADUCTION DE PAGE ET LOGIQUE DE VENTILATION PRE-CALCUL
    # ============================================================

    def traduire(self, dic: dict):
        """Met à jour dynamiquement tous les labels du formulaire depuis le JSON."""
        if not dic:
            return
        h = dic.get("heritage", {})
        p = dic.get("pdf", {})
        
        self.lbl_cadre_tiers.value = str(h.get("cadre_defunt", "Défunt"))
        self.lbl_defunt.value = str(h.get("genre_lbl", "Genre :"))
        
        # 🎯 RECTIFICATION : Utilisation exclusive des clés miroirs du bloc JSON "heritage"
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
        
        # Traduction individuelle réactive des 22 candidats scindés
        candidats_json = h.get("candidats", {})
        for c in self.famille: 
            self.labels[c].value = f"{candidats_json.get(c, c)} :"

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
            
            # 🌐 Extraction unifiée du dictionnaire de langue actif de la session
            langue_active = DICTIONNAIRE_LANGUES.actif
            txt_her = langue_active.get("heritage", {})
            txt_pdf = langue_active.get("pdf", {})
            
            saisi = {comp: int(self.entries[comp].value or 0) for comp in self.famille}
            
            # 🎯 GARDE-FOU SHARIA : Vérification stricte du non-cumul des deux conjoints scindés
            if saisi.get("epoux", 0) > 0 and saisi.get("epouse", 0) > 0:
                self.text_rapport.value = str(txt_her.get("err_doublon", "❌ Erreur Conjoints : Présence simultanée de l'époux et de l'épouse impossible."))
                self.update()
                return

            # Exécution de l'audit successoral via le HeritageEngine d'origine
            res = self.moteur_succession.executer_audit_successoral_complet(
                False, None, doc, {"brut": b, "creances_humains": c, "dettes_humains": d, "legs": l, "arbre_saisi": saisi}
            )
            
            # 🎯 VERROU SÉCURITÉ PDF : Stockage du dictionnaire brut pour éliminer les montants à 0
            self.dernier_resultat_succession = res
    
            self.titre_traduit = txt_her.get("rapport_succession", "RAPPORT DE SUCCESSION")
            b_outils = langue_active.get("barre_outils", {})
            self.ecole_traduite = b_outils.get("ecoles", {}).get(doc, doc)

            # Filtrer pour n'afficher que les exclus qui étaient vivants (Saisis > 0)
            self.lignes_exclus_mem = [
                str(ex) for ex in res.get("personnes_exclues", [])
                if saisi.get(str(ex).lower(), 0) > 0
            ]
            
            # Récupération des valeurs exactes calculées et plafonnées par le Core Engine
            self.m_nette = float(res.get("masse_successorale_nette", 0.0))
            self.wasiyya_retenue = float(res.get("wasiyya_retenue", 0.0))
            self.creances_inc = float(res.get("creances_actives_incluses", 0.0))
            self.dettes_purg = float(res.get("dettes_humaines_purgées", 0.0))
            self.ventilation = res.get("ventilation_fractions", {})

            # 🎯 FIX PORTEE DES VARIABLES : Poussées en propriétés de classe pour la suite du fichier
            self.lbl_ms_nette = txt_her.get("masse_successorale_nette", "Masse successorale nette à distribuer")
            self.lbl_creances_inc = txt_her.get("creances_actives_incluses", "Créances actives incluses")
            self.lbl_dettes_purg = txt_her.get("dettes_humaines_purgées", "Dettes et passif purgés")
            self.lbl_wasiyya = txt_her.get("wasiyya_retenue", "Legs testamentaires retenus (Max 1/3)")

            # Le compartiment des intrants utilise désormais les 4 clés i18n strictes du JSON
            self.intrants_mem = {
                self.lbl_ms_nette: f"{self.m_nette:.2f} {dev}",
                self.lbl_creances_inc: f"{self.creances_inc:.2f} {dev}",
                self.lbl_dettes_purg: f"-{self.dettes_purg:.2f} {dev}",
                self.lbl_wasiyya: f"{self.wasiyya_retenue:.2f} {dev}"
            }

            self.lignes_mem.clear()
            self.text_rapport.value = ""

    # ============================================================
    # 🎯 PARTIE 3/4 : HARMONISATION DU RAPPORT ÉCRAN ET SYSTÈME INTRANTS PDF
    # ============================================================

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
                    nom_heritier_traduit = candidats_json.get(heritier.lower(), heritier.upper())
                    ligne = f"     - {nom_heritier_traduit} : {fraction:.4f} ({(self.m_nette * fraction):.2f} {dev})"
                    v += f"{ligne}\n"
                    self.lignes_mem.append(ligne)
            else:
                v += f"   {txt_her.get('succession_sans_heritier', '❌ Aucun héritier éligible.')}\n"
            
            # 🎯 SECTION 3 : Affichage épuré des exclus (Hajb) sans commentaire parasite à l'écran
            if self.lignes_exclus_mem:
                v += f"\n   ▶ {txt_pdf.get('tableau_part', 'Exclus')} :\n"
                candidats_json = txt_her.get("candidats", {})
                for ex in self.lignes_exclus_mem:
                    cle_brute = str(ex).strip().split(":", 1)[0].strip().upper()
                    cle_json = cle_brute.lower().replace("-", "_")
                    v += f"     - {candidats_json.get(cle_json, cle_brute.capitalize())}\n"
                
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

        # 🎯 RECTIFICATION DIRECTE : Appel flash au moteur pour instancier la variable 'res' requise par la Section 2
        res = self.moteur_succession.executer_audit_successoral_complet(
            False, None, doc, {"brut": brut, "creances_humains": creances, "dettes_humains": dettes, "legs": legs_demande, "arbre_saisi": saisi}
        )

        masse_initiale = brut + creances
        safe_mass = max(0.0, max_initiale - dettes) if (max_initiale := masse_initiale) else 0.0
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
                # Crée un grand espace vide net et propre entre le nom de l'héritier et le commentaire
                if langue_est_arabe:
                    separateur_espace = "  \u200E◄\u200E  "
                    lignes_exclus_traduites.append(f"• {nom_traduit}{separateur_espace}{commentaire_final}")
                else:
                    separateur_espace = "  \u200E►\u200E  "
                    lignes_exclus_traduites.append(f"• {nom_traduit}{separateur_espace}{commentaire_final}")
            else:
                lignes_exclus_traduites.append(f"• {nom_traduit}")

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
        
        if self.ventilation:
            for heritier, fraction in self.ventilation.items():
                nom_heritier_traduit = candidats_json.get(heritier.lower(), heritier.upper())
                parts_entieres = int(round(fraction * denomination_commune))
                montant_calcule = self.m_nette * fraction
                
                # 🎯 RECTIFICATION RADICALE : Utilisation du séparateur symétrique ":" pour toutes les langues
                # Élimine définitivement le masquage ou l'inversion bidi de ReportLab
                label_parts = f"\u200E[{parts_entieres} : {denomination_commune}]\u200E"
                ligne_restructuree = f"{label_parts}  -  {nom_heritier_traduit}  :  {montant_calcule:.2f} {dev}"
                
                lignes_pdf_fractions.append(ligne_restructuree)
        else:
            lignes_pdf_fractions.append(txt_her.get('succession_sans_heritier', '❌ Aucun héritier éligible.'))

        # 🎯 FIX : Utilisation du dictionnaire i18n d'actifs ordonné transmis par la Partie 3
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
