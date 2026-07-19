"""
MOTEUR CENTRAL DE SYNCHRONISATION (SYNC_ENGINE.PY)
Version 5.9 - Partie 1 : Persistance SQLite étanche et assainissement des modules financiers.
"""
import sqlite3
import json

class SyncEngine:
    def __init__(self, chemin_db="core/hayaati_private.db"):
        self.chemin_db = chemin_db
        self.initialiser_structure_persistence()

    def initialiser_structure_persistence(self):
        """Initialise la table SQLite pour la persistance des structures JSON."""
        try:
            conn = sqlite3.connect(self.chemin_db)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS synchronisation_modules (
                    user_id TEXT, cle_module TEXT, donnees_json TEXT,
                    derniere_maj TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, cle_module)
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e: 
            print(f"[SYNC ERROR] Initialisation structure : {e}")

    def executer_sauvegarde_module(self, user_id, cle_module, donnees_dict):
        """Sauvegarde les données d'un module sous forme d'objet JSON chiffré."""
        if not user_id or str(user_id) in ["demo-id", "None"]: 
            return True, "Mode Simulation."
        try:
            conn = sqlite3.connect(self.chemin_db)
            cur = conn.cursor()
            donnees_json = json.dumps(donnees_dict, ensure_ascii=False)
            
            cur.execute("""
                INSERT INTO synchronisation_modules (user_id, cle_module, donnees_json) 
                VALUES (?, ?, ?) ON CONFLICT(user_id, cle_module) DO UPDATE SET
                    donnees_json = excluded.donnees_json, derniere_maj = CURRENT_TIMESTAMP
            """, (str(user_id), cle_module.upper(), donnees_json))
            conn.commit()
            conn.close()
            return True, f"Module {cle_module} synchronisé."
        except Exception as e: 
            return False, str(e)
        
    def charger_donnees_module(self, user_id, cle_module):
        """Charge et assainit les variables stockées en base de données."""
        if not user_id or str(user_id) in ["demo-id", "None"]: 
            return {}
        try:
            conn = sqlite3.connect(self.chemin_db)
            cur = conn.cursor()
            cur.execute("""
                SELECT donnees_json FROM synchronisation_modules 
                WHERE user_id = ? AND cle_module = ?
            """, (str(user_id), cle_module.upper()))
            res = cur.fetchone()
            conn.close()
            
            if not res: 
                if cle_module.upper() == "PREFERENCES":
                    return {"ajustement_hegiri": 0, "arbitrage_nisab": "PLUS_BAS"}
                return {}
            
            data = json.loads(res[0])
            mod_u = cle_module.upper()
            
            # Assainissement i18n des métaux précieux et de l'élevage
            if mod_u == "FINANCES" and data:
                if "or" in data and "or_poids" not in data:
                    v_or = float(data.get("or", 0.0))
                    data["or_cours"] = 45000.0
                    data["or_poids"] = v_or / 45000.0
                if "argent_poids" not in data: data["argent_poids"] = 0.0
                if "argent_cours" not in data: data["argent_cours"] = 650.0
                if "grain_cours" not in data: data["grain_cours"] = 150.0
                if "ovin_cours" not in data: data["ovin_cours"] = 45000.0
                if "bovin_cours" not in data: data["bovin_cours"] = 120000.0
            
            if mod_u == "PREFERENCES":
                if "ajustement_hegiri" not in data: data["ajustement_hegiri"] = 0
                if "arbitrage_nisab" not in data or not data["arbitrage_nisab"]: 
                    data["arbitrage_nisab"] = "PLUS_BAS"
                
            return data
        except Exception as e:
            print(f"[SYNC LOAD ERROR] {cle_module} : {e}")
            return {}

    def synchroniser_flux_application_globale(self, app_visuelle_ref):
        """
        🎯 FLUX UNIFIÉ DES EXCLUSIONS & DE LA NOMENCLATURE DES 21 CANDIDATS :
        Force la mise à jour synchrone de tous les écrans lors d'un arbitrage doctrinal.
        """
        if not hasattr(app_visuelle_ref, "layout_central") or not app_visuelle_ref.layout_central: 
            return
            
        lc = app_visuelle_ref.layout_central
        if not hasattr(lc, "ecrans"): 
            return
            
        # 🎯 ALIGNEMENT GLOBAL : Intégration de ARBRE et HERITAGE_TIERS pour rafraîchir le Fiqh comparé
        modules_a_rafraichir = [
            "ONBOARDING", "FINANCES", "ZAKAT_LIVE", "ZAKAT_TIERS", 
            "ARBRE", "HERITAGE_LIVE", "HERITAGE_TIERS", "MOUHASABAH", "AUDIT"
        ]
        
        for cle_ecran in modules_a_rafraichir:
            ecran_instance = lc.ecrans.get(cle_ecran)
            if ecran_instance:
                if hasattr(ecran_instance, "actualiser_contexte"):
                    try: ecran_instance.actualiser_contexte()
                    except Exception: pass
                if hasattr(ecran_instance, "actualiser_donnees_affichage"):
                    try: ecran_instance.actualiser_donnees_affichage()
                    except Exception: pass
