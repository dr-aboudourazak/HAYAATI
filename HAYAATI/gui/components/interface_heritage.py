"""
INTERFACE DES RATIOS DE SUCCESSION LIVE AUTOMATIQUE (GUI/COMPONENTS/INTERFACE_HERITAGE.PY)
Version Finale Intégrale Statique - Totalement compatible Flet 0.86.2, Python 3.14 & APK Android (Partie 1)
"""
from __future__ import annotations
import flet as ft
import re
from datetime import datetime
from gui.langues import DICTIONNAIRE_LANGUES
from core.certificate_engine import generer_certificat_pdf
from core.heritage_engine import HeritageEngine

class EcranHeritage(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.page_flet = app_reference.page
        self.mode_mobile = None
        
        # Initialisation du moteur de calcul successoral d'origine
        self.moteur_succession = HeritageEngine(
            sync_engine_reference=getattr(self.app, "sync_engine", None)
        )
        
        # Structure de stockage d'audit pour le CertificateEngine
        self.intrants_mem: dict[str, str] = {}
        self.lignes_mem: list[list[str]] = []
        self.personnes_exclues_mem: list[str] = []

        # --- 1. INSTANCIATION DES COMPOSANTS GRAPHIQUES MATERIAL 3 ---
        # Bandeau doctrinal supérieur
        self.lbl_sync = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.c_mode = ft.Container(
            content=self.lbl_sync,
            bgcolor="#d1fae5", padding=ft.Padding(10, 6, 10, 6),
            border_radius=6, border=ft.Border.all(1, "#064e3b"),
            alignment=ft.Alignment(0, 0)
        )

        # Cadre d'affichage du Grand Rapport de Bilan (Émule tk.LabelFrame + tk.Text)
        self.lbl_cadre_res = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#064e3b")
        self.text_rapport = ft.TextField(
            multiline=True, min_lines=10, max_lines=15, text_size=14, read_only=True,
            # 🎯 BLINDAGE VISUEL DIRECT : Passage en FontWeight.BOLD (Gras Épais)
            text_style=ft.TextStyle(font_family="Courier New", weight=ft.FontWeight.BOLD, color="#064e3b"),
            border_color=ft.Colors.GREY_400, bgcolor="#f9fafb",
            expand=True
        )
        
        self.cadre_res = ft.Container(
            content=ft.Column([self.lbl_cadre_res, self.text_rapport], spacing=6, expand=True),
            bgcolor=ft.Colors.WHITE, padding=12, border_radius=8, border=ft.Border.all(1, "#064e3b"),
            expand=True
        )

        # Bouton de génération du certificat PDF Sharia-Compliant (Syntaxe sécurisée Python 3.14)
            # 🎯 FIX HARMONISATION CLÉ : Renommé en self.btn_generer_pdf pour correspondre à Zakat Live
        self.btn_generer_pdf = ft.ElevatedButton(
            content=ft.Text(value="Générer PDF", size=13, weight=ft.FontWeight.BOLD),
            bgcolor="#064e3b", color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
            on_click=lambda _: self.imprimer_pdf_heritage_live()
        )

        # 🎯 BOUTON RETOUR ÉMOJI UNIVERSEL VERS LE HUB DEVOIRS
        self.btn_retour_hub = ft.IconButton(
            icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
            icon_color="#064e3b",
            icon_size=16,
            tooltip="↩️",
            on_click=lambda _: self.app.layout_central.basculer_vers_ecran("DEVOIRS")
        )

        # 🌟 RÉORGANISATION : Le bouton retour s'ancre en toute première position
        self.layout_heritage = ft.Column([
            self.btn_retour_hub,
            self.c_mode,
            self.cadre_res,
            self.btn_generer_pdf,
            self.btn_retour_hub
        ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)

        super().__init__(
            content=self.layout_heritage, expand=True, bgcolor="#f8fafc",
            padding=ft.Padding(left=15, right=15, top=15, bottom=15)
        )

        # ❌ L'ANCIEN ABONNEMENT EN CLOCHE CONCURRENT EST SUPPRIMÉ POUR ÉVITER LE DEADLOCK
        
        # On maintient l'hydratation initiale au démarrage
        self.actualiser_donnees_affichage()

    def action_langue(self, dic: dict):
        """Met à jour l'interface lors d'une modification linguistique globale."""
        self.traduire_page(dic)

    def traduire_page(self, dic: dict):
        """Injecte les données i18n traduits dans les contrôles graphiques correspondants."""
        if not dic:
            return
            
        h = dic.get("heritage", {})
        p = dic.get("pdf", {})
        b = dic.get("barre_outils", {})
        
        # Extraction de la doctrine active traduite pour l'en-tête
        ecole_technique = getattr(self.app, 'madhhab_actif', 'Malikite')
        ecole_traduite = b.get("ecoles", {}).get(ecole_technique, ecole_technique)
        
        self.lbl_sync.value = f"🔄 {b.get('mode_live', 'Live / Visiteur')} | {b.get('label_fiqh', 'Fiqh :')} {ecole_traduite}"
        self.lbl_cadre_res.value = str(p.get("rapport_succession_titre", "Distribution"))
        
        # 🎯 FIX HARMONISATION ET SÉCURITÉ DE REPLI LINGUISTIQUE (Lit h['btn_imprimer'] comme Zakat Live)
        libelle_pdf_final = h.get("btn_imprimer", h.get("btn_imprimer_succession", "Générer PDF"))
        
        if self.btn_generer_pdf.content:
            self.btn_generer_pdf.content.value = str(libelle_pdf_final)

        if self.page_flet:
            try:
                self.update()
            except Exception:
                pass

        # ============================================================
        # 🎯 PARTIE 2/3 : CONFECTION DU RAPPORT TEXTUEL POUR L'ÉCRAN
        # ============================================================
        
    def actualiser_contexte(self):
        """Lit la composition de l'Arbre Familial et dresse le tableau des quotas successoraux."""
        u_id = getattr(self.app, "user_id_connecte", None)
        dev = getattr(self.app, "devise_active", "XOF")
        doc = getattr(self.app, "madhhab_actif", "Malikite")
        
        # 🌐 Extraction unifiée et dynamique des dictionnaires i18n actifs de la session globale
        langue_active = DICTIONNAIRE_LANGUES.actif
        txt_her = l_active.get("heritage", {}) if (l_active := langue_active) else {}
        txt_pdf = l_active.get("pdf", {}) if l_active else {}

        # Exécution de l'audit lourd du Core Engine
        bilan = self.moteur_succession.executer_audit_successoral_complet(
            mode_persistant=True, user_id=u_id, madhhab_actif=doc
        )
        
        # 🎯 ALIGNEMENT LOCAL : Déclaration immédiate des variables pour nettoyer reportUndefinedVariable
        m_nette = float(bilan.get("masse_successorale_nette", 0.0))
        w_ret = float(bilan.get("wasiyya_retenue", 0.0))
        c_inc = float(bilan.get("creances_actives_incluses", 0.0))
        d_purg = float(bilan.get("dettes_humaines_purgées", 0.0))
        ventilation = bilan.get("ventilation_fractions", {})
        
        # Extraction de l'arbre généalogique saisi pour filtrer uniquement les membres vivants exclus
        cache_arbre = getattr(self.app, "sync_engine").charger_donnees_module(u_id, "ARBRE_FAMILIAL") if getattr(self.app, "sync_engine", None) and u_id else {}
        saisi = {str(k).strip().lower(): int(v) for k, v in cache_arbre.items() if str(v).isdigit()}

        self.personnes_exclues_mem = [
            str(ex) for ex in bilan.get("personnes_exclues", [])
            if saisi.get(str(ex).lower(), 0) > 0
        ]

        # Extraction sécurisée des 4 paramètres i18n depuis les clés du couplage JSON
        lbl_ms_nette = txt_her.get("masse_successorale_nette", "Masse successorale nette à distribuer")
        lbl_creances_inc = txt_her.get("creances_actives_incluses", "Créances actives incluses")
        lbl_dettes_purg = txt_her.get("dettes_humaines_purgées", "Dettes et passif purgés")
        lbl_wasiyya = txt_her.get("wasiyya_retenue", "Legs testamentaires retenus (Max 1/3)")

        # Restructuration de l'inventaire mémoire
        self.intrants_mem = {
            lbl_ms_nette: f"{m_nette:.2f} {dev}",
            lbl_creances_inc: f"{c_inc:.2f} {dev}",
            lbl_dettes_purg: f"-{d_purg:.2f} {dev}",
            lbl_wasiyya: f"{w_ret:.2f} {dev}"
        }
        
        self.lignes_mem.clear()

        # Traduction dynamique du Fiqh actif et titre du rapport
        ecole_traduite = langue_active.get("barre_outils", {}).get("ecoles", {}).get(doc, doc)
        titre_traduit = txt_her.get("rapport_succession", "RAPPORT DE SUCCESSION")

        # 🎯 CONFECTION DU RAPPORT TEXTUEL POUR L'ÉCRAN PRINCIPAL
        v = f"📜 {titre_traduit} ({ecole_traduite.upper()}) :\n"
        v += " ==================================================\n"
        v += f"   ▶ {lbl_ms_nette} : {m_nette:.2f} {dev}\n"
        v += f"   ▶ {lbl_creances_inc} : {c_inc:.2f} {dev}\n"
        v += f"   ▶ {lbl_dettes_purg} : -{d_purg:.2f} {dev}\n"
        v += f"   ▶ {lbl_wasiyya} : {w_ret:.2f} {dev}\n"
        v += " ==================================================\n\n"

        # Ventilation dynamique des parts à l'écran
        if ventilation:
            candidats_json = txt_her.get("candidats", {})
            for heritier, fraction in ventilation.items():
                # 🎯 HARMONISATION ÉCRAN LIVE : Remplacement par l'arabe littéraire pour le Khountha
                if str(heritier).lower() == "khountha":
                    nom_heritier_traduit = "الخنثى المشكل"
                else:
                    nom_heritier_traduit = candidats_json.get(heritier.lower(), heritier.upper())
                
                ligne = f"     - {nom_heritier_traduit} : {fraction:.4f} ({(m_nette * fraction):.2f} {dev})"
                v += f"{ligne}\n"
                self.lignes_mem.append(ligne)
        else:
            v += f"   {txt_her.get('succession_sans_heritier', '❌ Aucun héritier éligible.')}\n"

        # Affichage épuré des exclus (Hajb) à l'IHM
        # 🎯 L'ALIGNEMENT SOUVERAIN ASSAINI : Récupération du titre officiel du PDF
        label_bloques = txt_pdf.get("sec_3_titre_exclus", "3. Candidats Bloqués ou Écartés de la Succession (Hajb) :")
        label_bloques_clean = label_bloques.replace("<b>", "").replace("</b>", "").replace("3. ", "").replace(":", "").strip()
        
        exclus_text_IHM = ""
        candidats_json = txt_her.get("candidats", {})
        
        # Extraction propre sous forme de liste en minuscules de tous les bénéficiaires actifs
        liste_beneficiaires_actifs = [str(k).lower().strip() for k in ventilation.keys()]
        
        # A. Traitement initial exclusif des exclus physiques issus du moteur d'exclusions absolues
        if self.personnes_exclues_mem:
            for ex in self.personnes_exclues_mem: 
                # 🎯 SÉCURISATION INTÉGRALE : Isolation de la ligne et conversion forcée en String pure
                ligne_brute = str(ex).strip()
                if ":" in ligne_brute:
                    cle_brute = str(ligne_brute.split(":", 1)[0]).strip().upper()
                else:
                    cle_brute = str(ligne_brute).strip().upper()
                    
                cle_json = str(cle_brute.lower().replace("-", "_")).strip()
                
                # Gestion étanche de la racine pour neutraliser les multiplicités (ex: epouse_1 -> epouse)
                if "_" in cle_json and any(str(i) in cle_json for i in range(10)):
                    cle_json_base = str(cle_json.split("_")[0]).strip()
                else:
                    cle_json_base = str(cle_json).strip()
                
                # 🎯 LE SHIELD ANTI-DOUBLON UNIVERSEL SÉCURISÉ :
                # Si le candidat (ou sa racine) est déjà traité en haut avec une part (y compris à 0.0),
                # il est retiré de force de la section inférieure pour éviter les contradictions visuelles.
                if cle_json in liste_beneficiaires_actifs or cle_json_base in liste_beneficiaires_actifs:
                    continue
                    
                exclus_text_IHM += f"     - {candidats_json.get(cle_json, candidats_json.get(cle_json_base, cle_brute.capitalize()))}\n"

        # C. Injection physique de l'en-tête et des lignes nettoyées si des exclus subsistent
        if exclus_text_IHM.strip():
            v += f"\n   ▶ {label_bloques_clean} :\n" + exclus_text_IHM

        # Injection de la chaîne finale de manière réactive dans l'IHM Flet
        self.text_rapport.value = v
        
        if self.page_flet:
            try:
                self.update()
            except Exception:
                pass

    # ============================================================
    # 🎯 PARTIE 3/3 : COMPILATION DU CERTIFICAT SUCCESSORAL PDF (CORRIGÉE)
    # ============================================================

    def imprimer_pdf_heritage_live(self):
        """Génère le certificat d'hérédité au format PDF via le CertificateEngine."""
        if not self.lignes_mem: 
            return
        dev = getattr(self.app, "devise_active", "XOF")
        u_id = getattr(self.app, "user_id_connecte", None)
        doc_active = getattr(self.app, "madhhab_actif", "Malikite")
        
        langue_active = DICTIONNAIRE_LANGUES.actif
        txt_her = l_active.get("heritage", {}) if (l_active := langue_active) else {}
        b_candidats = txt_her.get("candidats", {})

        res_live = {}
        try:
            res_live = self.moteur_succession.executer_audit_successoral_complet(mode_persistant=True, user_id=u_id, madhhab_actif=doc_active)
        except Exception: 
            pass

        val_net = float(res_live.get("masse_successorale_nette", 0.0))
        val_creances = float(res_live.get("creances_actives_incluses", 0.0))
        val_dettes = float(res_live.get("dettes_humaines_purgées", 0.0))
        val_legs = float(res_live.get("wasiyya_retenue", 0.0))

        label_net = txt_her.get("masse_successorale_nette", "Masse successorale nette à distribuer")
        label_creances = txt_her.get("creances_actives_incluses", "Créances actives incluses")
        label_dettes = txt_her.get("dettes_humaines_purgées", "Dettes et passif purgés")
        label_legs = txt_her.get("wasiyya_retenue", "Legs testamentaires retenus (Max 1/3)")

        intrants_ordonnes_i18n = {
            label_net: f"{val_net:.2f} {dev}",
            label_creances: f"{val_creances:.2f} {dev}",
            label_dettes: f"-{val_dettes:.2f} {dev}",
            label_legs: f"{val_legs:.2f} {dev}"
        }

        langue_est_arabe = any('\u0600' <= char <= '\u06FF' for char in str(txt_her.get('rapport_succession', '')))
        lignes_exclus_traduites = []
        for ex in getattr(self, "personnes_exclues_mem", []):
            txt_ex = str(ex).strip()
            
            if ":" in txt_ex:
                cle_brute, commentaire_brut = txt_ex.split(":", 1)
                cle_brute = cle_brute.strip().upper()
                commentaire_final = commentaire_brut.strip()
            else:
                cle_brute = txt_ex.upper()
                commentaire_final = ""
            
            cle_json = cle_brute.lower().replace("-", "_")
            nom_traduit = b_candidats.get(cle_json, cle_brute.capitalize())
            
            if commentaire_final:
                if langue_est_arabe:
                    separateur_espace = "  \u200E◄\u200E  "
                    lignes_exclus_traduites.append(f"• {nom_traduit}{separateur_espace}{commentaire_final}")
                else:
                    separateur_espace = "  \u200E►\u200E  "
                    lignes_exclus_traduites.append(f"• {nom_traduit}{separateur_espace}{commentaire_final}")
            else:
                lignes_exclus_traduites.append(f"• {nom_traduit}")

        identite = {
            "nom": getattr(self.app, "nom_utilisateur_connecte", "Inconnu"), 
            "prenom": "", 
            "ville": getattr(self.app, "ville_utilisateur", "Espace"), 
            "pays": getattr(self.app, "pays_utilisateur", "Privé"), 
            "telephone": getattr(self.app, "telephone_utilisateur", "-"), 
            "personnes_exclues": lignes_exclus_traduites
        }
        
        from fractions import Fraction
        import math

        liste_fractions = []
        for ligne in self.lignes_mem:
            txt_ligne = " ".join(ligne) if isinstance(ligne, list) else str(ligne)
            motifs_decimaux = re.findall(r"\b0[\.,]\d+\b", txt_ligne)
            for dec_str in motifs_decimaux:
                try:
                    val_float = float(dec_str.replace(",", "."))
                    liste_fractions.append(Fraction(val_float).limit_denominator(96))
                except Exception: pass

        denomination_commune = 1
        for frac in liste_fractions:
            denomination_commune = abs(denomination_commune * frac.denominator) // math.gcd(denomination_commune, frac.denominator)

        lignes_pdf_fractions = []
        candidats_json = txt_her.get("candidats", {})
        ventilation = res_live.get("ventilation_fractions", {})
        
        if ventilation:
            for heritier, fraction in ventilation.items():
                # 🎯 INTERCEPTION LIVE BAS : Harmonisation en arabe littéraire pour le Khountha
                if str(heritier).lower() == "khountha":
                    nom_heritier_traduit = "الخنثى المشكل"
                else:
                    nom_heritier_traduit = candidats_json.get(heritier.lower(), heritier.upper())
                
                parts_entieres = int(round(fraction * denomination_commune))
                montant_calcule = val_net * fraction
                
                label_parts = f"\u200E[{parts_entieres} : {denomination_commune}]\u200E"
                ligne_restructuree = f"{label_parts}  -  {nom_heritier_traduit}  :  {montant_calcule:.2f} {dev}"
                lignes_pdf_fractions.append(ligne_restructuree)
        else:
            lignes_pdf_fractions.append(txt_her.get('succession_sans_heritier', '❌ Aucun héritier éligible.'))

        # ------------------------------------------------------------
        # 🎯 ULTRA-PRESTIGE RETOUR HOUSTAZ (INJECTION TEXTUELLE CADRE VERT LIVE)
        # ------------------------------------------------------------
        # Récupération brute du cache SQLite de l'arbre familial
        cache_arbre = getattr(self.app, "sync_engine").charger_donnees_module(u_id, "ARBRE_FAMILIAL") if getattr(self.app, "sync_engine", None) and u_id else {}
        
        # 1. Extraction et nettoyage strict de tous les compteurs numériques présents sur le disque
        saisi = {}
        candidats_canoniques = [
            "epoux", "epouse", "fils", "fille", "pere", "mere", "grand_pere", "grand_mere",
            "petit_fils", "petite_fille", "frere_germain", "soeur_germaine", "frere_paternel",
            "soeur_paternelle", "frere_uterin", "soeur_uterine", "fils_frere_germain",
            "fils_frere_paternel", "oncle_germain", "oncle_paternel", "cousin_germain", "cousin_paternel"
        ]
        for comp in candidats_canoniques:
            try:
                val_brute = cache_arbre.get(comp, 0)
                if val_brute is not None and str(val_brute).isdigit() and int(val_brute) > 0:
                    saisi[comp] = int(val_brute)
            except Exception: pass

        # 2. Détection du signal Zawil Arham & Khountha depuis la base
        cas_arham = cache_arbre.get("cas_zawil_arham_actif", False)
        is_arham_actif = str(cas_arham).lower() in ["true", "1"] or cas_arham is True

        cas_khountha = cache_arbre.get("cas_khountha_actif", False)
        is_khountha_actif = str(cas_khountha).lower() in ["true", "1"] or cas_khountha is True

        # 3. 🎯 LOGIQUE DE PROJECTION DE PRESTIGE :
        if is_arham_actif:
            try:
                qte_f = int(cache_arbre.get("frere_uterin", 0))
                qte_s = int(cache_arbre.get("soeur_uterine", 0))
                
                # Hydratation des personnes physiques
                if qte_f > 0: saisi["frere_uterin"] = qte_f
                if qte_s > 0: saisi["soeur_uterine"] = qte_s
                
                # 🎯 RECTIFICATION SANS TOUCHER AU PÈRE :
                # Au lieu d'écraser le père, on utilise le "grand_pere" à 0 pour ouvrir le cadre vert
                if "pere" not in saisi or int(saisi.get("pere", 0)) == 0:
                    saisi["grand_pere"] = 0
                    
                saisi["مسألة ذوي الأرحام"] = 1
                saisi["cas_zawil_arham_actif"] = True
            except Exception: pass

        # 🎯 AJOUT ÉTANCHE KHOUNTHA EN ARABE POUR LE CADRE SUPÉRIEUR
        if is_khountha_actif:
            # 🌟 ALIGNEMENT PARFAIT : Uniquement la clé arabe, aucune clé parasite textuelle
            saisi["مسألة الخنثى المشكل"] = 1  
            
            # 🎯 PIVOT DE SÉCURITÉ UNIVERSEL DU GRAND-PÈRE SANS TOUCHER AU PÈRE :
            # Force ReportLab à ouvrir et dessiner le cadre vert supérieur sans JAMAIS détruire
            # la valeur du vrai Père s'il est présent à l'écran (quantité = 1).
            if "pere" not in saisi or int(saisi.get("pere", 0)) == 0:
                saisi["grand_pere"] = 0 

        # Hydratation de l'enveloppe finale envoyée au CertificateEngine
        intrants_ordonnes_i18n["arbre_saisi"] = saisi

        # 🎯 TRANSMISSION FINALE AU PDF REPORTLAB INITIAL
        generer_certificat_pdf(identite, "HERITAGE", doc_active, dev, intrants_ordonnes_i18n, lignes_pdf_fractions)

    def changer_langue(self, n_lang: str): 
        """Méthode invoquée par la propagation descendante du Layout central."""
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)
        
    def actualiser_donnees_affichage(self): 
        """Cycle de vie : Force le re-calcul successoral et applique la traduction i18n différée."""
        self.actualiser_contexte()
        
        async def executer_traduction_heritage_differee(*args):
            import asyncio
            await asyncio.sleep(0.06)
            self.traduire_page(DICTIONNAIRE_LANGUES.actif)
            
        if self.page_flet:
            self.page_flet.run_task(executer_traduction_heritage_differee)
