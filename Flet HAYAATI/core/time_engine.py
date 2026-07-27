"""
MOTEUR TEMPOREL ISLAMIQUE DYNAMIQUE (TIME_ENGINE.PY)
Version 5.5 - Intégration de l'ajustement visuel de terrain.
"""
from datetime import datetime, date, timedelta

# Noms des 12 mois sacrés et lunaires de l'année hégirienne
MOIS_HEGIRIENS = [
    "Muharram", "Safar", "Rabi' al-Awwal", "Rabi' al-Thani",
    "Jumada al-Awwal", "Jumada al-Thani", "Rajab", "Sha'ban",
    "Ramadan", "Shawwal", "Dhu al-Qa'dah", "Dhu al-Hijjah"
]

def gregorien_vers_hegiri(annee, mois, jour, ajustement_fiqh=0):
    """
    Convertit une date grégorienne en date hégirienne.
    ajustement_fiqh : entier entre -2 et +2 jours (saisi IHM)
    pour synchroniser sur l'observation réelle du croissant.
    """
    # 🎯 SÉCURISATION DU PARAMÈTRE : Forçage des limites du Fiqh
    try:
        delta_jours = int(ajustement_fiqh or 0)
    except Exception:
        delta_jours = 0
        
    if delta_jours > 2: delta_jours = 2
    if delta_jours < -2: delta_jours = -2

    date_civile = date(annee, mois, jour)
    if delta_jours != 0:
        date_civile = date_civile + timedelta(days=delta_jours)
        
    g_annee = date_civile.year
    g_mois = date_civile.month
    g_jour = date_civile.day

    if g_mois <= 2:
        g_annee -= 1
        g_mois += 12
        
    A = int(g_annee / 100)
    B = 2 - A + int(A / 4)
    
    # Calcul du Jour Julien (JD)
    jd = int(365.25 * (g_annee + 4716)) + int(30.6001 * (g_mois + 1)) + g_jour + B - 1524.5
    
    # Constantes d'alignement avec l'époque de l'Hégire
    jd_epoch = 1948439.5
    jours_ecoules = jd - jd_epoch
    
    # Calcul de l'année hégirienne et du reliquat de jours
    annee_h = int((jours_ecoules * 30) / 10631.) + 1
    cycle_jours = jours_ecoules - int((annee_h - 1) * 10631 / 30)
    
    if cycle_jours < 0:
        annee_h -= 1
        cycle_jours = jours_ecoules - int((annee_h - 1) * 10631 / 30)
        
    mois_h = 1
    for m in range(1, 13):
        jours_mois = 30 if m % 2 != 0 else 29
        if m == 12 and ((11 * annee_h + 14) % 30 < 11):
            jours_mois = 30 # Année bissextile islamique
            
        if cycle_jours < jours_mois:
            mois_h = m
            break
        cycle_jours -= jours_mois
        
    jour_h = int(cycle_jours) + 1
    
    return {
        "annee": annee_h,
        "mois_num": mois_h,
        "mois_nom": MOIS_HEGIRIENS[mois_h - 1],
        "jour": jour_h
    }

def calculer_age_islamique(date_naissance_greg, ajustement_fiqh=0):
    """
    Calcule l'âge en années lunaires en prenant en compte
    l'ajustement du calendrier saisi manuellement.
    """
    if isinstance(date_naissance_greg, str):
        try:
            date_naissance_greg = datetime.strptime(
                date_naissance_greg, "%Y-%m-%d"
            ).date()
        except ValueError:
            return 0
            
    aujourdhui = date.today()
    
    h_naissance = gregorien_vers_hegiri(
        date_naissance_greg.year, 
        date_naissance_greg.month, 
        date_naissance_greg.day, 
        ajustement_fiqh=0
    )
    h_actuel = gregorien_vers_hegiri(
        aujourdhui.year, 
        aujourdhui.month, 
        aujourdhui.day, 
        ajustement_fiqh=ajustement_fiqh
    )
    
    age_h = h_actuel["annee"] - h_naissance["annee"]
    
    if h_actuel["mois_num"] < h_naissance["mois_num"] or \
       (h_actuel["mois_num"] == h_naissance["mois_num"] and \
        h_actuel["jour"] < h_naissance["jour"]):
        age_h -= 1
        
    return max(0, age_h)

def obtenir_evenement_hegiri(mois_h, jour_h):
    """Détecte les grandes dates du calendrier sunnite."""
    # Exclusion du mois de Ramadan (9) pour le jeûne surérogatoire
    if jour_h in [13, 14, 15] and mois_h != 9: 
        # Jours de Tashriq (13 Dhu al-Hijjah) exclu
        if not (mois_h == 12 and jour_h == 13):
            return (
                f"🌕 JOURS BLANCS ({jour_h} "
                f"{MOIS_HEGIRIENS[mois_h-1]}) : Jeûne surérogatoire "
                f"fortement recommandé (Sunnah Mouakkadah)."
            )

    if mois_h == 9 and jour_h >= 25:
        return (
            "🌙 PÉRIODE FIN RAMADAN : Préparez l'acquittement "
            "obligatoire de la Zakat Al-Fitr pour chaque membre."
        )
    
    if mois_h == 12 and 1 <= jour_h <= 9:
        if jour_h == 9:
            return (
                "📿 JOUR D'ARAFAT (9 Dhu al-Hijjah) : Le jeûne de ce "
                "jour expie les péchés de deux années (Hadith Muslim)."
            )
        return (
            f"🌟 10 PREMIERS JOURS DE DHU AL-HIJJAH (Jour {jour_h}) "
            f": Multipliez le Tasbih et le Takbir."
        )
    
    if mois_h == 12 and jour_h == 10:
        return (
            "🐑 AÏD AL-ADHA / TABASKI (10 Dhu al-Hijjah) : Prière de "
            "l'Aïd et immolation rituelle (Oudhiya) recommandées."
        )
    
    if mois_h == 1 & jour_h == 10:
        return (
            "📿 JOUR D'ACHOURA (10 Muharram) : Jeûne surérogatoire "
            "recommandé selon la Sunnah (Hadith Al-Boukhari)."
        )
    
    return None
