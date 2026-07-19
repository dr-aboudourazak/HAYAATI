"""
FONCTIONS DE GESTION DU INVENTAIRE PATRIMONIAL INTEGRAL (CORE/DB_PROFIL.PY)
Version 5.5 - Prise en charge de la sauvegarde des données avicoles.
"""
import sqlite3

DB_NAME = "hayaati_private.db"

def enregistrer_nouvel_utilisateur(user_id, prenom, nom, email, pwd_hash, pays, ville, tel, date_naiss):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP);", (user_id, prenom, nom, email, pwd_hash, pays, ville, tel, date_naiss))
        cursor.execute("INSERT INTO profils_sharia (user_id) VALUES (?);", (user_id,))
        conn.commit()
        return True
    except sqlite3.IntegrityError: return False
    finally: conn.close()

def mettre_a_jour_patrimoine_sharia(user_id, madhhab, devise, ajust_h, cash, or_p, stocks, pro_cash, immeubles, logistique, p_recolte, v_recolte, n_ovins, v_ovins, n_bovins, v_bovins, n_volailles, v_volailles, wasiyya_txt, legs_v):
    """Sauvegarde l'intégralité absolue des avoirs financiers, commerciaux, immobiliers et agropastoraux."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE profils_sharia SET madhhab_actif=?, devise_active=?, ajustement_hegiri_jours=?, capital_brut_declare=?, valeur_bijoux_or=?, valeur_stock_marchand=?, liquidites_entreprise=?, valeur_immeubles=?, valeur_logistique=?, poids_recolte_kg=?, valeur_recolte_stockee=?, nombre_ovins=?, valeur_troupeau_ovins=?, nombre_bovins=?, valeur_troupeau_bovins=?, nombre_volailles=?, valeur_volailles=?, wasiyya_textuelle=?, montant_legs_volontaire=? WHERE user_id=?;
    """, (madhhab, devise, ajust_h, cash, or_p, stocks, pro_cash, immeubles, logistique, p_recolte, v_recolte, n_ovins, v_ovins, n_bovins, v_bovins, n_volailles, v_volailles, wasiyya_txt, legs_v, user_id))
    conn.commit()
    conn.close()

def extraire_profil_sharia_complet(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT u.prenom, u.nom, u.pays, u.ville, u.telephone, u.date_naissance, p.* FROM users u JOIN profils_sharia p ON u.id = p.user_id WHERE u.id = ?;", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def inserer_nouvelle_dette(dette_id, user_id, type_dette, statut, montant, description):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO dettes (id, user_id, type_dette, statut_recouvrement, montant, description) VALUES (?,?,?,?,?,?);", (dette_id, user_id, type_dette, statut, montant, description))
    conn.commit()
    conn.close()

def extraire_dettes_actives_et_passives(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dettes WHERE user_id = ? ORDER BY date_declaration DESC;", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def enregistrer_mouhasabah_journaliere(user_id, date_greg, date_heg, prieres, rakahs, is_jeune, type_j, sadaqah, coran):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO mouhasabah_journaliere (user_id, date_gregorienne, date_hegirienne_calculee, prieres_obligatoires_validees, rakahs_nawafil, jeune_jour_valide, type_jeune, sadaqah_versee, lecture_coran_pages) VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(user_id, date_gregorienne) DO UPDATE SET prieres_obligatoires_validees=excluded.prieres_obligatoires_validees, rakahs_nawafil=excluded.rakahs_nawafil, jeune_jour_valide=excluded.jeune_jour_valide, type_jeune=excluded.type_jeune, sadaqah_versee=excluded.sadaqah_versee, lecture_coran_pages=excluded.lecture_coran_pages;
    """, (user_id, date_greg, date_heg, prieres, rakahs, int(is_jeune), type_j, sadaqah, coran))
    conn.commit()
    conn.close()

def extraire_historique_mouhasabah(user_id, limite=30):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mouhasabah_journaliere WHERE user_id = ? ORDER BY date_gregorienne DESC LIMIT ?;", (user_id, limite))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
