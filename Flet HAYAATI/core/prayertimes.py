"""
Hayaati — Module de calcul des horaires de prière (Python pur)
Remplace le package 'adhan' non disponible sur pypi.flet.dev (Android)
Méthodes supportées : MWL, ISNA, Egypt, Karachi, UmmAlQura, Gulf
"""

import math
from datetime import date, datetime, timedelta
from typing import Dict, Tuple, Optional


class CalculationMethod:
    """Paramètres des grandes méthodes de calcul."""
    MWL = {"name": "Muslim World League", "fajr_angle": 18.0, "isha_angle": 17.0, "isha_after_maghrib": None}
    ISNA = {"name": "ISNA", "fajr_angle": 15.0, "isha_angle": 15.0, "isha_after_maghrib": None}
    EGYPT = {"name": "Egyptian General Authority", "fajr_angle": 19.5, "isha_angle": 17.5, "isha_after_maghrib": None}
    KARACHI = {"name": "University of Islamic Sciences, Karachi", "fajr_angle": 18.0, "isha_angle": 18.0, "isha_after_maghrib": None}
    UMM_AL_QURA = {"name": "Umm Al-Qura", "fajr_angle": 18.5, "isha_angle": None, "isha_after_maghrib": 90}
    GULF = {"name": "Gulf Region", "fajr_angle": 19.5, "isha_angle": None, "isha_after_maghrib": 90}


class PrayerTimes:
    """
    Calculateur d'horaires de prière islamiques.

    Usage:
        pt = PrayerTimes(latitude=10.85, longitude=0.20, timezone=0)
        times = pt.get_times(date.today(), CalculationMethod.MWL)
        # {'fajr': '05:12', 'sunrise': '06:23', 'dhuhr': '12:34', 
        #  'asr': '15:45', 'maghrib': '18:56', 'isha': '20:15'}

        # Ou en datetime directement :
        dtimes = pt.get_times_datetime(datetime(2026, 8, 9), CalculationMethod.MWL)
        # {'fajr': datetime(2026, 8, 9, 5, 12), ...}
    """

    def __init__(self, latitude: float, longitude: float, timezone: Optional[float] = None):
        self.lat = math.radians(latitude)
        self.lng = longitude
        # Déduction automatique du timezone depuis la longitude si non fourni
        self.tz = timezone if timezone is not None else round(longitude / 15.0)

    # ------------------------------------------------------------------
    # Helpers astronomiques
    # ------------------------------------------------------------------
    @staticmethod
    def _julian_day(d: date) -> float:
        """Jour julien à 12h UTC."""
        a = (14 - d.month) // 12
        y = d.year + 4800 - a
        m = d.month + 12 * a - 3
        return d.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045

    @staticmethod
    def _sun_declination(jd: float) -> Tuple[float, float, float]:
        """Retourne (déclinaison en radians, équation du temps en minutes, longitude solaire)."""
        d = jd - 2451545.0
        g = math.radians((357.529 + 0.98560028 * d) % 360)
        q = math.radians((280.459 + 0.98564736 * d) % 360)
        L = math.radians((q + math.degrees(1.915 * math.sin(g)) + 0.020 * math.sin(2 * g)) % 360)
        e = 23.439 - 0.00000036 * d
        RA = math.degrees(math.atan2(math.cos(math.radians(e)) * math.sin(L), math.cos(L)))
        RA = (RA + 360) % 360
        eqt = (q - math.radians(RA)) * 4 * 180 / math.pi  # en minutes
        decl = math.asin(math.sin(math.radians(e)) * math.sin(L))
        return decl, eqt, L

    def _hour_angle(self, decl: float, angle: float) -> float:
        """Calcule l'angle horaire (degrés) pour une hauteur donnée."""
        num = math.sin(math.radians(angle)) - math.sin(self.lat) * math.sin(decl)
        den = math.cos(self.lat) * math.cos(decl)
        cos_omega = num / den
        # Protection contre les valeurs hors domaine (nuit polaire, etc.)
        if cos_omega < -1:
            return 999
        if cos_omega > 1:
            return 0
        return math.degrees(math.acos(cos_omega))

    @staticmethod
    def _fmt(hours: float) -> str:
        """Convertit un nombre d'heures décimal en HH:MM."""
        if hours >= 24:
            hours -= 24
        if hours < 0:
            hours += 24
        h = int(hours)
        m = int((hours - h) * 60)
        return f"{h:02d}:{m:02d}"

    # ------------------------------------------------------------------
    # Calcul principal
    # ------------------------------------------------------------------
    def get_times(self, d: date, method: Dict = CalculationMethod.MWL, asr_hanafi: bool = False) -> Dict[str, str]:
        """
        Retourne les 6 horaires de prière pour une date donnée (format string HH:MM).

        Args:
            d: date visée
            method: dictionnaire de méthode (voir CalculationMethod)
            asr_hanafi: True = méthode Hanafi (ombre double), False = standard
        """
        jd = self._julian_day(d)
        decl, eqt, _ = self._sun_declination(jd)

        # Dhuhr = transit solaire
        dhuhr = 12 + (self.tz - self.lng / 15.0) - (eqt / 60.0)

        # Lever / coucher du soleil (hauteur = -0.833° = réfraction + diamètre)
        omega_sun = self._hour_angle(decl, -0.833)
        sunrise = dhuhr - omega_sun / 15.0
        sunset = dhuhr + omega_sun / 15.0
        maghrib = sunset

        # Fajr
        omega_fajr = self._hour_angle(decl, -method["fajr_angle"])
        fajr = dhuhr - omega_fajr / 15.0

        # Asr
        # angle = arccot(t + tan|lat - decl|)  ; t = 1 (standard) ou 2 (Hanafi)
        t = 2.0 if asr_hanafi else 1.0
        asr_angle = math.degrees(math.atan(1.0 / (t + math.tan(abs(self.lat - decl)))))
        omega_asr = self._hour_angle(decl, -asr_angle)
        asr = dhuhr + omega_asr / 15.0

        # Isha
        if method.get("isha_after_maghrib") is not None:
            # Méthode UmmAlQura / Gulf : Isha = Maghrib + X minutes
            isha = maghrib + method["isha_after_maghrib"] / 60.0
        else:
            omega_isha = self._hour_angle(decl, -method["isha_angle"])
            isha = dhuhr + omega_isha / 15.0

        return {
            "fajr": self._fmt(fajr),
            "sunrise": self._fmt(sunrise),
            "dhuhr": self._fmt(dhuhr),
            "asr": self._fmt(asr),
            "maghrib": self._fmt(maghrib),
            "isha": self._fmt(isha),
            "method": method["name"]
        }

    def get_times_datetime(self, dt: datetime, method: Dict = CalculationMethod.MWL, asr_hanafi: bool = False) -> Dict[str, datetime]:
        """
        Retourne les 6 horaires de prière pour une date donnée (format datetime).

        Args:
            dt: datetime visé (seule la date est extraite, l'heure est recalculée)
            method: dictionnaire de méthode
            asr_hanafi: True = méthode Hanafi
        """
        times = self.get_times(dt.date(), method, asr_hanafi)
        result = {}
        for key in ["fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha"]:
            if key in times:
                h, m = map(int, times[key].split(":"))
                result[key] = dt.replace(hour=h, minute=m, second=0, microsecond=0)
        result["method"] = times["method"]
        return result

    def get_next_prayer(self, d: date, current_hour: float, method: Dict = CalculationMethod.MWL) -> Tuple[str, str]:
        """
        Retourne la prochaine prière après l'heure actuelle.

        Args:
            d: date du jour
            current_hour: heure décimale actuelle (ex: 14.5 pour 14h30)

        Returns:
            (nom_priere, heure HH:MM)
        """
        times = self.get_times(d, method)
        prayers = [("fajr", times["fajr"]), ("dhuhr", times["dhuhr"]),
                   ("asr", times["asr"]), ("maghrib", times["maghrib"]),
                   ("isha", times["isha"])]

        for name, t_str in prayers:
            h, m = map(int, t_str.split(":"))
            t_dec = h + m / 60.0
            if t_dec > current_hour:
                return name, t_str

        # Toutes les prières du jour sont passées → retourne Fajr du lendemain
        tomorrow = d + timedelta(days=1)
        next_times = self.get_times(tomorrow, method)
        return "fajr", next_times["fajr"]
