import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:hayaati_ui/hayaati_ui.dart';

void main() {
  // Toutes les apparences possibles : 3 fonds x 3 couleurs.
  final toutes = <ApparenceHayaati>[
    for (final f in fondsApparence)
      for (final c in couleursApparence) ApparenceHayaati(fond: f, couleur: c),
  ];

  test('le thème clair vert est la charte officielle, à l\'identique de palette_hayaati.py', () {
    final v = ValeursCharte.pour(ApparenceHayaati.defaut);
    expect(v.vertProfond, 0xFF064E3B);
    expect(v.vertClair, 0xFF0F766E);
    expect(v.terracotta, 0xFFC1502E);
    expect(v.ocre, 0xFFD9A441);
    expect(v.ocreClair, 0xFFFBF0DA);
    expect(v.texteFonce, 0xFF2B1607);
    expect(v.sable, 0xFFFBF6EE);
    expect(v.blanc, 0xFFFFFFFF);
    expect(v.grisTexte, 0xFF374151);
    expect(v.grisClair, 0xFFF3F4F6);
    expect(v.vertSucces, 0xFF27500A);
    expect(v.rougeErreur, 0xFF791F1F);
    expect(v.ambreAttente, 0xFFD97706);
    expect(v.primaire, v.vertProfond);
  });

  test('papier et sombre gardent l\'identité : même terracotta et même ocre, sauf éclaircies du sombre', () {
    for (final c in couleursApparence) {
      final p = ValeursCharte.pour(ApparenceHayaati(fond: 'papier', couleur: c));
      expect(p.terracotta, 0xFFC1502E);
      expect(p.ocre, 0xFFD9A441);
    }
    expect(ValeursCharte.pour(const ApparenceHayaati(fond: 'sombre')).ocre, 0xFFD9A441);
  });

  group('contrastes de lisibilité (WCAG), pour chacune des 9 apparences', () {
    for (final a in toutes) {
      final v = ValeursCharte.pour(a);
      final nom = '${a.fond}/${a.couleur}';
      void au_moins(double seuil, int texte, int fond, String quoi) {
        final r = contraste(texte, fond);
        expect(r, greaterThanOrEqualTo(seuil), reason: '$nom : $quoi = ${r.toStringAsFixed(2)} (minimum $seuil)');
      }

      test('$nom : texte courant', () {
        for (final fond in <int>[v.sable, v.blanc, v.grisClair, v.fondPage]) {
          au_moins(7.0, v.texteFonce, fond, 'texte de corps sur ${fond.toRadixString(16)}');
        }
        for (final fond in <int>[v.sable, v.blanc, v.grisClair]) {
          au_moins(4.5, v.grisTexte, fond, 'texte secondaire sur ${fond.toRadixString(16)}');
        }
      });

      test('$nom : accentuation, bandeaux et boutons', () {
        for (final fond in <int>[v.sable, v.blanc, v.grisClair, v.fondPage]) {
          au_moins(4.5, v.vertProfond, fond, 'accentuation sur ${fond.toRadixString(16)}');
          au_moins(4.5, v.vertClair, fond, 'accentuation 2 sur ${fond.toRadixString(16)}');
        }
        au_moins(4.5, v.surPrimaire, v.primaire, 'texte sur bandeau');
        au_moins(4.5, v.terracottaFonce, v.sable, 'terracotta foncé sur le fond');
        au_moins(4.5, v.terracottaFonce, v.blanc, 'terracotta foncé sur les cartes');
        au_moins(4.5, v.ocreFonce, v.sable, 'ocre foncé sur le fond');
        au_moins(4.5, v.ocreFonce, v.blanc, 'ocre foncé sur les cartes');
      });

      test('$nom : signalétique', () {
        for (final fond in <int>[v.sable, v.blanc]) {
          au_moins(4.5, v.rougeErreur, fond, 'erreur');
          au_moins(4.5, v.vertSucces, fond, 'succès');
        }
        // Charte d'origine : l'ambre (D97706) atteint 2,96 sur le fond sable, un peu sous 3 ; conservé à l'identique.
        final ambre = a.fond == 'clair' ? 2.9 : 3.0;
        au_moins(ambre, v.ambreAttente, v.blanc, 'attente (icône)');
        au_moins(ambre, v.ambreAttente, v.sable, 'attente (icône) sur le fond');
        au_moins(3.0, v.terracotta, v.blanc, 'terracotta (ornement) sur les cartes');
        au_moins(3.0, v.terracotta, v.sable, 'terracotta (ornement) sur le fond');
      });

      test('$nom : page du Coran', () {
        au_moins(4.5, v.numeroVerset, v.fondPage, 'numéro de verset');
        au_moins(4.5, v.numeroVerset, v.surlignage, 'numéro de verset sur surlignage');
        au_moins(4.5, v.numeroSignet, v.fondPage, 'numéro de signet');
        au_moins(4.5, v.numeroSignet, v.surlignage, 'numéro de signet sur surlignage');
        au_moins(7.0, v.texteFonce, v.surlignage, 'texte sur surlignage');
        au_moins(4.5, v.vertProfond, v.surlignage, 'verset vert sur surlignage');
        au_moins(1.2, v.surlignage, v.fondPage, 'le surlignage se distingue de la page');
      });

      test('$nom : tajweed lisible sur la page et sur le surlignage', () {
        final clair = a.fond == 'clair';
        for (var i = 0; i < 5; i++) {
          // Les lettres muettes (famille 4) sont volontairement atténuées. Le thème clair reprend à l'identique les
          // couleurs de la charte d'origine (orange 3,03 sur la page ; 3,96 à 4,44 sur le surlignage jaune).
          final page = i == 4 ? 2.4 : (clair && i == 2 ? 3.0 : 4.5);
          final surligne = i == 4 ? 4.0 : (clair ? 3.9 : 4.5);
          au_moins(page, v.tajweed[i], v.fondPage, 'tajweed $i sur la page');
          au_moins(surligne, v.tajweedSurSurlignage[i], v.surlignage, 'tajweed $i sur le surlignage');
        }
      });
    }
  });

  test('les cinq couleurs du tajweed restent distinctes entre elles dans chaque apparence', () {
    for (final a in toutes) {
      final v = ValeursCharte.pour(a);
      expect(v.tajweed.toSet().length, 5, reason: a.toString());
    }
  });

  group('ApparenceHayaati (enregistrée en JSON)', () {
    test('valeurs par défaut et allers-retours', () {
      expect(ApparenceHayaati.defaut, const ApparenceHayaati(fond: 'clair', couleur: 'vert'));
      for (final a in toutes) {
        expect(ApparenceHayaati.depuisJson(jsonDecode(jsonEncode(a.toJson()))), a);
      }
    });

    test('un contenu invalide ramène à des valeurs sûres, sans plantage', () {
      expect(ApparenceHayaati.depuisJson(null), ApparenceHayaati.defaut);
      expect(ApparenceHayaati.depuisJson('texte'), ApparenceHayaati.defaut);
      expect(ApparenceHayaati.depuisJson(<String, Object>{'fond': 'rose', 'couleur': 'rouge'}), ApparenceHayaati.defaut);
      expect(ApparenceHayaati.depuisJson(<String, Object>{'fond': 'sombre'}), const ApparenceHayaati(fond: 'sombre'));
      expect(ApparenceHayaati.depuisJson(<String, Object>{'fond': 7, 'couleur': 'ocre'}), const ApparenceHayaati(couleur: 'ocre'));
    });

    test('avec() et sombre', () {
      expect(ApparenceHayaati.defaut.avec(fond: 'sombre').sombre, isTrue);
      expect(ApparenceHayaati.defaut.avec(couleur: 'ocre').couleur, 'ocre');
      expect(ApparenceHayaati.defaut.sombre, isFalse);
    });
  });

  test('contraste : valeurs de référence', () {
    expect(contraste(0xFF000000, 0xFFFFFFFF), closeTo(21.0, 0.01));
    expect(contraste(0xFFFFFFFF, 0xFFFFFFFF), closeTo(1.0, 0.001));
    expect(contraste(0xFF777777, 0xFFFFFFFF), closeTo(4.48, 0.05));
  });
}
