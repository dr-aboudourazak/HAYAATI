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

/// Largeur d'une ligne à l'échelle [s], avec [ws] pixels ajoutés à chaque espace.
double largeurLigne(ModeleParagraphe m, LigneCalculee l, double s) {
  var w = 0.0;
  for (var i = l.debut; i < l.fin; i++) {
    w += m.mots[i] * s;
    if (i < l.fin - 1) w += m.espaces[i] * s + l.espace;
  }
  return w;
}

void main() {
  const largeur = 330.0;
  const reglages = ReglagesLignes();

  test('chaque ligne finit exactement au bout de la ligne, dernière comprise', () {
    final m = paragraphe(3, nb: 35);
    final r = calculerMiseEnLignes(m, largeur)!;
    expect(r.lignes.length, greaterThan(1));
    for (final l in r.lignes) {
      if (l.nbEspaces > 0) {
        expect(largeurLigne(m, l, r.echelle), closeTo(largeur - reglages.marge, 1e-6));
      }
    }
  });

  test('les lignes couvrent tous les mots, dans l\'ordre, sans trou ni chevauchement', () {
    for (var graine = 1; graine <= 60; graine++) {
      final m = paragraphe(graine, nb: 20 + graine % 30);
      final r = calculerMiseEnLignes(m, largeur);
      if (r == null) continue;
      expect(r.lignes.first.debut, 0);
      expect(r.lignes.last.fin, m.mots.length);
      for (var i = 1; i < r.lignes.length; i++) {
        expect(r.lignes[i].debut, r.lignes[i - 1].fin, reason: 'graine $graine');
      }
    }
  });

  test('les espaces restent dans les limites : jamais plus étirés ni plus comprimés que permis', () {
    for (var graine = 1; graine <= 200; graine++) {
      final m = paragraphe(graine, nb: 20 + graine % 40);
      final r = calculerMiseEnLignes(m, largeur);
      if (r == null) continue;
      final ref = 5.0 * r.echelle;
      for (final l in r.lignes) {
        if (l.nbEspaces == 0) continue;
        expect(l.espace / ref, lessThanOrEqualTo(reglages.etirementMax + 1e-9), reason: 'graine $graine');
        expect(l.espace / ref, greaterThanOrEqualTo(-reglages.compressionMax - 1e-9), reason: 'graine $graine');
      }
      expect(r.echelle, greaterThanOrEqualTo(reglages.echelleMin - 1e-9));
      expect(r.echelle, lessThanOrEqualTo(reglages.echelleMax + 1e-9));
    }
  });

  test('presque tous les paragraphes de plusieurs lignes obtiennent une mise en lignes complète', () {
    var total = 0, reussis = 0;
    var ecartEchelle = 0.0;
    for (var graine = 1; graine <= 300; graine++) {
      final m = paragraphe(graine, nb: 20 + graine % 45);
      if (m.mots.fold<double>(0, (a, b) => a + b) < largeur * 2) continue;
      total++;
      final r = calculerMiseEnLignesAvecRepli(m, largeur);
      if (r != null) {
        reussis++;
        ecartEchelle += (r.echelle - 1).abs();
      }
    }
    expect(total, greaterThan(250));
    expect(reussis / total, greaterThan(0.97)); // mesuré : 100 % dès 25 mots
    expect(ecartEchelle / reussis, lessThan(0.07)); // écart moyen de taille : environ 5 %
  });

  test('un bloc de 10 mots ou plus aboutit presque toujours grâce au repli souple', () {
    var total = 0, reussis = 0;
    for (var graine = 1; graine <= 200; graine++) {
      final m = paragraphe(graine, nb: 10 + graine % 6);
      if (m.mots.fold<double>(0, (a, b) => a + b) < largeur * 1.2) continue;
      total++;
      if (calculerMiseEnLignesAvecRepli(m, largeur) != null) reussis++;
    }
    expect(total, greaterThan(100));
    expect(reussis / total, greaterThan(0.95));
  });

  test('une fin de sourate trop courte pour remplir une ligne : aucune mise en lignes', () {
    // 3 mots de 40 px sur une ligne de 330 : même étirés au maximum (2,5 x 5 px par espace), ils n'atteignent pas le bout.
    const court = ModeleParagraphe(<double>[40, 40, 40], <double>[5, 5]);
    expect(calculerMiseEnLignes(court, largeur), isNull);
    expect(calculerMiseEnLignesAvecRepli(court, largeur), isNull);
    expect(calculerMiseEnLignes(const ModeleParagraphe(<double>[40], <double>[]), largeur), isNull);
  });

  test('une fin de sourate sur une seule ligne presque pleine est justifiée', () {
    const presque = ModeleParagraphe(<double>[70, 65, 60, 55, 50], <double>[5, 5, 5, 5]); // 325 px sur 330
    final r = calculerMiseEnLignes(presque, largeur)!;
    expect(r.lignes.length, 1);
    expect(r.lignes.first.espace, greaterThan(-1.5));
  });

  test('les espaces sont plus réguliers qu\'avec la coupure gloutonne d\'un moteur de texte', () {
    // Comparaison à taille égale (échelle 1) sur les lignes qui ne sont pas la dernière : étirement moyen des espaces.
    var gloutonne = 0.0, optimale = 0.0, lignesG = 0, lignesO = 0;
    for (var graine = 1; graine <= 200; graine++) {
      final m = paragraphe(graine, nb: 40);
      var debut = 0;
      while (debut < m.mots.length) {
        var fin = debut + 1;
        var w = m.mots[debut];
        while (fin < m.mots.length && w + 5 + m.mots[fin] <= largeur - 0.5) {
          w += 5 + m.mots[fin];
          fin++;
        }
        final k = fin - debut - 1;
        if (k > 0 && fin < m.mots.length) {
          gloutonne += (largeur - 0.5 - w) / k / 5;
          lignesG++;
        }
        debut = fin;
      }
      final r = calculerMiseEnLignes(m, largeur, reglages: const ReglagesLignes(echelleMin: 1.0, echelleMax: 1.0));
      if (r == null) continue;
      for (final l in r.lignes) {
        if (l.nbEspaces > 0 && l.fin < m.mots.length) {
          optimale += l.espace / 5;
          lignesO++;
        }
      }
    }
    expect(lignesG, greaterThan(500));
    expect(lignesO, greaterThan(100));
    expect(optimale / lignesO, lessThan(gloutonne / lignesG));
  });

  test('entrées invalides', () {
    expect(calculerMiseEnLignes(const ModeleParagraphe(<double>[], <double>[]), largeur), isNull);
    expect(calculerMiseEnLignes(const ModeleParagraphe(<double>[50, 50], <double>[5]), 0), isNull);
    expect(calculerMiseEnLignes(const ModeleParagraphe(<double>[50, 50], <double>[]), largeur), isNull);
  });
}
