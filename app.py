"""
POINT D'ENTRÉE ET SCRIPT DE DÉMARRAGE PRINCIPAL (APP.PY)
Version Finale - Alignement dynamique absolu pour le mode Visiteur et Connecté.
"""
import sys
import os
import traceback
import uuid

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class ControleurVisiteurGenerique:
    """Classe de secours si le gestionnaire de base de données est vide ou introuvable."""
    def __init__(self, chemin=""): self.chemin = chemin
    def modifier_donnees_profil_securite(self, *args, **kwargs): return False, "Indisponible."
    def sauvegarder_preferences_reglages(self, *args, **kwargs): return False, "Indisponible."
    def enregistrer_feedback_utilisateur(self, *args, **kwargs): return False, "Indisponible."
    def verifier_connexion_utilisateur(self, *args, **kwargs): return False, None, "Mode visiteur actif."
    def enregistrer_nouvel_utilisateur(self, *args, **kwargs): return False, "Mode visiteur actif."

def main():
    print("[DIAGNOSTIC] Initialisation du système graphique...")
    from gui.app_visuelle import ApplicationHayaati
    from gui.langues import DICTIONNAIRE_LANGUES
    
    controleur_auth = None; chemin_db = os.path.join("core", "hayaati_private.db")
    
    try:
        import core.database_manager as db_module
        if hasattr(db_module, "DatabaseManager"):
            manager_brut = db_module.DatabaseManager(chemin_db)
            print("[SQLITE SUCCESS] Classe DatabaseManager initialisée avec succès.")
            
            # ADAPTATEUR PONTAGE CONNEXION SÉCURISÉ
            def adaptateur_connexion_hayaati(login, password):
                succes, msg, u_id, email, compte = manager_brut.verifier_identifiants_connexion(login, password)
                if succes and compte:
                    app.devise_active = str(compte[5]).strip()
                    app.langue_actuelle = str(compte[6]).strip().upper()
                    app.madhhab_actif = str(compte[7]).strip()
                return succes, u_id, email

            def adaptateur_inscription_hayaati(username, email, password):
                id_generé = str(uuid.uuid4())[:8].upper()
                return manager_brut.creer_compte_utilisateur(id_generé, username, email, password)

            manager_brut.verifier_connexion_utilisateur = adaptateur_connexion_hayaati
            manager_brut.enregistrer_nouvel_utilisateur = adaptateur_inscription_hayaati
            controleur_auth = manager_brut
        else:
            controleur_auth = ControleurVisiteurGenerique(chemin_db)
            print("[SQLITE WARNING] Aucun gestionnaire trouvé. Mode visiteur actif.")
            
    except Exception as e:
        controleur_auth = ControleurVisiteurGenerique(chemin_db)
        print(f"[SQLITE WARNING] Chargement base de données contourné : {str(e)}")

    # 1. Instanciation de l'IHM maîtresse
    app = ApplicationHayaati(controleur_authentification=controleur_auth)
    
    # 2. 🎯 RECTIFICATION COMPACTE VISITEUR : Chargement direct via le code dynamique du fichier scanné
    c_pref_init = app.sync_engine.charger_donnees_module("INVITE", "PREFERENCES")
    langue_sauvegardee_visiteur = str(c_pref_init.get("langue_actuelle", "FR")).upper()
    
    app.langue_actuelle = langue_sauvegardee_visiteur
    
    # 🎯 Force le chargement du fichier JSON d'après son vrai nom lu au scan (ex: 'ENGLISH')
    DICTIONNAIRE_LANGUES.moteur_i18n.charger_dictionnaire_langue(langue_sauvegardee_visiteur)
    
    # Propagande immédiate de la langue sur Connexion et Inscription du mode Visiteur
    if hasattr(app, "declencher_changement_global"):
        app.declencher_changement_global()

    app.basculer_ecran("ONBOARDING")
    app.mainloop()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        chemin_erreur = "erreur_systeme.txt"
        with open(chemin_erreur, "w", encoding="utf-8") as f:
            f.write("=== RAPPORT D'ERREUR EXHAUSTIF HAYAATI ===\n\n")
            traceback.print_exc(file=f)
        print("\n" + "="*60 + f"\n❌ LE SCRIPT A PLANTÉ ! Erreur enregistrée dans :\n👉 {os.path.abspath(chemin_erreur)}\n" + "="*60 + "\n")
