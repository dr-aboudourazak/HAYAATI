"""
AFFICHAGE PARTAGÉ DES RÉSULTATS ZAKAT (GUI/COMPONENTS/ZAKAT_AFFICHAGE.PY)
Version 3.0 - 05/10/2026

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


def creer_cellule_irrigation(label: ft.Text, menu: ft.Dropdown, aide, col: dict) -> list:
    """Retourne la liste des cellules à insérer dans la grille : [cellule du menu], ou
    [cellule du menu, cellule d'aide] si un texte d'aide est fourni (plus utilisé : aide=None)."""
    cellules = [ft.Container(content=ft.Column([label, menu], spacing=4), col=col)]
    if aide is not None:
        cellules.append(ft.Container(content=aide, col={"xs": 12}, padding=ft.Padding(left=2, top=0, right=2, bottom=2)))
    return cellules


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


def _modele(txt_zk: dict, cle: str, defaut: str, n: int) -> str:
    return str(txt_zk.get(cle, defaut)).replace("{n}", str(n))


def _assembler(parties: list[str]) -> str:
    return " + ".join(parties)


def _texte_bovins(b: dict, txt_zk: dict) -> str:
    parties = []
    if b.get("tabi"):
        parties.append(_modele(txt_zk, "bovins_tabi_n", "{n} Tabi' (veau d'un an)", b["tabi"]))
    if b.get("musinna"):
        parties.append(_modele(txt_zk, "bovins_musinna_n", "{n} Musinna (vache de 2 ans)", b["musinna"]))
    return _assembler(parties)


def libelle_bovins(res: dict, txt_zk: dict) -> str:
    """Obligation sur les bovins, traduite. Barème complet (30-39, 40-59, puis une tabi' par 30 et une
    musinna par 40) ; une autre combinaison valable est indiquée avec « ou »."""
    b = res.get("bovins_dus")
    if isinstance(b, dict):
        texte = _texte_bovins(b, txt_zk)
        if not texte:
            return str(txt_zk.get("exempt", "Exempté"))
        alt = [(t, m) for t, m in b.get("alternatives", [])]
        if alt:
            ou = str(txt_zk.get("ou_alternative", "ou"))
            autres = " ; ".join(_texte_bovins({"tabi": t, "musinna": m}, txt_zk) for t, m in alt)
            texte += f" ({ou} {autres})"
        return texte
    code = res.get("code_obligation_bovins", 0)       # repli : ancien format
    if code == 1:
        return str(txt_zk.get("bovins_1", "1 Tabi (1 an)"))
    if code == 2:
        return str(txt_zk.get("bovins_2", "1 Musinnah (2 ans)"))
    if code == 3:
        return str(txt_zk.get("bovins_3", "2 Tabis"))
    return str(txt_zk.get("exempt", "Exempté"))


_CHAMEAUX = (
    ("brebis", "chameau_brebis_n", "{n} brebis"),
    ("bint_makhad", "chameau_bint_makhad_n", "{n} bint makhad (chamelle d'1 an)"),
    ("bint_labun", "chameau_bint_labun_n", "{n} bint labun (chamelle de 2 ans)"),
    ("hiqqa", "chameau_hiqqa_n", "{n} hiqqa (chamelle de 3 ans)"),
    ("jadha", "chameau_jadha_n", "{n} jadha'a (chamelle de 4 ans)"),
)


def _texte_chameaux(c: dict, txt_zk: dict) -> str:
    return _assembler([_modele(txt_zk, cle, defaut, c[k]) for k, cle, defaut in _CHAMEAUX if c.get(k)])


def libelle_chameaux(res: dict, txt_zk: dict) -> str:
    """Obligation sur les chameaux, traduite (barème des quatre écoles)."""
    c = res.get("chameaux_dus")
    if not isinstance(c, dict):
        return str(txt_zk.get("exempt", "Exempté"))
    texte = _texte_chameaux(c, txt_zk)
    if not texte:
        return str(txt_zk.get("exempt", "Exempté"))
    alt = c.get("alternatives") or []
    if alt:
        ou = str(txt_zk.get("ou_alternative", "ou"))
        texte += f" ({ou} " + " ; ".join(_texte_chameaux(a, txt_zk) for a in alt) + ")"
    return texte


def notes_zakat(res: dict, txt_zk: dict, dev: str) -> list[str]:
    """Rappels propres au cas calculé : hawl, déduction des dettes selon l'école, nisab agricole hanafite,
    conditions de l'élevage. Une note n'apparaît que si elle concerne la situation saisie."""
    t = txt_zk or {}
    notes: list[str] = []

    statut = res.get("hawl_statut")
    if statut == "en_cours":
        notes.append(str(t.get("hawl_en_cours",
                               "⏳ Année lunaire non accomplie : zakat monétaire de {montant} exigible à partir du {date}."))
                     .replace("{montant}", f"{float(res.get('zakat_monetaire_a_terme', 0.0)):.2f} {dev}")
                     .replace("{date}", str(res.get("hawl_echeance", ""))))
    elif statut == "date_invalide":
        notes.append(str(t.get("hawl_date_invalide",
                               "⚠️ Date du hawl invalide (format AAAA-MM-JJ, date passée) : une année lunaire complète est supposée.")))
    elif statut == "non_precise" and res.get("est_imposable_monetaire"):
        notes.append(str(t.get("hawl_non_precise",
                               "ℹ️ Date du hawl non renseignée : une année lunaire complète est supposée.")))

    if float(res.get("dettes_saisies", 0.0) or 0.0) > 0 or float(res.get("dettes_long_terme_exclues", 0.0) or 0.0) > 0:
        regime = res.get("regime_deduction_dettes")
        if regime == "aucune":
            notes.append(str(t.get("note_dettes_aucune",
                                   "ℹ️ Selon votre école (chafi'ite), les dettes ne sont pas déduites de l'assiette de la Zakat.")))
        elif regime == "gens_et_dieu":
            notes.append(str(t.get("note_dettes_gens_dieu",
                                   "ℹ️ Selon votre école (hanbalite), les dettes exigibles dans l'année sont déduites, y compris les dettes envers Dieu (kaffara, zakat impayée...). Les dettes à long terme saisies sont exclues.")))
        elif regime == "gens":
            notes.append(str(t.get("note_dettes_gens",
                                   "ℹ️ Seules les dettes exigibles dans l'année sont déduites ; les dettes à long terme saisies sont exclues.")))

    if res.get("madhhab_applique") == "Hanafite" and float(res.get("poids_recolte_kg", 0.0) or 0.0) > 0:
        notes.append(str(t.get("note_agri_hanafite",
                               "ℹ️ Selon l'école hanafite, la dîme agricole est due dès le premier kilogramme (pas de nisab de 653 kg).")))

    elevage = sum(int(res.get(k, 0) or 0) for k in ("brut_ovins", "brut_bovins", "brut_chameaux"))
    if elevage > 0:
        notes.append(str(t.get("note_elevage",
                               "ℹ️ Cheptel : la Zakat est due si l'animal est possédé depuis une année lunaire et pâture librement la majeure partie de l'année (sâ'ima).")))
    if res.get("madhhab_applique") == "Hanafite" and int(res.get("brut_chameaux", 0) or 0) > 120:
        notes.append(str(t.get("note_chameaux_hanafite",
                               "ℹ️ Au-delà de 120 chameaux, l'école hanafite reprend le barème depuis le début.")))
    return notes


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
