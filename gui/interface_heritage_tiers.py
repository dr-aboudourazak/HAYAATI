"""
ÉCRAN DE DIAGNOSTIC SUCCESSION TIERS (GUI/INTERFACE_HERITAGE_TIERS.PY)
Version 5.5 - Harmonisation totale de la Section 1 à l'écran et gestion i18n robuste.
"""
import tkinter as tk
from tkinter import ttk
import re
from gui.langues import DICTIONNAIRE_LANGUES
from core.certificate_engine import generer_certificat_pdf
from core.heritage_engine import HeritageEngine

class EcranHeritageTiers(tk.Frame):
    def __init__(self, parent, app_reference):
        super().__init__(parent, bg="#ffffff")
        self.app = app_reference
        self.mode_mobile = None
        self.moteur_succession = HeritageEngine()
        DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_langue)
        
        # 🎯 SÉPARATION CANONIQUE STRICTE : Époux et Épouse ont désormais deux compteurs distincts
        self.famille = [
            "epoux", "epouse", "fils", "fille", "pere", "mere", "grand_pere", "grand_mere",
            "petit_fils", "petite_fille", "frere_germain", "soeur_germaine", "frere_paternel",
            "soeur_paternelle", "frere_uterin", "soeur_uterine", "fils_frere_germain",
            "fils_frere_paternel", "oncle_germain", "oncle_paternel", "cousin_germain", "cousin_paternel"
        ]
        self.cles_caps = ["en_masse", "en_creances", "en_dettes", "en_legs"]
        self.labels, self.entries = {}, {}
        self.intrants_mem, self.lignes_mem, self.lignes_exclus_mem = {}, [], []
        
        # Mémorisation du dictionnaire brut du moteur pour le bouton imprimer
        self.dernier_resultat_succession = {}
        self.construire_interface()

    def construire_interface(self):
        self.c_tiers = tk.LabelFrame(self, font=("Helvetica", 9, "bold"), fg="#d97706", bg="#ffffff", padx=5)
        self.c_tiers.pack(fill="x", padx=10, pady=2)
        
        self.lbl_defunt = tk.Label(self.c_tiers, bg="#ffffff", font=("Helvetica", 8, "bold"))
        self.entree_nom = tk.Entry(self.c_tiers, font=("Arial", 9), bd=1, relief="solid", width=10)
        self.entree_nom.insert(0, "Amina Diallo")

        for k in self.cles_caps:
            self.labels[k] = tk.Label(self.c_tiers, bg="#ffffff", font=("Helvetica", 8))
            self.entries[k] = tk.Entry(self.c_tiers, font=("Arial", 9), bd=1, relief="solid", width=5)
            self.entries[k].insert(0, "0")
            setattr(self, k, self.entries[k])

        self.c_famille = tk.LabelFrame(self, font=("Helvetica", 9, "bold"), fg="#064e3b", bg="#ffffff", padx=5)
        self.c_famille.pack(fill="x", padx=10, pady=2)

        for c in self.famille:
            self.labels[c] = tk.Label(self.c_famille, bg="#ffffff", font=("Helvetica", 8))
            max_l = 1 if c in ["epoux", "pere", "mere", "grand_pere", "grand_mere"] else 4 if c == "epouse" else 20
            self.entries[c] = tk.Spinbox(self.c_famille, from_=0, to=max_l, width=3, font=("Arial", 9), bd=1, relief="solid")
            self.entries[c].delete(0, tk.END)
            self.entries[c].insert(0, "0")

        self.btn_calc = tk.Button(self, font=("Helvetica", 9, "bold"), bg="#064e3b", fg="white", command=self.calculer)
        self.btn_calc.pack(fill="x", padx=10, pady=2)
        self.btn_pdf = tk.Button(self, font=("Helvetica", 9, "bold"), bg="#0f766e", fg="white", command=self.imprimer)
        self.btn_pdf.pack(fill="x", padx=10, pady=2)

        self.c_res = tk.LabelFrame(self, font=("Helvetica", 9, "bold"), fg="#064e3b", bg="#ffffff", padx=5)
        self.c_res.pack(fill="both", expand=True, padx=10, pady=2)
        self.text_rapport = tk.Text(self.c_res, font=("Arial", 9), bg="#f9fafb", bd=1, height=4)
        self.text_rapport.pack(fill="both", expand=True)

        self.bind("<Configure>", lambda e: self.ordonner_layout(self.winfo_width() < 500))
        self.traduire(getattr(self.app, "langue_active", DICTIONNAIRE_LANGUES.actif))

    def ordonner_layout(self, is_mobile):
        if is_mobile == self.mode_mobile: return
        self.mode_mobile = is_mobile
        for w in [self.lbl_defunt, self.entree_nom] + list(self.labels.values()) + list(self.entries.values()): w.grid_forget()

        if is_mobile:
            self.lbl_defunt.grid(row=0, column=0, sticky="w")
            self.entree_nom.grid(row=1, column=0, sticky="ew")
            for i, k in enumerate(self.cles_caps):
                self.labels[k].grid(row=(i+1)*2, column=0, sticky="w")
                self.entries[k].grid(row=(i+1)*2+1, column=0, sticky="ew")
            for i, c in enumerate(self.famille):
                self.labels[c].grid(row=i, column=0, sticky="w")
                self.entries[c].grid(row=i, column=1, sticky="w", padx=5)
        else:
            self.lbl_defunt.grid(row=0, column=0, sticky="w"); self.entree_nom.grid(row=0, column=1, padx=2)
            for i, k in enumerate(self.cles_caps):
                self.labels[k].grid(row=0, column=2+i*2, sticky="w")
                self.entries[k].grid(row=0, column=2+i*2+1, padx=2)
            for i, c in enumerate(self.famille):
                r, col = divmod(i, 4)
                self.labels[c].grid(row=r, column=col*2, sticky="w", pady=1)
                self.entries[c].grid(row=r, column=col*2+1, sticky="w", padx=4)

    def action_langue(self, dic):
        if self.winfo_exists(): self.traduire(dic)

    def traduire(self, dic):
        h, p = dic.get("heritage", {}), dic.get("pdf", {})
        
        self.c_tiers.config(text=h.get("cadre_defunt", "Défunt"))
        self.lbl_defunt.config(text=h.get("genre_lbl", "Genre :"))
        
        # 🎯 RECTIFICATION : Utilisation exclusive des clés miroirs du bloc "heritage"
        self.labels["en_masse"].config(text=h.get("masse_successorale_nette", "Masse :") + " :")
        self.labels["en_creances"].config(text=h.get("creances_actives_incluses", "Créances :") + " :")
        self.labels["en_dettes"].config(text=h.get("dettes_humaines_purgées", "Dettes :") + " :")
        self.labels["en_legs"].config(text=h.get("wasiyya_retenue", "Legs :") + " :")
        
        self.c_famille.config(text=h.get("cadre_ayants_droit", "Composition"))
        self.btn_calc.config(text=h.get("btn_simuler", "Calculer"))
        self.btn_pdf.config(text=h.get("btn_imprimer_succession", "Générer PDF"))
        self.c_res.config(text=p.get("rapport_succession_titre", "Bilan"))
        
        # Traduction individuelle réactive des 21 candidats scindés
        candidats_json = h.get("candidats", {})
        for c in self.famille: 
            self.labels[c].config(text=f"{candidats_json.get(c, c)} :")

    def calculer(self):
        try:
            b = float(self.en_masse.get() or 0)
            c = float(self.en_creances.get() or 0)
            d = float(self.en_dettes.get() or 0)
            l = float(self.en_legs.get() or 0)
            dev = getattr(self.app, "devise_active", "XOF")
            doc = getattr(self.app, "madhhab_actif", "Malikite")
            
            # 🌐 Extraction unifiée du dictionnaire de langue actif (ar.json ou fr.json)
            langue_active = getattr(self.app, "langue_active", DICTIONNAIRE_LANGUES.actif)
            txt_her = langue_active.get("heritage", {})
            txt_pdf = langue_active.get("pdf", {})
            
            saisi = {comp: int(self.entries[comp].get() or 0) for comp in self.famille}
            
            # 🎯 GARDE-FOU SHARIA : Vérification stricte du non-cumul des deux conjoints scindés
            if saisi.get("epoux", 0) > 0 and saisi.get("epouse", 0) > 0:
                self.text_rapport.config(state=tk.NORMAL)
                self.text_rapport.delete("1.0", tk.END)
                self.text_rapport.insert(tk.END, txt_her.get("err_doublon", "❌ Erreur Conjoints : Présence simultanée impossible."))
                self.text_rapport.config(state=tk.DISABLED)
                return

            # Exécution de l'audit successoral
            res = self.moteur_succession.executer_audit_successoral_complet(
                False, None, doc, {"brut": b, "creances_humains": c, "dettes_humains": d, "legs": l, "arbre_saisi": saisi}
            )
            
            # 🎯 VERROU SÉCURITÉ PDF : Stockage du dictionnaire brut pour éliminer les montants à 0 sur le certificat
            self.dernier_resultat_succession = res
    
            titre_traduit = txt_her.get("rapport_succession", "RAPPORT DE SUCCESSION")
            b_outils = langue_active.get("barre_outils", {})
            ecole_traduite = b_outils.get("ecoles", {}).get(doc, doc)

            # Filtrer pour n'afficher que les exclus qui étaient vivants (Saisis > 0)
            self.lignes_exclus_mem = [
                str(ex) for ex in res.get("personnes_exclues", [])
                if saisi.get(str(ex).lower(), 0) > 0
            ]
            
            # Récupération des valeurs exactes calculées et plafonnées par le Core Engine
            m_nette = float(res.get("masse_successorale_nette", 0.0))
            wasiyya_retenue = float(res.get("wasiyya_retenue", 0.0))
            creances_inc = float(res.get("creances_actives_incluses", 0.0))
            dettes_purg = float(res.get("dettes_humaines_purgées", 0.0))

            # Extraction des variables d'instructions i18n pour la section 1 du PDF
            lbl_ms_nette = txt_her.get("masse_successorale_nette", "Masse successorale nette à distribuer")
            lbl_creances_inc = txt_her.get("creances_actives_incluses", "Créances actives incluses")
            lbl_dettes_purg = txt_her.get("dettes_humaines_purgées", "Dettes et passif purgés")
            lbl_wasiyya = txt_her.get("wasiyya_retenue", "Legs testamentaires retenus (Max 1/3)")

            # 🎯 LE COMPARTIMENT DES INTRANTS UTILISE DÉSORMAIS LES 4 CLÉS i18n STRICTES DU JSON
            self.intrants_mem = {
                lbl_ms_nette: f"{m_nette:.2f} {dev}",
                lbl_creances_inc: f"{creances_inc:.2f} {dev}",
                lbl_dettes_purg: f"-{dettes_purg:.2f} {dev}",
                lbl_wasiyya: f"{wasiyya_retenue:.2f} {dev}"
            }

            self.lignes_mem.clear()
            self.text_rapport.config(state=tk.NORMAL)
            self.text_rapport.delete("1.0", tk.END)
            
            # 🎯 HARMONISATION TEXTUELLE DE LA SECTION 1 SUR L'ÉCRAN PRINCIPAL (Widget Text)
            v = f"📜 {titre_traduit} ({ecole_traduite.upper()}) :\n"
            v += " ==================================================\n"
            v += f"   ▶ {lbl_ms_nette} : {m_nette:.2f} {dev}\n"
            v += f"   ▶ {lbl_creances_inc} : {creances_inc:.2f} {dev}\n"
            v += f"   ▶ {lbl_dettes_purg} : -{dettes_purg:.2f} {dev}\n"
            v += f"   ▶ {lbl_wasiyya} : {wasiyya_retenue:.2f} {dev}\n"
            v += " ==================================================\n\n"

            # 🎯 SECTION 2 : Ventilation des héritiers à l'écran
            ventilation = res.get("ventilation_fractions", {})
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
            if self.lignes_exclus_mem:
                v += f"\n   ▶ {txt_pdf.get('tableau_part', 'Exclus')} :\n"
                candidats_json = txt_her.get("candidats", {})
                for ex in self.lignes_exclus_mem:
                    cle_brute = str(ex).strip().split(":", 1)[0].strip().upper()
                    cle_json = cle_brute.lower().replace("-", "_")
                    v += f"     - {candidats_json.get(cle_json, cle_brute.capitalize())}\n"
                
            self.text_rapport.insert("1.0", v)
            self.text_rapport.config(state=tk.DISABLED)
        except Exception as e: 
            self.text_rapport.config(state=tk.NORMAL)
            self.text_rapport.delete("1.0", tk.END)
            self.text_rapport.insert("1.0", f"❌ : {e}")
            self.text_rapport.config(state=tk.DISABLED)

    def imprimer(self):
        if not self.lignes_mem: return
        n = self.entree_nom.get().strip() or "Tiers"
        dev = getattr(self.app, "devise_active", "XOF")
        doc = getattr(self.app, "madhhab_actif", "Malikite")
        
        langue_active = getattr(self.app, "langue_active", DICTIONNAIRE_LANGUES.actif)
        txt_her = langue_active.get("heritage", {})
        b_candidats = txt_her.get("candidats", {})

        # Extraction en temps réel des valeurs numériques de l'écran Tiers
        brut = float(self.en_masse.get().strip() or 0.0)
        creances = float(self.en_creances.get().strip() or 0.0)
        dettes = float(self.en_dettes.get().strip() or 0.0)
        legs_demande = float(self.en_legs.get().strip() or 0.0)

        # Re-compilation de la composition de l'arbre familial saisi à l'écran
        saisi = {comp: int(self.entries[comp].get() or 0) for comp in self.famille}

        # 🎯 RECTIFICATION DIRECTE : Appel flash au moteur pour instancier la variable 'res' requise par la Section 2
        res = self.moteur_succession.executer_audit_successoral_complet(
            False, None, doc, {"brut": brut, "creances_humains": creances, "dettes_humains": dettes, "legs": legs_demande, "arbre_saisi": saisi}
        )

        masse_initiale = brut + creances
        safe_mass = max(0.0, masse_initiale - dettes)
        wasiyya_retenue = min(legs_demande, safe_mass / 3.0)
        masse_nette = max(0.0, safe_mass - wasiyya_retenue)

        # Traduction forcée et étanche des 4 paramètres d'inventaire
        label_net = txt_her.get("masse_successorale_nette", "Masse successorale nette à distribuer")
        label_creances = txt_her.get("creances_actives_incluses", "Créances actives incluses")
        label_dettes = txt_her.get("dettes_humaines_purgées", "Dettes et passif purgés")
        label_legs = txt_her.get("wasiyya_retenue", "Legs testamentaires retenus (Max 1/3)")

        intrants_ordonnes_i18n = {
            label_net: f"{masse_nette:.2f} {dev}",
            label_creances: f"{creances:.2f} {dev}",
            label_dettes: f"-{dettes:.2f} {dev}",
            label_legs: f"{wasiyya_retenue:.2f} {dev}"
        }

        # 🎯 SECTION 3 VERROUILLÉE : ÉLARGISSEMENT DE L'ESPACE ENTRE HÉRITIER ET COMMENTAIRE
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

        id_t = {"nom": n, "prenom": "", "ville": "Saisie Manuelle", "pays": "Diagnostic", "telephone": "-", "personnes_exclues": lignes_exclus_traduites}
        
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
        langue_est_arabe = any('\u0600' <= char <= '\u06FF' for char in str(txt_her.get('rapport_succession', '')))
        
        lignes_pdf_fractions = []
        candidats_json = txt_her.get("candidats", {})
        ventilation = res.get("ventilation_fractions", {})
        
        if ventilation:
            for heritier, fraction in ventilation.items():
                nom_heritier_traduit = candidats_json.get(heritier.lower(), heritier.upper())
                parts_entieres = int(round(fraction * denomination_commune))
                montant_calcule = masse_nette * fraction
                
                # 🎯 RECTIFICATION RADICALE : Utilisation du séparateur symétrique ":" pour toutes les langues
                # Élimine définitivement le masquage ou l'inversion bidi de ReportLab
                label_parts = f"\u200E[{parts_entieres} : {denomination_commune}]\u200E"
                ligne_restructuree = f"{label_parts}  -  {nom_heritier_traduit}  :  {montant_calcule:.2f} {dev}"
                
                lignes_pdf_fractions.append(ligne_restructuree)
        else:
            lignes_pdf_fractions.append(txt_her.get('succession_sans_heritier', '❌ Aucun héritier éligible.'))

        generer_certificat_pdf(id_t, "HERITAGE", doc, dev, intrants_ordonnes_i18n, lignes_pdf_fractions)

    def changer_langue(self, n_lang): 
        self.traduire(getattr(self.app, "langue_active", DICTIONNAIRE_LANGUES.actif))
        
    def actualiser_contexte(self): 
        self.text_rapport.config(state=tk.NORMAL)
        self.text_rapport.delete("1.0", tk.END)
        self.text_rapport.config(state=tk.DISABLED)
        
    def actualiser_donnees_affichage(self): 
        self.actualiser_contexte()
