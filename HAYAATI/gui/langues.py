""" ROUTEUR ET CHARGEUR DYNAMIQUE MULTILINGUE (GUI/LANGUES.PY) - Flet 0.86+ """
from __future__ import annotations
import os
import json
import sys

class GestionnaireLangues:
    def __init__(self):
        self.langue_courante = "FR"
        self.cache_dictionnaire: dict = {}
        self.callbacks_mise_a_jour: list = []  
        self.langues_disponibles_index: dict[str, str] = {}
        
        # 🎯 CONFIGURATION DES CHEMINS ABSOLUS (Android APK & PyInstaller Windows)
        if hasattr(sys, '_MEIPASS'):
            self.chemin_dictionnaires = os.path.join(sys._MEIPASS, "assets", "locales")
        else:
            # Calcule de façon robuste le chemin à partir de la racine du projet
            racine_projet = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.chemin_dictionnaires = os.path.join(racine_projet, "assets", "locales")
        
        self.scanner_dossier_dictionnaires_physiques()
        self.charger_dictionnaire_langue("FR")

    def scanner_dossier_dictionnaires_physiques(self):
        """Scanne le stockage et extrait proprement le code brut (String) et le nom natif de vos langues."""
        if not os.path.exists(self.chemin_dictionnaires):
            try: os.makedirs(self.chemin_dictionnaires)
            except Exception: pass

        if os.path.exists(self.chemin_dictionnaires):
            files = [f for f in os.listdir(self.chemin_dictionnaires) if f.endswith(".json")]
            for nom_fichier in files:
                # 🎯 RECTIFICATION DIRECTE ET NETTOYAGE CHIRURGICAL :
                # Au lieu de stocker le tuple complexe, on extrait uniquement le nom pur (ex: 'fr')
                nom_pur_sans_extension = nom_fichier.split(".")[0]
                code = str(nom_pur_sans_extension).strip().upper()  # Devient 'FR', 'AR', 'EN', etc.
                
                chemin_complet = os.path.join(self.chemin_dictionnaires, nom_fichier)
                try:
                    with open(chemin_complet, "r", encoding="utf-8") as f:
                        donnees = json.load(f)
                        bo = donnees.get("barre_outils", {})
                        nom_natif = bo.get("nom_langue_natif", donnees.get("nom_langue", code))
                        
                        # Stockage propre : Clé 'FR' (String) -> Valeur 'Français' (String)
                        self.langues_disponibles_index[code] = str(nom_natif).strip()
                except Exception: 
                    pass

        if not self.langues_disponibles_index:
            self.langues_disponibles_index["FR"] = "Français"

    def charger_dictionnaire_langue(self, code_langue: str) -> dict:
        """Charge un dictionnaire en mémoire et notifie l'arbre de composants Flet."""
        code = str(code_langue).strip().upper()
        nom_fichier = f"{code.lower()}.json"
        chemin_complet = os.path.join(self.chemin_dictionnaires, nom_fichier)
        # ⚠️ DIAGNOSTIC 12/09/2026 : trace inconditionnelle. Le bandeau ET
        # plusieurs pages restent figés en français après un changement de
        # langue — avant de corriger une page en particulier, il faut
        # savoir si cette fonction racine est même appelée avec le bon
        # code, si le fichier est trouvé, et combien d'abonnés sont notifiés.
        print(f"[I18N][DIAG] charger_dictionnaire_langue appelé avec code_langue={code_langue!r} -> code={code!r}, chemin={chemin_complet}, existe={os.path.exists(chemin_complet)}, nb_abonnes={len(self.callbacks_mise_a_jour)}")

        try:
            if os.path.exists(chemin_complet):
                with open(chemin_complet, "r", encoding="utf-8") as f:
                    self.cache_dictionnaire = json.load(f)
                    self.langue_courante = code
                    self._notifier_les_interfaces()
                    return self.cache_dictionnaire
            
            # Repli de secours sur le Français si la langue demandée est absente
            if code != "FR": 
                return self.charger_dictionnaire_langue("FR")
        except Exception:
            if code != "FR": 
                return self.charger_dictionnaire_langue("FR")
                
        # Sécurité ultime : dictionnaire d'urgence si aucun fichier n'est lisible
        self.cache_dictionnaire = self._generer_dictionnaire_urgence_minimal()
        self._notifier_les_interfaces()
        return self.cache_dictionnaire

    def abonner_au_changement_langue(self, fonction_callback):
        """Permet aux composants graphiques Flet d'écouter les bascules linguistiques."""
        if fonction_callback not in self.callbacks_mise_a_jour:
            self.callbacks_mise_a_jour.append(fonction_callback)

    def _notifier_les_interfaces(self):
        """Propage le nouveau dictionnaire chargé à tous les abonnés."""
        succes, echecs = 0, 0
        for callback in self.callbacks_mise_a_jour:
            try: 
                callback(self.cache_dictionnaire)
                succes += 1
            except Exception as exc:
                echecs += 1
                # ⚠️ DIAGNOSTIC 12/09/2026 : auparavant "except Exception: pass"
                # — un abonné qui plante en silence est indiscernable d'un
                # abonné qui n'existe simplement pas. On log maintenant
                # lequel (nom de la méthode liée) et pourquoi.
                nom_abonne = getattr(callback, "__qualname__", repr(callback))
                print(f"[I18N][DIAG] Abonné {nom_abonne} a échoué : {exc}")
        print(f"[I18N][DIAG] _notifier_les_interfaces : {succes} succès, {echecs} échec(s), {len(self.callbacks_mise_a_jour)} abonné(s) au total")

    def _generer_dictionnaire_urgence_minimal(self) -> dict:
        """Évite les crashs de type KeyError si les assets sont temporairement inaccessibles."""
        return {
            "nom_langue": "Français",
            "menu": {
                "onboarding": "🏠 Accueil", "finances": "💰 Patrimoine", "zakat": "🏦 Zakat Live",
                "arbre": "👥 Famille", "heritage": "📜 Succession Live", "mouhasabah": "📿 Mouhasabah", 
                "reglages": "⚙️ Réglages", "profil": "👤 Profil"
            },
            "barre_outils": {
                "titre_app": "HAYAATI", "mode_live": "🟢 Live", "mode_tiers": "🟡 Tiers", "btn_deconnexion": "🚪 Déconnexion",
                "visiteur": "👤 Visiteur", "ecoles": {"Malikite": "Malikite", "Hanafite": "Hanafite", "Chafiite": "Chafi'ite", "Hanbalite": "Hanbalite"}
            },
            "auth": {
                "titre_connexion": "Connexion", "titre_inscription": "Configuration Initiale de Hayaati",
                "user_lbl": "Identifiant :", "pass_lbl": "Mot de passe :", "btn_soumettre": "Valider et installer",
                "pas_compte": "S'inscrire", "deja_compte": "Se connecter", "cadre_legal": "📜 Homologation & Conseils", 
                "message_bienvenue_doctrinal": "Bienvenue sur Hayaati.",
                "err_champs_vides": "❌ Champs vides.", "err_connexion": "❌ Identifiants incorrects."
            },
            "onboarding": {
                "bienvenue": "Assalâmou Alaykoum, {} 🌟",
                "sous_titre": "Rapport de vigilance doctrinale — École {}",
                "guide_visiteur_humain": "Mode Simulation Tiers actif. Connectez-vous pour un suivi personnalisé."
            },
            "reglages": {
                "cadre_pref": "Préférences", "lbl_guide_langue": "Veuillez choisir la langue principale de l'application", "btn_sauver_pref": "Enregistrer"
            },
            "heritage": { "rapport_succession": "RAPPORT DE SUCCESSION", "candidats": {} }
        }

class MatriceDictionnairesMiroir(dict):
    """ proxy dictionnaire pour garder une syntaxe d'accès transparente """
    def __init__(self):
        super().__init__()
        self.moteur_i18n = GestionnaireLangues()
        
    # 🎯 FIX TECHNIQUE CRITIQUE PROXY : Extraction depuis le cache actif réel pour stopper la boucle infinie
    def __getitem__(self, item): 
        return self.moteur_i18n.cache_dictionnaire.get(item)
        
    def get(self, item, default=None): 
        return self.moteur_i18n.cache_dictionnaire.get(item, default)
        
    @property
    def actif(self) -> dict: 
        return self.moteur_i18n.cache_dictionnaire
        
    @property
    def disponibles(self) -> dict[str, str]: 
        return self.moteur_i18n.langues_disponibles_index

# Instance globale à importer à travers l'application
DICTIONNAIRE_LANGUES = MatriceDictionnairesMiroir()
