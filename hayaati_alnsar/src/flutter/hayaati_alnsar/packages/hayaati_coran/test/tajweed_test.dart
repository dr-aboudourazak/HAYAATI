import 'package:flutter_test/flutter_test.dart';
import 'package:hayaati_coran/hayaati_coran.dart';

import 'aide_tests.dart';

void main() {
  final t = golden()['tajweed'] as Map<String, dynamic>;

  test('indiceFamille', () {
    for (final e in t['indice_famille'] as List) {
      expect(indiceFamille(e[0] as int), e[1], reason: 'code ${e[0]}');
    }
  });

  test('couleurFamille, avec et sans surlignage', () {
    for (final e in t['couleur_famille'] as List) {
      expect(couleurFamille(e[0] as int), e[1], reason: 'famille ${e[0]}');
      expect(couleurFamille(e[0] as int, surSurlignage: true), e[2], reason: 'famille ${e[0]} sur surlignage');
    }
  });

  test('avecSurlignage / sansSurlignage', () {
    for (final e in t['avec_surlignage'] as List) {
      expect(avecSurlignage(e[0] as String), e[1]);
    }
    for (final e in t['sans_surlignage'] as List) {
      expect(sansSurlignage(e[0] as String), e[1]);
    }
  });

  test('les 5 familles, leurs couleurs et leurs clés de libellé', () {
    final attendu = t['familles'] as List;
    expect(famillesTajweed.length, attendu.length);
    for (var i = 0; i < attendu.length; i++) {
      expect(famillesTajweed[i].cle, attendu[i][0]);
      expect(famillesTajweed[i].couleur, attendu[i][1]);
      expect(famillesTajweed[i].cleLibelle, attendu[i][2]);
    }
  });

  test('18 règles', () => expect(reglesTajweed.length, 18));
}
