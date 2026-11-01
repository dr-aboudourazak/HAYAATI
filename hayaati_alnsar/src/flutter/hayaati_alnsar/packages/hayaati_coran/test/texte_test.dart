import 'package:flutter_test/flutter_test.dart';
import 'package:hayaati_coran/hayaati_coran.dart';

import 'aide_tests.dart';

void main() {
  final g = golden();

  test('les constantes sont celles de Python', () {
    final c = g['constantes'] as Map<String, dynamic>;
    expect(signeSajda, c['sajda']);
    expect(signeHizb, c['hizb']);
    expect(signesPause, c['pause']);
    expect(marqueurPremier, c['premier']);
    expect(marqueurDernier, c['dernier']);
    expect(signesOrnementaux, c['ornementaux']);
    expect(nbPages, g['nb_pages']);
  });

  test('chiffresArabes', () {
    for (final e in g['chiffres_arabes'] as List) {
      expect(chiffresArabes(e[0] as int), e[1], reason: 'chiffres ${e[0]}');
    }
  });

  test('marqueurVerset', () {
    for (final e in g['marqueurs'] as List) {
      expect(marqueurVerset(e[0] as int), e[1], reason: 'marqueur ${e[0]}');
    }
  });

  group('versets de référence (tirés de tout le Coran, dont tous les versets à ۩ et à ۞)', () {
    final versets = (g['versets'] as List).cast<Map<String, dynamic>>();

    test('preparerTexteAffichage', () {
      for (final v in versets) {
        expect(preparerTexteAffichage(v['texte'] as String), v['prepare'], reason: 'verset ${v['sourate']}:${v['verset']}');
      }
    });

    test('decouperSignes', () {
      for (final v in versets) {
        final actuel = [for (final m in decouperSignes(v['prepare'] as String)) [m.texte, m.estSigne]];
        expect(actuel, equals(v['morceaux']), reason: 'verset ${v['sourate']}:${v['verset']}');
        // La concaténation redonne l'original.
        expect(decouperSignes(v['prepare'] as String).map((m) => m.texte).join(), v['prepare']);
      }
    });

    test('segmentsVerset avec tajweed', () {
      for (final v in versets) {
        final actuel = [
          for (final s in segmentsVerset(v['prepare'] as String, annotationsDepuisJson(v['annotations']), true)) [s.texte, s.famille],
        ];
        expect(actuel, equals(v['segments_tajweed']), reason: 'verset ${v['sourate']}:${v['verset']}');
      }
    });

    test('segmentsVerset sans tajweed : un seul segment', () {
      for (final v in versets) {
        final actuel = [
          for (final s in segmentsVerset(v['prepare'] as String, annotationsDepuisJson(v['annotations']), false)) [s.texte, s.famille],
        ];
        expect(actuel, equals(v['segments_sans_tajweed']), reason: 'verset ${v['sourate']}:${v['verset']}');
      }
    });

    test('le verset de sajda est reconnu', () {
      for (final v in versets) {
        expect((v['texte'] as String).contains(signeSajda), v['sajda']);
      }
    });
  });

  test('segmentsVerset : texte vide et annotations hors limites', () {
    expect(segmentsVerset('', const <List<int>>[], true).length, 1);
    expect(segmentsVerset('abc', const <List<int>>[<int>[-5, 99, 11]], true).map((s) => s.famille), <int>[0]);
    expect(segmentsVerset('abc', const <List<int>>[<int>[1, 2, 99]], true).map((s) => s.famille), <int>[-1]);
  });
}
