import 'package:al_ansar/al_ansar.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('palette identique à gui/palette_hayaati.py', () {
    expect(PaletteHayaati.vertProfond, const Color(0xFF064E3B));
    expect(PaletteHayaati.vertClair, const Color(0xFF0F766E));
    expect(PaletteHayaati.terracotta, const Color(0xFFC1502E));
    expect(PaletteHayaati.terracottaClair, const Color(0xFFF4E4DC));
    expect(PaletteHayaati.terracottaFonce, const Color(0xFF6B2712));
    expect(PaletteHayaati.ocre, const Color(0xFFD9A441));
    expect(PaletteHayaati.ocreClair, const Color(0xFFFBF0DA));
    expect(PaletteHayaati.ocreFonce, const Color(0xFF7A5510));
    expect(PaletteHayaati.texteFonce, const Color(0xFF2B1607));
    expect(PaletteHayaati.sable, const Color(0xFFFBF6EE));
    expect(PaletteHayaati.grisTexte, const Color(0xFF374151));
    expect(PaletteHayaati.grisClair, const Color(0xFFF3F4F6));
    expect(PaletteHayaati.vertSucces, const Color(0xFF27500A));
    expect(PaletteHayaati.rougeErreur, const Color(0xFF791F1F));
    expect(PaletteHayaati.ambreAttente, const Color(0xFFD97706));
  });

  test('thème : bandeau vert profond, fond sable, texte foncé, accents terracotta et ocre', () {
    final t = themeHayaati();
    expect(t.colorScheme.primary, PaletteHayaati.vertProfond);
    expect(t.colorScheme.secondary, PaletteHayaati.terracotta);
    expect(t.colorScheme.tertiary, PaletteHayaati.ocre);
    expect(t.colorScheme.onSurface, PaletteHayaati.texteFonce);
    expect(t.scaffoldBackgroundColor, PaletteHayaati.sable);
    expect(t.appBarTheme.backgroundColor, PaletteHayaati.vertProfond);
    expect(t.appBarTheme.foregroundColor, PaletteHayaati.blanc);
  });
}
