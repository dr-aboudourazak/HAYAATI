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


async def tenter_geolocalisation_native(page: ft.Page) -> bool:
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
        geo = ftg.Geolocator(
            configuration=ftg.GeolocatorConfiguration(
                accuracy=ftg.GeolocatorPositionAccuracy.HIGH
            ),
        )
        # ⚠️ Leçon retenue avec HayaatiAlarm : un Service Flet doit être
        # enregistré via page.services.append(), jamais page.add() —
        # sinon son init() côté Dart ne se déclenche jamais, et chaque
        # appel reste muet sans la moindre erreur visible.
        page.services.append(geo)
        page.update()

        service_actif = await geo.is_location_service_enabled()
        if not service_actif:
            print("[GEO-NATIF] Service de localisation désactivé sur l'appareil — repli IP.")
            return False

        statut = await geo.get_permission_status()
        statut_str = str(statut).lower()
        if "denied" in statut_str and "forever" not in statut_str:
            statut = await geo.request_permission()
            statut_str = str(statut).lower()

        if "denied" in statut_str:
            print(f"[GEO-NATIF] Permission de localisation refusée ({statut}) — repli IP.")
            return False

        position = await asyncio.wait_for(
            geo.get_current_position(), timeout=TIMEOUT_SECONDES
        )

        decalage_local = datetime.now().astimezone().utcoffset()
        offset_heures = decalage_local.total_seconds() / 3600.0 if decalage_local else 0.0

        from core.agenda_engine import AgendaEngine
        AgendaEngine._position_commune_cache = {
            "lat": float(position.latitude),
            "lon": float(position.longitude),
            "offset": offset_heures,
            "city": "Position GPS",
            "source": "gps",
        }
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
