"""
Hayaati — Couche de compatibilité API adhan (Python pur)
Remplace le package 'adhan' sans modifier le code consommateur.
À utiliser dans notification_scheduler.py à la place de : from adhan import ...
"""

from datetime import datetime
from core.prayertimes import PrayerTimes as _PurePT, CalculationMethod as _PureCM


class Coordinates:
    """Mock de adhan.Coordinates"""
    def __init__(self, latitude: float, longitude: float):
        self.latitude = latitude
        self.longitude = longitude


class Madhab:
    """Mock de adhan.Madhab"""
    SHAFI = "shafi"
    HANAFI = "hanafi"


class _Params:
    """Objet paramètres interne compatible adhan.CalculationParameters"""
    def __init__(self, method_dict):
        self._method = method_dict
        self.madhab = Madhab.SHAFI


class CalculationMethod:
    """Mock de adhan.CalculationMethod — toutes les méthodes retournent un _Params"""

    @staticmethod
    def MuslimWorldLeague():
        return _Params(_PureCM.MWL)

    @staticmethod
    def Egyptian():
        return _Params(_PureCM.EGYPT)

    @staticmethod
    def Karachi():
        return _Params(_PureCM.KARACHI)

    @staticmethod
    def UmmAlQura():
        return _Params(_PureCM.UMM_AL_QURA)

    @staticmethod
    def Dubai():
        return _Params(_PureCM.GULF)

    @staticmethod
    def MoonsightingCommittee():
        # Fallback sur MWL
        return _Params(_PureCM.MWL)

    @staticmethod
    def NorthAmerica():
        return _Params(_PureCM.ISNA)

    @staticmethod
    def Kuwait():
        # Fallback sur MWL
        return _Params(_PureCM.MWL)

    @staticmethod
    def Qatar():
        # Proche de UmmAlQura
        return _Params(_PureCM.UMM_AL_QURA)

    @staticmethod
    def Singapore():
        # Fallback sur MWL
        return _Params(_PureCM.MWL)

    @staticmethod
    def Turkey():
        # Fallback sur MWL
        return _Params(_PureCM.MWL)


class PrayerTimes:
    """
    Mock de adhan.PrayerTimes

    Attributs exposés : fajr, sunrise, dhuhr, asr, maghrib, isha
    Chaque attribut est un datetime naïf local (comparable à datetime.now()).
    """

    def __init__(self, coordinates, date_obj, params):
        # Déduction du timezone depuis la longitude
        tz = round(coordinates.longitude / 15.0)

        pt = _PurePT(
            latitude=coordinates.latitude,
            longitude=coordinates.longitude,
            timezone=tz
        )

        # Extraction de la méthode et du madhab
        method = params._method if hasattr(params, "_method") else _PureCM.MWL
        is_hanafi = (params.madhab == Madhab.HANAFI) if hasattr(params, "madhab") else False

        # Calcul — date_obj peut être datetime ou date
        base_date = date_obj.date() if hasattr(date_obj, "date") else date_obj
        base_dt = date_obj if hasattr(date_obj, "hour") else datetime(base_date.year, base_date.month, base_date.day)

        times = pt.get_times_datetime(base_dt, method, asr_hanafi=is_hanafi)

        self.fajr = times.get("fajr")
        self.sunrise = times.get("sunrise")
        self.dhuhr = times.get("dhuhr")
        self.asr = times.get("asr")
        self.maghrib = times.get("maghrib")
        self.isha = times.get("isha")
