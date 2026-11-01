import 'package:flutter_test/flutter_test.dart';
import 'package:hayaati_coran/hayaati_coran.dart';

import 'aide_tests.dart';

void main() {
  final g = golden();
  late MoteurCoran moteur;

  setUpAll(() async {
    moteur = await MoteurCoran.ouvrir(lireDisque);
  });

  test('index des 114 sourates', () {
    final attendu = (g['index'] as List).cast<Map<String, dynamic>>();
    expect(moteur.index.length, 114);
    for (var i = 0; i < 114; i++) {
      final e = moteur.index[i];
      expect(e.numero, attendu[i]['numero']);
      expect(e.nomArabe, attendu[i]['nom_arabe']);
      expect(e.translitteration, attendu[i]['translitteration']);
      expect(e.nomAnglais, attendu[i]['nom_anglais']);
      expect(e.nbVersets, attendu[i]['nb_versets']);
      expect(e.revelation, attendu[i]['revelation']);
    }
  });

  test('juz, sourate et segments de chacune des 604 pages', () {
    final juz = g['juz_par_page'] as List;
    final segments = g['segments_par_page'] as List;
    final sourates = g['sourate_de_page'] as List;
    for (var p = 1; p <= 604; p++) {
      expect(moteur.juzDePage(p), juz[p], reason: 'juz de la page $p');
      expect(moteur.sourateDePage(p), sourates[p], reason: 'sourate de la page $p');
      final actuel = [for (final s in moteur.segmentsDePage(p)) [s.sourate, s.premier, s.dernier]];
      expect(actuel, equals(segments[p]), reason: 'segments de la page $p');
    }
  });

  test('pages hors limites', () {
    for (final p in [-1, 0, 605, 9999]) {
      expect(moteur.juzDePage(p), isNull);
      expect(moteur.sourateDePage(p), isNull);
      expect(moteur.segmentsDePage(p), isEmpty);
    }
  });

  test('première page de chaque sourate', () async {
    final attendu = g['premiere_page_sourate'] as List;
    for (var n = 1; n <= 114; n++) {
      expect(await moteur.premierePageSourate(n), attendu[n - 1], reason: 'sourate $n');
    }
  });

  test('pages couvertes par une sourate', () async {
    final attendu = g['pages_de_sourate'] as Map<String, dynamic>;
    for (final e in attendu.entries) {
      expect(await moteur.pagesDeSourate(int.parse(e.key)), equals(e.value), reason: 'sourate ${e.key}');
    }
  });

  test('page d\'un verset, y compris inexistant', () async {
    for (final e in g['page_de_verset'] as List) {
      expect(await moteur.pageDeVerset(e[0] as int, e[1] as int), e[2], reason: 'verset ${e[0]}:${e[1]}');
    }
  });

  test('contenu de pages échantillons', () async {
    final attendu = g['blocs_de_page'] as Map<String, dynamic>;
    for (final e in attendu.entries) {
      final blocs = await moteur.versetsDePage(int.parse(e.key));
      final liste = e.value as List;
      expect(blocs.length, liste.length, reason: 'page ${e.key}');
      for (var i = 0; i < liste.length; i++) {
        final a = liste[i] as Map<String, dynamic>;
        final b = blocs[i];
        expect(b.sourate, a['sourate'], reason: 'page ${e.key}');
        expect(b.nomArabe, a['nom_arabe']);
        expect(b.debut, a['debut']);
        expect(b.basmalah, a['basmalah']);
        expect(b.basmalahTajweed == null ? null : [for (final x in b.basmalahTajweed!) x], a['basmalah_tajweed']);
        expect(b.versets.first.numero, a['premier']);
        expect(b.versets.last.numero, a['dernier']);
        expect(b.versets.length, a['nb']);
      }
    }
  });

  test('le texte des versets est conservé verbatim', () async {
    for (final v in (g['versets'] as List).cast<Map<String, dynamic>>()) {
      expect(await moteur.texteVerset(v['sourate'] as int, v['verset'] as int), v['texte']);
    }
  });

  test('un fichier illisible donne un moteur vide, pas une exception', () async {
    final erreurs = <String>[];
    final vide = await MoteurCoran.ouvrir((nom) async => throw Exception('absent'), journal: erreurs.add);
    expect(vide.index, isEmpty);
    expect(vide.segmentsDePage(1), isEmpty);
    expect(await vide.versetsDePage(1), isEmpty);
    expect(await vide.sourate(1), isNull);
    expect(erreurs, isNotEmpty);
  });
}
