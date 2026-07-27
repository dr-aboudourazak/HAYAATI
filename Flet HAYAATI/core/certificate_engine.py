"""
MOTEUR DE CERTIFICATION ET CERTIFICATS PDF EXHAUSTIFS (CORE/CERTIFICATE_ENGINE.PY)
Version Flet 0.86.2 - Partie 1/2 Spécifiée : Harmonisation Arabe BiDi & Logo PNG Officiel
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

if hasattr(sys, '_MEIPASS'):
    CHEMIN_FONTS_DIR = os.path.join(sys._MEIPASS, "assets", "fonts")
else:
    CHEMIN_FONTS_DIR = os.path.join("assets", "fonts")

POL_AR = 'NotoArabic'
POL_ZH = 'NotoChinese'

def initialiser_polices_reportlab_a_la_demande():
    """Importe et enregistre les polices uniquement à l'exécution pour éviter le crash global."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    global POL_AR, POL_ZH

    FICH_AR = os.path.join(CHEMIN_FONTS_DIR, "NotoSansArabic-Regular.ttf")
    if os.path.exists(FICH_AR):
        try: pdfmetrics.registerFont(TTFont('NotoArabic', FICH_AR))
        except Exception: POL_AR = 'Helvetica'
    else: POL_AR = 'Helvetica'

    FICH_ZH = os.path.join(CHEMIN_FONTS_DIR, "NotoSansSC-Regular.ttf")
    if os.path.exists(FICH_ZH):
        try: pdfmetrics.registerFont(TTFont('NotoChinese', FICH_ZH))
        except Exception: POL_ZH = 'Helvetica'
    else: POL_ZH = 'Helvetica'

def formater_texte_arabe(t):
    """Façonne et inverse l'écriture arabe pour ReportLab."""
    try: return get_display(arabic_reshaper.reshape(str(t)))
    except Exception: return str(t)

def preparer_flux_multilingue(texte):
    """Détecte l'arabe et applique le traitement bidirectionnel (BiDi)."""
    if not texte: return ""
    texte_str = str(texte)
    if any('\u0600' <= char <= '\u06FF' for char in texte_str):
        return formater_texte_arabe(texte_str)
    return texte_str

def obtenir_police_active_flux(texte):
    """Assigne la police adéquate selon le script unicode détecté (FR, AR, ZH)."""
    texte_str = str(texte)
    if any('\u4e00' <= char <= '\u9fff' for char in texte_str): return POL_ZH
    if any('\u0600' <= char <= '\u06FF' for char in texte_str): return POL_AR
    return 'Helvetica'

def generer_certificat_pdf(identite_dict, type_module, madhhab, devise, donnees_calcul, lignes_rapport, nisab_label="Or (85g)", dossier_destination="Certificats"):
    """Assemble et compile le document d'homologation ReportLab avec isolation stricte et alignement i18n."""
    
    # Initialisation sécurisée des polices orientales
    initialiser_polices_reportlab_a_la_demande()
    
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    
    if not os.path.exists(dossier_destination): 
        os.makedirs(dossier_destination)
        
    nom_c = str(identite_dict.get("nom", "Anonyme")).strip()
    prenom_c = str(identite_dict.get("prenom", "")).strip()
    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # 🌐 Récupération sécurisée et résiliente du dictionnaire actif global
    langue_active = DICTIONNAIRE_LANGUES.actif if hasattr(DICTIONNAIRE_LANGUES, "actif") else {}
    pdf_txt = langue_active.get("pdf", {})
    txt_zk = langue_active.get("zakat", {})
    txt_her = langue_active.get("heritage", {})

    est_un_email = bool(re.match(r"[^@]+@[^@]+\.[^@]+", nom_c))
    if est_un_email:
        libelle_beneficiaire = pdf_txt.get("compte_audite", "<b>Compte Utilisateur :</b> {}")
        texte_nom_propre = nom_c
    else:
        libelle_beneficiaire = pdf_txt.get("beneficiaire", "<b>Bénéficiaire Audité :</b> {}")
        texte_nom_propre = f"{prenom_c.upper()} {nom_c.upper()}".strip() if prenom_c else nom_c.upper()

    chemin_complet = os.path.join(dossier_destination, f"Hayaati_{type_module}_{nom_c.replace('@', '_').replace('.', '_')}_{date_str}.pdf")
    id_certif = hashlib.sha256(f"{nom_c}-{prenom_c}-{type_module}-{date_str}".encode('utf-8')).hexdigest()[:16].upper()
    
    doc = SimpleDocTemplate(chemin_complet, pagesize=letter, rightMargin=35, leftMargin=35, topMargin=15, bottomMargin=20)
    elements = []

    langue_est_arabe = any('\u0600' <= char <= '\u06FF' for char in str(pdf_txt.get('fiqh_applique', '')))
    nom_police_doc = POL_AR if langue_est_arabe else obtenir_police_active_flux(texte_nom_propre)
    fiqh_traduit = langue_active.get("barre_outils", {}).get("ecoles", {}).get(madhhab, madhhab)

    s_basmala = ParagraphStyle('B', fontName=POL_AR, fontSize=12, textColor=colors.HexColor('#064e3b'), alignment=1, leading=16)
    s_salam = ParagraphStyle('Sa', fontName=POL_AR, fontSize=10, textColor=colors.HexColor('#d97706'), alignment=1, leading=14)
    s_norm = ParagraphStyle('N', fontName=nom_police_doc, fontSize=8.5, textColor=colors.HexColor('#1f2937'), leading=12)
    s_imp = ParagraphStyle('I', parent=s_norm, fontName=nom_police_doc, textColor=colors.HexColor('#064e3b'))
    s_oran = ParagraphStyle('V', fontName=POL_AR, fontSize=9, textColor=colors.HexColor('#374151'), alignment=1, leading=13)

    p_basmala_complet = Paragraph(formater_texte_arabe(" بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ — حياتي "), s_basmala)
    p_salam_complet = Paragraph(formater_texte_arabe("السَّلَامُ عَلَيْكُمْ وَرَحْمَةُ اللهِ وَبَرَكَاتُهُ"), s_salam)
    
    # ------------------------------------------------------------
    # 🎯 ACTION 1 : INSERTION EXCLUSIVE DU LOGO PNG OFFICIEL ACCRÉDITÉ
    # ------------------------------------------------------------
    chemin_logo_png = os.path.join("assets", "images", "Logo-Hayaati.png")
    if not os.path.exists(chemin_logo_png):
        chemin_logo_png = os.path.join("assets", "images", "Icone Hayaati.png")

    try:
        if os.path.exists(chemin_logo_png):
            logo_pdf = Image(chemin_logo_png, width=100, height=100)
            logo_pdf.hAlign = 'CENTER'
            elements.append(logo_pdf)
            elements.append(Spacer(1, 4))
    except Exception as e:
        print(f"[PDF LOGO ERROR] Échec insertion logo PNG : {str(e)}")

    elements.extend([p_basmala_complet, p_salam_complet, Spacer(1, 4)])
    is_live = identite_dict.get("ville") != "Saisie Manuelle"
    env_txt = pdf_txt.get("env_live", "Espace Privé SQLite Sécurisé") if is_live else pdf_txt.get("env_tiers", "Diagnostic Manuel pour Tiers")
    sess_txt = pdf_txt.get("statut_live", "Données Certifiées Personnelles") if is_live else pdf_txt.get("statut_tiers", "Évaluation Isolée à Blanc")

    # ------------------------------------------------------------
    # 🎯 FIX PRODUCTION : NETTOYAGE ET SÉCURISATION DES BALISES HTML POUR REPORTLAB
    # ------------------------------------------------------------
    
    # Petite fonction locale interne pour nettoyer les résidus de balises <b> des fichiers JSON de langues
    def nettoyer_balise_json(cle_dictionnaire, repli_texte):
        texte_brut = str(pdf_txt.get(cle_dictionnaire, repli_texte))
        # Supprime proprement les balises ouvrantes et fermantes pour éviter les doublons
        texte_propre = texte_brut.replace('<b>', '').replace('</b>', '').split(':')[0].strip()
        return preparer_flux_multilingue(texte_propre)

    # Reconstruction étanche de chaque ligne d'en-tête (ID) avec balises uniques et fermées
    tag_id = nettoyer_balise_json('id_certification', 'ID Certification')
    lbl_id = f"<b>{tag_id} :</b> {id_certif}"
    
    # Adaptation dynamique pour le bénéficiaire ou compte utilisateur audité
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

    # Injection sécurisée dans le flux ReportLab
    elements.extend([Paragraph(f"{lbl_id}<br/>{lbl_ben}<br/>{lbl_env}<br/>{lbl_coor}<br/>{lbl_meta}", s_norm), Spacer(1, 6)])

    t_s1 = pdf_txt.get("sec_1_titre_zakat", "<b>1. Données Zakat Déclarées :</b>") if type_module == "ZAKAT" else pdf_txt.get("sec_1_titre_heritage", "<b>1. Masse Patrimoniale Successorale :</b>")
    elements.extend([Paragraph(preparer_flux_multilingue(t_s1), ParagraphStyle('S1D', parent=s_imp, fontName=obtenir_police_active_flux(t_s1))), Spacer(1, 2)])

    # ------------------------------------------------------------
    # 🎯 FIX ULTIME DIRECT TABLEAU : Élimination complète des Paragraphs sur l'en-tête
    # ------------------------------------------------------------
    col_param_label = preparer_flux_multilingue(str(pdf_txt.get('col_parametre', 'Poste Budgétaire / Inventaire')).replace('<b>','').replace('</b>','').strip())
    col_val_label = preparer_flux_multilingue(str(pdf_txt.get('col_valeur', 'Montant ou Quantité')).replace('<b>','').replace('</b>','').strip())
    
    # 🎯 Injection directe des chaînes de caractères pures sans balises ni Paragraph
    t_data = [[col_param_label, col_val_label]]
    
    txt_fin_reel = langue_active.get("finances", {})

    for k, v in donnees_calcul.items():
        cle_recherche = str(k).strip().upper()
        cle_traduite = k
        dictionnaire_mappage_postes = {
            "LIQ": txt_fin_reel.get("liq_lbl", "Liquidités").replace(":", "").strip(), "NET": txt_fin_reel.get("liq_lbl", "Liquidités").replace(":", "").strip(),
            "STOC": txt_fin_reel.get("auto_lbl", "Stocks").replace(":", "").strip(), "OR_REF": txt_fin_reel.get("lbl_or_refuge", "Or Refuge").replace(":", "").strip(),
            "OR_PAR": txt_fin_reel.get("lbl_or_parures", "Or Parure").replace(":", "").strip(), "OR": txt_fin_reel.get("lbl_or_refuge", "Patrimoine Or").replace(":", "").strip(),
            "ARGENT_REF": txt_fin_reel.get("lbl_argent_refuge", "Argent Refuge").replace(":", "").strip(), "ARGENT_PAR": txt_fin_reel.get("lbl_argent_parures", "Argent Parure").replace(":", "").strip(),
            "ARG": txt_fin_reel.get("lbl_argent_refuge", "Patrimoine Argent").replace(":", "").strip(), "DETT": txt_fin_reel.get("dettes_lbl", "Dettes déduites").replace(":", "").strip(),
            "PASS": txt_fin_reel.get("dettes_lbl", "Dettes déduites").replace(":", "").strip(), "CREA": txt_fin_reel.get("creances_lbl", "Créances incluses").replace(":", "").strip(),
            "ACTI": txt_fin_reel.get("creances_lbl", "Créances incluses").replace(":", "").strip(), "AGRO": txt_fin_reel.get("lbl_grain", "Production Agricole").replace(":", "").strip(),
            "GRAI": txt_fin_reel.get("lbl_grain", "Production Agricole").replace(":", "").strip(), "BOVI": txt_fin_reel.get("lbl_bovins", "Cheptel Bovins").replace(":", "").strip(),
            "OVIN": txt_fin_reel.get("lbl_moutons", "Cheptel Ovins").replace(":", "").strip(), "MOUT": txt_fin_reel.get("lbl_moutons", "Cheptel Ovins").replace(":", "").strip(),
            "ASSI": txt_fin_reel.get("liq_lbl", "Assimilés").replace(":", "").strip()
        }
        for radical_technique, label_traduit in dictionnaire_mappage_postes.items():
            if radical_technique in cle_recherche: 
                cle_traduite = label_traduit
                break

        t_data.append([
            Paragraph(preparer_flux_multilingue(cle_traduite.upper()), ParagraphStyle('ck', parent=s_norm, fontName=obtenir_police_active_flux(cle_traduite))), 
            Paragraph(f"<b>{preparer_flux_multilingue(v)}</b>", ParagraphStyle('vk', parent=s_norm, fontName=obtenir_police_active_flux(v)))
        ])

    # Détermination de la police pour l'en-tête du tableau
    police_table_entete = POL_AR if langue_est_arabe else 'Helvetica-Bold'

    t_intrants = Table(t_data, colWidths=[270, 270])
    t_intrants.setStyle(TableStyle([
        # 🎯 FORCE LA COULEUR DE FOND VERT ISLAMIQUE
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#064e3b')), 
        
        # 🎯 FIX TECHNIQUE CRITIQUE : Force la police NotoArabic directement sur les cellules de la ligne 0
        ('FONTNAME', (0, 0), (1, 0), police_table_entete),
        ('FONTSIZE', (0, 0), (1, 0), 10),
        
        # Force la couleur blanche sur le texte brut
        ('TEXTCOLOR', (0, 0), (1, 0), colors.white), 
        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
        
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4), 
        ('TOPPADDING', (0, 0), (-1, -1), 4), 
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cbd5e1')), 
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    elements.extend([t_intrants, Spacer(1, 5)])

    t_s2 = pdf_txt.get("sec_2_titre_zakat", "<b>2. Bilan d'Éligibilité et Purification :</b>") if type_module == "ZAKAT" else pdf_txt.get("sec_2_titre_heritage", "<b>2. Répartition Légale des Parts (Fara'idh) :</b>")
    elements.extend([Paragraph(preparer_flux_multilingue(t_s2), ParagraphStyle('S2D', parent=s_imp, fontName=obtenir_police_active_flux(t_s2))), Spacer(1, 2)])

    t_res = []
    for l in lignes_rapport:
        if isinstance(l, list): 
            txt_l = " ".join([str(item) for item in l])
        else: 
            txt_l = str(l)
        if txt_l.strip() and not txt_l.startswith("==") and not txt_l.startswith(" [📜"):
            t_res.append([Paragraph(preparer_flux_multilingue(txt_l.strip()), ParagraphStyle('Rd', parent=s_norm, fontName=obtenir_police_active_flux(txt_l), textColor=colors.HexColor('#064e3b')))])

    t_resultats = Table(t_res, colWidths=[540])
    t_resultats.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1,-1), colors.HexColor('#e6f4ea')), 
        ('TEXTCOLOR', (0, 0), (-1,-1), colors.HexColor('#064e3b')), 
        ('BOTTOMPADDING', (0, 0), (-1,-1), 3), 
        ('TOPPADDING', (0, 0), (-1,-1), 3), 
        ('GRID', (0, 0), (-1,-1), 0.4, colors.HexColor('#d1fae5')), 
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    elements.extend([t_resultats, Spacer(1, 5)])

    membres_exclus = identite_dict.get("personnes_exclues", [])
    if type_module == "HERITAGE" and membres_exclus:
        t_s3 = pdf_txt.get("sec_3_titre_exclus", "<b>3. Candidats Bloqués ou Écartés de la Succession (Hajb) :</b>")
        elements.extend([Paragraph(preparer_flux_multilingue(t_s3), ParagraphStyle('S3D', parent=s_imp, fontName=obtenir_police_active_flux(t_s3))), Spacer(1, 2)])
        
        t_ex_data = []
        for ex in membres_exclus:
            texte_corps_exclus = str(pdf_txt.get("sec_3_corps_exclus", "• {} (Évincé)")).format(str(ex).replace("'", "").replace("[", "").replace("]", "").strip().upper())
            t_ex_data.append([Paragraph(preparer_flux_multilingue(texte_corps_exclus), ParagraphStyle('Exd', parent=s_norm, fontName=obtenir_police_active_flux(texte_corps_exclus), textColor=colors.HexColor('#991b1b')))])

        t_exclus = Table(t_ex_data, colWidths=[540])
        t_exclus.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1,-1), colors.HexColor('#fee2e2')), 
            ('TEXTCOLOR', (0, 0), (-1,-1), colors.HexColor('#991b1b')), 
            ('BOTTOMPADDING', (0, 0), (-1,-1), 3), 
            ('TOPPADDING', (0, 0), (-1,-1), 3), 
            ('GRID', (0, 0), (-1,-1), 0.4, colors.HexColor('#fca5a5')), 
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        elements.extend([t_exclus, Spacer(1, 5)])

    texte_sceau_global = f"{pdf_txt.get('sceau_titre', '<b>SCEAU HAYAATI v1.2</b>')}<br/>{pdf_txt.get('sceau_corps', '<i>Certifié Conforme</i>').format(type_module)}"
    t_sceau = Table([[Paragraph(preparer_flux_multilingue(texte_sceau_global), ParagraphStyle('SceauD', parent=s_norm, fontName=obtenir_police_active_flux(texte_sceau_global), alignment=1))]], colWidths=[540])
    t_sceau.setStyle(TableStyle([
        ('BOX', (0, 0), (-1,-1), 1.2, colors.HexColor('#064e3b')), 
        ('BACKGROUND', (0, 0), (-1,-1), colors.HexColor('#f9fafb')), 
        ('PADDING', (0, 0), (-1,-1), 4), 
        ('ALIGN', (0, 0), (-1,-1), 'CENTER'), 
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    elements.extend([t_sceau, Spacer(1, 4)])

    v_zk = "2 : 110 : وَأَقِيمُوا۟ ٱلصَّلَوٰةَ وَءَاتُوا۟ ٱلزَّكَوٰةَ وَمَا تُقَدِّمُوا۟ Lِأَنفُسِكُم مِّن خَيْرٍ تَجِدُوهُ عِندَ ٱللَّهِ إِنَّ ٱللَّهَ بِمَا تَعْمَلُونَ بَصِيرٌ "
    v_he = "4 : 11 : يُوصِيكُمُ اللَّهُ فِي أَوْلَادِكُمْ ۖ لِلذَّكَرِ mِثْلُ حَظِّ ٱلْأُنثَيَيْنِ ۚ فَإِن كُنَّ نِسَآءً فَوْقَ ٱثْنَتَيْنِ فَلَهُنَّ ثُلُثَا مَا تَرَكَ ۖ وَإِن كَانَتْ وَٰحِدَةً فَلَهَا ٱلنِّصْفُ ۚ... حَكِيمًا "
    elements.extend([Paragraph(formater_texte_arabe(v_zk), s_oran), Spacer(1, 2), Paragraph(formater_texte_arabe(v_he), s_oran)])

    doc.build(elements)
    
    try:
        import platform
        if os.name == 'nt': 
            os.startfile(chemin_complet)
        elif platform.system() == 'Darwin': 
            os.system(f"open {chemin_complet}")
        else:
            if not hasattr(sys, "getandroidapilevel"): 
                os.system(f"xdg-open {chemin_complet}")
    except Exception: 
        pass
        
    return chemin_complet
