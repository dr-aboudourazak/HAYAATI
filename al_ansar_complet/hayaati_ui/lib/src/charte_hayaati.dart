import 'package:flutter/material.dart';

import 'apparence.dart';

/// Les couleurs de l'apparence en cours, lues depuis le thème : `CharteHayaati.of(context).vertProfond`.
///
/// Les noms sont ceux de la palette officielle (PaletteHayaati) : un écran qui lisait `PaletteHayaati.sable` lit
/// maintenant `CharteHayaati.of(context).sable` et suit l'apparence choisie (clair, papier, sombre ; vert, terracotta,
/// ocre). Hors d'un thème HAYAATI, la charte clair/vert (la charte officielle) s'applique : un module reste donc
/// affichable seul, par exemple dans un test.
@immutable
class CharteHayaati extends ThemeExtension<CharteHayaati> {
  CharteHayaati._(this.apparence, this.valeurs);

  factory CharteHayaati.depuis(ApparenceHayaati apparence) => CharteHayaati._(apparence, ValeursCharte.pour(apparence));

  /// La charte officielle : fond clair, couleur principale verte.
  static final CharteHayaati defaut = CharteHayaati.depuis(ApparenceHayaati.defaut);

  static CharteHayaati of(BuildContext context) => Theme.of(context).extension<CharteHayaati>() ?? defaut;

  final ApparenceHayaati apparence;
  final ValeursCharte valeurs;

  bool get sombre => valeurs.sombre;

  // Bandeaux et boutons pleins, et le texte qui s'y trouve.
  Color get primaire => Color(valeurs.primaire);
  Color get surPrimaire => Color(valeurs.surPrimaire);

  // Accentuation du texte et des icônes (le vert, ou la couleur principale choisie).
  Color get vertProfond => Color(valeurs.vertProfond);
  Color get vertClair => Color(valeurs.vertClair);

  // Identité chaude.
  Color get terracotta => Color(valeurs.terracotta);
  Color get terracottaClair => Color(valeurs.terracottaClair);
  Color get terracottaFonce => Color(valeurs.terracottaFonce);
  Color get ocre => Color(valeurs.ocre);
  Color get ocreClair => Color(valeurs.ocreClair);
  Color get ocreFonce => Color(valeurs.ocreFonce);

  // Texte, fonds et bordures.
  Color get texteFonce => Color(valeurs.texteFonce);
  Color get sable => Color(valeurs.sable);
  Color get blanc => Color(valeurs.blanc);
  Color get grisTexte => Color(valeurs.grisTexte);
  Color get grisClair => Color(valeurs.grisClair);
  Color get bordure => Color(valeurs.bordure);

  // Signalétique.
  Color get vertSucces => Color(valeurs.vertSucces);
  Color get rougeErreur => Color(valeurs.rougeErreur);
  Color get ambreAttente => Color(valeurs.ambreAttente);

  // Page du Coran.
  Color get fondPage => Color(valeurs.fondPage);
  Color get surlignage => Color(valeurs.surlignage);
  Color get numeroVerset => Color(valeurs.numeroVerset);
  Color get numeroSignet => Color(valeurs.numeroSignet);

  /// Couleur d'une famille du tajweed (0 à 4) ; null hors limites.
  Color? tajweed(int famille, {bool surSurlignage = false}) {
    final liste = surSurlignage ? valeurs.tajweedSurSurlignage : valeurs.tajweed;
    return famille >= 0 && famille < liste.length ? Color(liste[famille]) : null;
  }

  @override
  CharteHayaati copyWith({ApparenceHayaati? apparence}) =>
      apparence == null ? this : CharteHayaati.depuis(apparence);

  /// Pas d'interpolation entre deux chartes : le thème bascule à mi-parcours de l'animation.
  @override
  CharteHayaati lerp(ThemeExtension<CharteHayaati>? other, double t) => other is CharteHayaati && t >= 0.5 ? other : this;
}
