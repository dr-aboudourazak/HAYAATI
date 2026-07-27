"""
EXTENSION ALGORITHMIQUE DES ALERTES SHARIA (GUI/PAGE_ONBOARDING_ALERTS.PY)
Version Finale Intégrale - Totalement compatible Flet 0.86.2, Python 3.14 & APK Android
"""
from __future__ import annotations
from datetime import datetime
import os
import sys
import sqlite3
from core.agenda_engine import AgendaEngine
from core.time_engine import gregorien_vers_hegiri, obtenir_evenement_hegiri
from gui.langues import DICTIONNAIRE_LANGUES

def obtenir_chemin_base_donnees() -> str:
    """Résout dynamiquement l'emplacement physique de la base SQLite hayaati_private.db."""
    nom_db = "hayaati_private.db"
    if hasattr(sys, "getandroidapilevel") or "ANDROID_BOOTLOGO" in os.environ:
        d_and = os.path.dirname(sys.executable) if hasattr(sys, "executable") else os.getcwd()
        chemin = os.path.join(d_and, nom_db)
        if not os.path.exists(chemin):
            c_orig = os.path.join("core", nom_db)
            if os.path.exists(c_orig):
                try:
                    import shutil
                    shutil.copy(c_orig, chemin)
                except Exception: return c_orig
        return chemin
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "core", nom_db))

def compiler_alertes_espace_prive(c_fin: dict, c_sp: dict, net: float, dev: str, fiqh: str, user_id: str | None = None, ajustement_lune: int = 0):
    """Compile et retourne le quadruple diagnostic de vigilance Sharia (txt_pr, txt_cal, bg_c, fg_c)."""
    moteur_agenda = AgendaEngine()
    txt_onb = DICTIONNAIRE_LANGUES.actif.get("onboarding", {})
    txt_mouh = DICTIONNAIRE_LANGUES.actif.get("mouhasabah", {})
    
    # 1. ANALYSE ET TRADUCTION DES PRIÈRES EN RETARD
    prieres_profil = {p: c_sp.get(p, 0) for p in ["fajr", "dhouhr", "asr", "maghrib", "isha"]}
    manquees = moteur_agenda.evaluer_prieres_manquees_en_direct(prieres_profil, madhhab_actif=fiqh)

    if manquees:
        # 🎯 TRADUCTION DES PRIÈRES : Convertit les clés techniques dans la langue active
        prieres_json = txt_mouh.get("prieres", {})
        trad_manquees = [prieres_json.get(p, p.capitalize()) for p in manquees]
        chaine_prieres = ", ".join(trad_manquees)
        
        txt_pr = txt_onb.get("prieres_manquees", "⚠️ VIGILANCE PRIÈRE : {}").format(chaine_prieres)
        bg_c, fg_c = "#fee2e2", "#991b1b"
    else:
        txt_pr = txt_onb.get("prieres_ok", "✨ Excellent.")
        bg_c, fg_c = "#d1fae5", "#166534"

    # 2. EVALUATION CHRONOLOGIQUE ET TRADUCTION DES MOIS HÉGIRIENS
    maintenant = datetime.now()
    jour_s = maintenant.weekday()
    txt_cal = ""
    
    h_date = gregorien_vers_hegiri(maintenant.year, maintenant.month, maintenant.day, ajustement_fiqh=ajustement_lune)
    
    # 🎯 RECUPERATION DU NOM DU MOIS DEPUIS LE DICTIONNAIRE ACTIF
    cle_mois = f"mois_nom_{h_date['mois_num']}"
    nom_mois_traduit = txt_onb.get(cle_mois, h_date['mois_nom'])
    
    texte_date_hegirie = f"📅 {h_date['jour']} {nom_mois_traduit} {h_date['annee']} AH\n\n"
    txt_cal += texte_date_hegirie

    # Alerte Vendredi (Joumou'ah)
    if jour_s == 4:
        txt_cal += txt_onb.get("joumouah", "🌟 VENDREDI.\n\n")

    # Extraction de l'âge hégirien et de l'alerte anniversaire depuis la base SQLite
    if user_id:
        try:
            conn = sqlite3.connect(obtenir_chemin_base_donnees())
            curseur = conn.cursor()
            curseur.execute("SELECT date_naissance FROM comptes_utilisateurs WHERE user_id = ?", (str(user_id),))
            db_res = curseur.fetchone()
            conn.close()
            
            if db_res and db_res[0]:
                date_naiss = datetime.strptime(db_res[0], "%Y-%m-%d")
                jours_solaires = (maintenant - date_naiss).days
                age_islamique = (jours_solaires / 354.367)
                txt_cal += txt_onb.get("age_islamique", "🎂 AGE : {:.1f} ans.\n").format(age_islamique)
                
                if maintenant.day == date_naiss.day and maintenant.month == date_naiss.month:
                    txt_cal += txt_onb.get("anniversaire_alerte", "⚠️ RAPPEL RE-CYCLE ANNUEL.\n\n")
        except Exception: 
            pass

    # Événements lunaires (Ramadan, Achoura, etc.)
    evenement_lunaire = obtenir_evenement_hegiri(h_date["mois_num"], h_date["jour"])
    if evenement_lunaire:
        txt_cal += f"📌 PROMPT LUNAIRE : {evenement_lunaire}\n\n"

    # Nawafil / Sadaqah
    txt_cal += txt_onb.get("entete_devotion", "📿 EXAMEN DE VIGILANCE SPIRITUELLE DU JOUR :\n")
    if int(c_sp.get("nawafil", 0)) == 1: 
        txt_cal += txt_onb.get("nawafil_ok", "   • ✅ Nawafil.\n")
    else: 
        txt_cal += txt_onb.get("nawafil_ko", "   • 🔴 RAPPEL NAWAFIL.\n")

    if int(c_sp.get("sadaqah", 0)) == 1: 
        txt_cal += txt_onb.get("sadaqah_ok", "   • ✅ Sadaqah.\n\n")
    else: 
        txt_cal += txt_onb.get("sadaqah_ko", "   • 🔴 RAPPEL SADAQAH.\n\n")

    # Éligibilité Hadj
    deja_fait_hadj = int(c_sp.get("deja_fait_hadj", 0))
    seuil_hadj = 3500000.0 if dev in ["XOF", "FCFA"] else 5500.0
    if net >= seuil_hadj:
        if deja_fait_hadj == 1: 
            txt_cal += txt_onb.get("hadj_ok", "🕋 HADJ ACCOMPLI.\n")
        else: 
            txt_cal += txt_onb.get("hadj_ko", "🕋 APTITUDE HADJ ACTIVE ({:.0f} {}).\n").format(net, dev)

    # Rappel spécifique Muharram
    if h_date["mois_num"] == 1:
        txt_cal += txt_onb.get("fin_muharram", "📌 CHRONOLOGIE : MOUHARRAM.\n\n")

    # Clôture du rapport des dévotions générales
    txt_cal += txt_onb.get("general_devotion", "📖 MÉMOIRE DU QUOTIDIEN.")

    return txt_pr, txt_cal, bg_c, fg_c
