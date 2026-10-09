"""
SUIVI DE POSITION (CORE/SUIVI_POSITION.PY) - 08/10/2026

Problème traité : un utilisateur qui voyage change de pays alors que HAYAATI
garde l'ancienne position en cache. Qibla, horaires et alarmes d'adhan seraient
alors calculés pour le mauvais endroit.

Ce module :
  - compare la position utilisée par le planificateur d'alarmes à celle du cache
    (GPS ou IP) et, si l'écart dépasse 25 km ou si le fuseau change, met à jour
    le planificateur, replanifie les alarmes et recalcule les horaires du jour ;
  - lance, app ouverte, une boucle de rafraîchissement toutes les 30 minutes.
    Elle passe par HayaatiTaskRegistry (contrat des boucles de fond du projet).

Limite assumée : si l'app est complètement fermée pendant le voyage, rien ne
peut s'exécuter. Les alarmes déjà programmées (2 jours) gardent l'ancienne
position jusqu'à la prochaine ouverture de l'app, qui les corrige aussitôt.
"""
from __future__ import annotations
import asyncio

from core.agenda_engine import AgendaEngine, distance_entre_points_km, SEUIL_DEPLACEMENT_KM
from core.hayaati_task_registry import HayaatiTaskRegistry

CANAL = "position.suivi"
INTERVALLE_SECONDES = 30 * 60
DELAI_PREMIER_PASSAGE_SECONDES = 120


async def synchroniser_avec_la_position(app, forcer: bool = False) -> bool:
    """Aligne planificateur et horaires du jour sur la position en cache.
    Retourne True si les alarmes ont été replanifiées."""
    planificateur = getattr(app, "notification_scheduler", None)
    if planificateur is None:
        return False
    cache = AgendaEngine._position_commune_cache
    try:
        lat, lon = float(cache["lat"]), float(cache["lon"])
        fuseau = cache.get("offset")
        ecart = distance_entre_points_km(planificateur.lat, planificateur.lng, lat, lon)
        fuseau_change = fuseau is not None and abs(float(fuseau) - float(planificateur.tz_offset)) > 1e-6
    except Exception as exc:
        print(f"[SUIVI-POSITION] Comparaison impossible : {exc}")
        return False

    if not (forcer or ecart >= SEUIL_DEPLACEMENT_KM or fuseau_change):
        return False

    print(f"[SUIVI-POSITION] Nouvelle position ({ecart:.0f} km, fuseau changé : {fuseau_change}) : replanification.")
    planificateur.lat = lat
    planificateur.lng = lon
    if fuseau is not None:
        planificateur.tz_offset = float(fuseau)
    try:
        await planificateur.reschedule_all()
    except Exception as exc:
        print(f"[SUIVI-POSITION] Replanification échouée : {exc}")

    # Les écrans (onboarding, mouhasabah) lisent ces horaires, calculés une seule
    # fois au démarrage : il faut les recalculer pour le nouvel endroit.
    try:
        heures = AgendaEngine().obtenir_heures_prieres_journee(app.madhhab_actif)
        app.horaires_prieres_aujourdhui = {
            nom.capitalize(): f"{h.hour:02d}:{h.minute:02d}" for nom, h in heures.items()
        }
    except Exception as exc:
        print(f"[SUIVI-POSITION] Recalcul des horaires du jour échoué : {exc}")
    return True


async def _boucle(app, page, generation):
    await asyncio.sleep(DELAI_PREMIER_PASSAGE_SECONDES)
    while HayaatiTaskRegistry.generation_active(CANAL, generation):
        try:
            from core import geolocation_natif as geo_natif
            resultat = await geo_natif.rafraichir_position_si_necessaire(page)
            if resultat == "ok":
                etat = geo_natif.etat_dernier_suivi()
                await synchroniser_avec_la_position(app, forcer=bool(etat["voyage"] or etat["premiere_position"]))
            elif resultat != "deja_gps":
                # GPS inutilisable (éteint, refusé, PC...) : l'IP prend le relais.
                # Elle ne peut jamais dégrader un GPS récent (voir AgendaEngine).
                if AgendaEngine.lancer_rafraichissement_ip():
                    await asyncio.sleep(20)  # laisse le fil IP finir (2 fournisseurs x 4 s max)
                await synchroniser_avec_la_position(app)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            print(f"[SUIVI-POSITION] Tour ignoré : {exc}")
        await asyncio.sleep(INTERVALLE_SECONDES)


def demarrer_suivi_position(app, page) -> None:
    """À appeler une fois, après le bootstrap du planificateur."""
    async def _lancee(generation):
        await _boucle(app, page, generation)

    HayaatiTaskRegistry.lancer(page, CANAL, _lancee)
    print("[SUIVI-POSITION] Boucle de suivi démarrée (30 min).")
