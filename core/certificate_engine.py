"""
MOTEUR DE CERTIFICATION ET GENERATION DE RAPPORTS PDF (CORE/CERTIFICATE_ENGINE.PY)
Version 2.7 - Correction de la chaîne corrompue et stabilisation du moteur de rendu arabe RTL.
"""
import os
import hashlib
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Circle, String, Group, Line

# Importation des outils d'enregistrement de polices pour l'arabe Windows
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Importation des moteurs de rendu arabe complexe
import arabic_reshaper
from bidi.algorithm import get_display

# Enregistrement sécurisé de la police Arial de Windows qui supporte nativement l'arabe
try:
    chemin_font_arial = "C:\\Windows\\Fonts\\arial.ttf"
    if os.path.exists(chemin_font_arial):
        pdfmetrics.registerFont(TTFont('Arial-Arabe', chemin_font_arial))
        POLICE_ARABE = 'Arial-Arabe'
    else:
        POLICE_ARABE = 'Helvetica'
except Exception:
    POLICE_ARABE = 'Helvetica'

def formater_texte_arabe(texte_brut):
    """Ligature les lettres arabes et inverse le sens d'affichage (RTL)."""
    try:
        texte_reshape = arabic_reshaper.reshape(texte_brut)
        texte_correct = get_display(texte_reshape)
        return texte_correct
    except Exception:
        return texte_brut

def creer_logo_arabe_hayaati():
    """Conçoit le blason vectoriel géométrique, stable et centré de Hayaati."""
    d = Drawing(80, 70)
    g = Group()
    
    cercle_ext = Circle(40, 35, 33)
    cercle_ext.fillColor = colors.HexColor('#064e3b') 
    cercle_ext.strokeColor = colors.HexColor('#d97706') 
    cercle_ext.strokeWidth = 2
    g.add(cercle_ext)
    
    cercle_int = Circle(40, 35, 29)
    cercle_int.fillColor = colors.HexColor('#064e3b')
    cercle_int.strokeColor = colors.HexColor('#f59e0b')
    cercle_int.strokeWidth = 0.5
    g.add(cercle_int)
    
    barre_sup = Line(28, 43, 52, 43, strokeColor=colors.HexColor('#f59e0b'), strokeWidth=3.5)
    barre_sup.strokeLineCap = 1 
    g.add(barre_sup)
    
    boucle_ha = Circle(40, 31, 10)
    boucle_ha.fillColor = colors.transparent 
    boucle_ha.strokeColor = colors.HexColor('#f59e0b')
    boucle_ha.strokeWidth = 3.5
    g.add(boucle_ha)
    
    cache_vide = Circle(49, 37, 7)
    cache_vide.fillColor = colors.HexColor('#064e3b')
    cache_vide.strokeColor = colors.HexColor('#064e3b')
    g.add(cache_vide)
    
    nom_marque_correct = formater_texte_arabe("حياتي")
    texte_arabe = String(28, 19, nom_marque_correct, fontName=POLICE_ARABE, fontSize=11)
    texte_arabe.fillColor = colors.HexColor('#ffffff')
    g.add(texte_arabe)
    
    d.add(g)
    return d

def generer_certificat_pdf(identite_dict, type_module, madhhab, devise, donnees_calcul, lignes_rapport, dossier_destination="Certificats"):
    """Génère un rapport PDF officiel épuré, compacté sur une seule page avec arabe correct."""
    if not os.path.exists(dossier_destination):
        os.makedirs(dossier_destination)

    nom_client = identite_dict.get("nom", "Inconnu")
    prenom_client = identite_dict.get("prenom", "")
    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nom_fichier = f"Hayaati_{type_module}_{nom_client.replace(' ', '_')}_{date_str}.pdf"
    chemin_complet = os.path.join(dossier_destination, nom_fichier)

    empreinte_brute = f"{nom_client}-{prenom_client}-{type_module}-{madhhab}-{date_str}".encode('utf-8')
    id_certification = hashlib.sha256(empreinte_brute).hexdigest()[:16].upper()

    doc = SimpleDocTemplate(chemin_complet, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=25, bottomMargin=25)
    styles = getSampleStyleSheet()
    elements = []

    style_titre = ParagraphStyle('TitreCertif', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=22, textColor=colors.HexColor('#064e3b'), alignment=1, spaceAfter=2)
    style_basmala = ParagraphStyle('Basmala', parent=styles['Normal'], fontName=POLICE_ARABE, fontSize=13, textColor=colors.HexColor('#064e3b'), alignment=1, spaceAfter=8)
    style_salam = ParagraphStyle('SalamCertif', parent=styles['Normal'], fontName=POLICE_ARABE, fontSize=11, textColor=colors.HexColor('#d97706'), alignment=1, spaceAfter=10)
    style_normal = ParagraphStyle('TextNormal', parent=styles['Normal'], fontName='Helvetica', fontSize=9, textColor=colors.HexColor('#1f2937'), leading=13)
    style_important = ParagraphStyle('TextImportant', parent=style_normal, fontName='Helvetica-Bold', textColor=colors.HexColor('#064e3b'))
    style_versets_sacres = ParagraphStyle('VersetsCoran', parent=styles['Normal'], fontName=POLICE_ARABE, fontSize=9, textColor=colors.HexColor('#374151'), alignment=1, leading=14)

    # --- EN-TÊTE ---
    logo_arabe = creer_logo_arabe_hayaati()
    t_logo = Table([[logo_arabe]], colWidths=[540])
    t_logo.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    elements.append(t_logo)
    elements.append(Spacer(1, 5))

    elements.append(Paragraph("H A Y A A T I", style_titre))
    
    basmala_propre = formater_texte_arabe("حياتي — بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ")
    salam_propre = formater_texte_arabe("السَّلَامُ عَلَيْكُمْ وَرَحْمَةُ اللهِ وَبَرَكَاتُهُ")
    
    elements.append(Paragraph(basmala_propre, style_basmala))
    elements.append(Paragraph(salam_propre, style_salam))
    elements.append(Spacer(1, 4))

    # --- BLOC D'IDENTIFICATION ---
    date_lecture = datetime.now().strftime("%d/%m/%Y à %H:%M")
    info_texte = f"""
    <b>ID Certification :</b> <font color='#d97706'>{id_certification}</font><br/>
    <b>Bénéficiaire :</b> {prenom_client.upper()} {nom_client.upper()}<br/>
    <b>Localisation :</b> {identite_dict.get('ville', '')} ({identite_dict.get('pays', '')}) &nbsp;|&nbsp; <b>Téléphone :</b> {identite_dict.get('telephone', '')}<br/>
    <b>Date d'Analyse :</b> {date_lecture} &nbsp;|&nbsp; <b>Fiqh :</b> École {madhhab.upper()} &nbsp;|&nbsp; <b>Devise :</b> {devise}
    """
    elements.append(Paragraph(info_texte, style_normal))
    elements.append(Spacer(1, 10))

    # Section 1 : Intrants déclarés
    elements.append(Paragraph("<b>1. Données Patrimoniales Déclarées :</b>", style_important))
    elements.append(Spacer(1, 4))
    
    tableau_donnees = [["Paramètre / Catégorie", "Valeur Déclarée"]]
    for cle, valeur in donnees_calcul.items():
        tableau_donnees.append([cle.upper(), f"{valeur}"])
        
    t_intrants = Table(tableau_donnees, colWidths=[340, 200])
    t_intrants.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.HexColor('#f3f4f6')),
        ('TEXTCOLOR', (0,0), (1,0), colors.HexColor('#374151')),
        ('FONTNAME', (0,0), (1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2), 
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
    ]))
    elements.append(t_intrants)
    elements.append(Spacer(1, 12))

    # Section 2 : Résultats du calcul
    elements.append(Paragraph("<b>2. Bilan de Ventilation et Conformité Légale :</b>", style_important))
    elements.append(Spacer(1, 4))

    tableau_resultats = []
    for ligne in lignes_rapport:
        if ligne.strip() and not ligne.startswith("===") and not ligne.startswith(" [📜"):
            tableau_resultats.append([ligne.strip()])

    t_resultats = Table(tableau_resultats, colWidths=[540])
    t_resultats.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#e6f4ea')),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#064e3b')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#d1fae5')),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
    ]))
    elements.append(t_resultats)
    elements.append(Spacer(1, 12))

    # Sceau final de conformité
    design_sceau = [
        [Paragraph("<b>SCEAU DE CONFORMITÉ NUMÉRIQUE</b><br/>Plateforme Globale Hayaati v1.2 &nbsp;|&nbsp; <i>Certifié Conforme aux Textes Jurisprudentiels</i>", style_normal)]
    ]
    t_sceau = Table(design_sceau, colWidths=[540])
    t_sceau.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor('#064e3b')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f9fafb')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('ALIGN', (0,0), (-1,-1), 'CENTER')
    ]))
    elements.append(t_sceau)
    elements.append(Spacer(1, 15))

    # --- TRAITEMENT ET APPLICATION DU FILTRE RTL SUR LES DEUX VERSETS NETTOYÉS ---
    v_zakat = "وَأَقِيمُوا الصَّلَاةَ وَآتُوا الزَّكَاةَ وَمَا تُقَدِّمُوا لِأَنfُسِكُم مِّنْ خَيْرٍ تَجِدُوهُ عِندَ اللَّهِ ۗ إِنَّ اللَّهَ بِمَا تَعْمَلُونَ بَصِيرٌ (سورة البقرة - آية 110)"
    v_heritage = "يُوصِيكُمُ اللَّهُ فِي أَوْلَادِكُمْ ۖ لِلذَّكَرِ مِثْلُ حَظِّ الْأُنثَيَيْنِ ۚ فَإِن كُنَّ نِسَاءً فَوْقَ اثْنَتَيْنِ فَلَهُنَّ ثُلُثَا مَا تَرَكَ ۖ وَإِن كَانَتْ وَاحِدَةً فَلَهَا النِّصْفُ (سورة النساء - آية 11)"
    
    verset_zakat_propre = formater_texte_arabe(v_zakat)
    verset_heritage_propre = formater_texte_arabe(v_heritage)

    elements.append(Paragraph(verset_zakat_propre, style_versets_sacres))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(verset_heritage_propre, style_versets_sacres))

    # Construction physique et lancement automatique Windows
    doc.build(elements)
    try:
        os.startfile(chemin_complet)
    except Exception as e:
        print(f"Erreur d'ouverture : {e}")

    return chemin_complet
