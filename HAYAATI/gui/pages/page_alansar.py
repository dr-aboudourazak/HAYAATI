"""
ÉCRAN AL-ANSÂR (GUI/PAGES/PAGE_ALANSAR.PY)
Héberge le module Al Ansâr (annuaire, cours, mosquées proches, Hadj et Omra),
écrit en Flutter natif et fourni par l'extension hayaati-alnsar.

Ce que fait cette page, et rien de plus :
  • transmettre au module la langue, les textes traduits (section « al_ansar »
    des fichiers de langue), la dernière position connue de HAYAATI et un
    raccourci vers l'écran Madrassa ;
  • recevoir l'ouverture d'un écran de l'hôte et la profondeur de navigation
    du module, pour que le bouton « retour » d'Android reste cohérent.
La position GPS n'est jamais redemandée ici : le module relève lui-même la
position quand l'utilisateur choisit « Autour de moi ».
"""
from __future__ import annotations

import flet as ft

from gui.langues import DICTIONNAIRE_LANGUES

try:
    from hayaati_alnsar import HayaatiAlAnsar
except Exception as _exc:  # extension non installée : la page affiche un message clair
    HayaatiAlAnsar = None
    _ERREUR_IMPORT = _exc
else:
    _ERREUR_IMPORT = None

# Adresse où sont publiés manifest.json, annuaire_XX.json et mosquees_XX.json
# (terminée par « / »). Vide : le module n'utilise que les données embarquées.
URL_DONNEES_AL_ANSAR = ""

# Pays d'origine par défaut ; le module bascule seul vers le pays de la position GPS
# quand le manifeste est disponible.
PAYS_PAR_DEFAUT = "TG"

# À mettre à False pour la publication : les fiches « brouillon » et les fiches
# d'exemple ne s'affichent alors plus.
MODE_DEMO_AL_ANSAR = True


def _sans_emoji(libelle: str) -> str:
    """« 🏫 Madrassa » -> « Madrassa »."""
    parties = (libelle or "").split(" ", 1)
    return parties[1] if len(parties) == 2 and not parties[0].isalnum() else (libelle or "")


def _derniere_position():
    """Dernière position réelle connue de HAYAATI (même cache que les heures de prière)."""
    try:
        from core.agenda_engine import _charger_position_persistee
        p = _charger_position_persistee()
        if p and "lat" in p and "lon" in p:
            return float(p["lat"]), float(p["lon"])
    except Exception:
        pass
    return None, None


class PageAlAnsar(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.page_flet = app_reference.page
        self._profondeur = 0
        self.module = None

        if HayaatiAlAnsar is None:
            contenu = ft.Column(
                [ft.Text("Al-Ansâr n'est pas disponible dans cette version de l'application.", size=14),
                 ft.Text(f"Détail : {_ERREUR_IMPORT}", size=11, color="#6b7280")],
                alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        else:
            dic = DICTIONNAIRE_LANGUES.actif or {}
            menu = dic.get("menu", {})
            lat, lon = _derniere_position()
            self.module = HayaatiAlAnsar(
                expand=True,
                base_url=URL_DONNEES_AL_ANSAR,
                langue=str(dic.get("code_langue", "FR")).lower(),
                pays=PAYS_PAR_DEFAUT,
                latitude=lat,
                longitude=lon,
                mode_demo=MODE_DEMO_AL_ANSAR,
                on_ouvrir_hote=self._ouvrir_ecran_hote,
                on_profondeur=self._maj_profondeur,
            )
            self.module.definir_textes(dic.get("al_ansar", {}))
            self.module.definir_raccourcis([
                {"cle": "MADRASSA", "titre": _sans_emoji(menu.get("madrassa_hub", "🏫 Madrassa")), "icone": "school"},
            ])
            contenu = self.module

        super().__init__(content=contenu, expand=True, bgcolor=ft.Colors.WHITE, padding=0)

    # --- Événements venus du module -----------------------------------------
    def _ouvrir_ecran_hote(self, e):
        cle = str(getattr(e, "data", "") or "").strip()
        if cle:
            try:
                self.app.basculer_ecran(cle)
            except Exception as exc:
                print(f"[AL-ANSÂR] Ouverture de l'écran {cle} impossible : {exc}")

    def _maj_profondeur(self, e):
        try:
            self._profondeur = int(float(getattr(e, "data", 0) or 0))
        except (TypeError, ValueError):
            self._profondeur = 0

    # --- Bouton « retour » matériel -------------------------------------------
    async def gerer_retour(self) -> bool:
        """Vrai si le module a consommé le retour (il revient d'un écran interne)."""
        if self.module is not None and self._profondeur > 0:
            try:
                await self.module.retour()
                return True
            except Exception as exc:
                print(f"[AL-ANSÂR] Retour interne impossible : {exc}")
        return False

    def actualiser_donnees_affichage(self):
        """Rien à reconstruire : le module Flutter garde son propre état."""
        return None
