"""
INTERFACE DE LA ZAKAT LIVE AUTOMATIQUE
Version 6.2 - Alignement i18n synchrone et harmonisation du verdict vert calqué sur Zakat Tiers.
"""
import tkinter as tk
from tkinter import ttk
from gui.langues import DICTIONNAIRE_LANGUES
from core.financial_engine import FinancialEngine
from core.certificate_engine import generer_certificat_pdf

class EcranZakat(tk.Frame):
    def __init__(self, parent, app_reference):
        super().__init__(parent, bg="#ffffff")
        self.app = app_reference
        self.mode_mobile = None
        self.moteur_finance = FinancialEngine(
            sync_engine_reference=getattr(self.app, "sync_engine", None)
        )
        
        DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(
            self.action_langue
        )
        self.fortune_calculee = {
            "liq": 0.0, "or": 0.0, "argent": 0.0, 
            "due": 0.0, "creances": 0.0, "dettes": 0.0
        }
        self.agri_calcule = {"poids": 0.0, "due": 0.0}
        self.pastoral_calcule = {
            "o": "Exempté", "b": "Exempté", "ovins": 0, "bovins": 0
        }
        self.intrants_mem = {}
        self.construire_interface()

    def construire_interface(self):
        # 🎯 BANDEAU SUPÉRIEUR : Mode et Doctrine active
        self.c_mode = tk.Frame(self, bg="#d1fae5", height=35, bd=1, relief="groove")
        self.c_mode.pack(fill="x", padx=15, pady=4)
        self.lbl_info_fiqh = tk.Label(
            self.c_mode, font=("Helvetica", 10, "bold"), fg="#064e3b", bg="#d1fae5"
        )
        self.lbl_info_fiqh.pack(pady=6)

        # 🎯 BLOC DE VÉRITÉ : Affichage clair des cours en lecture seule i18n
        self.cadre_cours_live = tk.LabelFrame(
            self, bg="#ffffff", font=("Helvetica", 9, "bold"), fg="#064e3b", padx=10, pady=6
        )
        self.cadre_cours_live.pack(fill="x", padx=15, pady=6)
        
        self.lbl_cours_or = tk.Label(
            self.cadre_cours_live, font=("Helvetica", 9, "bold"), bg="#ffffff", fg="#4b5563"
        )
        self.lbl_cours_or.pack(anchor="w", pady=2)

        self.lbl_cours_argent = tk.Label(
            self.cadre_cours_live, font=("Helvetica", 9, "bold"), bg="#ffffff", fg="#4b5563"
        )
        self.lbl_cours_argent.pack(anchor="w", pady=2)

        # 🎯 LE CADRE DE BILAN : Grand espace d'affichage pour une lecture limpide
        self.cadre_res = tk.LabelFrame(
            self, font=("Helvetica", 10, "bold"), fg="#064e3b", bg="#ffffff", padx=10, pady=8
        )
        self.cadre_res.pack(fill="both", expand=True, padx=15, pady=6)

        # Ajout d'un widget Text défilant verticalement pour le rapport détaillé
        self.scr_txt = tk.Scrollbar(self.cadre_res)
        self.scr_txt.pack(side="right", fill="y")

        self.text_rapport = tk.Text(
            self.cadre_res, font=("Courier New", 10), bg="#f9fafb", bd=1, relief="solid",
            wrap=tk.WORD, height=12, yscrollcommand=self.scr_txt.set
        )
        self.text_rapport.pack(fill="both", expand=True)
        self.scr_txt.config(command=self.text_rapport.yview)

        # 🎯 BOUTON D'IMPRESSION DU CERTIFICAT PDF SHARIA-COMPLIANT
        self.btn_pdf = tk.Button(
            self, font=("Helvetica", 10, "bold"), bg="#064e3b", fg="white", 
            bd=0, pady=8, command=self.imprimer_pdf_live_nominatif
        )
        self.btn_pdf.pack(fill="x", padx=15, pady=6)

        self.traduire_page(DICTIONNAIRE_LANGUES.actif)

    def action_langue(self, dic):
        if self.winfo_exists(): self.traduire_page(dic)

    def traduire_page(self, dic):
        z = dic.get("zakat", {})
        b = dic.get("barre_outils", {})
        
        # 🎯 RECTIFICATION : Capture et traduction du nom de l'école juridique active
        ecole_technique = getattr(self.app, 'madhhab_actif', 'Malikite')
        ecole_traduite = b.get("ecoles", {}).get(ecole_technique, ecole_technique)
        
        self.lbl_info_fiqh.config(
            text=f"🔄 {b.get('mode_live', 'Live')} | {b.get('label_fiqh', 'Fiqh:')} {ecole_traduite}"
        )
        self.cadre_cours_live.config(text=z.get("cadre_cours", "Cours Référentiels"))
        self.cadre_res.config(text=z.get("cadre_analyse", "Rapport"))
        self.btn_pdf.config(text=z.get("btn_imprimer", "Générer PDF"))

    def actualiser_contexte(self):
        u_id = getattr(self.app, "user_id_connecte", None)
        doctrine = getattr(self.app, "madhhab_actif", "Malikite")
        dev = getattr(self.app, "devise_active", "XOF")
        
        c_or, c_arg = 45000.0, 650.0
        agri_brut_kg = 0.0
        
        if getattr(self.app, "sync_engine", None) and u_id:
            cache_fin = self.app.sync_engine.charger_donnees_module(u_id, "FINANCES")
            c_or = float(cache_fin.get("or_cours", 45000.0))
            c_arg = float(cache_fin.get("argent_cours", 650.0))
            agri_brut_kg = float(cache_fin.get("poids", 0.0))

        # 🌐 Extraction unifiée et dynamique des dictionnaires i18n actifs
        langue_active = getattr(self.app, "langue_active", DICTIONNAIRE_LANGUES.actif)
        txt_zk = langue_active.get("zakat", {})
        txt_auth = langue_active.get("auth", {})
        txt_fin = langue_active.get("patrimoine", {})

        # 🎯 ALIGNEMENT DU FIQH TRADUIT (Évite l'apparition de la clé technique brute)
        ecole_traduite = langue_active.get("barre_outils", {}).get("ecoles", {}).get(doctrine, doctrine)

        self.lbl_cours_or.config(text=f"{txt_zk.get('lbl_cours_or', 'Cours Or')} : {c_or:.0f} {dev}/g")
        self.lbl_cours_argent.config(text=f"{txt_zk.get('lbl_cours_argent', 'Cours Argent')} : {c_arg:.0f} {dev}/g")

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

            # 🎯 UNIFICATION DE LA SECTION 1 SUR LES CLÉS TECHNIQUES UNIVERSELLES
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

            # 🎯 RECTIFICATION I18N : Récupération dynamique pour le live avec Fiqh traduit
            titre_traduit = txt_zk.get("rapport_titre", "BILAN DE ZAKAT")

            # 🎯 RECONSTRUCTION DU RAPPORT TEXTUEL MULTILINGUE SÉCURISÉ POUR L'ÉCRAN
            b_v = txt_zk.get("statut_eligible", "🟢 ÉLIGIBLE") if res["est_imposable_monetaire"] else txt_zk.get("statut_non_eligible", "🔴 EXEMPTÉ")
            
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
            
            self.text_rapport.config(state=tk.NORMAL)
            self.text_rapport.delete("1.0", tk.END)
            self.text_rapport.insert("1.0", v)
            self.text_rapport.config(state=tk.DISABLED)
        except Exception as e:
            self.text_rapport.config(state=tk.NORMAL)
            self.text_rapport.delete("1.0", tk.END)
            self.text_rapport.insert("1.0", f"⚠️ {txt_auth.get('err_champs_vides', 'Error')}")
            self.text_rapport.config(state=tk.DISABLED)

    def imprimer_pdf_live_nominatif(self):
        if not self.intrants_mem: return
        dev = getattr(self.app, "devise_active", "XOF")
        
        # 🌐 Récupération dynamique du dictionnaire de langue actif
        langue_active = getattr(self.app, "langue_active", DICTIONNAIRE_LANGUES.actif)
        txt_zk = langue_active.get("zakat", {})
        
        identite = {
            "nom": getattr(self.app, "nom_utilisateur_connecte", "Inconnu"), 
            "prenom": "", 
            "ville": getattr(self.app, "ville_utilisateur", "Espace"), 
            "pays": getattr(self.app, "pays_utilisateur", "Privé"), 
            "telephone": getattr(self.app, "telephone_utilisateur", "-")
        }
        
        # 🎯 HARMONISATION DE LA SECTION 2 : Structure de verdict vert épuré
        self.lignes_mem = [
            [f"{txt_zk.get('assiette_imposable', 'Assiette')} : {self.fortune_calculee['liq']:.2f} {dev}"],
            [f"{txt_zk.get('montant_du', 'Zakat monétaire due')} (2.5%) : {self.fortune_calculee['due']:.2f} {dev}"],
            [f"{txt_zk.get('zakat_grain', 'Zakat Agricole')} : {self.agri_calcule['due']:.2f} kg"],
            [f"{txt_zk.get('zakat_moutons', 'Zakat Ovins')} : {self.pastoral_calcule['o']}"],
            [f"{txt_zk.get('zakat_bovins', 'Zakat Bovins')} : {self.pastoral_calcule['b']}"]
        ]
        
        # 🎯 CAPTURE DIRECTE DU TEXTE DE L'ÉCRAN : Plus aucun intermédiaire ou calcul asynchrone
        nisab_live_texte = getattr(self, "nisab_affiche_ecran", txt_zk.get("options_nisab", {}).get("nisab_plus_bas", "Baromètre Prudent"))

        # Envoi direct au compilateur PDF avec la valeur textuelle validée à l'écran
        generer_certificat_pdf(
            identite, 
            "ZAKAT", 
            self.app.madhhab_actif, 
            dev, 
            self.intrants_mem, 
            self.lignes_mem, 
            nisab_label=nisab_live_texte
        )

    def changer_langue(self, n_lang): 
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)
        
    def actualiser_donnees_affichage(self): 
        self.actualiser_contexte()
