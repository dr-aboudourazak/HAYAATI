"""
MOTEUR DE CERTIFICATION ET CERTIFICATS PDF EXHAUSTIFS
Version 12.0 - Alignement à gauche, éradication des Tofus et métadonnées sécurisées.
"""
import os, hashlib, re
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Circle, Group, String
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display
from gui.langues import DICTIONNAIRE_LANGUES

# 🎯 ENREGISTREMENT ET SÉCURISATION DES POLICES DE SECOURS UNICODE CHINOISE ET ARABE
CHEMIN_FONTS_DIR = os.path.join(os.getcwd(), "fonts")
POL_AR = 'NotoArabic'
POL_ZH = 'NotoChinese'

# Enregistrement de la police Arabe locale
FICH_AR = os.path.join(CHEMIN_FONTS_DIR, "NotoSansArabic-Regular.ttf")
if os.path.exists(FICH_AR):
    try: pdfmetrics.registerFont(TTFont('NotoArabic', FICH_AR))
    except Exception: POL_AR = 'Helvetica'
else:
    POL_AR = 'Helvetica'

# Enregistrement de la police Chinoise locale
FICH_ZH = os.path.join(CHEMIN_FONTS_DIR, "NotoSansSC-Regular.ttf")
if os.path.exists(FICH_ZH):
    try: pdfmetrics.registerFont(TTFont('NotoChinese', FICH_ZH))
    except Exception: POL_ZH = 'Helvetica'
else:
    POL_ZH = 'Helvetica'

def formater_texte_arabe(t):
    try: return get_display(arabic_reshaper.reshape(t))
    except Exception: return t

def preparer_flux_multilingue(texte):
    if not texte: return ""
    texte_str = str(texte)
    if any('\u0600' <= char <= '\u06FF' for char in texte_str):
        return formater_texte_arabe(texte_str)
    return texte_str

def obtenir_police_active_flux(texte):
    texte_str = str(texte)
    if any('\u4e00' <= char <= '\u9fff' for char in texte_str):
        return POL_ZH
    if any('\u0600' <= char <= '\u06FF' for char in texte_str):
        return POL_AR
    return 'Helvetica'

def creer_logo_double_couronne_hayaati():
    d = Drawing(80, 68); g = Group()
    c_ext = Circle(40, 34, 32); c_ext.fillColor, c_ext.strokeColor, c_ext.strokeWidth = colors.HexColor('#064e3b'), colors.HexColor('#d97706'), 2; g.add(c_ext)
    c_int = Circle(40, 34, 28); c_int.fillColor, c_int.strokeColor, c_int.strokeWidth = colors.HexColor('#064e3b'), colors.HexColor('#f59e0b'), 1.2; g.add(c_int)
    txt = String(33, 22, formater_texte_arabe("ح"), fontName=POL_AR, fontSize=34); txt.fillColor = colors.HexColor('#fef08a'); g.add(txt); d.add(g)
    return d

def generer_certificat_pdf(identite_dict, type_module, madhhab, devise, donnees_calcul, lignes_rapport, nisab_label="Or (85g)", dossier_destination="Certificats"):
    if not os.path.exists(dossier_destination): os.makedirs(dossier_destination)
    nom_c, prenom_c, date_str = str(identite_dict.get("nom", "Anonyme")).strip(), str(identite_dict.get("prenom", "")).strip(), datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # 🌐 COUPLAGE i18n DIRECT : Lecture du dictionnaire actif global de la session utilisateur
    langue_active = getattr(DICTIONNAIRE_LANGUES, "actif", {})
    pdf_txt = langue_active.get("pdf", {})
    txt_zk = langue_active.get("zakat", {})
    txt_her = langue_active.get("heritage", {})
    txt_fin = langue_active.get("patrimoine", {})

    est_un_email = bool(re.match(r"[^@]+@[^@]+\.[^@]+", nom_c))
    if est_un_email:
        libelle_beneficiaire = pdf_txt.get("compte_audite", "<b>Compte Utilisateur :</b> {}")
        texte_nom_propre = nom_c
    else:
        libelle_beneficiaire = pdf_txt.get("beneficiaire", "<b>Bénéficiaire Audité :</b> {}")
        texte_nom_propre = f"{prenom_c.upper()} {nom_c.upper()}".strip() if prenom_c else nom_c.upper()

    chemin_complet = os.path.join(dossier_destination, f"Hayaati_{type_module}_{nom_c.replace('@', '_').replace('.', '_')}_{date_str}.pdf")
    id_certif = hashlib.sha256(f"{nom_c}-{prenom_c}-{type_module}-{date_str}".encode('utf-8')).hexdigest()[:16].upper()
    doc = SimpleDocTemplate(chemin_complet, pagesize=letter, rightMargin=35, leftMargin=35, topMargin=15, bottomMargin=20); elements = []

    # 🎯 FORCE UNICODE SUR EN-TÊTE : Activation automatique de NotoArabic si la langue active est l'arabe
    langue_est_arabe = any('\u0600' <= char <= '\u06FF' for char in str(pdf_txt.get('fiqh_applique', '')))
    nom_police_doc = POL_AR if langue_est_arabe else obtenir_police_active_flux(texte_nom_propre)
    fiqh_traduit = langue_active.get("barre_outils", {}).get("ecoles", {}).get(madhhab, madhhab)

    s_titre = ParagraphStyle('Ti', fontName='Helvetica-Bold', fontSize=20, textColor=colors.HexColor('#064e3b'), alignment=1, leading=24)
    s_basmala = ParagraphStyle('B', fontName=POL_AR, fontSize=12, textColor=colors.HexColor('#064e3b'), alignment=1, leading=16)
    s_salam = ParagraphStyle('Sa', fontName=POL_AR, fontSize=10, textColor=colors.HexColor('#d97706'), alignment=1, leading=14)
    
    s_norm = ParagraphStyle('N', fontName=nom_police_doc, fontSize=8.5, textColor=colors.HexColor('#1f2937'), leading=12)
    s_imp = ParagraphStyle('I', parent=s_norm, fontName=nom_police_doc, textColor=colors.HexColor('#064e3b'))
    s_coran = ParagraphStyle('V', fontName=POL_AR, fontSize=9, textColor=colors.HexColor('#374151'), alignment=1, leading=13)

    p_titre_fr = Paragraph("H A Y A A T I", s_titre)
    p_basmala_complet = Paragraph(formater_texte_arabe(" بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ — حياتي "), s_basmala)
    p_salam_complet = Paragraph(formater_texte_arabe("السَّلَامُ عَلَيْكُمْ وَرَحْمَةُ اللهِ وَبَرَكَاتُهُ"), s_salam)
    donnees_entete = [[creer_logo_double_couronne_hayaati()], [p_titre_fr], [p_basmala_complet], [p_salam_complet]]
    
    t_entete = Table(donnees_entete, colWidths=[540])
    t_entete.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('BOTTOMPADDING', (0,0), (-1,-1), 1), ('TOPPADDING', (0,0), (-1,-1), 1)]))
    elements.extend([t_entete, Spacer(1, 4)])

    # 🎯 SÉCURISATION DU PAVÉ : Nettoyage des balises pour empêcher la disparition des variables
    is_live = identite_dict.get("ville") != "Saisie Manuelle"
    env_txt = pdf_txt.get("env_live", "Espace Privé SQLite Sécurisé") if is_live else pdf_txt.get("env_tiers", "Diagnostic Manuel pour Tiers")
    sess_txt = pdf_txt.get("statut_live", "Données Certifiées Personnelles") if is_live else pdf_txt.get("statut_tiers", "Évaluation Isolée à Blanc")

    lbl_id = pdf_txt.get('id_certification', '<b>ID Certification :</b> {}').format(id_certif)
    lbl_ben = libelle_beneficiaire.format(preparer_flux_multilingue(texte_nom_propre))
    
    # Extraction propre des titres pour éviter les conflits d'imbrication HTML
    titre_env = pdf_txt.get('environnement', '<b>Environnement :</b> {}').split(':')[0].replace('<b>','').replace('</b>','').strip()
    titre_sess = pdf_txt.get('type_session', '<b>Session :</b> {}').split(':')[0].replace('<b>','').replace('</b>','').strip()
    lbl_env = f"<b>{titre_env} :</b> {preparer_flux_multilingue(env_txt)} &nbsp;|&nbsp; <b>{titre_sess} :</b> {preparer_flux_multilingue(sess_txt)}"
    
    lbl_coor_titre = pdf_txt.get('coordonnees', '<b>Coordonnées :</b> {} ({}, {})')
    if "{}" not in str(lbl_coor_titre): lbl_coor_titre = "<b>Coordonnées :</b> {} ({}, {})"
    lbl_coor = lbl_coor_titre.format(preparer_flux_multilingue(identite_dict.get('telephone', '-')), preparer_flux_multilingue(identite_dict.get('ville', 'Unifié')), preparer_flux_multilingue(identite_dict.get('pays', 'Global')))
    
    titre_dt = pdf_txt.get('date_analyse', '<b>Date :</b> {}').split(':')[0].replace('<b>','').replace('</b>','').strip()
    titre_fq = pdf_txt.get('fiqh_applique', '<b>Fiqh :</b> {}').split(':')[0].replace('<b>','').replace('</b>','').strip()
    titre_dv = pdf_txt.get('devise_rapport', '<b>Devise :</b> {}').split(':')[0].replace('<b>','').replace('</b>','').strip()
    
    txt_dt = f"<b>{titre_dt} :</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    txt_fq = f"<b>{titre_fq} :</b> {preparer_flux_multilingue(fiqh_traduit.upper())}"
    txt_ns = f"<b>{pdf_txt.get('lbl_guide_nisab', 'Nisab')} :</b> {preparer_flux_multilingue(nisab_label)}"
    txt_dv = f"<b>{titre_dv} :</b> {devise}"
    lbl_meta = f"{txt_dt} &nbsp;|&nbsp; {txt_fq} &nbsp;|&nbsp; {txt_ns} &nbsp;|&nbsp; {txt_dv}"

    info_texte = f"{lbl_id}<br/>{lbl_ben}<br/>{lbl_env}<br/>{lbl_coor}<br/>{lbl_meta}"
    elements.extend([Paragraph(info_texte, s_norm), Spacer(1, 6)])

    # --- SECTION 1 : ADAPTATION STRICTE DU MOTEUR PDF À L'EXISTANT JSON ---
    t_s1 = pdf_txt.get("sec_1_titre_zakat", "<b>1. Données Zakat Déclarées :</b>") if type_module == "ZAKAT" else pdf_txt.get("sec_1_titre_heritage", "<b>1. Masse Patrimoniale Successorale :</b>")
    pol_s1 = obtenir_police_active_flux(t_s1)
    s_s1_dynamique = ParagraphStyle('S1D', parent=s_imp, fontName=pol_s1)
    elements.extend([Paragraph(preparer_flux_multilingue(t_s1), s_s1_dynamique), Spacer(1, 2)])

    t_data = [[Paragraph(f"<b>{pdf_txt.get('col_parametre', 'Poste Budgétaire / Inventaire')}</b>", s_norm), Paragraph(f"<b>{pdf_txt.get('col_valeur', 'Montant ou Quantité')}</b>", s_norm)]]
    
    # Récupération du vrai bloc de traduction existant
    txt_fin_reel = langue_active.get("finances", {})

    for k, v in donnees_calcul.items():
        cle_recherche = str(k).strip().upper()
        cle_traduite = k  # Repli par défaut
        
        # 🎯 LE MOTEUR S'ADAPTE : Extraction et nettoyage des deux points ":" de vos libellés existants
        dictionnaire_mappage_postes = {
            "LIQ": txt_fin_reel.get("liq_lbl", "Liquidités").replace(":", "").strip(),
            "NET": txt_fin_reel.get("liq_lbl", "Liquidités").replace(":", "").strip(),
            "STOC": txt_fin_reel.get("auto_lbl", "Stocks").replace(":", "").strip(),
            "OR_REF": txt_fin_reel.get("lbl_or_refuge", "Or Refuge").replace(":", "").strip(),
            "OR_PAR": txt_fin_reel.get("lbl_or_parures", "Or Parure").replace(":", "").strip(),
            "OR": txt_fin_reel.get("lbl_or_refuge", "Patrimoine Or").replace(":", "").strip(),
            "ARGENT_REF": txt_fin_reel.get("lbl_argent_refuge", "Argent Refuge").replace(":", "").strip(),
            "ARGENT_PAR": txt_fin_reel.get("lbl_argent_parures", "Argent Parure").replace(":", "").strip(),
            "ARG": txt_fin_reel.get("lbl_argent_refuge", "Patrimoine Argent").replace(":", "").strip(),
            "DETT": txt_fin_reel.get("dettes_lbl", "Dettes déduites").replace(":", "").strip(),
            "PASS": txt_fin_reel.get("dettes_lbl", "Dettes déduites").replace(":", "").strip(),
            "CREA": txt_fin_reel.get("creances_lbl", "Créances incluses").replace(":", "").strip(),
            "ACTI": txt_fin_reel.get("creances_lbl", "Créances incluses").replace(":", "").strip(),
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

        pol_cle = obtenir_police_active_flux(cle_traduite)
        pol_val = obtenir_police_active_flux(v)
        s_cle = ParagraphStyle('ck', parent=s_norm, fontName=pol_cle)
        s_val = ParagraphStyle('vk', parent=s_norm, fontName=pol_val)
        
        t_data.append([
            Paragraph(preparer_flux_multilingue(cle_traduite.upper()), s_cle), 
            Paragraph(f"<b>{preparer_flux_multilingue(v)}</b>", s_val)
        ])

    t_intrants = Table(t_data, colWidths=[270, 270])
    t_intrants.setStyle(TableStyle([('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#f3f4f6')), ('TEXTCOLOR', (0, 0), (1, 0), colors.HexColor('#374151')), ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5), ('TOPPADDING', (0, 0), (-1, -1), 1.5), ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#e5e7eb')), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
    elements.extend([t_intrants, Spacer(1, 5)])

    # --- SECTION 2 : VERDICT / FARA'IDH ---
    t_s2 = pdf_txt.get("sec_2_titre_zakat", "<b>2. Bilan d'Éligibilité et Purification :</b>") if type_module == "ZAKAT" else pdf_txt.get("sec_2_titre_heritage", "<b>2. Répartition Légale des Parts (Fara'idh) :</b>")
    pol_s2 = obtenir_police_active_flux(t_s2)
    s_s2_dynamique = ParagraphStyle('S2D', parent=s_imp, fontName=pol_s2)
    elements.extend([Paragraph(preparer_flux_multilingue(t_s2), s_s2_dynamique), Spacer(1, 2)])

    t_res = []
    for l in lignes_rapport:
        txt_l = " ".join(l) if isinstance(l, list) else str(l)
        if txt_l.strip() and not txt_l.startswith("==") and not txt_l.startswith(" [📜"):
            pol_ligne = obtenir_police_active_flux(txt_l)
            s_res_dynamique = ParagraphStyle('Rd', parent=s_norm, fontName=pol_ligne, textColor=colors.HexColor('#064e3b'))
            t_res.append([Paragraph(preparer_flux_multilingue(txt_l.strip()), s_res_dynamique)])

    t_resultats = Table(t_res, colWidths=[540])
    t_resultats.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1,-1), colors.HexColor('#e6f4ea')), ('TEXTCOLOR', (0, 0), (-1,-1), colors.HexColor('#064e3b')), ('BOTTOMPADDING', (0, 0), (-1,-1), 3), ('TOPPADDING', (0, 0), (-1,-1), 3), ('GRID', (0, 0), (-1,-1), 0.4, colors.HexColor('#d1fae5')), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
    elements.extend([t_resultats, Spacer(1, 5)])

    # --- SECTION 3 : HAJB / EXCLUSIONS ---
    membres_exclus = identite_dict.get("personnes_exclues", [])
    if type_module == "HERITAGE" and membres_exclus:
        t_s3 = pdf_txt.get("sec_3_titre_exclus", "<b>3. Candidats Bloqués ou Écartés de la Succession (Hajb) :</b>")
        pol_s3 = obtenir_police_active_flux(t_s3)
        s_s3_dynamique = ParagraphStyle('S3D', parent=s_imp, fontName=pol_s3)
        elements.extend([Paragraph(preparer_flux_multilingue(t_s3), s_s3_dynamique), Spacer(1, 2)])
        
        t_ex_data = []
        for ex in membres_exclus:
            txt_p = str(ex).replace("'", "").replace("[", "").replace("]", "").strip()
            c_ex = pdf_txt.get("sec_3_corps_exclus", "• {} (Évincé de la ventilation conformément aux règles de priorité du Fiqh)")
            texte_corps_exclus = c_ex.format(txt_p.upper())
            pol_ex = obtenir_police_active_flux(texte_corps_exclus)
            s_ex_dynamique = ParagraphStyle('Exd', parent=s_norm, fontName=pol_ex, textColor=colors.HexColor('#991b1b'))
            t_ex_data.append([Paragraph(preparer_flux_multilingue(texte_corps_exclus), s_ex_dynamique)])

        t_exclus = Table(t_ex_data, colWidths=[540])
        t_exclus.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1,-1), colors.HexColor('#fee2e2')), ('TEXTCOLOR', (0, 0), (-1,-1), colors.HexColor('#991b1b')), ('BOTTOMPADDING', (0, 0), (-1,-1), 3), ('TOPPADDING', (0, 0), (-1,-1), 3), ('GRID', (0, 0), (-1,-1), 0.4, colors.HexColor('#fca5a5')), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
        elements.extend([t_exclus, Spacer(1, 5)])

    # --- SCEAU DOCTRINAL HAYAATI ---
    s_t = pdf_txt.get("sceau_titre", "<b>SCEAU DE CONFORMITÉ NUMÉRIQUE HAYAATI v1.2</b>")
    s_c = pdf_txt.get("sceau_corps", "<i>Rapport d'audit officiel {}- Certifié Conforme aux Sources Doctrinales</i>").format(type_module)
    texte_sceau_global = f"{s_t}<br/>{s_c}"
    pol_sceau = obtenir_police_active_flux(texte_sceau_global)
    s_sceau_dynamique = ParagraphStyle('SceauD', parent=s_norm, fontName=pol_sceau, alignment=1)
    
    t_sceau = Table([[Paragraph(preparer_flux_multilingue(texte_sceau_global), s_sceau_dynamique)]], colWidths=[540])
    t_sceau.setStyle(TableStyle([('BOX', (0, 0), (-1,-1), 1.2, colors.HexColor('#064e3b')), ('BACKGROUND', (0, 0), (-1,-1), colors.HexColor('#f9fafb')), ('PADDING', (0, 0), (-1,-1), 4), ('ALIGN', (0, 0), (-1,-1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
    elements.extend([t_sceau, Spacer(1, 4)])

    # 🎯 VERSETS CORANIQUES UNICODE NETTOYÉS SANS SENS DE LECTURE BRISÉ
    v_zk = "2 : 110 : وَأَقِيمُوا۟ ٱلصَّلَوٰةَ وَءَاتُوا۟ ٱلزَّكَوٰةَ وَمَا تُقَدِّمُوا۟ لِأَنفُسِكُم مِّنْ خَيْرٍ تَجِدُوهُ عِندَ ٱللَّهِ إِنَّ ٱللَّهَ بِمَا تَعْمَلُونَ بَصِيرٌ "
    v_he = "4 : 11 : يُوصِيكُمُ اللَّهُ فِي أَوْلَادِكُمْ ۖ لِلذَّكَرِ مِثْلُ حَظِّ الْأُنثَيَيْنِ ۚ فَإِن كُنَّ نِسَاءً فَوْقَ اثْنَتَيْنِ فَلَهُنَّ ثُلُثَا مَا تَرَكَ ۖ وَإِن كَانَتْ وَاحِدَةً فَلَهَا النِّصْفُ ۚ... حَكِيمًا "
    elements.extend([Paragraph(formater_texte_arabe(v_zk), s_coran), Spacer(1, 2), Paragraph(formater_texte_arabe(v_he), s_coran)])

    doc.build(elements)
    try:
        import platform
        if os.name == 'nt': os.startfile(chemin_complet)
        elif platform.system() == 'Darwin': os.system(f"open {chemin_complet}")
        else: os.system(f"xdg-open {chemin_complet}")
    except Exception: pass
    return chemin_complet
