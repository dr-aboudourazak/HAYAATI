"""
GESTIONNAIRE PHYSIQUE DE LA BASE DE DONNÉES (CORE/DATABASE_MANAGER.PY)
Version 6.0 - Sécurisation : hachage PBKDF2-HMAC des mots de passe,
verrouillage anti-brute-force, connexions étanches (context manager).
Signatures et valeurs de retour inchangées pour rester compatible avec
app.py, page_connexion.py, page_inscription.py et page_reglages.py.
"""
import sqlite3
import os
import hashlib
import hmac
import secrets
from contextlib import contextmanager
from datetime import datetime, timedelta

# --- Paramètres de sécurité du mot de passe ---
ALGO_HACHAGE = "pbkdf2_sha256"
ITERATIONS_PBKDF2 = 260_000          # Recommandation OWASP 2023+ pour PBKDF2-SHA256
LONGUEUR_SEL_OCTETS = 16
LONGUEUR_MIN_MOT_DE_PASSE = 8

# --- Paramètres anti-brute-force ---
TENTATIVES_MAX_AVANT_VERROUILLAGE = 5
DUREE_VERROUILLAGE_MINUTES = 15


def _hacher_mot_de_passe(mot_de_passe_clair):
    """Dérive une empreinte PBKDF2-HMAC-SHA256 avec sel aléatoire par utilisateur."""
    sel = secrets.token_hex(LONGUEUR_SEL_OCTETS)
    empreinte = hashlib.pbkdf2_hmac(
        "sha256",
        str(mot_de_passe_clair).encode("utf-8"),
        bytes.fromhex(sel),
        ITERATIONS_PBKDF2,
    )
    return f"{ALGO_HACHAGE}${ITERATIONS_PBKDF2}${sel}${empreinte.hex()}"


def _verifier_mot_de_passe(mot_de_passe_saisi, empreinte_stockee):
    """Compare en temps constant le mot de passe saisi à l'empreinte stockée.
    Renvoie False (sans lever d'exception) si le format stocké est invalide
    ou hérité d'une ancienne version en clair : ce compte doit être recréé."""
    try:
        algo, iterations, sel, empreinte_hex = str(empreinte_stockee).split("$")
        if algo != ALGO_HACHAGE:
            return False
        empreinte_calculee = hashlib.pbkdf2_hmac(
            "sha256",
            str(mot_de_passe_saisi).encode("utf-8"),
            bytes.fromhex(sel),
            int(iterations),
        )
        return hmac.compare_digest(empreinte_calculee.hex(), empreinte_hex)
    except (ValueError, AttributeError, TypeError):
        return False


def _mot_de_passe_valide(mot_de_passe):
    """Contrôle minimal de robustesse. Renvoie (bool, message)."""
    if not mot_de_passe or len(str(mot_de_passe)) < LONGUEUR_MIN_MOT_DE_PASSE:
        return False, f"Le mot de passe doit contenir au moins {LONGUEUR_MIN_MOT_DE_PASSE} caractères."
    return True, ""


class DatabaseManager:
    def __init__(self, chemin_db="core/hayaati_private.db"):
        self.chemin_db = chemin_db
        self.initialiser_base_de_donnees()

    @contextmanager
    def _ouvrir_connexion(self):
        """Garantit la fermeture de la connexion même en cas d'exception."""
        conn = sqlite3.connect(self.chemin_db)
        try:
            yield conn
        finally:
            conn.close()

    def initialiser_base_de_donnees(self):
        """Initialise la table maîtresse et s'assure de la présence des colonnes indispensables."""
        dossier = os.path.dirname(self.chemin_db)
        if dossier and not os.path.exists(dossier):
            os.makedirs(dossier)

        try:
            with self._ouvrir_connexion() as conn:
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

                # Migration : ajout des colonnes manquantes sur une base déjà existante
                colonnes = [
                    ("nom", "TEXT DEFAULT '-'"), ("prenom", "TEXT DEFAULT '-'"),
                    ("date_naissance", "TEXT DEFAULT '2000-01-01'"), ("devise_defaut", "TEXT DEFAULT 'XOF'"),
                    ("langue_defaut", "TEXT DEFAULT 'FR'"), ("fiqh_defaut", "TEXT DEFAULT 'Malikite'"),
                    ("tentatives_echouees", "INTEGER DEFAULT 0"),
                    ("verrouillage_jusqu_a", "TEXT DEFAULT NULL"),
                ]
                for nom_c, type_c in colonnes:
                    try:
                        curseur.execute(f"ALTER TABLE comptes_utilisateurs ADD COLUMN {nom_c} {type_c}")
                        conn.commit()
                    except sqlite3.OperationalError:
                        pass
        except Exception as e:
            print(f"[SQLITE ERROR] Initialisation compromise : {str(e)}")

    def enregistrer_feedback_utilisateur(self, user_id, etoiles, commentaire):
        try:
            with self._ouvrir_connexion() as conn:
                curseur = conn.cursor()
                curseur.execute(
                    "INSERT INTO retours_feedback (user_id, note_etoiles, commentaire) VALUES (?, ?, ?)",
                    (str(user_id), int(etoiles), str(commentaire).strip())
                )
                conn.commit()
            return True, "Feedback enregistré."
        except Exception as e:
            return False, str(e)

    def modifier_donnees_profil_securite(self, user_id, nouvel_identifiant, nouvel_email, nouveau_password, nouveau_nom, nouveau_prenom):
        """Signature inchangée (6 arguments). Si nouveau_password est vide, le mot de
        passe existant est conservé plutôt qu'écrasé par une valeur vide."""
        try:
            with self._ouvrir_connexion() as conn:
                curseur = conn.cursor()

                if nouveau_password and str(nouveau_password).strip():
                    valide, msg_erreur = _mot_de_passe_valide(nouveau_password)
                    if not valide:
                        return False, msg_erreur
                    empreinte = _hacher_mot_de_passe(str(nouveau_password).strip())

                    curseur.execute("""
                        UPDATE comptes_utilisateurs
                        SET identifiant = ?, adresse_email = ?, mot_de_passe = ?, nom = ?, prenom = ?
                        WHERE user_id = ?
                    """, (str(nouvel_identifiant).strip(), str(nouvel_email).strip(), empreinte,
                          str(nouveau_nom).strip(), str(nouveau_prenom).strip(), str(user_id)))
                else:
                    curseur.execute("""
                        UPDATE comptes_utilisateurs
                        SET identifiant = ?, adresse_email = ?, nom = ?, prenom = ?
                        WHERE user_id = ?
                    """, (str(nouvel_identifiant).strip(), str(nouvel_email).strip(),
                          str(nouveau_nom).strip(), str(nouveau_prenom).strip(), str(user_id)))

                conn.commit()
            return True, "Identifiants de sécurité enregistrés."
        except sqlite3.IntegrityError:
            return False, "Ce nom d'utilisateur est déjà pris."
        except Exception as e:
            return False, str(e)

    def sauvegarder_preferences_reglages(self, user_id, date_n, devise, langue, fiqh):
        """Permet d'ancrer de façon permanente les choix par défaut de la session connectée."""
        try:
            with self._ouvrir_connexion() as conn:
                curseur = conn.cursor()
                curseur.execute("""
                    UPDATE comptes_utilisateurs
                    SET date_naissance = ?, devise_defaut = ?, langue_defaut = ?, fiqh_defaut = ?
                    WHERE user_id = ?
                """, (str(date_n).strip(), str(devise).strip(), str(langue).strip(), str(fiqh).strip(), str(user_id)))
                conn.commit()
            return True, "Préférences fixées de manière persistante."
        except Exception as e:
            return False, str(e)

    def creer_compte_utilisateur(self, user_id, identifiant, email, password):
        valide, msg_erreur = _mot_de_passe_valide(password)
        if not valide:
            return False, msg_erreur
        try:
            empreinte = _hacher_mot_de_passe(str(password).strip())
            with self._ouvrir_connexion() as conn:
                curseur = conn.cursor()
                curseur.execute(
                    "INSERT INTO comptes_utilisateurs (user_id, identifiant, adresse_email, mot_de_passe) VALUES (?, ?, ?, ?)",
                    (str(user_id), str(identifiant).strip(), str(email).strip(), empreinte)
                )
                conn.commit()
            return True, "Compte créé."
        except sqlite3.IntegrityError:
            return False, "Ce nom d'utilisateur est déjà pris."
        except Exception as e:
            return False, str(e)

    def verifier_identifiants_connexion(self, identifiant, password_saisi):
        """Vérifie l'identité, applique le verrouillage anti-brute-force, et ne renvoie
        jamais l'empreinte du mot de passe à l'appelant (champ neutralisé dans le tuple)."""
        try:
            with self._ouvrir_connexion() as conn:
                curseur = conn.cursor()
                curseur.execute("""
                    SELECT user_id, identifiant, adresse_email, mot_de_passe, date_naissance,
                           devise_defaut, langue_defaut, fiqh_defaut,
                           tentatives_echouees, verrouillage_jusqu_a
                    FROM comptes_utilisateurs
                    WHERE identifiant = ? OR adresse_email = ?
                """, (str(identifiant).strip(), str(identifiant).strip()))
                compte = curseur.fetchone()

                if not compte:
                    return False, "Aucun compte trouvé.", None, "", None

                user_id = compte[0]
                empreinte_stockee = compte[3]
                tentatives = compte[8] or 0
                verrouillage_str = compte[9]

                # Compte verrouillé ?
                if verrouillage_str:
                    try:
                        verrouille_jusqu_a = datetime.fromisoformat(verrouillage_str)
                        if datetime.now() < verrouille_jusqu_a:
                            minutes_restantes = int((verrouille_jusqu_a - datetime.now()).total_seconds() // 60) + 1
                            return False, f"Compte temporairement verrouillé. Réessayez dans {minutes_restantes} min.", None, "", None
                    except ValueError:
                        pass  # Format invalide, on ignore et on continue normalement

                mot_de_passe_correct = _verifier_mot_de_passe(password_saisi, empreinte_stockee)

                if not mot_de_passe_correct:
                    tentatives += 1
                    if tentatives >= TENTATIVES_MAX_AVANT_VERROUILLAGE:
                        verrouille_jusqu_a = datetime.now() + timedelta(minutes=DUREE_VERROUILLAGE_MINUTES)
                        curseur.execute(
                            "UPDATE comptes_utilisateurs SET tentatives_echouees = 0, verrouillage_jusqu_a = ? WHERE user_id = ?",
                            (verrouille_jusqu_a.isoformat(), user_id)
                        )
                        conn.commit()
                        return False, f"Trop de tentatives échouées. Compte verrouillé {DUREE_VERROUILLAGE_MINUTES} min.", None, "", None
                    else:
                        curseur.execute(
                            "UPDATE comptes_utilisateurs SET tentatives_echouees = ? WHERE user_id = ?",
                            (tentatives, user_id)
                        )
                        conn.commit()
                    return False, "Identifiant ou mot de passe incorrect.", None, "", None

                # Connexion réussie : on réinitialise le compteur de tentatives
                curseur.execute(
                    "UPDATE comptes_utilisateurs SET tentatives_echouees = 0, verrouillage_jusqu_a = NULL WHERE user_id = ?",
                    (user_id,)
                )
                conn.commit()

                # On ne renvoie jamais l'empreinte du mot de passe à l'appelant
                compte_assaini = compte[:3] + (None,) + compte[4:]
                return True, "Authentification réussie.", compte[0], compte[2], compte_assaini
        except Exception as e:
            return False, str(e), None, "", None
