"""
Génère test/fixtures/priere_reference.json à partir du moteur Python de HAYAATI (core/prayertimes.py et core/qibla_engine.py).

Ces valeurs sont la RÉFÉRENCE de parité du moteur Dart (lib/src/fonctionnalites/priere/core). Une fois HAYAATI en Python retiré,
le fichier produit reste la référence gelée : ne le régénérez que pour changer volontairement un comportement.

    python outils/generer_references_priere.py --hayaati "F:\\HAYAATI-main"        (dossier qui contient core/prayertimes.py)

Le fichier contient aussi, section « mesures », les résultats du moteur PRUDENT (minute de précaution, ajustements, règle des hautes
latitudes, soleil de minuit) recalculés ici en Python à partir des fonctions astronomiques de l'ancien moteur : une seconde écriture
indépendante de la version Dart, pour que les deux se contrôlent l'une l'autre.

Les cas dont une heure tombe à moins de 0,001 minute (0,06 s) d'une frontière de minute sont écartés : à cet endroit, la dernière
décimale de sin/cos peut différer d'une plateforme à l'autre sans que le moteur soit en cause.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from datetime import date
from pathlib import Path

VILLES = (
    ("dapaong", 10.8627, 0.2076, 0.0), ("lome", 6.1375, 1.2123, 0.0), ("paris", 48.8566, 2.3522, None),
    ("la_mecque", 21.4225, 39.8262, 3.0), ("jakarta", -6.2088, 106.8456, 7.0), ("sydney", -33.8688, 151.2093, None),
    ("new_york", 40.7128, -74.0060, None), ("karachi", 24.8607, 67.0011, 5.0),
)
# (date, décalage d'hiver, décalage d'été) pour les villes à heure d'été (None ci-dessus)
FUSEAUX = {"paris": (1.0, 2.0, "nord"), "sydney": (10.0, 11.0, "sud"), "new_york": (-5.0, -4.0, "nord")}
DATES = (date(2026, 1, 15), date(2026, 3, 20), date(2026, 6, 21), date(2026, 9, 8), date(2026, 12, 21), date(2024, 2, 29),
         date(2000, 1, 1), date(1999, 12, 31))
METHODES = ("MWL", "ISNA", "EGYPT", "KARACHI", "UMM_AL_QURA", "GULF")
POINTS_QIBLA = ((10.8627, 0.2076), (6.1375, 1.2123), (48.8566, 2.3522), (-33.8688, 151.2093), (40.7128, -74.0060),
                (21.4225, 39.8262), (0.0, 0.0), (-6.2088, 106.8456), (64.1466, -21.9426), (35.6762, 139.6503))


def charger(chemin: Path, nom: str):
    spec = importlib.util.spec_from_file_location(nom, chemin)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nom] = mod
    spec.loader.exec_module(mod)
    return mod


def fuseau(ville: str, fixe, d: date) -> float:
    if fixe is not None:
        return fixe
    hiver, ete, hemi = FUSEAUX[ville]
    mois = d.month
    ete_actif = 4 <= mois <= 10 if hemi == "nord" else (mois >= 11 or mois <= 3)
    return ete if ete_actif else hiver


def proche_frontiere(pt, d: date, methode: dict, hanafi: bool) -> bool:
    """Vrai si une des six heures est à moins de 0,001 minute d'une frontière de minute."""
    jd = pt._julian_day(d)
    decl, eqt, _ = pt._sun_declination(jd)
    dhuhr = 12 + (pt.tz - pt.lng / 15.0) - (eqt / 60.0)
    om = pt._hour_angle(decl, -0.833)
    t = 2.0 if hanafi else 1.0
    asr_angle = math.degrees(math.atan(1.0 / (t + math.tan(abs(pt.lat - decl)))))
    heures = [dhuhr - om / 15.0, dhuhr, dhuhr + om / 15.0, dhuhr - pt._hour_angle(decl, -methode["fajr_angle"]) / 15.0,
              dhuhr + pt._hour_angle(decl, asr_angle) / 15.0]
    if methode.get("isha_after_maghrib") is not None:
        heures.append(dhuhr + om / 15.0 + methode["isha_after_maghrib"] / 60.0)
    else:
        heures.append(dhuhr + pt._hour_angle(decl, -methode["isha_angle"]) / 15.0)
    for h in heures:
        h = h % 24
        reste = (h * 60) % 1.0
        if reste < 0.001 or reste > 0.999:
            return True
    return False


# ---------------------------------------------------------------------------- moteur prudent (miroir Python de horaires.dart)
HAUTES_LATITUDES = (
    ("paris", 48.8566, 2.3522, 2.0, ("2026-06-21", "2026-05-20", "2026-12-21")),
    ("londres", 51.5074, -0.1278, 1.0, ("2026-06-21",)),
    ("oslo", 59.9139, 10.7522, 2.0, ("2026-06-21", "2026-12-21")),
    ("moscou", 55.7558, 37.6173, 3.0, ("2026-06-21",)),
    ("reykjavik", 64.1466, -21.9426, 0.0, ("2026-06-21", "2026-12-21")),
    ("tromso", 69.6492, 18.9553, 2.0, ("2026-06-21",)),
    ("tromso_hiver", 69.6492, 18.9553, 1.0, ("2026-12-21",)),
    ("dapaong", 10.8627, 0.2076, 0.0, ("2026-09-08", "2026-03-20")),
    ("la_mecque", 21.4225, 39.8262, 3.0, ("2026-06-21",)),
)
REGLES = ("automatique", "milieuDeLaNuit", "septiemeDeLaNuit", "angleCrepuscule")
AJUSTEMENTS = {"fajr": 2, "sunrise": -1, "maghrib": 1, "isha": -3}


def formater_heure(h: float, haut: bool = False, ajust: int = 0) -> str:
    minutes = h * 60.0
    entier = math.ceil(minutes - 1e-6) if haut else math.floor(minutes + 1e-6)
    total = (entier + ajust) % 1440
    return f"{total // 60:02d}:{total % 60:02d}"


def part_de_nuit(regle: str, angle: float, lat_deg: float) -> float:
    r = regle
    if r == "automatique":
        r = "septiemeDeLaNuit" if abs(lat_deg) > 48 else "milieuDeLaNuit"
    if r == "septiemeDeLaNuit":
        return 1.0 / 7.0
    if r == "angleCrepuscule":
        return angle / 60.0
    return 0.5


def calcul_prudent(pt, lat_deg: float, d: date, methode: dict, hanafi: bool, regle: str, prudent: bool, ajust: dict):
    """Renvoie ({six horaires}, situation, hautes_latitudes, [heures décimales non nulles])."""
    jd = pt._julian_day(d)
    decl, eqt, _ = pt._sun_declination(jd)
    dhuhr = 12 + (pt.tz - pt.lng / 15.0) - (eqt / 60.0)
    om = pt._hour_angle(decl, -0.833)
    lever = dhuhr - om / 15.0
    maghrib = dhuhr + om / 15.0
    omf = pt._hour_angle(decl, -methode["fajr_angle"])
    fajr = dhuhr - omf / 15.0
    t = 2.0 if hanafi else 1.0
    asr_angle = math.degrees(math.atan(1.0 / (t + math.tan(abs(pt.lat - decl)))))
    oma = pt._hour_angle(decl, asr_angle)
    asr = dhuhr + oma / 15.0
    fixe = methode.get("isha_after_maghrib")
    omi = None if fixe is not None else pt._hour_angle(decl, -methode["isha_angle"])
    isha = maghrib + fixe / 60.0 if fixe is not None else dhuhr + omi / 15.0

    def sentinelle(o):
        return o == 999 or o == 0

    situation = "normale"
    h = {"fajr": fajr, "sunrise": lever, "dhuhr": dhuhr, "asr": asr, "maghrib": maghrib, "isha": isha}
    hl = False
    if om == 999:
        situation = "soleilDeMinuit"
    elif om == 0:
        situation = "nuitPolaire"
    if situation != "normale":
        h["sunrise"] = h["maghrib"] = h["fajr"] = h["isha"] = None
        if sentinelle(oma):
            h["asr"] = None
    else:
        nuit = (lever - maghrib + 24) % 24
        pf = part_de_nuit(regle, methode["fajr_angle"], lat_deg)
        if sentinelle(omf) or (lever - fajr + 24) % 24 > pf * nuit:
            h["fajr"] = lever - pf * nuit
            hl = True
        if omi is not None:
            pi_ = part_de_nuit(regle, methode["isha_angle"], lat_deg)
            if sentinelle(omi) or (isha - maghrib + 24) % 24 > pi_ * nuit:
                h["isha"] = maghrib + pi_ * nuit
                hl = True
    sortie, decimales = {}, []
    for cle, valeur in h.items():
        if valeur is None:
            sortie[cle] = "--:--"
            continue
        decimales.append(valeur * 60.0)
        sortie[cle] = formater_heure(valeur, haut=prudent and cle != "sunrise", ajust=ajust.get(cle, 0))
    return sortie, situation, hl, decimales


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hayaati", required=True, help="dossier HAYAATI (contenant core/prayertimes.py)")
    ap.add_argument("--sortie", default=str(Path(__file__).resolve().parent.parent / "test" / "fixtures" / "priere_reference.json"))
    a = ap.parse_args()
    base = Path(a.hayaati)
    pt_mod = charger(base / "core" / "prayertimes.py", "prayertimes_ref")
    qb_mod = charger(base / "core" / "qibla_engine.py", "qibla_ref")

    horaires, ecartes = [], 0
    for ville, lat, lon, fixe in VILLES:
        for d in DATES:
            tz = fuseau(ville, fixe, d)
            pt = pt_mod.PrayerTimes(lat, lon, tz)
            for cle in METHODES:
                methode = getattr(pt_mod.CalculationMethod, cle)
                for hanafi in (False, True):
                    if proche_frontiere(pt, d, methode, hanafi):
                        ecartes += 1
                        continue
                    t = pt.get_times(d, methode, hanafi)
                    horaires.append({"ville": ville, "lat": lat, "lon": lon, "fuseau": tz, "date": d.isoformat(), "methode": cle,
                                     "hanafi": hanafi,
                                     "attendu": {k: t[k] for k in ("fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha")}})
    # fuseau déduit de la longitude (arrondi « au pair » de Python : 0,5 -> 0 ; 1,5 -> 2)
    deduits = []
    for lon in (0.2076, 7.5, 22.5, 37.5, -7.5, -22.5, 106.8456, -74.006):
        pt = pt_mod.PrayerTimes(10.0, lon)
        deduits.append({"lon": lon, "fuseau": float(pt.tz)})
    prochaines = []
    pt = pt_mod.PrayerTimes(10.8627, 0.2076, 0.0)
    for heure in (0.0, 5.0, 6.5, 12.0, 15.0, 18.0, 19.5, 23.9):
        nom, h = pt.get_next_prayer(date(2026, 9, 8), heure)
        prochaines.append({"heure": heure, "nom": nom, "valeur": h})
    mesures = []
    for ville, lat, lon, tz, dates in HAUTES_LATITUDES:
        pt = pt_mod.PrayerTimes(lat, lon, tz)
        for iso in dates:
            d = date.fromisoformat(iso)
            for cle in ("MWL", "ISNA", "UMM_AL_QURA"):
                methode = getattr(pt_mod.CalculationMethod, cle)
                for hanafi in (False, True) if ville == "paris" else (False,):
                    for regle in REGLES:
                        for prudent in (True, False):
                            for ajust in ({}, AJUSTEMENTS) if (regle == "automatique" and prudent) else ({},):
                                sortie, situation, hl, dec = calcul_prudent(pt, lat, d, methode, hanafi, regle, prudent, ajust)
                                if any(abs(x - round(x)) < 1e-4 for x in dec):
                                    continue
                                mesures.append({"ville": ville, "lat": lat, "lon": lon, "fuseau": tz, "date": iso, "methode": cle,
                                                "hanafi": hanafi, "regle": regle, "arrondi": "prudent" if prudent else "tronque",
                                                "ajustements": ajust, "attendu": sortie, "situation": situation,
                                                "hautes_latitudes": hl})
    formats = [{"heures": h, "haut": hh, "ajust": aj, "attendu": formater_heure(h, hh, aj)}
               for h, hh, aj in ((5.5, True, 0), (5.5 + 1e-12, True, 0), (5.5, False, 0), (5.503, True, 0), (5.503, False, 0),
                                 (23.99, False, 5), (23.99, True, 5), (0.0, False, -1), (24.0, False, 0), (-0.5, False, 0),
                                 (12.999999, False, 0), (12.999999, True, 0))]
    qibla = [{"lat": la, "lon": lo, "direction": qb_mod.calculer_direction_qibla(la, lo),
              "distance_km": qb_mod.calculer_distance_kaaba_km(la, lo)} for la, lo in POINTS_QIBLA]
    relatifs = [{"qibla": q, "boussole": b, "attendu": qb_mod.angle_relatif_aiguille(q, b)}
                for q, b in ((90.0, 0.0), (90.0, 270.0), (10.0, 350.0), (359.0, 1.0), (45.0, None))]
    Path(a.sortie).write_text(json.dumps({"horaires": horaires, "fuseaux_deduits": deduits, "prochaines": prochaines, "qibla": qibla,
                                          "relatifs": relatifs, "mesures": mesures, "formats": formats}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(horaires)} cas d'horaires et {len(mesures)} cas de mesures écrits ({ecartes} écartés près d'une frontière de minute) -> {a.sortie}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
