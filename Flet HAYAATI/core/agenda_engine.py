"""
MOTEUR ASTRONOMIQUE OPTIMISÉ (CORE/AGENDA_ENGINE.PY)
Version 3.6 - Correction du point d'accès JSON et
rafraîchissement dynamique de l'instance asynchrone.
"""
from datetime import datetime, time
import math
import urllib.request
import json
import threading

class AgendaEngine:
    # Boîte de secours locale immuable par défaut
    _position_commune_cache = {
        "lat": 10.86,
        "lon": 0.20,
        "offset": 0,
        "city": "Dapaong (Togo)"
    }
    _thread_lance = False

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
            # 🎯 RECTIFICATION POINT D'ACCÈS : Ciblage du JSON
            url = "http://ip-api.com"
            req = urllib.request.Request(
                url, headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=1.5) as reponse:
                data = json.loads(reponse.read().decode())
                if data.get("status") == "success":
                    # Écriture immédiate dans le cache de classe
                    AgendaEngine._position_commune_cache = {
                        "lat": float(data.get("lat", 10.86)),
                        "lon": float(data.get("lon", 0.20)),
                        "offset": int(data.get("offset", 0) / 3600),
                        "city": str(data.get("city", "Locale"))
                    }
        except Exception:
            pass

    def calculer_minutes_depuis_minuit(self, heure_obj):
        return heure_obj.hour * 60 + heure_obj.minute

    def obtenir_heures_prieres_journee(self, madhhab_actif="Malikite"):
        doctrine = str(madhhab_actif).strip().capitalize()
        facteur = 2.0 * math.pi * (datetime.now().timetuple().tm_yday - 1) / 365.0
        declinaison = 0.006918 - 0.399912 * math.cos(facteur) + 0.070257 * math.sin(facteur)
        equation_temps = 229.18 * (0.000075 + 0.001868 * math.cos(facteur) - 0.032077 * math.sin(facteur))
        
        gmt_midi_solaire = 12.0 - (self.longitude / 15.0) - (equation_temps / 60.0)
        minutes_dhuhr = int((gmt_midi_solaire + self.fuseau_horaire) * 60) + 15 

        rad_lat = math.radians(self.latitude)
        def angle_horaire(degres_under):
            num = math.sin(math.radians(-degres_under)) - math.sin(rad_lat) * math.sin(declinaison)
            return math.degrees(math.acos(num / (math.cos(rad_lat) * math.cos(declinaison)))) / 15.0

        minutes_fajr = minutes_dhuhr - int(angle_horaire(18.0) * 60)
        minutes_maghrib = minutes_dhuhr + int(angle_horaire(0.833) * 60) + 3 
        minutes_isha = minutes_maghrib + 75 

        nombre_ombres = 2 if doctrine == "Hanafite" else 1
        angle_asr_rad = math.atan(1.0 / (nombre_ombres + math.tan(abs(rad_lat - declinaison))))
        num_asr = math.sin(angle_asr_rad) - math.sin(rad_lat) * math.sin(declinaison)
        minutes_asr = minutes_dhuhr + int((math.degrees(math.acos(num_asr / (math.cos(rad_lat) * math.cos(declinaison)))) / 15.0) * 60)

        def convertir_en_time(m): return time((m % 1440) // 60, m % 60)
        return {"fajr": convertir_en_time(minutes_fajr), "dhouhr": convertir_en_time(minutes_dhuhr),
                "asr": convertir_en_time(minutes_asr), "maghrib": convertir_en_time(minutes_maghrib), "isha": convertir_en_time(minutes_isha)}

    def evaluer_prieres_manquees_en_direct(self, dictionnaire_deja_cochees, madhhab_actif="Malikite"):
        heures_legales = self.obtenir_heures_prieres_journee(madhhab_actif)
        min_courantes = self.calculer_minutes_depuis_minuit(datetime.now().time())
        prieres_manquees = []
        for p in ["fajr", "dhouhr", "asr", "maghrib", "isha"]:
            if min_courantes > self.calculer_minutes_depuis_minuit(heures_legales[p]):
                if not dictionnaire_deja_cochees.get(p, 0): prieres_manquees.append(p.upper())
        return prieres_manquees
