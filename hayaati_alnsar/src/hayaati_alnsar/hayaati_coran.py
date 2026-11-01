"""Contrôle Flet du module Coran de HAYAATI.

Le rendu, le feuilletage des 604 pages du mushaf et la navigation interne sont en Flutter natif (paquet
« hayaati_coran »). Le texte du Coran est embarqué dans ce paquet : Python ne transmet que la langue, les textes
traduits et l'état de lecture enregistré (réglages, signets, progression), et reçoit deux événements : un changement
d'état de lecture à enregistrer, et la profondeur de la navigation interne (pour le bouton « retour » d'Android).
"""
import json
from typing import Optional

import flet as ft

__all__ = ["HayaatiCoran"]


@ft.control("HayaatiCoran")
class HayaatiCoran(ft.LayoutControl):
    """Module Coran. À placer dans un conteneur qui occupe tout l'écran."""

    langue: str = "fr"
    """Code de langue de l'interface (fr, en, ar, ha...). « ar » : interface de droite à gauche."""

    textes_json: Optional[str] = None
    """Textes de l'interface déjà traduits (section « coran » des fichiers de langue), JSON {clé: texte}."""

    etat_json: Optional[str] = None
    """Contenu de coran_lecture.json (réglages, signets, progression) au moment de la création du module, en JSON."""

    integre: bool = True
    """Module affiché dans HAYAATI : pas de second bandeau vert."""

    on_sauver_etat: Optional[ft.ControlEventHandler["HayaatiCoran"]] = None
    """L'état de lecture a changé : `e.data` est le JSON complet de l'état, à enregistrer."""

    on_profondeur: Optional[ft.ControlEventHandler["HayaatiCoran"]] = None
    """La profondeur de la navigation interne a changé : `e.data` contient le nombre d'écrans empilés."""

    def definir_textes(self, textes: dict) -> None:
        """Prépare les textes traduits à transmettre au module."""
        self.textes_json = json.dumps(textes or {}, ensure_ascii=False)

    def definir_etat(self, etat: dict) -> None:
        """Prépare l'état de lecture à transmettre au module."""
        self.etat_json = json.dumps(etat or {}, ensure_ascii=False)

    async def retour(self) -> None:
        """Demande au module de revenir d'un écran (bouton « retour » matériel)."""
        await self._invoke_method("retour")
