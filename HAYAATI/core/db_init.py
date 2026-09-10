"""
INITIALISATION DE LA BASE DE DONNÉES INTEGRALE AVEC VOLAILLES (CORE/DB_INIT.PY)
Version 5.5 - Intègre le stockage des volailles pour l'héritage et le commerce.
"""
import sqlite3

DB_NAME = "hayaati_private.db"

def initialiser_base_de_donnees_locale():
    """Crée l'infrastructure SQLite locale chiffrée avec ses contraintes de Fiqh."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY, prenom TEXT NOT NULL, nom TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
            pays TEXT NOT NULL, ville TEXT NOT NULL, telephone TEXT NOT NULL,
            date_naissance TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 🚨 INFRASTRUCTURE TOTALE EXTENSIBLE : Ajout du volet avicole rural
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profils_sharia (
            user_id TEXT PRIMARY KEY, madhhab_actif TEXT NOT NULL DEFAULT 'Maliki',
            devise_active TEXT NOT NULL DEFAULT 'CFA', ajustement_hegiri_jours INTEGER NOT NULL DEFAULT 0,
            capital_brut_declare REAL NOT NULL DEFAULT 0.0, valeur_bijoux_or REAL NOT NULL DEFAULT 0.0,
            valeur_stock_marchand REAL NOT NULL DEFAULT 0.0, liquidites_entreprise REAL NOT NULL DEFAULT 0.0,
            valeur_immeubles REAL NOT NULL DEFAULT 0.0, valeur_logistique REAL NOT NULL DEFAULT 0.0,
            poids_recolte_kg REAL NOT NULL DEFAULT 0.0, valeur_recolte_stockee REAL NOT NULL DEFAULT 0.0,
            nombre_ovins INTEGER NOT NULL DEFAULT 0, valeur_troupeau_ovins REAL NOT NULL DEFAULT 0.0,
            nombre_bovins INTEGER NOT NULL DEFAULT 0, valeur_troupeau_bovins REAL NOT NULL DEFAULT 0.0,
            nombre_volailles INTEGER NOT NULL DEFAULT 0, valeur_volailles REAL NOT NULL DEFAULT 0.0,
            wasiyya_textuelle TEXT, montant_legs_volontaire REAL NOT NULL DEFAULT 0.0,
            date_ouverture_nissab TEXT, FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dettes (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL, type_dette TEXT NOT NULL,
            statut_recouvrement TEXT NOT NULL, montant REAL NOT NULL, description TEXT NOT NULL,
            date_declaration TEXT DEFAULT CURRENT_DATE, FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mouhasabah_journaliere (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, date_gregorienne TEXT NOT NULL,
            date_hegirienne_calculee TEXT NOT NULL, prieres_obligatoires_validees INTEGER NOT NULL DEFAULT 0,
            rakahs_nawafil INTEGER NOT NULL DEFAULT 0, jeune_jour_valide INTEGER NOT NULL DEFAULT 0,
            type_jeune TEXT DEFAULT 'AUCUN', sadaqah_versee REAL NOT NULL DEFAULT 0.0,
            lecture_coran_pages INTEGER NOT NULL DEFAULT 0, FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, date_gregorienne)
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS arbre_genealogique (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL, lien_parente TEXT NOT NULL,
            nombre INTEGER NOT NULL DEFAULT 1, est_exclu_indignite INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE, UNIQUE(user_id, lien_parente)
        );
    """)

    conn.commit()
    conn.close()
    print("[Base] L'infrastructure de stockage universelle (avec Volailles) est scellée.")
