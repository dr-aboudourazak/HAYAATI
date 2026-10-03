"""
SERVICE D'ENVOI DES AVIS UTILISATEURS (CORE/FEEDBACK_SERVICE.PY)
Version 1.0 — 01/10/2026

Logique pure Python, sans dépendance à Flet (testable séparément).

Deux canaux, tous deux configurés dans core/config_privee.py (fichier ignoré
par Git, voir config_privee_exemple.py) :

  1. En ligne : envoi silencieux vers un Google Form. Ne demande rien à
     l'utilisateur et fonctionne même si WhatsApp n'est pas installé.
  2. WhatsApp : lien wa.me avec message pré-rempli.

Les deux canaux sont tentés à chaque envoi (voir page_reglages.py) ; chacun
échoue silencieusement s'il est indisponible.

Aucun identifiant interne, e-mail ni nom d'utilisateur n'est transmis :
uniquement la note, la langue de l'app, la plateforme et le texte saisi.
"""
from __future__ import annotations

import asyncio
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

# Au-delà d'environ 1000 caractères, certains appareils tronquent ou
# refusent un lien wa.me ; on coupe donc proprement avant.
LIMITE_MESSAGE = 1000
DELAI_ENVOI_SECONDES = 8


def _config() -> dict:
    """Lit core/config_privee.py s'il existe. Aucune erreur s'il manque :
    les canaux sont alors simplement désactivés."""
    try:
        from core import config_privee as cfg  # type: ignore
    except Exception:
        return {"whatsapp": "", "url": "", "champs": {}}
    return {
        "whatsapp": "".join(ch for ch in str(getattr(cfg, "NUMERO_WHATSAPP_FEEDBACK", "")) if ch.isdigit()),
        "url": str(getattr(cfg, "FORMULAIRE_FEEDBACK_URL", "") or "").strip(),
        "champs": dict(getattr(cfg, "FORMULAIRE_FEEDBACK_CHAMPS", {}) or {}),
    }


def canal_en_ligne_disponible() -> bool:
    c = _config()
    return c["url"].startswith("https://docs.google.com/forms/") and any(c["champs"].values())


def canal_whatsapp_disponible() -> bool:
    return bool(_config()["whatsapp"])


def _tronquer(texte: str) -> str:
    texte = texte.strip()
    if len(texte) > LIMITE_MESSAGE:
        return texte[:LIMITE_MESSAGE - 1].rstrip() + "…"
    return texte


def construire_message(note: int, langue: str, plateforme: str, commentaire: str) -> str:
    """Message en français quelle que soit la langue de l'app, pour rester
    lisible côté réception."""
    return (
        f"Hayaati - Avis {note}/5 ★\n"
        f"Langue : {langue} | Plateforme : {plateforme}\n\n"
        f"{_tronquer(commentaire)}"
    )


def construire_lien_whatsapp(message: str) -> str | None:
    numero = _config()["whatsapp"]
    if not numero:
        return None
    return f"https://wa.me/{numero}?text={quote(message, safe='')}"


def _envoyer_formulaire_sync(note: int, langue: str, plateforme: str, commentaire: str) -> bool:
    c = _config()
    valeurs = {
        "note": str(note),
        "langue": langue,
        "plateforme": plateforme,
        "message": _tronquer(commentaire),
    }
    donnees = {c["champs"][cle]: val for cle, val in valeurs.items() if c["champs"].get(cle)}
    if not donnees or not c["url"].startswith("https://docs.google.com/forms/"):
        return False
    try:
        requete = Request(
            c["url"],
            data=urlencode(donnees).encode("utf-8"),
            headers={"User-Agent": "Hayaati-Feedback/1.0"},
            method="POST",
        )
        with urlopen(requete, timeout=DELAI_ENVOI_SECONDES) as reponse:
            return 200 <= int(reponse.status) < 400
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        # Visible dans adb logcat : permet de distinguer un problème de
        # certificat (Android) d'un simple manque de réseau.
        print(f"[FEEDBACK] Envoi en ligne impossible : {type(exc).__name__}: {exc}")
        return False


async def envoyer_en_ligne(note: int, langue: str, plateforme: str, commentaire: str) -> bool:
    """Envoi hors du fil de l'interface (to_thread) : l'écran ne se fige pas
    pendant la requête réseau. Retourne True si le formulaire a accepté l'avis."""
    return await asyncio.to_thread(_envoyer_formulaire_sync, note, langue, plateforme, commentaire)
