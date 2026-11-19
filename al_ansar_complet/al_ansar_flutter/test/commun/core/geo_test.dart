import 'package:al_ansar/al_ansar.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  const dapaong = Coord(10.8627, 0.2076);
  const lome = Coord(6.1319, 1.2228);

  test('distance Dapaong-Lomé proche de 537,8 km', () {
    expect(distanceM(dapaong, lome), closeTo(537751, 1000));
  });

  test('distance nulle entre deux points identiques', () {
    expect(distanceM(dapaong, dapaong), closeTo(0, 0.001));
  });

  test('caps : nord 0, est 90', () {
    expect(capDeg(const Coord(0, 0), const Coord(1, 0)), closeTo(0, 0.01));
    expect(capDeg(const Coord(0, 0), const Coord(0, 1)), closeTo(90, 0.01));
  });

  test('points cardinaux', () {
    expect(pointCardinal(0), 'N');
    expect(pointCardinal(46), 'NE');
    expect(pointCardinal(200), 'S');
    expect(pointCardinal(359), 'N');
  });

  test('formatage des distances', () {
    expect(formaterDistance(366), '366 m');
    expect(formaterDistance(1500), '1.5 km');
  });

  test('plusProches trie par distance et respecte le rayon', () {
    const points = <String, Coord>{
      'loin': Coord(9.5520, 1.1870),
      'proche': Coord(10.8650, 0.2100),
      'moyen': Coord(10.8590, 0.2040),
    };
    final res = plusProches<String>(points.keys, dapaong, (k) => points[k], rayonMaxM: 1000);
    expect(res.map((r) => r.item).toList(), <String>['proche', 'moyen']);
    expect(res.first.distanceM, closeTo(366, 5));

    final tous = plusProches<String>(points.keys, dapaong, (k) => points[k]);
    expect(tous.map((r) => r.item).toList(), <String>['proche', 'moyen', 'loin']);
  });

  test('plusProches ignore les éléments sans coordonnées et applique max', () {
    final res = plusProches<int>(<int>[1, 2, 3], dapaong, (i) => i == 2 ? null : const Coord(10.86, 0.21), max: 1);
    expect(res.length, 1);
  });
}
