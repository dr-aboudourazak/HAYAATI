import 'dart:math' as math;

import 'config.dart';

const double _rayonTerreM = 6371000.0;

double _rad(double deg) => deg * math.pi / 180.0;

/// Distance à vol d'oiseau en mètres (formule de haversine).
double distanceM(Coord a, Coord b) {
  final dLat = _rad(b.lat - a.lat);
  final dLon = _rad(b.lon - a.lon);
  final h = math.pow(math.sin(dLat / 2), 2) +
      math.cos(_rad(a.lat)) * math.cos(_rad(b.lat)) * math.pow(math.sin(dLon / 2), 2);
  return 2 * _rayonTerreM * math.asin(math.sqrt(h.toDouble()));
}

/// Cap initial de a vers b, en degrés de 0 (nord) à 360, sens horaire.
double capDeg(Coord a, Coord b) {
  final dLon = _rad(b.lon - a.lon);
  final y = math.sin(dLon) * math.cos(_rad(b.lat));
  final x = math.cos(_rad(a.lat)) * math.sin(_rad(b.lat)) -
      math.sin(_rad(a.lat)) * math.cos(_rad(b.lat)) * math.cos(dLon);
  return (math.atan2(y, x) * 180 / math.pi + 360) % 360;
}

/// Code de point cardinal : N, NE, E, SE, S, SO, O, NO.
String pointCardinal(double deg) {
  const codes = <String>['N', 'NE', 'E', 'SE', 'S', 'SO', 'O', 'NO'];
  final i = ((deg % 360) / 45).round() % 8;
  return codes[i];
}

String formaterDistance(double metres) {
  if (metres < 1000) return '${metres.round()} m';
  return '${(metres / 1000).toStringAsFixed(1)} km';
}

class Resultat<T> {
  const Resultat(this.item, this.distanceM, this.capDeg);

  final T item;
  final double distanceM;
  final double capDeg;
}

/// Les éléments les plus proches de [origine], triés par distance.
///
/// Un filtre rectangulaire écarte d'abord les points éloignés, ce qui évite de
/// faire la trigonométrie complète sur des milliers de mosquées (téléphones lents).
List<Resultat<T>> plusProches<T>(
  Iterable<T> elements,
  Coord origine,
  Coord? Function(T) coordDe, {
  int max = 30,
  double? rayonMaxM,
}) {
  double dLatMax = 180;
  double dLonMax = 360;
  if (rayonMaxM != null) {
    dLatMax = rayonMaxM / 111320.0;
    final c = math.cos(_rad(origine.lat)).abs();
    dLonMax = rayonMaxM / (111320.0 * (c < 0.01 ? 0.01 : c));
  }
  final resultats = <Resultat<T>>[];
  for (final e in elements) {
    final p = coordDe(e);
    if (p == null) continue;
    if ((p.lat - origine.lat).abs() > dLatMax) continue;
    if ((p.lon - origine.lon).abs() > dLonMax) continue;
    final d = distanceM(origine, p);
    if (rayonMaxM != null && d > rayonMaxM) continue;
    resultats.add(Resultat<T>(e, d, capDeg(origine, p)));
  }
  resultats.sort((a, b) => a.distanceM.compareTo(b.distanceM));
  return resultats.length > max ? resultats.sublist(0, max) : resultats;
}
