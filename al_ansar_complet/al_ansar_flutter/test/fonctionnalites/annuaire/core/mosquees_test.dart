import 'dart:convert';
import 'dart:io';

import 'package:al_ansar/al_ansar.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  late Annuaire mosquees;

  setUpAll(() {
    mosquees = Annuaire.fromJson(
      jsonDecode(File('example/assets/al_ansar/mosquees_TG.json').readAsStringSync()) as Json,
    );
  });

  test('positions : source, vérification et précision', () {
    expect(mosquees.fiches.every((f) => !f.gpsVerifiee), isTrue);
    expect(mosquees.fiches.first.gpsSource, 'estimee');
    expect(mosquees.fiches.where((f) => f.gpsSource == 'openstreetmap').length, 2);
    expect(mosquees.fiches.first.gpsPrecisionM, isNull);
  });

  test('contact du responsable qui reçoit les propositions', () {
    expect(mosquees.moderationWhatsapp, startsWith('+'));
  });
}
