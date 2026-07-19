"""
ROUTEUR ET CHARGEUR DYNAMIQUE MULTILINGUE (GUI/LANGUES.PY)
Version 9.0 - Scan et indexation automatique des fichiers JSON du disque.
"""
import os
import json

class GestionnaireLangues:
    def __init__(self):
        self.langue_courante = "FR"
        self.chemin_dictionnaires = os.path.join("gui", "dictionnaires")
        self.cache_dictionnaire = {}
        self.callbacks_mise_a_jour = []  
        self.langues_disponibles_index = {} # Index dynamique (Ex: {"ENGLISH": "English"})
        
        self.scanner_dossier_dictionnaires_physiques()
        self.charger_dictionnaire_langue("FR")

    def scanner_dossier_dictionnaires_physiques(self):
        """Scanne le dossier et extrait le nom natif de chaque langue présente."""
        if not os.path.exists(self.chemin_dictionnaires):
            os.makedirs(self.chemin_dictionnaires)

        files = [f for f in os.listdir(self.chemin_dictionnaires) if f.endswith(".json")]
        for nom_fichier in files:
            # Extrait le nom exact du fichier sans extension pour en faire la clé technique
            code = os.path.splitext(nom_fichier)[0].upper() # Ex: "ENGLISH"
            chemin_complet = os.path.join(self.chemin_dictionnaires, nom_fichier)
            try:
                with open(chemin_complet, "r", encoding="utf-8") as f:
                    donnees = json.load(f)
                    self.langues_disponibles_index[code] = donnees.get("nom_langue", code)
            except Exception: pass

        if not self.langues_disponibles_index:
            self.langues_disponibles_index["FR"] = "Français"

    def charger_dictionnaire_langue(self, code_langue):
        """Lit le fichier JSON correspondant sur le disque et alerte les interfaces."""
        code = str(code_langue).strip().upper()
        nom_fichier = f"{code.lower()}.json"
        chemin_complet = os.path.join(self.chemin_dictionnaires, nom_fichier)

        try:
            if os.path.exists(chemin_complet):
                with open(chemin_complet, "r", encoding="utf-8") as f:
                    self.cache_dictionnaire = json.load(f)
                    self.langue_courante = code
                    self._notifier_les_interfaces()
                    return self.cache_dictionnaire
            
            if code != "FR":
                print(f"[I18N WARNING] Fichier {nom_fichier} introuvable. Repli sur le Français.")
                return self.charger_dictionnaire_langue("FR")
                
        except Exception as e:
            print(f"[I18N CRITICAL ERROR] Erreur lecture {nom_fichier} : {str(e)}")
            if code != "FR": return self.charger_dictionnaire_langue("FR")
                
        self.cache_dictionnaire = self._generer_dictionnaire_urgence_minimal()
        self._notifier_les_interfaces()
        return self.cache_dictionnaire

    def abonner_au_changement_langue(self, fonction_callback):
        if fonction_callback not in self.callbacks_mise_a_jour:
            self.callbacks_mise_a_jour.append(fonction_callback)

    def _notifier_les_interfaces(self):
        for callback in self.callbacks_mise_a_jour:
            try: callback(self.cache_dictionnaire)
            except Exception: pass

    def _generer_dictionnaire_urgence_minimal(self):
        return {
            "nom_langue": "Français",
            "menu": {
                "onboarding": "🏠 Accueil", "finances": "💰 Patrimoine", "zakat": "🏦 Zakat Live",
                "arbre": "👥 Famille", "heritage": "📜 Succession Live", "mouhasabah": "📿 Mouhasabah", "reglages": "⚙️ Réglages"
            },
            "barre_outils": {
                "titre_app": "🕌 HAYAATI", "mode_live": "🟢 Live", "mode_tiers": "🟡 Tiers", "btn_deconnexion": "🚪 Déconnexion"
            }
        }

class MatriceDictionnairesMiroir(dict):
    def __init__(self):
        super().__init__()
        self.moteur_i18n = GestionnaireLangues()

    def __getitem__(self, item): return self.moteur_i18n.charger_dictionnaire_langue(item)
    def get(self, item, default=None): return self.moteur_i18n.charger_dictionnaire_langue(item)
    
    @property
    def actif(self): return self.moteur_i18n.cache_dictionnaire

DICTIONNAIRE_LANGUES = MatriceDictionnairesMiroir()
