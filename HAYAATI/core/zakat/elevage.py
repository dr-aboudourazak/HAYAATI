"""
ZAKAT DE L'ELEVAGE : OVINS, BOVINS, CHAMEAUX (CORE/ZAKAT/ELEVAGE.PY)
Version 1.0 - 04/10/2026

Barèmes classiques du Fiqh. Les résultats sont des dictionnaires de nombres d'animaux ; les libellés
traduits sont construits côté interface (gui/components/zakat_affichage.py).

Conditions non modélisées (rappelées dans l'interface) : le cheptel doit avoir été possédé une
année lunaire et avoir brouté librement la majeure partie de l'année (sâ'ima).

Chameaux : barème jusqu'à 120 commun aux quatre écoles. Au-delà de 120 :
  - Malikite, Chafi'ite, Hanbalite : une bint labun par 40 et une hiqqa par 50.
  - Hanafite : le barème reprend depuis le début (2 hiqqa + petit barème), avec un nouveau palier
    à 150, 200, 250... (à faire valider par l'utilisateur).
Bovins : 30-39 : 1 tabi' ; 40-59 : 1 musinna ; puis une tabi' par 30 et une musinna par 40
(plusieurs combinaisons possibles à 120, 150... : la plus courte est proposée en premier).
"""
from __future__ import annotations


def zakat_ovins(nombre) -> int:
    """Nombre de brebis (ou chèvres) dues : 40-120 : 1 ; 121-200 : 2 ; 201-399 : 3 ; ensuite 1 par centaine."""
    n = int(nombre or 0)
    if n < 40:
        return 0
    if n <= 120:
        return 1
    if n <= 200:
        return 2
    if n <= 399:
        return 3
    return n // 100


def _combinaisons(m: int, a_unite: int, b_unite: int):
    """Toutes les paires (a, b) positives avec a*a_unite + b*b_unite == m."""
    sols = []
    for b in range(m // b_unite + 1):
        reste = m - b * b_unite
        if reste % a_unite == 0:
            sols.append((reste // a_unite, b))
    return sols


def zakat_bovins(nombre) -> dict:
    """{'tabi': a, 'musinna': b, 'alternatives': [(a, b), ...]} ; tout à 0 sous 30 têtes."""
    n = int(nombre or 0)
    if n < 30:
        return {"tabi": 0, "musinna": 0, "alternatives": []}
    if n <= 39:
        return {"tabi": 1, "musinna": 0, "alternatives": []}
    if n <= 59:
        return {"tabi": 0, "musinna": 1, "alternatives": []}
    m = (n // 10) * 10
    sols = sorted(_combinaisons(m, 30, 40), key=lambda ab: (ab[0] + ab[1], -ab[1]))
    a, b = sols[0]
    return {"tabi": a, "musinna": b, "alternatives": sols[1:]}


# Petit barème des chameaux (de 5 à 120), commun aux quatre écoles.
def _petit_bareme_chameaux(n: int) -> dict:
    animaux = {"brebis": 0, "bint_makhad": 0, "bint_labun": 0, "hiqqa": 0, "jadha": 0}
    if n < 5:
        return animaux
    if n <= 24:
        animaux["brebis"] = n // 5            # 5-9 : 1 ; 10-14 : 2 ; 15-19 : 3 ; 20-24 : 4
    elif n <= 35:
        animaux["bint_makhad"] = 1
    elif n <= 45:
        animaux["bint_labun"] = 1
    elif n <= 60:
        animaux["hiqqa"] = 1
    elif n <= 75:
        animaux["jadha"] = 1
    elif n <= 90:
        animaux["bint_labun"] = 2
    else:                                    # 91-120
        animaux["hiqqa"] = 2
    return animaux


def _suite_hanafite(r: int) -> dict:
    """Complément ajouté, chez les Hanafites, au-dessus d'un palier de hiqqa (r = chameaux au-delà du palier)."""
    ajout = {"brebis": 0, "bint_makhad": 0, "bint_labun": 0, "hiqqa": 0, "jadha": 0}
    if r < 5:
        return ajout
    if r <= 24:
        ajout["brebis"] = r // 5
    elif r <= 35:
        ajout["bint_makhad"] = 1
    elif r <= 45:
        ajout["bint_labun"] = 1
    else:
        ajout["hiqqa"] = 1
    return ajout


def zakat_chameaux(nombre, madhhab="Malikite") -> dict:
    """
    {'brebis', 'bint_makhad', 'bint_labun', 'hiqqa', 'jadha', 'alternatives': [dict, ...]}.
    'alternatives' : autres combinaisons valables (ex. 200 : 4 hiqqa ou 5 bint labun).
    """
    n = int(nombre or 0)
    doc = str(madhhab or "").strip().capitalize()
    if n <= 120:
        res = _petit_bareme_chameaux(n)
        res["alternatives"] = []
        return res

    if doc == "Hanafite":
        if n < 150:
            base, reste = 2, n - 120
        else:
            paliers = (n - 150) // 50
            base, reste = 3 + paliers, n - (150 + 50 * paliers)
        res = {"brebis": 0, "bint_makhad": 0, "bint_labun": 0, "hiqqa": base, "jadha": 0}
        for k, v in _suite_hanafite(reste).items():
            res[k] += v
        res["alternatives"] = []
        return res

    # Malikite, Chafi'ite, Hanbalite : une bint labun par 40, une hiqqa par 50
    m = (n // 10) * 10
    sols = sorted(_combinaisons(m, 40, 50), key=lambda ab: (ab[0] + ab[1], -ab[1]))
    a, b = sols[0]
    res = {"brebis": 0, "bint_makhad": 0, "bint_labun": a, "hiqqa": b, "jadha": 0}
    res["alternatives"] = [
        {"brebis": 0, "bint_makhad": 0, "bint_labun": x, "hiqqa": y, "jadha": 0} for x, y in sols[1:]
    ]
    return res
