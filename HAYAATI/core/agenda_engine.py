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
"""
from datetime import datetime, timedelta
import urllib.request
import json
import threading

from core.adhan_compat import Coordinates, PrayerTimes, CalculationMethod, Madhab

class AgendaEngine:
    # ⏱ 09/09/2026 : ramenée de 12 à 5 minutes après test terrain — 12
    # minutes avant la prière donnait l'impression de sonner trop tôt.
    # Source unique : notification_scheduler.py importe cette même
    # constante pour programmer l'alarme adhan, afin que le bandeau
    # Mouhasabah/onboarding et l'alarme sonnent selon la même règle.
    FENETRE_RAPPEL_MINUTES: int = 5

    # Boîte de secours locale immuable par défaut
    _position_commune_cache = {
        "lat": 10.86,
        "lon": 0.20,
        "offset": 0,
        "city": "Dapaong (Togo)",
        "source": "defaut",
    }
    _thread_lance = False

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
        try:
            # ⚠️ CORRECTION 08/09/2026 : "http://ip-api.com" seul renvoie la
            # page d'accueil HTML du service, pas du JSON. Le point d'accès
            # correct est "/json". Avec l'ancienne URL, json.loads() levait
            # une exception à chaque appel, interceptée juste en dessous
            # sans aucun log, donc invisible en pratique.
            url = "http://ip-api.com/json"
            req = urllib.request.Request(
                url, headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=1.5) as reponse:
                data = json.loads(reponse.read().decode())
                if data.get("status") == "success":
                    lat = float(data.get("lat", 10.86))
                    lon = float(data.get("lon", 0.20))
                    coordonnees_valides = (
                        self._LAT_MIN <= lat <= self._LAT_MAX
                        and self._LON_MIN <= lon <= self._LON_MAX
                    )
                    if coordonnees_valides:
                        # ⚠️ 08/09/2026 : si la géolocalisation native
                        # (core/geolocation_natif.py) a déjà réussi entre-temps,
                        # on ne l'écrase pas avec une position IP moins précise.
                        # Ce thread tourne dès __init__ ; la tentative GPS peut
                        # se terminer avant ou après selon le temps de réponse.
                        if AgendaEngine._position_commune_cache.get("source") == "gps":
                            print("[AgendaEngine] Position GPS déjà confirmée — position IP ignorée.")
                            return
                        # ⚠️ 08/09/2026 : offset gardé en heures fractionnaires
                        # (division par 3600.0, pas de int()) — l'ancien code
                        # tronquait à l'heure pleine, ce qui aurait ignoré les
                        # décalages non-entiers (Inde UTC+5:30, Iran UTC+3:30,
                        # Népal UTC+5:45...) et faussé l'heure d'une trentaine
                        # de minutes à une heure pour ces pays.
                        AgendaEngine._position_commune_cache = {
                            "lat": lat,
                            "lon": lon,
                            "offset": data.get("offset", 0) / 3600.0,
                            "city": str(data.get("city", "Locale")),
                            "source": "ip",
                        }
                        print(f"[AgendaEngine] Position IP appliquée : {lat:.3f}, {lon:.3f} ({data.get('city', '?')})")
                    else:
                        print(f"[AgendaEngine] Coordonnées IP invalides ignorées ({lat:.3f}, {lon:.3f}) — position précédente conservée")
                else:
                    print(f"[AgendaEngine] Réponse ip-api sans succès : {data.get('message', data)}")
        except Exception as exc:
            print(f"[AgendaEngine] Géolocalisation IP indisponible : {exc}")

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
