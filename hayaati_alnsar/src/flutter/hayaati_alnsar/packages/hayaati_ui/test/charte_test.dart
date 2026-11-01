import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hayaati_ui/hayaati_ui.dart';

void main() {
  test('couleurDepuisHex lit les formats valides', () {
    expect(couleurDepuisHex('#dc2626'), const Color(0xFFDC2626));
    expect(couleurDepuisHex('2563EB'), const Color(0xFF2563EB));
    expect(couleurDepuisHex(' #f9fafb '), const Color(0xFFF9FAFB));
  });

  test('couleurDepuisHex refuse les valeurs invalides', () {
    expect(couleurDepuisHex(null), isNull);
    expect(couleurDepuisHex(''), isNull);
    expect(couleurDepuisHex('#fff'), isNull);
    expect(couleurDepuisHex('#zzzzzz'), isNull);
  });

  test('la palette officielle est inchangée', () {
    expect(PaletteHayaati.vertProfond, const Color(0xFF064E3B));
    expect(PaletteHayaati.terracotta, const Color(0xFFC1502E));
    expect(PaletteHayaati.ocre, const Color(0xFFD9A441));
    expect(PaletteHayaati.sable, const Color(0xFFFBF6EE));
  });
}
