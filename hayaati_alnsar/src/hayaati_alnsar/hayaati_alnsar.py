"""Contrôle Flet du module Al Ansâr de HAYAATI.

Le rendu et la navigation interne sont en Flutter natif (paquet « al_ansar »).
Python ne fait que transmettre les réglages (langue, textes traduits, position
déjà connue de l'application, raccourcis vers d'autres écrans de HAYAATI) et
recevoir deux événements : l'ouverture d'un écran de l'hôte et la profondeur de
la navigation interne (pour le bouton « retour » d'Android).
"""
import json
from typing import Optional

import flet as ft

__all__ = ["HayaatiAlAnsar"]


@ft.control("HayaatiAlAnsar")
class HayaatiAlAnsar(ft.LayoutControl):
    """Module Al Ansâr. À placer dans un conteneur qui occupe tout l'écran."""

    base_url: str = ""
    """Adresse de publication des fichiers (manifest.json, annuaire_XX.json...), terminée par « / »."""

    asset_prefix: str = "packages/hayaati_alnsar/assets/al_ansar/"
    """Dossier des données embarquées, utilisées tant qu'aucune version en ligne n'a été téléchargée."""

    langue: str = "fr"
    """Code de langue de l'interface (fr, en, ar, ha...)."""

    pays: str = "TG"
    """Code ISO du pays d'origine de l'utilisateur."""

    ville_id: Optional[str] = None
    """Identifiant de la ville d'origine, si connue (ex. tg-dapaong)."""

    latitude: Optional[float] = None
    longitude: Optional[float] = None
    """Dernière position connue de HAYAATI (heures de prière). Aucune permission supplémentaire n'est demandée."""

    textes_json: Optional[str] = None
    """Textes de l'interface déjà traduits, sous forme de JSON {clé: texte}."""

    raccourcis_json: Optional[str] = None
    """Raccourcis vers des écrans de l'hôte, JSON [{cle, titre, icone}]."""

    mode_demo: Optional[bool] = True
    """None : suit les données (un fichier marqué `demonstration` affiche ses fiches fictives) ; True : affiche aussi les brouillons ; False : les masque."""

    integre: bool = True
    """Module affiché dans HAYAATI : pas de second bandeau vert, titres discrets."""

    madrassa_json: Optional[str] = None
    """Contenu pédagogique de la langue active (sections madrassa, interface_savoir, encyclopedie, langue_arabe, sciences_islamiques), en JSON."""

    progres_json: Optional[str] = None
    """Progression de l'utilisateur connecté, JSON {JEU_EDUCATIF_PROGRES, LANGUE_ARABE_PROGRES, SCIENCES_ISLAMIQUES_PROGRES}."""

    visiteur: bool = False
    """Aucun utilisateur connecté : la progression n'est pas conservée."""

    ecran_initial: Optional[str] = None
    """« madrassa » : le module s'ouvre directement sur le hub Madrassa."""

    on_sauver_progres: Optional[ft.ControlEventHandler["HayaatiAlAnsar"]] = None
    """La progression d'un module a changé : `e.data` est un JSON {module, donnees} à enregistrer."""

    on_ouvrir_hote: Optional[ft.ControlEventHandler["HayaatiAlAnsar"]] = None
    """L'utilisateur a touché un raccourci : `e.data` contient la clé de l'écran demandé."""

    on_profondeur: Optional[ft.ControlEventHandler["HayaatiAlAnsar"]] = None
    """La profondeur de la navigation interne a changé : `e.data` contient le nombre d'écrans empilés."""

    def definir_textes(self, textes: dict) -> None:
        """Prépare les textes traduits à transmettre au module."""
        self.textes_json = json.dumps(textes or {}, ensure_ascii=False)

    def definir_raccourcis(self, raccourcis: list) -> None:
        """Prépare les raccourcis [{cle, titre, icone}] à afficher sur l'accueil du module."""
        self.raccourcis_json = json.dumps(raccourcis or [], ensure_ascii=False)

    async def retour(self) -> None:
        """Demande au module de revenir d'un écran (bouton « retour » matériel)."""
        await self._invoke_method("retour")
