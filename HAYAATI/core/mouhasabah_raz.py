"""
RAZ QUOTIDIENNE DU SUIVI MOUHASABAH — VÉRIFICATION PROACTIVE
(CORE/MOUHASABAH_RAZ.PY)

Sépare la logique de données (calcul de la journée Sharia en cours,
décision de remise à zéro, persistance) de son affichage, pour qu'elle
puisse tourner en tâche de fond indépendamment de la présence à l'écran
de gui/components/interface_mouhasabah.py.

Historique : jusqu'au 24/09/2026, cette vérification ne se déclenchait
qu'à l'ouverture de l'écran Mouhasabah (EcranMouhasabah.__init__) — la
date de bascule elle-même était (et reste) calculée correctement
(bascule à Fajr - 1h), mais comme rien ne vérifiait en tâche de fond,
la RAZ n'avait lieu qu'au moment où l'utilisateur ouvrait enfin l'écran
ce jour-là — même tard dans la soirée, plutôt qu'au moment réel de la
bascule. Confirmé sans perte de données (la RAZ ne remet à zéro qu'une
fois par journée Sharia, jamais deux fois), mais le déclenchement
tardif n'était pas ce qui était attendu. Ce module ajoute la
vérification proactive périodique, sur le même principe que
core/notification_scheduler.py::boucle_topup_automatique.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Optional

from core.hayaati_task_registry import HayaatiTaskRegistry

CHAMPS_PRIERES = ["fajr", "dhuhr", "asr", "maghrib", "isha"]

# Les jours de jeûne surérogatoire ne sont proposés à l'écran que
# lorsqu'ils tombent réellement dans le calendrier lunaire du moment —
# mais les remettre à zéro inconditionnellement ici ne coûte rien : ça
# signifie juste "pas encore marqué comme jeûné", déjà l'état par
# défaut en leur absence.
CHAMPS_JEUNE_CONNUS = ["ramadan_jeune", "achoura_9", "achoura_10", "neuf_jours", "arafat"]

# Toutes les 15 minutes suffit largement : la fenêtre de bascule
# elle-même fait environ 1h (Fajr - 1h jusqu'à Fajr), pas besoin d'une
# cadence plus fine pour rester réactif au bon moment.
INTERVALLE_VERIFICATION_RAZ_SECONDES: int = 15 * 60


def calculer_date_sharia_actuelle(app) -> str:
    """Même calcul qu'avant (bascule à Fajr - 1h), extrait pour être
    appelable sans instance d'écran Mouhasabah."""
    maintenant = datetime.now()
    heure_fadjr_str = "05:00"
    if getattr(app, "horaires_prieres_aujourdhui", None):
        heure_fadjr_str = app.horaires_prieres_aujourdhui.get("Fajr", "05:00")
    try:
        h_f, m_f = map(int, heure_fadjr_str.split(":"))
        instant_bascule = maintenant.replace(hour=h_f, minute=m_f, second=0, microsecond=0) - timedelta(hours=1)
    except Exception:
        instant_bascule = maintenant.replace(hour=4, minute=0, second=0, microsecond=0)
    if maintenant < instant_bascule:
        return (maintenant - timedelta(days=1)).strftime("%Y-%m-%d")
    return maintenant.strftime("%Y-%m-%d")


def executer_raz_si_necessaire(app) -> Optional[dict]:
    """Exécute la RAZ si la journée Sharia a changé depuis la dernière
    fois, en une seule sauvegarde atomique — ne touche à aucun contrôle
    d'écran. Retourne le dict fraîchement remis à zéro si une RAZ a eu
    lieu, None sinon (déjà fait pour aujourd'hui, mode invité, ou pas
    encore connecté)."""
    if not getattr(app, "est_mode_connecte", False):
        return None
    u_id = getattr(app, "user_id_connecte", None)
    if not u_id or not hasattr(app, "sync_engine"):
        return None

    donnees = app.sync_engine.charger_donnees_module(u_id, "MOUHASABAH") or {}
    derniere_raz = donnees.get("derniere_raz_date", "")
    historique_existant = str(donnees.get("historique", ""))

    date_sharia = calculer_date_sharia_actuelle(app)
    if derniere_raz == date_sharia:
        return None

    print(f"[MOUHASABAH] RAZ déclenchée pour la journée Sharia {date_sharia}")

    donnees_raz = {p: 0 for p in CHAMPS_PRIERES}
    donnees_raz.update({
        "score_spirituel": 0,
        "nawafil": 0,
        "sadaqah": 0,
        # Hadj conservé à vie — on relit la dernière valeur persistée,
        # pas un état d'écran (cette fonction n'en a pas).
        "deja_fait_hadj": donnees.get("deja_fait_hadj", 0),
        "historique": historique_existant,
        "derniere_raz_date": date_sharia,
    })
    for cle in CHAMPS_JEUNE_CONNUS:
        donnees_raz[cle] = 0

    app.sync_engine.executer_sauvegarde_module(u_id, "MOUHASABAH", donnees_raz)
    print("[MOUHASABAH] RAZ persistée en base (sauvegarde unique avec derniere_raz_date).")
    return donnees_raz


def _rafraichir_ecran_si_monte(app, donnees_raz: dict) -> None:
    """Si l'écran Mouhasabah a déjà été construit (visité au moins une
    fois depuis le lancement de l'app — les écrans sont mis en cache,
    pas détruits, voir gui/app_layout.py::ecrans_instances) et qu'il est
    actuellement affiché, répercute la RAZ sur les cases visibles.
    Sans effet, sans erreur, si l'écran n'a jamais été visité ou n'est
    pas affiché en ce moment."""
    layout = getattr(app, "layout_central", None)
    if not layout:
        return
    instance = getattr(layout, "ecrans_instances", {}).get("MOUHASABAH")
    if instance is None or not hasattr(instance, "appliquer_raz_depuis_fond"):
        return
    try:
        instance.appliquer_raz_depuis_fond(donnees_raz)
    except Exception as exc:
        print(f"[MOUHASABAH] Rafraîchissement de l'écran après RAZ proactive a échoué (sans conséquence) : {exc}")


async def boucle_raz_proactive(generation, app):
    """Vérifie toutes les INTERVALLE_VERIFICATION_RAZ_SECONDES (défaut :
    15 min) si la journée Sharia a changé, et exécute la RAZ dès que
    c'est le cas — que l'écran Mouhasabah soit affiché ou non. Lancée
    une seule fois pour toute la durée de vie de l'app (voir
    demarrer_raz_proactive, appelé depuis main.py) ; passe par
    HayaatiTaskRegistry comme toute boucle de fond du projet."""
    canal = "mouhasabah.raz_proactive"
    while HayaatiTaskRegistry.generation_active(canal, generation):
        try:
            donnees_raz = executer_raz_si_necessaire(app)
            if donnees_raz is not None:
                _rafraichir_ecran_si_monte(app, donnees_raz)
        except Exception as exc:
            print(f"[MOUHASABAH] Vérification RAZ proactive a échoué (retentée au prochain cycle) : {exc}")
        await asyncio.sleep(INTERVALLE_VERIFICATION_RAZ_SECONDES)


def demarrer_raz_proactive(app) -> None:
    """À appeler une fois depuis main.py, après le démarrage de l'app."""
    page = getattr(app, "page", None)
    if page:
        HayaatiTaskRegistry.lancer(page, "mouhasabah.raz_proactive", boucle_raz_proactive, app)
    else:
        print("[MOUHASABAH] RAZ proactive non démarrée : page Flet indisponible.")
