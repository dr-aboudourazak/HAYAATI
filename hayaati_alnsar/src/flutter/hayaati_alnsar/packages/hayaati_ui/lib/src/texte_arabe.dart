import 'package:flutter/material.dart';

import 'palette.dart';

/// Polices embarquées dans ce paquet : Noto Sans Arabic (interface, arabe vocalisé) et HayaatiSignes
/// (signes ۩ ۞ ﷺ). Les familles d'un paquet sont désignées par « packages/<paquet>/<famille> ».
const String familleArabe = 'packages/hayaati_ui/NotoSansArabic';
const String familleSignes = 'packages/hayaati_ui/HayaatiSignes';
const List<String> reserveArabe = <String>[familleArabe, familleSignes];

/// Texte de lecture courant ; les passages arabes retombent sur les polices du paquet.
TextStyle styleCorps(BuildContext context, {double taille = 15}) =>
    (Theme.of(context).textTheme.bodyMedium ?? const TextStyle()).copyWith(
      fontSize: taille,
      height: 1.5,
      fontFamilyFallback: reserveArabe,
    );

/// Ligne purement arabe (lettre, mot, forme conjuguée, exemple) : grande, vocalisée, de droite à gauche.
TextStyle styleArabe({double taille = 26, Color? couleur}) => TextStyle(
      fontFamily: familleArabe,
      fontFamilyFallback: reserveArabe,
      fontSize: taille,
      height: 1.7,
      color: couleur ?? PaletteHayaati.texteFonce,
    );

class TexteArabe extends StatelessWidget {
  const TexteArabe(this.texte, {super.key, this.taille = 26, this.centre = false, this.couleur});

  final String texte;
  final double taille;
  final bool centre;
  final Color? couleur;

  @override
  Widget build(BuildContext context) {
    return Text(
      texte,
      textDirection: TextDirection.rtl,
      textAlign: centre ? TextAlign.center : TextAlign.start,
      style: styleArabe(taille: taille, couleur: couleur),
    );
  }
}
