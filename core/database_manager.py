"""
GESTIONNAIRE PHYSIQUE DE LA BASE DE DONNÉES (CORE/DATABASE_MANAGER.PY)
Version 5.1 - Resynchronisation des signatures d'accès et des préférences par défaut.
"""
import sqlite3
import os

class DatabaseManager:
    def __init__(self, chemin_db="core/hayaati_private.db"):
        self.chemin_db = chemin_db
        self.initialiser_base_de_donnees()

    def initialiser_base_de_donnees(self):
        """Initialise la table maîtresse et s'assure de la présence des colonnes indispensables."""
        dossier = os.path.dirname(self.chemin_db)
        if dossier and not os.path.exists(dossier):
            os.makedirs(dossier)
            
        try:
            conn = sqlite3.connect(self.chemin_db)
            curseur = conn.cursor()
            curseur.execute("""
                CREATE TABLE IF NOT EXISTS comptes_utilisateurs (
                    user_id TEXT PRIMARY KEY,
                    identifiant TEXT UNIQUE,
                    adresse_email TEXT,
                    mot_de_passe TEXT,
                    nom TEXT DEFAULT '-',
                    prenom TEXT DEFAULT '-',
                    date_naissance TEXT DEFAULT '2000-01-01',
                    devise_defaut TEXT DEFAULT 'XOF',
                    langue_defaut TEXT DEFAULT 'FR',
                    fiqh_defaut TEXT DEFAULT 'Malikite'
                )
            """)
            
            curseur.execute("""
                CREATE TABLE IF NOT EXISTS retours_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    note_etoiles INTEGER,
                    commentaire TEXT,
                    date_envoi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

            # Forcer la migration si les colonnes manquent dans l'ancien fichier
            colonnes = [
                ("nom", "TEXT DEFAULT '-'"), ("prenom", "TEXT DEFAULT '-'"),
                ("date_naissance", "TEXT DEFAULT '2000-01-01'"), ("devise_defaut", "TEXT DEFAULT 'XOF'"),
                ("langue_defaut", "TEXT DEFAULT 'FR'"), ("fiqh_defaut", "TEXT DEFAULT 'Malikite'")
            ]
            for nom_c, type_c in colonnes:
                try:
                    curseur.execute(f"ALTER TABLE comptes_utilisateurs ADD COLUMN {nom_c} {type_c}")
                    conn.commit()
                except sqlite3.OperationalError:
                    pass
            conn.close()
        except Exception as e:
            print(f"[SQLITE ERROR] Initialisation compromise : {str(e)}")

    def enregistrer_feedback_utilisateur(self, user_id, etoiles, commentaire):
        try:
            conn = sqlite3.connect(self.chemin_db)
            curseur = conn.cursor()
            curseur.execute("INSERT INTO retours_feedback (user_id, note_etoiles, commentaire) VALUES (?, ?, ?)",
                            (str(user_id), int(etoiles), str(commentaire).strip()))
            conn.commit()
            conn.close()
            return True, "Feedback enregistré."
        except Exception as e:
            return False, str(e)

    def modifier_donnees_profil_securite(self, user_id, nouvel_identifiant, nouvel_email, nouveau_password, nouveau_nom, nouveau_prenom):
        """Signature synchronisée à 6 arguments pour éviter le TypeError."""
        try:
            conn = sqlite3.connect(self.chemin_db)
            curseur = conn.cursor()
            curseur.execute("""
                UPDATE comptes_utilisateurs 
                SET identifiant = ?, adresse_email = ?, mot_de_passe = ?, nom = ?, prenom = ?
                WHERE user_id = ?
            """, (str(nouvel_identifiant).strip(), str(nouvel_email).strip(), str(nouveau_password).strip(),
                  str(nouveau_nom).strip(), str(nouveau_prenom).strip(), str(user_id)))
            conn.commit()
            conn.close()
            return True, "Identifiants de sécurité enregistrés."
        except sqlite3.IntegrityError:
            return False, "Ce nom d'utilisateur est déjà pris."
        except Exception as e:
            return False, str(e)

    def sauvegarder_preferences_reglages(self, user_id, date_n, devise, langue, fiqh):
        """Permet d'ancrer de façon permanente les choix par défaut de la session connectée."""
        try:
            conn = sqlite3.connect(self.chemin_db)
            curseur = conn.cursor()
            curseur.execute("""
                UPDATE comptes_utilisateurs 
                SET date_naissance = ?, devise_defaut = ?, langue_defaut = ?, fiqh_defaut = ?
                WHERE user_id = ?
            """, (str(date_n).strip(), str(devise).strip(), str(langue).strip(), str(fiqh).strip(), str(user_id)))
            conn.commit()
            conn.close()
            return True, "Préférences fixées de manière persistante."
        except Exception as e:
            return False, str(e)

    def creer_compte_utilisateur(self, user_id, identifiant, email, password):
        try:
            conn = sqlite3.connect(self.chemin_db)
            curseur = conn.cursor()
            curseur.execute("INSERT INTO comptes_utilisateurs (user_id, identifiant, adresse_email, mot_de_passe) VALUES (?, ?, ?, ?)",
                            (str(user_id), str(identifiant).strip(), str(email).strip(), str(password).strip()))
            conn.commit()
            conn.close()
            return True, "Compte créé."
        except Exception as e:
            return False, str(e)

    def verifier_identifiants_connexion(self, identifiant, password_saisi):
        """Extrait l'ensemble des données, y compris les préférences par défaut au moment de la connexion."""
        try:
            conn = sqlite3.connect(self.chemin_db)
            curseur = conn.cursor()
            curseur.execute("""
                SELECT user_id, identifiant, adresse_email, mot_de_passe, date_naissance, devise_defaut, langue_defaut, fiqh_defaut
                FROM comptes_utilisateurs 
                WHERE identifiant = ? OR adresse_email = ?
            """, (str(identifiant).strip(), str(identifiant).strip()))
            compte = curseur.fetchone()
            conn.close()
            if not compte: 
                return False, "Aucun compte trouvé.", None, "", None
            return True, "Authentification réussie.", compte[0], compte[2], compte # Renvoie le tuple entier de session
        except Exception as e:
            return False, str(e), None, "", None
