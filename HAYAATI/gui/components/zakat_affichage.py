"""
AFFICHAGE PARTAGÉ DES RÉSULTATS ZAKAT (GUI/COMPONENTS/ZAKAT_AFFICHAGE.PY)
Version 2.0 - 04/10/2026

Fonctions communes aux écrans Finances, Zakat Live et Zakat Tiers : libellés de l'élevage,
taux agricole, mode d'irrigation (liste déroulante au style des champs de saisie) et
actualisation des cours de l'or et de l'argent en ligne (saisie manuelle toujours possible).
"""
from __future__ import annotations

import asyncio

import flet as ft

MODES_IRRIGATION = ("pluie", "artificielle", "mixte")

_DEFAUT_IRRIGATION = {
    "pluie": "🌧️ Pluie (10 %)",
    "artificielle": "🚰 Artificielle (5 %)",
    "mixte": "🌧️🚰 Mixte (7,5 %)",
}


def libelle_irrigation(mode: str, txt_fin: dict) -> str:
    """Texte traduit d'un mode d'irrigation (clé technique : pluie / artificielle / mixte)."""
    mode = mode if mode in MODES_IRRIGATION else "pluie"
    return str((txt_fin or {}).get(f"irrigation_{mode}", _DEFAUT_IRRIGATION[mode]))


def creer_menu_irrigation(hauteur: int = 40, taille_texte: int = 13) -> ft.Dropdown:
    """Liste déroulante de l'irrigation, au même gabarit et aux mêmes couleurs que les champs de saisie."""
    return ft.Dropdown(
        value="pluie", height=hauteur, text_size=taille_texte, dense=True,
        filled=True, fill_color=ft.Colors.WHITE,
        border_width=1, border_color=ft.Colors.GREY_400, border_radius=6,
        focused_border_color="#064e3b",
        content_padding=ft.Padding(left=10, top=0, right=10, bottom=0),
        expanded_insets=ft.Padding(left=0, top=0, right=0, bottom=0),
        options=[ft.dropdown.Option(key=m, text=libelle_irrigation(m, {})) for m in MODES_IRRIGATION],
    )


def creer_cellule_irrigation(label: ft.Text, menu: ft.Dropdown, aide: ft.Text, col: dict) -> list:
    """Retourne [cellule du menu, cellule d'aide pleine largeur] à insérer dans la grille.
    L'aide est dans une cellule à part : elle ne peut plus être recouverte par la liste."""
    return [
        ft.Container(content=ft.Column([label, menu], spacing=4), col=col),
        ft.Container(content=aide, col={"xs": 12}, padding=ft.Padding(left=2, top=0, right=2, bottom=2)),
    ]


def suffixe_taux(taux_pct) -> str:
    """' (10 %)' / ' (7,5 %)' ; chaîne vide si aucune zakat agricole n'est due."""
    try:
        t = float(taux_pct or 0.0)
    except (TypeError, ValueError):
        return ""
    if t <= 0:
        return ""
    texte = f"{t:g}".replace(".", ",")
    return f" ({texte} %)"


def libelle_ovins(res: dict, txt_zk: dict) -> str:
    """Obligation sur les ovins, traduite. Gère les troupeaux de plus de 399 têtes."""
    n = int(res.get("ovins_dus", 0) or 0)
    if n > 3:
        return str(txt_zk.get("ovins_n", "{n} brebis dues")).replace("{n}", str(n))
    code = res.get("code_obligation_ovins", 0)
    if code == 1:
        return str(txt_zk.get("ovins_1", "1 brebis due"))
    if code == 2:
        return str(txt_zk.get("ovins_2", "2 brebis dues"))
    if code == 3:
        return str(txt_zk.get("ovins_3", "3 brebis dues"))
    return str(txt_zk.get("exempt", "Exempté"))


def libelle_bovins(res: dict, txt_zk: dict) -> str:
    """Obligation sur les bovins, traduite (codes calculés par FinancialEngine)."""
    code = res.get("code_obligation_bovins", 0)
    if code == 1:
        return str(txt_zk.get("bovins_1", "1 Tabi (1 an)"))
    if code == 2:
        return str(txt_zk.get("bovins_2", "1 Musinnah (2 ans)"))
    if code == 3:
        return str(txt_zk.get("bovins_3", "2 Tabis"))
    return str(txt_zk.get("exempt", "Exempté"))


# ----------------------------------------------------------------------------
# COURS DE L'OR ET DE L'ARGENT EN LIGNE
# ----------------------------------------------------------------------------
def _maj(ecran) -> None:
    try:
        ecran.update()
    except Exception:
        pass


def appliquer_cours(resultat, champ_or, champ_argent, lbl_etat, txt_fin: dict, dev: str) -> bool:
    """Écrit les cours reçus dans les champs de saisie (modifiables ensuite) et affiche l'état."""
    from core.prix_metaux import MENTION_SOURCES
    if resultat:
        champ_or.value = f"{resultat['or']:.2f}"
        champ_argent.value = f"{resultat['argent']:.2f}"
        modele = str(txt_fin.get("cours_maj_ok", "✓ Cours mis à jour : or {or}, argent {argent} {devise}/g ({date})"))
        ligne = (modele.replace("{or}", champ_or.value).replace("{argent}", champ_argent.value)
                 .replace("{devise}", str(dev)).replace("{date}", str(resultat.get("date", ""))[:10]))
        lbl_etat.value = ligne + "\n" + str(txt_fin.get("cours_attribution", MENTION_SOURCES))
        lbl_etat.color = "#064e3b"
        return True
    lbl_etat.value = str(txt_fin.get("cours_maj_echec", "⚠️ Connexion impossible : saisissez les cours à la main."))
    lbl_etat.color = "#b45309"
    return False


async def actualiser_cours_en_ligne(ecran, champ_or, champ_argent, lbl_etat, txt_fin: dict, dev: str) -> bool:
    """Interroge les services en ligne hors du fil de l'interface, puis remplit les champs.
    En cas d'échec, les valeurs saisies à la main sont conservées."""
    from core.prix_metaux import obtenir_cours_gramme
    lbl_etat.value = str(txt_fin.get("cours_en_cours", "⏳ Récupération des cours..."))
    lbl_etat.color = "#6b7280"
    _maj(ecran)
    try:
        resultat = await asyncio.to_thread(obtenir_cours_gramme, dev)
    except Exception:
        resultat = None
    ok = appliquer_cours(resultat, champ_or, champ_argent, lbl_etat, txt_fin, dev)
    _maj(ecran)
    return ok
