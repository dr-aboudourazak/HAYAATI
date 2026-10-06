"""
COURS DE L'OR ET DE L'ARGENT EN LIGNE (CORE/PRIX_METAUX.PY)
Version 1.0 - 04/10/2026

Fournit le prix du gramme d'or et d'argent dans la devise de l'utilisateur, pour calculer
le nisab de la Zakat. Sans nouvelle dependance (urllib seulement). La saisie manuelle reste
toujours possible : ce module n'est appele que lorsque l'utilisateur appuie sur le bouton.

Sources (gratuites, sans cle) :
  - Cours des metaux (USD par once troy) : https://api.gold-api.com/price/XAU et /XAG
  - Taux de change : https://open.er-api.com/v6/latest/USD
    (ExchangeRate-API, acces ouvert : une mention de la source est exigee -> voir MENTION_SOURCES)
  - Zone CFA (XOF, XAF) : repli sur la parite fixe 655,957 pour 1 euro si le taux n'est pas fourni.

Seuls les symboles des metaux et la devise sont envoyes aux services ; aucune donnee personnelle.
"""
from __future__ import annotations

import json
import time
import urllib.request

GRAMMES_PAR_ONCE_TROY = 31.1034768
PARITE_CFA_PAR_EURO = 655.957
URL_METAL = "https://api.gold-api.com/price/{symbole}"
URL_METAL_EUR = "https://api.gold-api.com/price/{symbole}/EUR"
URL_CHANGE_USD = "https://open.er-api.com/v6/latest/USD"
MENTION_SOURCES = "Cours : gold-api.com · Taux de change : exchangerate-api.com"
DELAI_REQUETE_SECONDES = 6
DUREE_CACHE_SECONDES = 1800

_cache: dict = {}


def _ouvrir_json(url: str) -> dict:
    requete = urllib.request.Request(url, headers={"User-Agent": "Hayaati/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(requete, timeout=DELAI_REQUETE_SECONDES) as reponse:
        return json.loads(reponse.read().decode("utf-8"))


def _prix_usd_once(symbole: str, ouvrir) -> tuple[float, str]:
    data = ouvrir(URL_METAL.format(symbole=symbole))
    prix = float(data["price"])
    if prix <= 0:
        raise ValueError(f"prix {symbole} invalide")
    return prix, str(data.get("updatedAt", ""))


def _taux_depuis_usd(devise: str, ouvrir, prix_usd_or: float) -> float:
    """Nombre d'unites de `devise` pour 1 USD."""
    if devise == "USD":
        return 1.0
    try:
        data = ouvrir(URL_CHANGE_USD)
        taux = float((data.get("rates") or {})[devise])
        if taux > 0:
            return taux
    except Exception:
        pass
    if devise in ("XOF", "XAF"):
        # Repli : or en euros (gold-api) -> euros par dollar -> parite fixe de la zone CFA
        prix_eur = float(ouvrir(URL_METAL_EUR.format(symbole="XAU"))["price"])
        return (prix_eur / prix_usd_or) * PARITE_CFA_PAR_EURO
    raise ValueError(f"taux de change indisponible pour {devise}")


def obtenir_cours_gramme(devise: str, ouvrir=None, maintenant=None):
    """
    Retourne {"or": ..., "argent": ..., "devise": ..., "date": ..., "taux_change": ...} avec les
    prix PAR GRAMME en `devise`, ou None si le reseau ou les services sont indisponibles.
    `ouvrir` (fonction url -> dict) et `maintenant` servent aux tests.
    """
    ouvrir = ouvrir or _ouvrir_json
    horloge = maintenant or time.time
    devise = str(devise or "USD").strip().upper()

    en_cache = _cache.get(devise)
    if en_cache and horloge() - en_cache["_t"] < DUREE_CACHE_SECONDES:
        return {k: v for k, v in en_cache.items() if k != "_t"}

    try:
        usd_or, date_or = _prix_usd_once("XAU", ouvrir)
        usd_argent, _ = _prix_usd_once("XAG", ouvrir)
        taux = _taux_depuis_usd(devise, ouvrir, usd_or)
    except Exception as exc:
        print(f"[PRIX_METAUX] Indisponible ({type(exc).__name__}: {exc})")
        return None

    resultat = {
        "or": round(usd_or / GRAMMES_PAR_ONCE_TROY * taux, 2),
        "argent": round(usd_argent / GRAMMES_PAR_ONCE_TROY * taux, 2),
        "devise": devise,
        "date": date_or,
        "taux_change": taux,
    }
    _cache[devise] = dict(resultat, _t=horloge())
    return resultat


def vider_cache() -> None:
    _cache.clear()
