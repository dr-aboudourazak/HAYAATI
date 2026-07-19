"""
INTERFACE DES RATIOS DE SUCCESSION LIVE AUTOMATIQUE
Version 6.2 - Alignement i18n synchrone et en-tête épuré à 4 masses universelles.
"""
import tkinter as tk
from tkinter import ttk
import re
from gui.langues import DICTIONNAIRE_LANGUES
from core.certificate_engine import generer_certificat_pdf
from core.heritage_engine import HeritageEngine

class EcranHeritage(tk.Frame):
    def __init__(self, parent, app_reference):
        super().__init__(parent, bg="#ffffff")
        self.app = app_reference
        self.moteur_succession = HeritageEngine(
            sync_engine_reference=getattr(self.app, "sync_engine", None)
        )
        
        DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(
            self.action_langue
        )
        self.intrants_mem, self.lignes_mem, self.personnes_exclues_mem = {}, [], []  
        self.construire_interface()

    def construire_interface(self):
        self.c_mode = tk.Frame(self, bg="#d1fae5", height=25, bd=1, relief="groove")
        self.c_mode.pack(fill="x", padx=10, pady=2)
        self.lbl_sync = tk.Label(
            self.c_mode, font=("Helvetica", 9, "bold"), fg="#064e3b", bg="#d1fae5"
        )
        self.lbl_sync.pack(pady=2)

        self.cadre_res = tk.LabelFrame(
            self, font=("Helvetica", 9, "bold"), fg="#064e3b", bg="#ffffff", padx=5, pady=5
        )
        self.cadre_res.pack(fill="both", expand=True, padx=10, pady=2)

        self.text_rapport = tk.Text(
            self.cadre_res, font=("Courier New", 9), bg="#f9fafb", bd=1, 
            relief="solid", wrap=tk.WORD, height=10
        )
        self.text_rapport.pack(fill="both", expand=True)

        self.btn_pdf = tk.Button(
            self, font=("Helvetica", 9, "bold"), bg="#064e3b", fg="white", 
            bd=0, pady=6, command=self.imprimer_pdf_heritage_live
        )
        self.btn_pdf.pack(fill="x", padx=10, pady=4)

        self.traduire_page(getattr(self.app, "langue_active", DICTIONNAIRE_LANGUES.actif))

    def action_langue(self, dic):
        if self.winfo_exists(): self.traduire_page(dic)

    def traduire_page(self, dic):
        h, p = dic.get("heritage", {}), dic.get("pdf", {})
        b = dic.get("barre_outils", {})
        
        # 🎯 RECTIFICATION : Extraction de la doctrine traduite pour l'en-tête
        ecole_technique = getattr(self.app, 'madhhab_actif', 'Malikite')
        ecole_traduite = b.get("ecoles", {}).get(ecole_technique, ecole_technique)
        
        if hasattr(self, "lbl_sync"):
            self.lbl_sync.config(
                text=f"🔄 {b.get('mode_live', 'Live')} | {b.get('label_fiqh', 'Fiqh:')} {ecole_traduite}"
            )
        if hasattr(self, "cadre_res"):
            self.cadre_res.config(text=p.get("rapport_succession_titre", "Distribution"))
        if hasattr(self, "btn_pdf"):
            self.btn_pdf.config(text=h.get("btn_imprimer_succession", "Générer PDF"))

    def actualiser_contexte(self):
        u_id = getattr(self.app, "user_id_connecte", None)
        dev = getattr(self.app, "devise_active", "XOF")
        doc = getattr(self.app, "madhhab_actif", "Malikite")
        
        # 🌐 Extraction unifiée et dynamique des dictionnaires i18n actifs de la session globale
        langue_active = getattr(self.app, "langue_active", DICTIONNAIRE_LANGUES.actif)
        txt_her = langue_active.get("heritage", {})
        txt_pdf = langue_active.get("pdf", {})

        bilan = self.moteur_succession.executer_audit_successoral_complet(
            mode_persistant=True, user_id=u_id, madhhab_actif=doc
        )
        
        # 🎯 Récupération des valeurs exactes calculées et validées par le Core Engine
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

        # 🎯 EXTRACTION SÉCURISÉE DES 4 PARAMÈTRES i18n DIRECTEMENT DEPUIS LES CLÉS DU COUPLAGE JSON
        lbl_ms_nette = txt_her.get("masse_successorale_nette", "Masse successorale nette à distribuer")
        lbl_creances_inc = txt_her.get("creances_actives_incluses", "Créances actives incluses")
        lbl_dettes_purg = txt_her.get("dettes_humaines_purgées", "Dettes et passif purgés")
        lbl_wasiyya = txt_her.get("wasiyya_retenue", "Legs testamentaires retenus (Max 1/3)")

        # 🎯 RESTRUCTURATION DE L'INVENTAIRE : Alimentation stricte sans four-tout
        self.intrants_mem = {
            lbl_ms_nette: f"{m_nette:.2f} {dev}",
            lbl_creances_inc: f"{c_inc:.2f} {dev}",
            lbl_dettes_purg: f"-{d_purg:.2f} {dev}",
            lbl_wasiyya: f"{w_ret:.2f} {dev}"
        }
        
        self.lignes_mem.clear()
        self.text_rapport.config(state=tk.NORMAL)
        self.text_rapport.delete("1.0", tk.END)

        # Traduction dynamique du Fiqh actif
        ecole_traduite = langue_active.get("barre_outils", {}).get("ecoles", {}).get(doc, doc)
        titre_traduit = txt_her.get("rapport_succession", "RAPPORT DE SUCCESSION")

        # 🎯 HARMONISATION DE LA SECTION 1 SUR L'ÉCRAN PRINCIPAL (Widget Text Live)
        v = f"📜 {titre_traduit} ({ecole_traduite.upper()}) :\n"
        v += " ==================================================\n"
        v += f"   ▶ {lbl_ms_nette} : {m_nette:.2f} {dev}\n"
        v += f"   ▶ {lbl_creances_inc} : {c_inc:.2f} {dev}\n"
        v += f"   ▶ {lbl_dettes_purg} : -{d_purg:.2f} {dev}\n"
        v += f"   ▶ {lbl_wasiyya} : {w_ret:.2f} {dev}\n"
        v += " ==================================================\n\n"

        # 🎯 SECTION 2 : Ventilation des parts à l'écran
        if ventilation:
            candidats_json = txt_her.get("candidats", {})
            for heritier, fraction in ventilation.items():
                nom_heritier_traduit = candidats_json.get(heritier.lower(), heritier.upper())
                ligne = f"     - {nom_heritier_traduit} : {fraction:.4f} ({(m_nette * fraction):.2f} {dev})"
                v += f"{ligne}\n"
                self.lignes_mem.append(ligne)
        else:
            v += f"   {txt_her.get('succession_sans_heritier', '❌ Aucun héritier éligible.')}\n"

        # 🎯 SECTION 3 : Affichage épuré des exclus (Hajb) sans commentaire parasite à l'écran
        if self.personnes_exclues_mem:
            v += f"\n   ▶ {txt_pdf.get('tableau_part', 'Exclus')} :\n"
            candidats_json = txt_her.get("candidats", {})
            for ex in self.personnes_exclues_mem: 
                cle_brute = str(ex).strip().split(":", 1)[0].strip().upper()
                cle_json = cle_brute.lower().replace("-", "_")
                v += f"     - {candidats_json.get(cle_json, cle_brute.capitalize())}\n"

        self.text_rapport.insert("1.0", v)
        self.text_rapport.config(state=tk.DISABLED)

    def imprimer_pdf_heritage_live(self):
        if not self.lignes_mem: return
        dev = getattr(self.app, "devise_active", "XOF")
        u_id = getattr(self.app, "user_id_connecte", None)
        doc_active = getattr(self.app, "madhhab_actif", "Malikite")
        
        langue_active = getattr(self.app, "langue_active", DICTIONNAIRE_LANGUES.actif)
        txt_her = langue_active.get("heritage", {})
        b_candidats = txt_her.get("candidats", {})

        # Lecture synchrone directe du HeritageEngine
        res_live = {}
        try:
            res_live = self.moteur_succession.executer_audit_successoral_complet(mode_persistant=True, user_id=u_id, madhhab_actif=doc_active)
        except Exception: pass

        # 🎯 CORRECTION ABSOLUE DE LA SECTION 1 SANS CLÉ TECHNIQUE NI CHUTE À 0
        val_net = float(res_live.get("masse_successorale_nette", 0.0))
        val_creances = float(res_live.get("creances_actives_incluses", 0.0))
        val_dettes = float(res_live.get("dettes_humaines_purgées", 0.0))
        val_legs = float(res_live.get("wasiyya_retenue", 0.0))

        # Mappage sur les clés i18n pures de votre fichier JSON
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

        # 🎯 SECTION 3 LIVE VERROUILLÉE : ÉLARGISSEMENT DE L'ESPACE ENTRE HÉRITIER ET COMMENTAIRE
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
                # 🎯 INJECTION D'UN SÉPARATEUR ÉLARGIS ET SÉCURISÉ BiDi
                if langue_est_arabe:
                    separateur_espace = "  \u200E◄\u200E  "
                    lignes_exclus_traduites.append(f"• {nom_traduit}{separateur_espace}{commentaire_final}")
                else:
                    separateur_espace = "  \u200E►\u200E  "
                    lignes_exclus_traduites.append(f"• {nom_traduit}{separateur_espace}{commentaire_final}")
            else:
                lignes_exclus_traduites.append(f"• {nom_traduit}")

        identite = {"nom": getattr(self.app, "nom_utilisateur_connecte", "Inconnu"), "prenom": "", "ville": getattr(self.app, "ville_utilisateur", "Espace"), "pays": getattr(self.app, "pays_utilisateur", "Privé"), "telephone": getattr(self.app, "telephone_utilisateur", "-"), "personnes_exclues": lignes_exclus_traduites}
        
        # 🎯 SECTION 2 LIVE PARFAITE : ALIGNEMENT UNIVERSEL PAR LA FRACTION (ا) ANTI-INVERSION BiDi
        from fractions import Fraction
        import math

        # Étape 1 : Analyser toutes les parts décimales pour trouver le dénominateur commun (Asl)
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
        langue_est_arabe = any('\u0600' <= char <= '\u06FF' for char in str(txt_her.get('rapport_succession', '')))
        
        lignes_pdf_fractions = []
        candidats_json = txt_her.get("candidats", {})
        ventilation = res_live.get("ventilation_fractions", {})
        
        if ventilation:
            for heritier, fraction in ventilation.items():
                nom_heritier_traduit = candidats_json.get(heritier.lower(), heritier.upper())
                parts_entieres = int(round(fraction * denomination_commune))
                montant_calcule = val_net * fraction
                
                # 🎯 RECTIFICATION RADICALE : Utilisation du séparateur symétrique ":" pour toutes les langues
                # Élimine définitivement le masquage ou l'inversion bidi de ReportLab
                label_parts = f"\u200E[{parts_entieres} : {denomination_commune}]\u200E"
                ligne_restructuree = f"{label_parts}  -  {nom_heritier_traduit}  :  {montant_calcule:.2f} {dev}"
                
                lignes_pdf_fractions.append(ligne_restructuree)
        else:
            lignes_pdf_fractions.append(txt_her.get('succession_sans_heritier', '❌ Aucun héritier éligible.'))

        generer_certificat_pdf(identite, "HERITAGE", doc_active, dev, intrants_ordonnes_i18n, lignes_pdf_fractions)

    def changer_langue(self, n_lang): 
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)
        
    def actualiser_donnees_affichage(self): 
        self.actualiser_contexte()
