"""
MOTEUR DE CERTIFICATION ET CERTIFICATS PDF EXHAUSTIFS (CORE/CERTIFICATE_ENGINE.PY)
Version ReportLab Stabilisée - Harmonisation Arabe BiDi & Déploiement APK Android
"""
from __future__ import annotations
import os
import hashlib
import re
import sys
from datetime import datetime
import arabic_reshaper
from bidi.algorithm import get_display
from gui.langues import DICTIONNAIRE_LANGUES

# 🎯 CONFIGURATION ET RÉSOLUTION DYNAMIQUE DES CHEMINS (PC & ANDROID)
if hasattr(sys, '_MEIPASS'):
    # Cas spécifique si vous compilez un jour la version PC avec PyInstaller
    CHEMIN_FONTS_DIR = os.path.join(sys._MEIPASS, "assets", "fonts")
    CHEMIN_IMAGES_DIR = os.path.join(sys._MEIPASS, "assets", "images")
else:
    # Solution universelle pour PC (développement) ET Android (APK) :
    # On récupère le dossier où se trouve certificate_engine.py (le dossier "core")
    DOSSIER_COURANT = os.path.dirname(os.path.abspath(__file__))
    
    # On remonte d'un niveau (..) pour cibler le dossier "assets" réel
    CHEMIN_FONTS_DIR = os.path.normpath(os.path.join(DOSSIER_COURANT, "..", "assets", "fonts"))
    CHEMIN_IMAGES_DIR = os.path.normpath(os.path.join(DOSSIER_COURANT, "..", "assets", "images"))

POL_AR = 'NotoArabic'
POL_ZH = 'NotoChinese'

def initialiser_polices_reportlab_a_la_demande():
    """Importe et enregistre les polices uniquement à l'exécution pour éviter le crash global."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    global POL_AR, POL_ZH

    # 🌟 Liaison stricte pointant sur le dossier d'extraction réel
    FICH_AR = os.path.normpath(os.path.join(CHEMIN_FONTS_DIR, "NotoSansArabic-Regular.ttf"))
    
    if os.path.exists(FICH_AR):
        try: 
            pdfmetrics.registerFont(TTFont('NotoArabic', FICH_AR))
            POL_AR = 'NotoArabic'
        except Exception: 
            POL_AR = 'Helvetica'
    else: 
        # Double vérification : Recherche agressive de la police dans les dossiers parents
        FICH_ALT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "fonts", "NotoSansArabic-Regular.ttf"))
        if os.path.exists(FICH_ALT):
            try:
                pdfmetrics.registerFont(TTFont('NotoArabic', FICH_ALT))
                POL_AR = 'NotoArabic'
            except Exception: 
                POL_AR = 'Helvetica'
        else:
            print(f"CRITICAL: Police introuvable aux emplacements: {FICH_AR} et {FICH_ALT}")
            POL_AR = 'Helvetica'

    FICH_ZH = os.path.normpath(os.path.join(CHEMIN_FONTS_DIR, "NotoSansSC-Regular.ttf"))
    if os.path.exists(FICH_ZH):
        try: 
            pdfmetrics.registerFont(TTFont('NotoChinese', FICH_ZH))
            POL_ZH = 'NotoChinese'
        except Exception: 
            POL_ZH = 'Helvetica'
    else: 
        POL_ZH = 'Helvetica'

def formater_texte_arabe(t):
    """Façonne et inverse l'écriture arabe pour ReportLab."""
    if not t: return ""
    try: 
        # Configuration stricte pour éviter que le texte ne s'inverse de manière incohérente
        reshaped_text = arabic_reshaper.reshape(str(t))
        return get_display(reshaped_text)
    except Exception: 
        return str(t)

def __contient_arabe(texte_str: str) -> bool:
    """Fonction utilitaire interne pour centraliser la détection des caractères arabes."""
    return any('\u0600' <= char <= '\u06FF' or '\u0750' <= char <= '\u077F' for char in texte_str)

def preparer_flux_multilingue(texte):
    """Détecte l'arabe et applique le traitement bidirectionnel (BiDi)."""
    if not texte: return ""
    texte_str = str(texte)
    if __contient_arabe(texte_str):
        return formater_texte_arabe(texte_str)
    return texte_str

def obtenir_police_active_flux(texte):
    """Assigne la police adéquate selon le script unicode détecté (FR, AR, ZH)."""
    texte_str = str(texte)
    if any('\u4e00' <= char <= '\u9fff' for char in texte_str): return POL_ZH
    if __contient_arabe(texte_str): return POL_AR
    return 'Helvetica'

def generer_certificat_pdf(identite_dict, type_module, madhhab, devise, donnees_calcul, lignes_rapport, nisab_label="Or (85g)", dossier_destination="Certificats"):
    """Assemble et compile le document d'homologation ReportLab avec isolation stricte et alignement i18n."""
    
    # Initialisation sécurisée des polices orientales avant toute construction de layout
    initialiser_polices_reportlab_a_la_demande()
    
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    
    nom_c = str(identite_dict.get("nom", "Anonyme")).strip()
    prenom_c = str(identite_dict.get("prenom", "")).strip()
    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    langue_active = DICTIONNAIRE_LANGUES.actif if hasattr(DICTIONNAIRE_LANGUES, "actif") else {}
    pdf_txt = langue_active.get("pdf", {})

    est_un_email = bool(re.match(r"[^@]+@[^@]+\.[^v]+", nom_c))
    if est_un_email:
        texte_nom_propre = nom_c
    else:
        texte_nom_propre = f"{prenom_c.upper()} {nom_c.upper()}".strip() if prenom_c else nom_c.upper()

    nom_fichier_brut = f"Hayaati_{type_module}_{nom_c.replace('@', '_').replace('.', '_')}_{date_str}.pdf"
    
    # Gestion sécurisée du stockage Android (Vérification et création de dossier)
    if hasattr(sys, "getandroidapilevel"):
        dossier_racine_android = "/storage/emulated/0/Documents"
        if not os.path.exists(dossier_racine_android):
            dossier_destination = os.path.join(os.path.expanduser("~"), "Documents")
        else:
            dossier_destination = os.path.join(dossier_racine_android, "Hayaati")
    else:
        dossier_destination = "Certificats"

    if not os.path.exists(dossier_destination): 
        try: os.makedirs(dossier_destination, exist_ok=True)
        except Exception: dossier_destination = "."
        
    chemin_complet = os.path.join(dossier_destination, nom_fichier_brut)
    id_certif = hashlib.sha256(f"{nom_c}-{prenom_c}-{type_module}-{date_str}".encode('utf-8')).hexdigest()[:16].upper()

    # doc avec marges sécurisées
    doc = SimpleDocTemplate(chemin_complet, pagesize=letter, rightMargin=35, leftMargin=35, topMargin=65, bottomMargin=35)
    elements = []

    # Espace initial préservé mais sécurisé
    elements.append(Spacer(1, 15))

    langue_est_arabe = __contient_arabe(str(pdf_txt.get('fiqh_applique', '')))
    nom_police_doc = POL_AR if langue_est_arabe else obtenir_police_active_flux(texte_nom_propre)
    fiqh_traduit = langue_active.get("barre_outils", {}).get("ecoles", {}).get(madhhab, madhhab)

    # PARTIE 2/3

    # Paramétrages de styles adaptés
    s_basmala = ParagraphStyle('B', fontName=POL_AR, fontSize=12, textColor=colors.HexColor('#064e3b'), alignment=1, leading=16)
    s_salam = ParagraphStyle('Sa', fontName=POL_AR, fontSize=10, textColor=colors.HexColor('#d97706'), alignment=1, leading=14)
    s_norm = ParagraphStyle('N', fontName=nom_police_doc, fontSize=8.5, textColor=colors.HexColor('#1f2937'), leading=14)
    s_imp = ParagraphStyle('I', parent=s_norm, fontName=nom_police_doc, textColor=colors.HexColor('#064e3b'), leading=14)
    s_oran = ParagraphStyle('V', fontName=POL_AR, fontSize=9, textColor=colors.HexColor('#374151'), alignment=1, leading=14)

    p_basmala_complet = Paragraph(formater_texte_arabe(" بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ — حياتي "), s_basmala)
    p_salam_complet = Paragraph(formater_texte_arabe("السَّلَامُ عَلَيْكُمْ وَرَحْمَةُ اللهِ وَبَرَكَاتُهُ"), s_salam)

    # 🎯 CONFIGURATION ET CHARGEMENT DU LOGO SUR ANDROID
    chemin_logo_png = os.path.normpath(os.path.join(CHEMIN_IMAGES_DIR, "Logo-Hayaati.png"))
    
    if not os.path.exists(chemin_logo_png):
        chemin_logo_png = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "assets", "images", "Logo-Hayaati.png"))

    try:
        if os.path.exists(chemin_logo_png):
            logo_pdf = Image(chemin_logo_png, width=80, height=80)
            logo_pdf.hAlign = 'CENTER'
            elements.append(logo_pdf)
            elements.append(Spacer(1, 10))
        else:
            print(f"[PDF LOGO WARNING] Image introuvable au chemin configuré : {chemin_logo_png}")
    except Exception as e:
        print(f"[PDF LOGO ERROR] Échec insertion logo PNG : {str(e)}")

    elements.extend([p_basmala_complet, p_salam_complet, Spacer(1, 10)])
    is_live = identite_dict.get("ville") != "Saisie Manuelle"
    env_txt = pdf_txt.get("env_live", "Espace Privé SQLite Sécurisé") if is_live else pdf_txt.get("env_tiers", "Diagnostic Manuel pour Tiers")
    sess_txt = pdf_txt.get("statut_live", "Données Certifiées Personnelles") if is_live else pdf_txt.get("statut_tiers", "Évaluation Isolée à Blanc")

    # ------------------------------------------------------------
    # 🎯 FIX PRODUCTION : NETTOYAGE ET SÉCURISATION DES BALISES HTML
    # ------------------------------------------------------------
    def nettoyer_balise_json(cle_dictionnaire, repli_texte):
        texte_brut = str(pdf_txt.get(cle_dictionnaire, repli_texte))
        texte_propre = texte_brut.replace('<b>', '').replace('</b>', '').split(':')[0].strip()
        return preparer_flux_multilingue(texte_propre)

    tag_id = nettoyer_balise_json('id_certification', 'ID Certification')
    lbl_id = f"<b>{tag_id} :</b> {id_certif}"
    
    if est_un_email:
        tag_ben = nettoyer_balise_json('compte_audite', 'Compte Utilisateur')
    else:
        tag_ben = nettoyer_balise_json('beneficiaire', 'Bénéficiaire Audité')
    lbl_ben = f"<b>{tag_ben} :</b> {preparer_flux_multilingue(texte_nom_propre)}"

    titre_env = nettoyer_balise_json('environnement', 'Environnement')
    titre_sess = nettoyer_balise_json('type_session', 'Type de session')
    lbl_env = f"<b>{titre_env} :</b> {preparer_flux_multilingue(env_txt)} &nbsp;|&nbsp; <b>{titre_sess} :</b> {preparer_flux_multilingue(sess_txt)}"
    
    tag_coor = nettoyer_balise_json('coordonnees', 'Coordonnées')
    lbl_coor = f"<b>{tag_coor} :</b> {preparer_flux_multilingue(identite_dict.get('telephone', '-'))} ({preparer_flux_multilingue(identite_dict.get('ville', 'Unifié'))}, {preparer_flux_multilingue(identite_dict.get('pays', 'Global'))})"
    
    titre_dt = nettoyer_balise_json('date_analyse', 'Date')
    titre_fq = nettoyer_balise_json('fiqh_applique', 'Fiqh')
    titre_dv = nettoyer_balise_json('devise_rapport', 'Devise')
    tag_nisab = preparer_flux_multilingue(str(pdf_txt.get('lbl_guide_nisab', 'Nisab')).replace('<b>','').replace('</b>','').strip())
    
    lbl_meta = f"<b>{titre_dt} :</b> {datetime.now().strftime('%d/%m/%Y %H:%M')} &nbsp;|&nbsp; <b>{titre_fq} :</b> {preparer_flux_multilingue(str(fiqh_traduit).upper())} &nbsp;|&nbsp; <b>{tag_nisab} :</b> {preparer_flux_multilingue(nisab_label)} &nbsp;|&nbsp; <b>{titre_dv} :</b> {devise}"

    # Configuration de l'alignement global du paragraphe de métadonnées pour l'arabe
    alignement_meta = 2 if langue_est_arabe else 0 # 2 = Droite, 0 = Gauche
    s_meta_block = ParagraphStyle('MetaBlock', parent=s_norm, alignment=alignement_meta, leading=14)

    # 🎯 FIX PRODUCTION UNIFIÉ : Injection isolée ligne par ligne pour étanchéifier le BiDi
    elements.append(Paragraph(lbl_id, s_meta_block))
    elements.append(Paragraph(lbl_ben, s_meta_block))
    elements.append(Paragraph(lbl_env, s_meta_block))
    elements.append(Paragraph(lbl_coor, s_meta_block))
    elements.append(Paragraph(lbl_meta, s_meta_block))
    
    elements.append(Spacer(1, 10))
    
    t_s1 = pdf_txt.get("sec_1_titre_zakat", "<b>1. Données Zakat Déclarées :</b>") if type_module == "ZAKAT" else pdf_txt.get("sec_1_titre_heritage", "<b>1. Masse Patrimoniale Successorale :</b>")
    
    t_s1_propre = t_s1.replace('<b>', '').replace('</b>', '')
    alignement_titre = 2 if langue_est_arabe else 0
    s_titre_sec = ParagraphStyle('S1D', parent=s_imp, fontName=obtenir_police_active_flux(t_s1_propre), alignment=alignement_titre, fontSize=11)
    
    elements.extend([Paragraph(preparer_flux_multilingue(t_s1_propre), s_titre_sec), Spacer(1, 4)])

    col_param_label = str(pdf_txt.get('col_parametre', 'Poste Budgétaire / Inventaire')).replace('<b>','').replace('</b>','').strip()
    col_val_label = str(pdf_txt.get('col_valeur', 'Montant ou Quantité')).replace('<b>','').replace('</b>','').strip()
    
    # Configuration structurelle du tableau d'inventaire budgétaire
    police_table_entete = POL_AR if langue_est_arabe else 'Helvetica-Bold'
    alignement_cellule = 2 if langue_est_arabe else 0

    s_entete_tab = ParagraphStyle('ET', fontName=police_table_entete, fontSize=9.5, textColor=colors.white, alignment=1, leading=12)
    s_cell_label = ParagraphStyle('CL', parent=s_norm, fontName=nom_police_doc, alignment=alignement_cellule)
    s_cell_val = ParagraphStyle('CV', parent=s_norm, fontName=nom_police_doc, alignment=alignement_cellule)

    t_data = [[
        Paragraph(preparer_flux_multilingue(col_param_label), s_entete_tab), 
        Paragraph(preparer_flux_multilingue(col_val_label), s_entete_tab)
    ]]

    txt_fin_reel = langue_active.get("finances", {})

    # PARTIE 3/3 A

    # ------------------------------------------------------------
    # 🎯 CONFIGURATION INTERNATIONALE DU DÉCOMPTE (CONNEXION COMPATIBILITÉ JSON)
    # ------------------------------------------------------------
    if type_module == "HERITAGE":
        # Extraction de l'arbre d'origine
        composition_arbre = donnees_calcul.get("arbre_saisi", donnees_calcul) if isinstance(donnees_calcul, dict) else {}
        
        # Détection alternative au premier niveau si nécessaire
        if not composition_arbre or not any(k in composition_arbre for k in ["fils", "fille", "epouse", "epoux", "pere", "mere"]):
            les_21_cles_canoniques = ["fils", "fille", "epouse", "epoux", "pere", "mere", "grand_pere", "grand_mere", "frere_germain", "soeur_germaine", "frere_consanguin", "soeur_consanguine", "frere_uterin", "soeur_uterine", "fils_frere_germain", "fils_frere_consanguin", "oncle_germain", "oncle_consanguin", "fils_oncle_germain", "fils_oncle_consanguin"]
            composition_arbre = {k: v for k, v in donnees_calcul.items() if str(k).lower() in les_21_cles_canoniques}

        if composition_arbre:
            txt_her_bloc = langue_active.get("heritage", {})
            
            # 🌟 ÉCOUTE ET TRADUCTION DYNAMIQUE DU TITRE DU RECONGLEMENT DE DECOMPTE
            t_s_decompte = txt_her_bloc.get("sec_decompte_heritiers", pdf_txt.get("sec_decompte_heritiers", "Composition Quantitative des Ayants Droit :"))
            t_s_decompte_propre = str(t_s_decompte).replace('<b>', '').replace('</b>', '').strip()
            
            s_titre_decompte = ParagraphStyle(
                'SDecompte', 
                parent=s_imp, 
                fontName=obtenir_police_active_flux(t_s_decompte_propre), 
                alignment=alignement_meta, 
                fontSize=10, 
                leading=14
            )
            elements.extend([Paragraph(preparer_flux_multilingue(t_s_decompte_propre), s_titre_decompte), Spacer(1, 4)])
            
            t_dec_data = []
            txt_her_candidats = txt_her_bloc.get("candidats", {})
            
            for lien_technique, quantite in composition_arbre.items():
                try:
                    val_str = str(quantite).replace('<b>', '').replace('</b>', '').strip()
                    qte_int = int(float(val_str)) if '.' in val_str else int(val_str)
                except Exception:
                    qte_int = 0
                    
                if qte_int > 0:
                    # Normalisation stricte vers la casse minuscule du dictionnaire d'interface
                    cle_brute = str(lien_technique).lower().strip()
                    
                    # 🎯 DICTIONNAIRE DE TRANSITION : Traduit instantanément les variables du code vers votre dictionnaire JSON réel
                    dictionnaire_passerelle_candidats = {
                        "frere_consanguin": "frere_paternel",
                        "soeur_consanguine": "soeur_paternelle",
                        "fils_frere_consanguin": "fils_frere_paternel",
                        "oncle_consanguin": "oncle_paternel",
                        "fils_oncle_germain": "cousin_germain",
                        "fils_oncle_consanguin": "cousin_paternel",
                        "soeur_uterine": "soeur_uterine"
                    }
                    
                    # Si la clé du code a un équivalent dans votre JSON, on effectue la substitution
                    cle_json_officielle = dictionnaire_passerelle_candidats.get(cle_brute, cle_brute)
                    
                    # Extraction sécurisée du dictionnaire JSON avec repli sur le nom de clé d'origine
                    label_parente = txt_her_candidats.get(cle_json_officielle, cle_brute.upper()).upper()
                    
                    # Formatage grammatical de la ligne du décompte
                    texte_quantifie = f"• {qte_int} {label_parente}(S)" if qte_int > 1 else f"• {qte_int} {label_parente}"
                        
                    s_style_dec = ParagraphStyle(
                        'DecStyle', 
                        parent=s_norm, 
                        fontName=obtenir_police_active_flux(texte_quantifie), 
                        textColor=colors.HexColor('#064e3b'), 
                        alignment=alignement_meta, 
                        leading=12
                    )
                    t_dec_data.append([Paragraph(preparer_flux_multilingue(texte_quantifie), s_style_dec)])

            # Tracé du conteneur géométrique ReportLab
            if t_dec_data:
                t_decompte_table = Table(t_dec_data, colWidths=[530])
                t_decompte_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1,-1), colors.HexColor('#f0fdf4')), 
                    ('BOTTOMPADDING', (0, 0), (-1,-1), 4), 
                    ('TOPPADDING', (0, 0), (-1,-1), 4), 
                    ('LEFTPADDING', (0, 0), (-1,-1), 10),
                    ('RIGHTPADDING', (0, 0), (-1,-1), 10),
                    ('GRID', (0, 0), (-1,-1), 0.4, colors.HexColor('#bbf7d0')), 
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
                ]))
                elements.extend([t_decompte_table, Spacer(1, 12)])

    # ------------------------------------------------------------
    # 🎯 RECUPERATION ET TRACÉ DE VOTRE GRAND TABLEAU D'INVENTAIRE
    # ------------------------------------------------------------
    for k, v in donnees_calcul.items():
        cle_recherche = str(k).strip().upper()

        # 🌟 CORRECTIF DIRECT : On ignore absolument la clé technique de l'arbre 
        # pour empêcher son affichage brut à la fin du tableau financier de la Section 1
        if cle_recherche == "ARBRE_SAISI":
            continue        

        cle_traduite = k
        # 🎯 FIX PRODUCTION COMPLET : Extraction i18n étanche pour vos 12 langues
        # Le PDF va chercher la clé de stock dans le fichier JSON de la langue active.
        # Si le JSON de la langue africaine ou européenne ne l'a pas encore, il prend le titre du rapport.
        traduction_stock_dynamique = txt_fin_reel.get("stock_lbl", pdf_txt.get("rapport_titre", "STOCKS"))
        
        dictionnaire_mappage_postes = {
            "LIQ": txt_fin_reel.get("liq_lbl", "Liquidités").replace(":", "").strip(), 
            "NET": txt_fin_reel.get("liq_lbl", "Liquidités").replace(":", "").strip(),
            "STOC": str(traduction_stock_dynamique).replace(":", "").strip(), # 🌟 BRANCHEMENT UNIVERSEL DIRECT
            "OR_REF": txt_fin_reel.get("lbl_or_refuge", "Or Refuge").replace(":", "").strip(),
            "OR_PAR": txt_fin_reel.get("lbl_or_parures", "Or Parure").replace(":", "").strip(), 
            "OR": txt_fin_reel.get("lbl_or_refuge", "Patrimoine Or").replace(":", "").strip(),
            "ARGENT_REF": txt_fin_reel.get("lbl_argent_refuge", "Argent Refuge").replace(":", "").strip(), 
            "ARGENT_PAR": txt_fin_reel.get("lbl_argent_parures", "Argent Parure").replace(":", "").strip(),
            "ARG": txt_fin_reel.get("lbl_argent_refuge", "Patrimoine Argent").replace(":", "").strip(), 
            "DETT": txt_fin_reel.get("dettes_lbl", "Dettes").replace(":", "").strip(),
            "PASS": txt_fin_reel.get("dettes_lbl", "Dettes").replace(":", "").strip(), 
            "CREA": txt_fin_reel.get("creances_lbl", "Créances").replace(":", "").strip(),
            "ACTI": txt_fin_reel.get("creances_lbl", "Créances").replace(":", "").strip(), 
            "AGRO": txt_fin_reel.get("lbl_grain", "Production Agricole").replace(":", "").strip(),
            "GRAI": txt_fin_reel.get("lbl_grain", "Production Agricole").replace(":", "").strip(), 
            "BOVI": txt_fin_reel.get("lbl_bovins", "Cheptel Bovins").replace(":", "").strip(),
            "OVIN": txt_fin_reel.get("lbl_moutons", "Cheptel Ovins").replace(":", "").strip(), 
            "MOUT": txt_fin_reel.get("lbl_moutons", "Cheptel Ovins").replace(":", "").strip(),
            "ASSI": txt_fin_reel.get("liq_lbl", "Assimilés").replace(":", "").strip()
        }

        for radical_technique, label_traduit in dictionnaire_mappage_postes.items():
            if radical_technique in cle_recherche: 
                cle_traduite = label_traduit
                break

        v_propre = str(v).replace('<b>', '').replace('</b>', '')
        
        if langue_est_arabe:
            t_data.append([
                Paragraph(preparer_flux_multilingue(v_propre), s_cell_val),
                Paragraph(preparer_flux_multilingue(cle_traduite.upper()), s_cell_label)
            ])
        else:
            t_data.append([
                Paragraph(preparer_flux_multilingue(cle_traduite.upper()), s_cell_label), 
                Paragraph(preparer_flux_multilingue(v_propre), s_cell_val)
            ])

    # 🎯 FIX LINE 361 : Rétablissement de la dimension symétrique d'origine
    t_intrants = Table(t_data, colWidths=[265, 265])
    align_entete = 'RIGHT' if langue_est_arabe else 'LEFT'
    
    t_intrants.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#064e3b')), 
        ('ALIGN', (0, 0), (-1, 0), align_entete),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4), 
        ('TOPPADDING', (0, 0), (-1, -1), 4), 
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cbd5e1')), 
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    elements.extend([t_intrants, Spacer(1, 10)])

    # PARTIE 3/3 B

    # ------------------------------------------------------------
    # 🎯 RENDER DE LA SECTION 2 : CONCLUSIONS DOCTRINALES ET FRACTIONS INTACTES
    # ------------------------------------------------------------
    t_s2 = pdf_txt.get("sec_2_titre_zakat", "2. Bilan d'Éligibilité et Purification :") if type_module == "ZAKAT" else pdf_txt.get("sec_2_titre_heritage", "2. Répartition Légale des Parts (Fara'idh) :")
    t_s2_propre = str(t_s2).replace('<b>', '').replace('</b>', '')
    
    alignement_titre2 = 2 if langue_est_arabe else 0
    s_titre_sec2 = ParagraphStyle('S2D', parent=s_imp, fontName=obtenir_police_active_flux(t_s2_propre), alignment=alignement_titre2, fontSize=11)
    elements.extend([Paragraph(preparer_flux_multilingue(t_s2_propre), s_titre_sec2), Spacer(1, 4)])

    t_res = []
    for l in lignes_rapport:
        txt_l = " ".join([str(item) for item in l]) if isinstance(l, list) else str(l)
        txt_l_propre = txt_l.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '')
        
        if txt_l_propre.strip() and not txt_l_propre.startswith("==") and not txt_l_propre.startswith(" [📜"):
            alignement_ligne = 2 if langue_est_arabe else 0
            s_style_ligne = ParagraphStyle('Rd', parent=s_norm, fontName=obtenir_police_active_flux(txt_l_propre), textColor=colors.HexColor('#064e3b'), alignment=alignement_ligne)
            t_res.append([Paragraph(preparer_flux_multilingue(txt_l_propre.strip()), s_style_ligne)])

    t_resultats = Table(t_res, colWidths=[530])
    t_resultats.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1,-1), colors.HexColor('#e6f4ea')), 
        ('BOTTOMPADDING', (0, 0), (-1,-1), 3.5), 
        ('TOPPADDING', (0, 0), (-1,-1), 3.5), 
        ('GRID', (0, 0), (-1,-1), 0.4, colors.HexColor('#d1fae5')), 
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    elements.extend([t_resultats, Spacer(1, 10)])

    # ------------------------------------------------------------
    # 🎯 MANAGEMENT DE LA SECTION 3 : CANDIDATS EXCLUS (HAJB)
    # ------------------------------------------------------------
    membres_exclus = identite_dict.get("personnes_exclues", [])
    if type_module == "HERITAGE" and membres_exclus:
        t_s3 = pdf_txt.get("sec_3_titre_exclus", "3. Candidats Bloqués ou Écartés de la Succession (Hajb) :")
        t_s3_propre = str(t_s3).replace('<b>', '').replace('</b>', '')
        s_titre_sec3 = ParagraphStyle('S3D', parent=s_imp, fontName=obtenir_police_active_flux(t_s3_propre), alignment=alignement_titre2, fontSize=11)
        elements.extend([Paragraph(preparer_flux_multilingue(t_s3_propre), s_titre_sec3), Spacer(1, 4)])
        
        t_ex_data = []
        for ex in membres_exclus:
            texte_corps_exclus = str(pdf_txt.get("sec_3_corps_exclus", "• {} (Évincé)")).format(str(ex).replace("'", "").replace("[", "").replace("]", "").strip().upper())
            texte_ex_propre = texte_corps_exclus.replace('<b>', '').replace('</b>', '')
            alignement_exclus = 2 if langue_est_arabe else 0
            s_style_exclus = ParagraphStyle('Exd', parent=s_norm, fontName=obtenir_police_active_flux(texte_ex_propre), textColor=colors.HexColor('#991b1b'), alignment=alignement_exclus)
            t_ex_data.append([Paragraph(preparer_flux_multilingue(texte_ex_propre), s_style_exclus)])

        t_exclus = Table(t_ex_data, colWidths=[530])
        t_exclus.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1,-1), colors.HexColor('#fee2e2')), 
            ('BOTTOMPADDING', (0, 0), (-1,-1), 3.5), 
            ('TOPPADDING', (0, 0), (-1,-1), 3.5), 
            ('GRID', (0, 0), (-1,-1), 0.4, colors.HexColor('#fca5a5')), 
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        elements.extend([t_exclus, Spacer(1, 10)])

    # ------------------------------------------------------------
    # 🎯 COUPLAGE DU SCEAU OFFICIEL ET AVERTISSEMENT DOCTRINAL DE SÉCURITÉ
    # ------------------------------------------------------------
    sceau_titre_clean = str(pdf_txt.get('sceau_titre', 'SCEAU HAYAATI v1.2')).replace('<b>', '').replace('</b>', '')
    sceau_corps_clean = str(pdf_txt.get('sceau_corps', 'Certifié Conforme')).replace('<i>', '').replace('</i>', '').format(type_module)
    
    # 🌟 EXTRACTION DE L'AVERTISSEMENT DE SUPERVISION DEPUIS LE JSON (Avec repli si absent)
    # Exemple de texte : "⚠️ Hayaati est un outil d'aide au calcul puissant. Il nécessite la supervision d'un savant qualifié."
    txt_her_bloc = langue_active.get("heritage", {})
    avertissement_savant = txt_her_bloc.get("alerte_supervision_savant", pdf_txt.get("alerte_supervision_savant", "⚠️ Application de calcul. Requiert la supervision d'un savant qualifié."))
    
    titre_traite = preparer_flux_multilingue(sceau_titre_clean)
    corps_traite = preparer_flux_multilingue(sceau_corps_clean)
    avertissement_traite = preparer_flux_multilingue(avertissement_savant)
    
    # Injection de l'avertissement dans le Paragraph en petits caractères italiques (fontSize=7, leading=10)
    texte_sceau_global = f"{titre_traite}<br/>{corps_traite}<br/><br/><font size=7 color='#b91c1c'><i>{avertissement_traite}</i></font>"
    police_sceau = POL_AR if langue_est_arabe else obtenir_police_active_flux(texte_sceau_global)
    
    # 🎯 CONFIGURATION HAUTEUR : leading=11 (au lieu de 14) réduit légèrement la hauteur de ligne 
    # sans toucher aux Spacers ni risquer de chevauchement. Cela fait remonter la ligne qui débordait !
    style_sceau_compact = ParagraphStyle(
        'SceauD', 
        parent=s_norm, 
        fontName=police_sceau, 
        alignment=1, 
        fontSize=9.5, 
        leading=11
    )
    
    t_SCEAU = Table([[Paragraph(texte_sceau_global, style_sceau_compact)]], colWidths=[530])
    t_SCEAU.setStyle(TableStyle([
        ('BOX', (0, 0), (-1,-1), 1.2, colors.HexColor('#064e3b')), 
        ('BACKGROUND', (0, 0), (-1,-1), colors.HexColor('#f9fafb')), 
        ('PADDING', (0, 0), (-1,-1), 6), 
        ('ALIGN', (0, 0), (-1,-1), 'CENTER'), 
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    elements.extend([t_SCEAU, Spacer(1, 10)])

    # 🎯 INTERPRÉTATION SÉCURISÉE DES VERSETS CORANIQUES
    v_zk_texte = "وَأَقِيمُوا۟ ٱلصَّلَوٰةَ وَءَاتُوا۟ ٱلزَّكَوٰةَ وَمَا تُقَدِّمُوا۟ لِأَنفُسِكُم مِّنْ خَيْرٍ تَجِدُوهُ عِندَ ٱللَّهِ إِنَّ ٱللَّهَ بِمَا تَعْمَلُونَ بَصِيرٌ "
    v_he_texte = "يُوصِيكُمُ اللَّهُ فِي أَوْلَادِكُمْ ۖ لِلذَّكَرِ مِثْلُ حَظِّ ٱلْأُنثَيَيْنِ ۚ فَإِن كُنَّ نِسَآءً فَوْقَ ٱثْنَتَيْنِ فَلَهُنَّ ثُلُثَا مَا تَرَكَ ۖ وَإِن كَانَتْ وَٰحِدَةً فَلَهَا ٱلنِّصْفُ ۚ... حَكِيمًا "
    
    v_zk_final = f"110 : 2 — {formater_texte_arabe(v_zk_texte)}"
    v_he_final = f"11 : 4 — {formater_texte_arabe(v_he_texte)}"
    
    # 🎯 CONFIGURATION INTERLIGNE COMPACTE : passage du leading par défaut à 12 
    # Cela resserre subtilement les deux versets et les fait remonter immédiatement sur la page 1
    s_oran_fix = ParagraphStyle('OranF', parent=s_oran, alignment=2, leading=12)
    elements.extend([Paragraph(v_zk_final, s_oran_fix), Spacer(1, 4), Paragraph(v_he_final, s_oran_fix)])

    doc.build(elements)
    
    # 🎯 LOGIQUE DE PARTAGE AUTOMATIQUE ANDROID SUR FLET
    try:
        import platform
        if os.name == 'nt': 
            os.startfile(chemin_complet)
        elif platform.system() == 'Darwin': 
            os.system(f"open {chemin_complet}")
        else:
            if hasattr(sys, "getandroidapilevel") or platform.system() == 'Linux':
                import main
                if hasattr(main, 'APPLICATION_HAYAATI_INSTANCE') and main.APPLICATION_HAYAATI_INSTANCE and main.APPLICATION_HAYAATI_INSTANCE.page:
                    p = main.APPLICATION_HAYAATI_INSTANCE.page
                    p.share_file(chemin_complet)
                else:
                    os.system(f"xdg-open {chemin_complet}")
            else:
                if not hasattr(sys, "getandroidapilevel"): 
                    os.system(f"xdg-open {chemin_complet}")
    except Exception as err: 
        print(f"[PDF SYSTEM CRITICAL] Canal de traitement Android indisponible : {str(err)}")
        
    return chemin_complet
