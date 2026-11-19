import 'dart:math' as m;

/// Coordonnées de la Kaaba (Masjid al-Haram, La Mecque), comme core/qibla_engine.py.
const double kaabaLatitude = 21.4225;
const double kaabaLongitude = 39.8262;
const double rayonTerreKm = 6371.0;

double _enRadians(double degres) => degres * (m.pi / 180.0);
double _enDegres(double radians) => radians * (180.0 / m.pi);

/// Cap initial (orthodromique) de la position vers la Kaaba, en degrés depuis le nord VRAI, dans le sens horaire
/// (0 = nord, 90 = est, 180 = sud, 270 = ouest). Le nord magnétique d'une boussole diffère du nord vrai de la déclinaison
/// magnétique (faible en Afrique de l'Ouest, quelques degrés) : elle est négligée ici, comme dans le moteur Python.
double calculerDirectionQibla(double latitude, double longitude) {
  final phi1 = _enRadians(latitude);
  final phi2 = _enRadians(kaabaLatitude);
  final deltaLambda = _enRadians(kaabaLongitude - longitude);
  final x = m.sin(deltaLambda) * m.cos(phi2);
  final y = m.cos(phi1) * m.sin(phi2) - m.sin(phi1) * m.cos(phi2) * m.cos(deltaLambda);
  final cap = _enDegres(m.atan2(x, y));
  return (cap + 360.0) % 360.0;
}

/// Distance à vol d'oiseau jusqu'à la Kaaba, en km (formule de Haversine). Purement informatif.
double calculerDistanceKaabaKm(double latitude, double longitude) {
  final phi1 = _enRadians(latitude);
  final phi2 = _enRadians(kaabaLatitude);
  final deltaPhi = _enRadians(kaabaLatitude - latitude);
  final deltaLambda = _enRadians(kaabaLongitude - longitude);
  final sp = m.sin(deltaPhi / 2);
  final sl = m.sin(deltaLambda / 2);
  final a = sp * sp + m.cos(phi1) * m.cos(phi2) * sl * sl;
  final c = 2 * m.atan2(m.sqrt(a), m.sqrt(1 - a));
  return rayonTerreKm * c;
}

/// Rotation (degrés) à donner à l'aiguille pour qu'elle pointe vers la qibla, sachant le cap actuel de la boussole.
/// Sans capteur ([capBoussole] null), l'aiguille reste fixe : le nord est supposé en haut de l'écran.
double angleRelatifAiguille(double capQibla, double? capBoussole) {
  if (capBoussole == null) return capQibla;
  return (capQibla - capBoussole + 360.0) % 360.0;
}
