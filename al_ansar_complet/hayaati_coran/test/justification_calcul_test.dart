import 'package:flutter_test/flutter_test.dart';
import 'package:hayaati_coran/hayaati_coran.dart';

/// Paragraphe fabriqué : mots de 30 à 94 px (suite pseudo-aléatoire reproductible) séparés par des espaces de 5 px.
ModeleParagraphe paragraphe(int graine, {int nb = 40}) {
  var x = graine * 7919 + 13;
  double suivant() {
    x = (x * 1103515245 + 12345) & 0x7fffffff;
    return 30 + (x >> 8) % 65;
  }

  return ModeleParagraphe(<double>[for (var i = 0; i < nb; i++) suivant()], List<double>.filled(nb - 1, 5));
}

void main() {
  const largeur = 300.0;

  test('simuler : coupure aux espaces, dernière ligne, mot plus large que la ligne', () {
    const m = ModeleParagraphe(<double>[100, 100, 100, 100], <double>[5, 5, 5]);
    final r = simuler(m, largeur);
    expect(r.nbLignes, 2); // 100+5+100+5+100 = 310 > 300 : 2 mots par ligne
    expect(r.largeurFin, 205.0);
    expect(simuler(m, largeur, echelle: 0.5).nbLignes, 1); // tout tient : 0,5 x 415 = 207,5
    const large = ModeleParagraphe(<double>[400, 50], <double>[5]);
    expect(simuler(large, largeur).nbLignes, 2);
    expect(simuler(const ModeleParagraphe(<double>[], <double>[]), largeur).nbLignes, 0);
  });

  test('un texte d\'une seule ligne : aucun candidat', () {
    expect(chercherCandidats(const ModeleParagraphe(<double>[50, 60], <double>[5]), largeur), isEmpty);
    expect(chercherCandidats(const ModeleParagraphe(<double>[50], <double>[]), largeur), isEmpty);
  });

  test('un paragraphe déjà plein reste tel quel (coût nul)', () {
    const m = ModeleParagraphe(<double>[145, 145, 145, 145], <double>[5, 5, 5]); // 2 lignes de 295
    final c = chercherCandidats(m, largeur);
    expect(c.first.echelle, closeTo(1.0, 0.0026));
    expect(c.first.espaceMots.abs(), lessThan(0.3));
    expect(c.first.remplissage, greaterThanOrEqualTo(0.97));
  });

  test('sur 300 paragraphes, la dernière ligne est presque toujours pleine et ne déborde jamais', () {
    var total = 0, au88 = 0, au80 = 0;
    for (var graine = 1; graine <= 300; graine++) {
      final m = paragraphe(graine, nb: 25 + graine % 40);
      if (simuler(m, 330).nbLignes < 2) continue;
      total++;
      final candidats = chercherCandidats(m, 330);
      expect(candidats, isNotEmpty, reason: 'graine $graine');
      final c = candidats.first;
      final r = simuler(m, 330, echelle: c.echelle, espaceMots: c.espaceMots);
      expect(r.largeurFin, lessThanOrEqualTo(330 - margeJustification + 1e-9), reason: 'graine $graine');
      expect(r.largeurFin / 330, closeTo(c.remplissage, 1e-9));
      expect(c.echelle, greaterThanOrEqualTo(0.91 - 1e-9));
      expect(c.echelle, lessThanOrEqualTo(1.09 + 1e-9));
      if (c.remplissage >= 0.88) au88++;
      if (c.remplissage >= 0.80) au80++;
    }
    expect(total, greaterThan(250));
    // Mesuré : environ 90 % des paragraphes atteignent 88 %, 98 % atteignent 80 % (le reste est comblé par espaceFinPour).
    expect(au88 / total, greaterThan(0.85));
    expect(au80 / total, greaterThan(0.95));
  });

  test('le meilleur palier disponible est toujours choisi en premier', () {
    for (var graine = 1; graine <= 40; graine++) {
      final m = paragraphe(graine, nb: 30);
      final c = chercherCandidats(m, 330);
      if (c.isEmpty) continue;
      for (final autre in c.skip(1)) {
        final p0 = paliersRemplissage.where((p) => c.first.remplissage >= p).length;
        final p1 = paliersRemplissage.where((p) => autre.remplissage >= p).length;
        expect(p0, greaterThanOrEqualTo(p1));
      }
    }
  });

  test('les candidats sont triés du plus discret au moins discret', () {
    final c = chercherCandidats(paragraphe(7), largeur);
    for (var i = 1; i < c.length; i++) {
      expect(c[i].cout, greaterThanOrEqualTo(c[i - 1].cout));
    }
  });

  test('espaceFinPour : comble le manque, borné, et ignore une ligne sans espace', () {
    // dernière ligne : 240 px, 5 espaces élargissables (1 px de plus par espace = 5 px de plus)
    final ws = espaceFinPour(largeur: 300, w0: 240, w1: 245, maximum: 20);
    expect(ws, closeTo((300 - margeJustification - 240) / 5, 1e-9));
    expect(espaceFinPour(largeur: 300, w0: 240, w1: 240), 0); // aucun espace
    expect(espaceFinPour(largeur: 300, w0: 299, w1: 304), 0); // déjà plein
    expect(espaceFinPour(largeur: 300, w0: 100, w1: 101, maximum: 10), 10); // borné
    expect(espaceFinPour(largeur: 300, w0: 100, w1: 101), 14); // borne par défaut
  });
}
