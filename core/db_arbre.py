"""
MOTEUR DE PERSISTANCE DE L'ARBRE FAMILIAL (CORE/DB_ARBRE.PY)
Version 3.0 - Écriture et lecture physique des 12 catégories d'héritiers dans SQLite.
"""
import sqlite3

CHEMIN_DB_PAR_DEFAUT = "core/hayaati_private.db"

def configurer_membre_arbre_genealogique(id_unique, user_id, lien_parente, quantite, est_indigne=0):
    """Insère ou met à jour de façon persistante une catégorie d'héritiers pour l'utilisateur."""
    try:
        conn = sqlite3.connect(CHEMIN_DB_PAR_DEFAUT)
        curseur = conn.cursor()
        
        # Création de la table des membres si elle n'existe pas encore
        curseur.execute("""
            CREATE TABLE IF NOT EXISTS membres_arbre_genealogique (
                user_id TEXT,
                lien_parente TEXT,
                quantite INTEGER,
                est_indigne INTEGER,
                PRIMARY KEY (user_id, lien_parente)
            )
        """)
        
        # Enregistrement ou mise à jour (ON CONFLICT) pour préserver les modifications
        curseur.execute("""
            INSERT INTO membres_arbre_genealogique (user_id, lien_parente, quantite, est_indigne)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, lien_parente) DO UPDATE SET
                quantite = excluded.quantite,
                est_indigne = excluded.est_indigne
        """, (str(user_id), str(lien_parente).lower().strip(), int(quantite), int(est_indigne)))
        
        conn.commit()
        conn.close()
        print(f"[SQLITE SUCCESS] Arbre mis à jour : {lien_parente} (Quantité: {quantite})")
        return True
    except Exception as e:
        print(f"[SQLITE ARBRE ERROR] Échec de l'écriture : {str(e)}")
        return False
