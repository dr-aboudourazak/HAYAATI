import 'dart:convert';
import 'dart:io';

import 'package:al_ansar/al_ansar.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  late Annuaire annuaire;

  setUpAll(() {
    annuaire = Annuaire.fromJson(
      jsonDecode(File('example/assets/al_ansar/annuaire_TG.json').readAsStringSync()) as Json,
    );
  });

  test('module Hadj et Omra actif et agence avec agrément', () {
    expect(annuaire.modulesActifs, contains('hadj_omra'));
    final agence = annuaire.fiches.firstWhere((f) => f.type == 'agence');
    expect(agence.agence.agrement?.numero, 'EXEMPLE-0000');
    expect(agence.agence.agrement?.valideJusqua, '2028-12-31');
    expect(agence.niveau, 2);
  });

  test('forfait complet : 14 jours, score de transparence 100', () {
    final f = annuaire.forfaits.firstWhere((x) => x.id == 'tg-lome-fft-001');
    expect(f.type, 'omra');
    expect(f.dureeJours, 14);
    expect(f.montant, 1450000);
    expect(f.devise, 'XOF');
    expect(f.hotelMakkah?.distanceM, 350);
    expect(f.hotelMadina?.distanceM, 250);
    expect(f.fraisNonInclus?.length, 2);
    expect(f.scoreTransparence, 100);
  });

  test('forfait partiel : rubriques absentes comptées comme non renseignées', () {
    final f = annuaire.forfaits.firstWhere((x) => x.id == 'tg-lome-fft-002');
    expect(f.type, 'hadj');
    expect(f.hotelMadina, isNull);
    expect(f.fraisNonInclus, isNull);
    expect(f.annulation, isEmpty);
    expect(f.scoreTransparence, 18);
  });
}
