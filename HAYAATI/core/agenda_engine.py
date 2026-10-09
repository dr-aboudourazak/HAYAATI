"""
MOTEUR ASTRONOMIQUE OPTIMISÉ (CORE/AGENDA_ENGINE.PY)
Version 4.0 - 08/09/2026 : le calcul astronomique fait main dans ce fichier
(équation du temps tronquée à 3 termes au lieu de 5, Isha calculé comme
Maghrib + 75 min fixes au lieu de suivre l'angle de la méthode choisie)
a été retiré. Il produisait des heures différentes de celles calculées
par core/prayertimes.py (utilisé par notification_scheduler.py pour les
alarmes), avec un écart qui variait selon la période de l'année, ce qui
donnait l'impression d'un bug intermittent plutôt que d'une formule
incomplète. Ce fichier délègue maintenant à core/adhan_compat.py, le même
moteur que notification_scheduler.py, pour que Mouhasabah et les alarmes
adhan affichent toujours la même heure pour la même prière.

Correction également de l'URL de géolocalisation par IP : le code
interrogeait "http://ip-api.com" (page d'accueil HTML) au lieu de
"http://ip-api.com/json" (le vrai point d'accès JSON). Le parsing JSON
échouait donc silencieusement à chaque tentative, et _position_commune_cache
ne quittait jamais sa valeur de secours (Dapaong). Comme
notification_scheduler.py se calait ensuite sur cette valeur de secours
faute de mieux, l'application a en pratique toujours calculé les prières
pour Dapaong, quel que soit l'endroit réel où elle tournait.

Version 4.1 - 23/09/2026 : mode hors-ligne renforcé.
  • La dernière position réelle obtenue (GPS natif ou IP) est désormais
    persistée sur disque (core/emplacements_donnees.py) et rechargée au
    démarrage. Avant cette version, une coupure réseau/GPS au lancement
    faisait toujours repartir sur la valeur de secours codée en dur
    (Dapaong), même si l'utilisateur avait déjà une position réelle
    connue d'une session précédente, ailleurs sur Terre.
  • La tentative IP ne se fait plus une seule fois pour toute la durée
    de vie de l'app : en l'absence de position réelle, jusqu'à
    TENTATIVES_IP_MAX relances espacées sont effectuées, au lieu d'un
    unique essai qui, s'il échoue une fois (réseau pas encore prêt au
    démarrage, par exemple), condamnait la session entière à la valeur
    de secours.

Version 4.2 - 01/10/2026 : géolocalisation par IP en HTTPS d'abord.
  • Deux fournisseurs essayés dans l'ordre : ipwho.is (HTTPS, l'IP ne
    circule plus en clair) puis ip-api.com (HTTP, en dernier recours).
  • CORRECTION : ip-api.com ne renvoie PAS le champ "offset" dans sa
    réponse par défaut, il faut le demander avec ?fields=. L'ancien code
    lisait data.get("offset", 0) et retombait donc toujours sur UTC+0 :
    invisible au Togo (UTC+0), mais décalage d'une heure ou plus sur les
    heures de prière dans tout autre fuseau en mode IP.
  • Chaque fournisseur est tenté séparément ; une panne de l'un (réseau,
    certificat HTTPS sur Android) bascule sur le suivant, et le journal
    indique lequel a répondu.
"""
from datetime import datetime, timedelta
import urllib.request
import json
import os
import threading

from core.adhan_compat import Coordinates, PrayerTimes, CalculationMethod, Madhab
from core.emplacements_donnees import chemin_cache_position


def _decalage_en_heures(texte_utc):
    """'+05:30' -> 5.5 ; '-03:00' -> -3.0 ; retourne None si illisible."""
    try:
        t = str(texte_utc).strip()
        signe = -1.0 if t.startswith("-") else 1.0
        t = t.lstrip("+-")
        h, _, m = t.partition(":")
        return signe * (int(h) + (int(m) / 60.0 if m else 0.0))
    except Exception:
        return None


def _lire_ipwho(data):
    """ipwho.is : {"success": true, "latitude", "longitude", "city",
    "timezone": {"utc": "+01:00", "offset": 3600}}"""
    if not data.get("success", False):
        return None
    tz = data.get("timezone") or {}
    decalage = _decalage_en_heures(tz.get("utc"))
    if decalage is None and isinstance(tz.get("offset"), (int, float)):
        decalage = tz["offset"] / 3600.0
    return {
        "lat": float(data["latitude"]),
        "lon": float(data["longitude"]),
        "offset": decalage,
        "city": str(data.get("city") or "Locale"),
    }


def _lire_ipapi(data):
    """ip-api.com avec ?fields=status,message,lat,lon,city,offset"""
    if data.get("status") != "success":
        return None
    off = data.get("offset")
    return {
        "lat": float(data["lat"]),
        "lon": float(data["lon"]),
        "offset": (off / 3600.0) if isinstance(off, (int, float)) else None,
        "city": str(data.get("city") or "Locale"),
    }


# Ordre voulu : HTTPS d'abord, HTTP (en clair) seulement en dernier recours.
FOURNISSEURS_IP = (
    ("ipwho.is", "https://ipwho.is/", _lire_ipwho),
    ("ip-api.com", "http://ip-api.com/json?fields=status,message,lat,lon,city,offset", _lire_ipapi),
)
DELAI_FOURNISSEUR_IP_SECONDES = 4


def _charger_position_persistee():
    """Relit la dernière position réelle connue depuis le disque. Ne lève
    jamais d'exception : un cache absent, corrompu ou illisible retourne
    simplement None, et l'appelant garde alors la valeur de secours."""
    try:
        chemin = chemin_cache_position()
        if not os.path.exists(chemin):
            return None
        with open(chemin, "r", encoding="utf-8") as f:
            position = json.load(f)
        champs_requis = {"lat", "lon", "offset", "city", "source"}
        if not champs_requis.issubset(position):
            return None
        return position
    except Exception:
        return None


def _sauvegarder_position_sur_disque(position: dict):
    """Best-effort : une écriture qui échoue ne doit jamais interrompre
    l'obtention normale d'une position fraîche."""
    try:
        with open(chemin_cache_position(), "w", encoding="utf-8") as f:
            json.dump(position, f)
    except Exception as exc:
        print(f"[AgendaEngine] Cache position non sauvegardé (sans conséquence) : {exc}")


# ===========================================================================
# 08/10/2026 : suivi de position (voyages)
# ===========================================================================
import math as _math
import time as _t

# Un GPS plus récent que ça est jugé frais : inutile de le redemander.
DUREE_FRAICHEUR_GPS_SECONDES = 4 * 3600
# Un GPS plus vieux que ça peut être remplacé par une position IP lointaine.
DUREE_GPS_PERIME_POUR_IP_SECONDES = 24 * 3600
# Écart au-delà duquel la position IP remplace un GPS ancien (voyage probable).
SEUIL_IP_REMPLACE_GPS_KM = 100.0
# Écart au-delà duquel on replanifie alarmes et horaires.
SEUIL_DEPLACEMENT_KM = 25.0


def distance_entre_points_km(lat1, lon1, lat2, lon2) -> float:
    """Distance à vol d'oiseau (haversine), en kilomètres."""
    r = 6371.0
    p1, p2 = _math.radians(float(lat1)), _math.radians(float(lat2))
    dp = p2 - p1
    dl = _math.radians(float(lon2) - float(lon1))
    a = _math.sin(dp / 2) ** 2 + _math.cos(p1) * _math.cos(p2) * _math.sin(dl / 2) ** 2
    return 2 * r * _math.asin(min(1.0, _math.sqrt(a)))


def age_position_secondes(position: dict):
    """Âge d'une position en secondes, ou None si elle n'est pas datée
    (anciens fichiers de cache d'avant le 08/10/2026 : traités comme périmés)."""
    h = position.get("horodatage") if isinstance(position, dict) else None
    return (_t.time() - h) if isinstance(h, (int, float)) else None


class AgendaEngine:
    # ⏱ 09/09/2026 : ramenée de 12 à 5 minutes après test terrain — 12
    # minutes avant la prière donnait l'impression de sonner trop tôt.
    # Source unique : notification_scheduler.py importe cette même
    # constante pour programmer l'alarme adhan, afin que le bandeau
    # Mouhasabah/onboarding et l'alarme sonnent selon la même règle.
    FENETRE_RAPPEL_MINUTES: int = 5

    # Combien de relances de la géolocalisation IP en cas d'échec, avant
    # de s'en tenir définitivement à la meilleure position disponible
    # (persistée ou, à défaut, la valeur de secours ci-dessous).
    TENTATIVES_IP_MAX: int = 4
    DELAI_ENTRE_TENTATIVES_SECONDES: int = 20

    # Boîte de secours locale immuable par défaut — utilisée seulement si
    # aucune position réelle n'a jamais été obtenue sur cet appareil.
    _POSITION_SECOURS_ULTIME = {
        "lat": 10.86,
        "lon": 0.20,
        "offset": 0,
        "city": "Dapaong (Togo)",
        "source": "defaut",
    }
    _position_commune_cache = _charger_position_persistee() or dict(_POSITION_SECOURS_ULTIME)
    _thread_lance = False
    _tentatives_ip_effectuees = 0

    # Validation minimale des coordonnées reçues (toute la surface de la
    # Terre est acceptée). Avant le 08/09/2026, une boîte géographique
    # limitée au Togo rejetait toute position hors de cette zone — un
    # garde-fou pensé pour un usage local, qui aurait empêché la
    # détection de fonctionner pour un utilisateur sur un autre
    # continent. Retiré : HAYAATI doit fonctionner partout sur Terre.
    _LAT_MIN, _LAT_MAX = -90.0, 90.0
    _LON_MIN, _LON_MAX = -180.0, 180.0

    def __init__(self):
        # 🎯 LECTURE DYNAMIQUE PROPRIÉTÉS : Pointe vers 
        # le dictionnaire pour capter la mise à jour 
        # asynchrone du thread
        if not AgendaEngine._thread_lance:
            AgendaEngine._thread_lance = True
            threading.Thread(
                target=self._detecter_gps_asynchrone, 
                daemon=True
            ).start()

    @property
    def latitude(self):
        return AgendaEngine._position_commune_cache["lat"]

    @property
    def longitude(self):
        return AgendaEngine._position_commune_cache["lon"]

    @property
    def fuseau_horaire(self):
        return AgendaEngine._position_commune_cache["offset"]

    @property
    def ville_detectee(self):
        return AgendaEngine._position_commune_cache["city"]

    def _detecter_gps_asynchrone(self):
        # Une position réelle (GPS ou IP) a déjà été rechargée du cache
        # disque avant même ce premier essai : inutile de retenter tout
        # de suite, on ne relance que si on en reste à la valeur de
        # secours codée en dur.
        while (
            AgendaEngine._position_commune_cache.get("source") == "defaut"
            and AgendaEngine._tentatives_ip_effectuees < AgendaEngine.TENTATIVES_IP_MAX
        ):
            AgendaEngine._tentatives_ip_effectuees += 1
            self._tenter_geolocalisation_ip()
            if AgendaEngine._position_commune_cache.get("source") != "defaut":
                break
            if AgendaEngine._tentatives_ip_effectuees < AgendaEngine.TENTATIVES_IP_MAX:
                import time
                time.sleep(AgendaEngine.DELAI_ENTRE_TENTATIVES_SECONDES)

    _rafraichissement_ip_en_cours = False

    @classmethod
    def lancer_rafraichissement_ip(cls) -> bool:
        """08/10/2026 : relance une détection par IP en arrière-plan (fil séparé,
        jamais plusieurs à la fois). Utile quand le GPS n'est pas utilisable (GPS
        éteint, permission refusée, PC) pour suivre un voyage. Les règles de
        _appliquer_position_ip protègent un GPS récent. Retourne False si un
        rafraîchissement est déjà en cours."""
        if cls._rafraichissement_ip_en_cours:
            return False
        cls._rafraichissement_ip_en_cours = True

        def _travail():
            try:
                cls()._tenter_geolocalisation_ip()
            except Exception as exc:
                print(f"[AgendaEngine] Rafraîchissement IP échoué : {exc}")
            finally:
                cls._rafraichissement_ip_en_cours = False

        threading.Thread(target=_travail, daemon=True).start()
        return True

    def _tenter_geolocalisation_ip(self):
        """Essaie chaque fournisseur de FOURNISSEURS_IP jusqu'à obtenir une
        position valide. Estimation grossière (ville) : la position précise
        reste du ressort du GPS natif (core/geolocation_natif.py)."""
        for nom, url, lecteur in FOURNISSEURS_IP:
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=DELAI_FOURNISSEUR_IP_SECONDES) as reponse:
                    data = json.loads(reponse.read().decode())
                resultat = lecteur(data)
                if resultat is None:
                    print(f"[AgendaEngine] {nom} : réponse sans succès, fournisseur suivant")
                    continue
                if self._appliquer_position_ip(resultat, nom):
                    return
            except Exception as exc:
                print(f"[AgendaEngine] {nom} indisponible (tentative {AgendaEngine._tentatives_ip_effectuees}/{AgendaEngine.TENTATIVES_IP_MAX}) : {type(exc).__name__}: {exc}")

    def _appliquer_position_ip(self, resultat, nom_fournisseur):
        """Valide et enregistre une position IP. Retourne True si appliquée
        (ou volontairement ignorée car le GPS a déjà répondu)."""
        lat, lon = resultat["lat"], resultat["lon"]
        if not (self._LAT_MIN <= lat <= self._LAT_MAX and self._LON_MIN <= lon <= self._LON_MAX):
            print(f"[AgendaEngine] {nom_fournisseur} : coordonnées invalides ignorées ({lat:.3f}, {lon:.3f})")
            return False

        # Le GPS natif, plus précis, n'est jamais écrasé par l'IP tant qu'il est
        # récent. 08/10/2026 : un GPS ancien (> 24 h ou non daté) peut être
        # remplacé si l'IP indique un lieu à plus de 100 km (voyage), sinon on
        # le garde (même région : le GPS reste plus précis).
        cache_actuel = AgendaEngine._position_commune_cache
        if cache_actuel.get("source") == "gps":
            age = age_position_secondes(cache_actuel)
            if age is not None and age < DUREE_GPS_PERIME_POUR_IP_SECONDES:
                print("[AgendaEngine] Position GPS récente — position IP ignorée.")
                return True
            ecart = distance_entre_points_km(cache_actuel["lat"], cache_actuel["lon"], lat, lon)
            if ecart < SEUIL_IP_REMPLACE_GPS_KM:
                print(f"[AgendaEngine] GPS ancien mais même région ({ecart:.0f} km) — position IP ignorée.")
                return True
            print(f"[AgendaEngine] GPS ancien et IP à {ecart:.0f} km : voyage probable, l'IP prend le relais.")

        # Offset gardé en heures fractionnaires (Inde +5:30, Népal +5:45...).
        # Si le fournisseur n'en donne pas, estimation par la longitude (au
        # demi-heure près) plutôt que UTC+0 par défaut.
        offset = resultat.get("offset")
        estime = offset is None
        if estime:
            offset = round(lon / 15.0 * 2) / 2.0

        nouvelle_position = {
            "lat": lat,
            "lon": lon,
            "offset": offset,
            "city": resultat["city"],
            "source": "ip",
            "horodatage": _t.time(),
        }
        AgendaEngine._position_commune_cache = nouvelle_position
        _sauvegarder_position_sur_disque(nouvelle_position)
        print(f"[AgendaEngine] Position IP appliquée via {nom_fournisseur} : {lat:.3f}, {lon:.3f} ({resultat['city']}) UTC{offset:+g}{' (estimé)' if estime else ''}")
        return True

    def calculer_minutes_depuis_minuit(self, heure_obj):
        return heure_obj.hour * 60 + heure_obj.minute

    def obtenir_heures_prieres_journee(self, madhhab_actif="Malikite"):
        """Délègue le calcul à core/adhan_compat.py — le même moteur que
        notification_scheduler.py — pour garantir une heure identique
        entre le bandeau Mouhasabah/onboarding et l'alarme adhan."""
        doctrine = str(madhhab_actif).strip().capitalize()
        # ⚠️ 08/09/2026 : transmet le fuseau civil réel (self.fuseau_horaire,
        # issu de l'offset ip-api) plutôt que de laisser adhan_compat
        # l'estimer depuis la seule longitude. Nécessaire hors du Togo.
        coords = Coordinates(self.latitude, self.longitude, timezone=self.fuseau_horaire)
        params = CalculationMethod.MuslimWorldLeague()
        params.madhab = Madhab.HANAFI if doctrine == "Hanafite" else Madhab.SHAFI

        prayers = PrayerTimes(coords, datetime.now(), params)
        return {
            "fajr": prayers.fajr.time(),
            # 🆕 09/09/2026 : sunrise était déjà calculé par PrayerTimes
            # (nécessaire pour Maghrib/Fajr en interne) mais jamais exposé
            # ici. Ajouté pour l'écran Qiblah (6ᵉ branche du cadran).
            "sunrise": prayers.sunrise.time(),
            "dhuhr": prayers.dhuhr.time(),
            "asr": prayers.asr.time(),
            "maghrib": prayers.maghrib.time(),
            "isha": prayers.isha.time(),
        }

    def evaluer_etat_prieres_en_direct(self, dictionnaire_deja_cochees, madhhab_actif="Malikite") -> dict:
        """
        🆕 08/09/2026 : remplace evaluer_prieres_manquees_en_direct().

        Retourne, pour chacune des 5 prières obligatoires, un état parmi :
          "faite"     : déjà cochée par l'utilisateur
          "imminente" : dans les FENETRE_RAPPEL_MINUTES minutes précédant
                        l'heure légale, pas encore cochée — c'est la
                        fenêtre où l'alarme adhan sonne aussi
          "manquee"   : heure légale dépassée, toujours pas cochée
          "a_venir"   : aucun des cas ci-dessus pour l'instant

        Cette distinction remplace l'ancienne logique tout-ou-rien
        (manquée / pas manquée) pour permettre au bandeau onboarding de
        prévenir en amont, sur le même principe que l'adhan : on informe
        avant l'heure, pas seulement après coup.
        """
        heures_legales = self.obtenir_heures_prieres_journee(madhhab_actif)
        maintenant = datetime.now()
        etats = {}
        for p in ["fajr", "dhuhr", "asr", "maghrib", "isha"]:
            if dictionnaire_deja_cochees.get(p, 0):
                etats[p] = "faite"
                continue
            h = heures_legales[p]
            heure_legale_dt = maintenant.replace(
                hour=h.hour, minute=h.minute, second=0, microsecond=0
            )
            debut_rappel = heure_legale_dt - timedelta(minutes=self.FENETRE_RAPPEL_MINUTES)
            if maintenant >= heure_legale_dt:
                etats[p] = "manquee"
            elif maintenant >= debut_rappel:
                etats[p] = "imminente"
            else:
                etats[p] = "a_venir"
        return etats

    def evaluer_prieres_manquees_en_direct(self, dictionnaire_deja_cochees, madhhab_actif="Malikite"):
        """Conservée pour compatibilité ascendante : ne retourne que les
        prières effectivement manquées, comme avant. Les appelants qui
        veulent aussi détecter les prières imminentes doivent utiliser
        evaluer_etat_prieres_en_direct() directement."""
        etats = self.evaluer_etat_prieres_en_direct(dictionnaire_deja_cochees, madhhab_actif)
        return [p.upper() for p, etat in etats.items() if etat == "manquee"]
