"""
core/geolocation_natif.py — 08/09/2026

Géolocalisation native de l'appareil (GPS/réseau), via l'extension
officielle flet-geolocator (wrapper du paquet Flutter 'geolocator',
https://docs.flet.dev/geolocator/ — le même paquet Flutter qu'utilise
Muslim Pro et la plupart des apps de prière).

Plus précise que la géolocalisation par IP (quelques mètres à quelques
dizaines de mètres, contre plusieurs dizaines de kilomètres pour l'IP,
en particulier sur réseau mobile où l'IP publique sort souvent par une
passerelle opérateur éloignée de la position réelle de l'utilisateur).

⚠️ À AJOUTER avant de builder :
  - "flet-geolocator" dans les dépendances du pyproject.toml de l'app
    principale (pas celui de hayaati_alarm, un autre fichier).
  - Vérifier après build que les permissions ACCESS_FINE_LOCATION /
    ACCESS_COARSE_LOCATION apparaissent bien dans l'AndroidManifest.xml
    généré. Le paquet flet-geolocator est censé les fusionner
    automatiquement (paquet officiel, contrairement à hayaati_alarm),
    mais après toutes les surprises rencontrées sur ce projet, une
    vérification directe dans l'APK décompressé reste plus sûre qu'une
    supposition.
  - Vérifier le nom exact des membres de GeolocatorPositionAccuracy dans
    la version installée :
        python -c "import flet_geolocator as ftg; print([m for m in dir(ftg.GeolocatorPositionAccuracy) if not m.startswith('_')])"
    HIGH est utilisé ci-dessous par analogie avec l'énumération LocationAccuracy
    du paquet Flutter d'origine, mais je n'ai pas pu vérifier ce nom précis
    dans votre version installée.

Repli : si la géolocalisation native échoue pour une raison quelconque
(permission refusée, service désactivé, timeout, paquet absent), rien à
faire de spécial ici — le thread de détection par IP dans
core/agenda_engine.py tourne déjà en arrière-plan depuis le tout premier
AgendaEngine() instancié dans l'application (voir AgendaEngine.__init__),
donc la position déjà en cache (IP ou valeur de secours) reste valide.
"""
from __future__ import annotations
import asyncio
from datetime import datetime

import flet as ft

try:
    import flet_geolocator as ftg
    _HAS_GEOLOCATOR = True
except ImportError:
    _HAS_GEOLOCATOR = False
    print("[GEO-NATIF] WARNING: flet_geolocator introuvable — ajoutez 'flet-geolocator' au pyproject.toml de l'app.")

# Délai maximum accordé à la localisation native avant d'abandonner et de
# laisser le repli IP (déjà en cours en arrière-plan depuis le démarrage)
# faire foi. Un cold fix GPS peut prendre bien plus longtemps que ça en
# intérieur ; au-delà de ce délai, on préfère démarrer avec une position
# approximative plutôt que de retarder tout le reste du bootstrap.
TIMEOUT_SECONDES = 8.0


async def _tenter_geolocalisation_interne(page: ft.Page) -> bool:
    """
    Tente d'obtenir la position réelle de l'appareil via GPS/réseau natif.

    En cas de succès, écrit directement dans
    AgendaEngine._position_commune_cache (le même cache que celui utilisé
    par la détection IP), avec le fuseau horaire lu depuis l'horloge
    système de l'appareil plutôt que déduit des coordonnées — un GPS ne
    donne que lat/lon, jamais le fuseau civil, et une base de données de
    fuseaux par zone géographique serait trop lourde pour ce projet
    (RAM limitée sur la machine de build). L'horloge système d'Android
    est déjà correctement réglée (réseau ou GPS), heure d'été comprise,
    donc plus simple et tout aussi fiable de la lire directement.

    Retourne True si la position native a été appliquée, False sinon
    (auquel cas la position déjà en cache — IP ou valeur de secours —
    reste en vigueur, sans action supplémentaire nécessaire).
    """
    if not _HAS_GEOLOCATOR:
        return False

    try:
        # 08/10/2026 : un SEUL service Geolocator pour toute la vie de l'app
        # (voir _obtenir_geo). Le recréer à chaque tentative empilerait des
        # services dans page.services, ce qui est exactement la fuite à éviter.
        # ⚠️ Leçon retenue avec HayaatiAlarm : un Service Flet doit être
        # enregistré via page.services.append(), jamais page.add().
        geo = _obtenir_geo(page)

        service_actif = await geo.is_location_service_enabled()
        if not service_actif:
            print("[GEO-NATIF] Service de localisation désactivé sur l'appareil — repli IP.")
            return False

        statut = await geo.get_permission_status()
        statut_str = str(statut).lower()
        print(f"[GEO-NATIF] Statut initial de la permission : {statut}")

        # 08/10/2026 : Android n'affiche qu'une boîte de dialogue de permission à
        # la fois. Si celle des notifications est déjà à l'écran, la demande de
        # localisation est rejetée presque instantanément (sans que l'utilisateur
        # ait rien vu) et le code concluait à tort à un refus. Une vraie réponse
        # humaine prend plus de 1,5 s : on ne réessaie donc que si la réponse
        # est arrivée plus vite que ça, avec 3 essais au maximum.
        boucle = asyncio.get_running_loop()
        for essai in range(1, 4):
            if not ("denied" in statut_str and "forever" not in statut_str):
                break
            debut = boucle.time()
            print(f"[GEO-NATIF] Demande de permission (essai {essai}/3)...")
            statut = await geo.request_permission()
            statut_str = str(statut).lower()
            duree = boucle.time() - debut
            print(f"[GEO-NATIF] Réponse : {statut} en {duree:.2f}s")
            refus_sans_dialogue = (
                "denied" in statut_str and "forever" not in statut_str and duree < 1.5
            )
            if refus_sans_dialogue and essai < 3:
                print("[GEO-NATIF] Réponse trop rapide : une autre boîte de dialogue était sans doute affichée, nouvel essai dans 5 s.")
                await asyncio.sleep(5.0)
                statut = await geo.get_permission_status()
                statut_str = str(statut).lower()
            else:
                break

        if "denied" in statut_str:
            print(f"[GEO-NATIF] Permission de localisation refusée ({statut}) — repli IP.")
            return False

        position = await _obtenir_position(geo)

        decalage_local = datetime.now().astimezone().utcoffset()
        offset_heures = decalage_local.total_seconds() / 3600.0 if decalage_local else 0.0

        from core.agenda_engine import (
            AgendaEngine, _sauvegarder_position_sur_disque,
            distance_entre_points_km, SEUIL_DEPLACEMENT_KM,
        )
        # 08/10/2026 : mémorise si cette position correspond à un VOYAGE (ancienne
        # position GPS précise, à plus de 25 km) ou à une PREMIÈRE position réelle.
        try:
            _ancienne = AgendaEngine._position_commune_cache
            _etait_gps = _ancienne.get("source") == "gps"
            _ecart = distance_entre_points_km(
                _ancienne["lat"], _ancienne["lon"], float(position.latitude), float(position.longitude)
            )
            _etat_suivi["premiere_position"] = not _etait_gps
            _etat_suivi["deplacement_km"] = _ecart
            _etat_suivi["voyage"] = bool(_etait_gps and _ecart >= SEUIL_DEPLACEMENT_KM)
        except Exception:
            _etat_suivi.update({"premiere_position": False, "deplacement_km": 0.0, "voyage": False})
        nouvelle_position = {
            "lat": float(position.latitude),
            "lon": float(position.longitude),
            "offset": offset_heures,
            "city": "Position GPS",
            "source": "gps",
            "horodatage": _time.time(),
        }
        AgendaEngine._position_commune_cache = nouvelle_position
        # 23/09/2026 : persistée sur disque pour le mode hors-ligne renforcé
        # — au prochain lancement sans réseau ni GPS disponible, l'app
        # repart de cette dernière position réelle plutôt que de la valeur
        # de secours codée en dur.
        _sauvegarder_position_sur_disque(nouvelle_position)
        print(
            f"[GEO-NATIF] Position GPS appliquée : "
            f"{position.latitude:.5f}, {position.longitude:.5f}, UTC{offset_heures:+.2f}"
        )
        return True

    except asyncio.TimeoutError:
        print(f"[GEO-NATIF] Timeout ({TIMEOUT_SECONDES}s) sans réponse GPS — repli IP.")
        return False
    except Exception as exc:
        print(f"[GEO-NATIF] Échec géolocalisation native ({exc}) — repli IP.")
        return False


# ===========================================================================
# 08/10/2026 : suivi de position (voyages) et nouvel essai
# ===========================================================================
import time as _time

_geo_instance = None
_tentative_en_cours = False
_fin_derniere_tentative = 0.0
_cas_deja_signales: set[str] = set()
_etat_suivi = {"premiere_position": False, "deplacement_km": 0.0, "voyage": False}
DELAI_ENTRE_TENTATIVES_SECONDES = 90.0
# Une « dernière position connue » plus vieille que ça n'est pas utilisée.
AGE_MAX_DERNIERE_POSITION_SECONDES = 12 * 3600


def _obtenir_geo(page: ft.Page):
    """Crée le service Geolocator une seule fois et le réutilise ensuite.
    Précision MEDIUM : plus rapide à obtenir qu'HIGH et largement suffisante
    pour la qibla et les horaires de prière."""
    global _geo_instance
    if _geo_instance is not None:
        try:
            if _geo_instance in page.services:
                return _geo_instance
        except Exception:
            pass
    geo = ftg.Geolocator(
        configuration=ftg.GeolocatorConfiguration(
            accuracy=ftg.GeolocatorPositionAccuracy.MEDIUM
        ),
    )
    page.services.append(geo)
    page.update()
    _geo_instance = geo
    return geo


async def _obtenir_position(geo):
    """Position actuelle ; si le GPS ne répond pas à temps (intérieur, démarrage
    à froid), repli sur la dernière position connue si elle date de moins de 12 h."""
    try:
        return await asyncio.wait_for(geo.get_current_position(), timeout=TIMEOUT_SECONDES)
    except asyncio.TimeoutError:
        try:
            derniere = await geo.get_last_known_position()
            if derniere is not None and derniere.timestamp is not None:
                horodatage = derniere.timestamp
                maintenant = datetime.now(horodatage.tzinfo) if horodatage.tzinfo else datetime.now()
                if (maintenant - horodatage).total_seconds() < AGE_MAX_DERNIERE_POSITION_SECONDES:
                    print("[GEO-NATIF] GPS trop lent : dernière position connue utilisée.")
                    return derniere
        except Exception as exc:
            print(f"[GEO-NATIF] Dernière position connue indisponible : {exc}")
        raise


async def tenter_geolocalisation_native(page: ft.Page) -> bool:
    """Une seule tentative à la fois (démarrage de l'app, page Prière ou suivi)."""
    global _tentative_en_cours, _fin_derniere_tentative
    if _tentative_en_cours:
        return False
    _tentative_en_cours = True
    try:
        return await _tenter_geolocalisation_interne(page)
    finally:
        _tentative_en_cours = False
        _fin_derniere_tentative = _time.monotonic()


def _plateforme_mobile(page) -> bool:
    plateforme = str(getattr(page, "platform", "") or "").upper()
    return "ANDROID" in plateforme or "IOS" in plateforme


def etat_dernier_suivi() -> dict:
    """Copie de l'état de la dernière position GPS obtenue :
    premiere_position (aucun GPS avant), voyage (>= 25 km depuis le GPS précédent),
    deplacement_km."""
    return dict(_etat_suivi)


async def rafraichir_position_si_necessaire(page: ft.Page) -> str:
    """
    Rafraîchit la position GPS quand elle manque OU qu'elle date de plus de 4 h.

    Résultats possibles :
      "ignore"            : PC, paquet absent, tentative en cours ou trop récente
      "deja_gps"          : position GPS récente en cache, rien à faire
      "ok"                : position GPS obtenue et appliquée
      "service_desactive" : le GPS / la localisation du téléphone est éteint
      "refuse_definitif"  : permission refusée « pour toujours » (réglages Android)
      "refuse"            : permission refusée
      "indisponible"      : échec sans cause identifiable (délai dépassé, erreur)
    """
    if not _HAS_GEOLOCATOR or page is None or not _plateforme_mobile(page):
        return "ignore"
    try:
        from core.agenda_engine import AgendaEngine, age_position_secondes, DUREE_FRAICHEUR_GPS_SECONDES
        cache = AgendaEngine._position_commune_cache
        age = age_position_secondes(cache)
        if cache.get("source") == "gps" and age is not None and age < DUREE_FRAICHEUR_GPS_SECONDES:
            return "deja_gps"
    except Exception:
        return "ignore"
    if _tentative_en_cours:
        return "ignore"
    if _fin_derniere_tentative and (_time.monotonic() - _fin_derniere_tentative) < DELAI_ENTRE_TENTATIVES_SECONDES:
        return "ignore"

    if await tenter_geolocalisation_native(page):
        return "ok"

    geo = _geo_instance
    if geo is None:
        return "indisponible"
    try:
        if not await geo.is_location_service_enabled():
            return "service_desactive"
        statut = str(await geo.get_permission_status()).lower()
    except Exception:
        return "indisponible"
    if "forever" in statut:
        return "refuse_definitif"
    if "denied" in statut:
        return "refuse"
    return "indisponible"


def signaler_une_fois(cas: str) -> bool:
    """True la première fois qu'un cas est rencontré dans la session (évite de
    réafficher le même message à chaque ouverture de la page Prière)."""
    if cas in _cas_deja_signales:
        return False
    _cas_deja_signales.add(cas)
    return True


async def ouvrir_reglages_localisation(definitif: bool) -> bool:
    """Ouvre les réglages Android : ceux de l'app (refus définitif) ou ceux de
    la localisation du téléphone (GPS éteint)."""
    geo = _geo_instance
    if geo is None:
        return False
    try:
        if definitif:
            return bool(await geo.open_app_settings())
        return bool(await geo.open_location_settings())
    except Exception as exc:
        print(f"[GEO-NATIF] Ouverture des réglages impossible : {exc}")
        return False
