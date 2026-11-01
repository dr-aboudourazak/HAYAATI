import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:hayaati_ui/hayaati_ui.dart';

import '../etat_lecture.dart';
import '../moteur_coran.dart';
import '../polices.dart';
import '../tajweed.dart';
import '../texte.dart';
import 'constantes_ui.dart';

/// Style du texte coranique : police choisie, taille effective, interligne propre à la police.
TextStyle styleTexteCoran(ConfigPolice police, double taille) => TextStyle(
      fontFamily: police.famille,
      fontFamilyFallback: reserveArabe,
      fontSize: taille,
      height: police.hauteur,
      color: PaletteHayaati.texteFonce,
    );

/// Morceaux de texte d'un passage : tajweed (si actif) par segments de couleur, sinon un seul morceau. Les signes
/// ۩ et ۞ sont découpés à part et dessinés avec la police HayaatiSignes.
///
/// [taille] est la taille effective du texte (taille choisie x facteur de la police). [fond] : surlignage du verset
/// sélectionné ; le texte orange et gris du tajweed y prend alors sa variante plus foncée, lisible sur le jaune.
/// [geste] : reconnaisseur de toucher partagé par tous les morceaux du verset.
List<InlineSpan> spansTexte({
  required String texte,
  required List<List<int>>? annotations,
  required Color couleurBase,
  required bool tajweed,
  required double taille,
  Color? fond,
  GestureRecognizer? geste,
}) {
  final prepare = preparerTexteAffichage(texte);
  final surSurlignage = fond != null;
  final spans = <InlineSpan>[];
  for (final segment in segmentsVerset(prepare, annotations, tajweed)) {
    final hex = couleurFamille(segment.famille, surSurlignage: surSurlignage);
    final couleur = (hex != null ? couleurDepuisHex(hex) : null) ?? couleurBase;
    for (final morceau in decouperSignes(segment.texte)) {
      if (morceau.estSigne) {
        spans.add(TextSpan(
          text: morceau.texte,
          recognizer: geste,
          style: TextStyle(fontFamily: familleSignes, color: couleur, backgroundColor: fond, fontSize: taille * rapportSigne),
        ));
      } else {
        spans.add(TextSpan(
          text: morceau.texte,
          recognizer: geste,
          style: TextStyle(color: couleur, backgroundColor: fond),
        ));
      }
    }
  }
  return spans;
}

/// Versets d'une sourate, chacun suivi de son numéro entre parenthèses ornées, à la suite comme dans un mushaf.
/// Vert alterné (pairs plus foncés) quand le tajweed est éteint ; texte foncé uni quand il est allumé, pour que
/// ses couleurs ressortent. Toucher n'importe quelle partie d'un verset (texte, signe ou numéro) le sélectionne.
List<InlineSpan> spansVersets({
  required int sourate,
  required List<VersetCoran> versets,
  required EtatLecture etat,
  required double taille,
  VersetRef? selection,
  GestureRecognizer Function(int sourate, int verset)? geste,
}) {
  final spans = <InlineSpan>[];
  for (final v in versets) {
    final base = etat.tajweed
        ? PaletteHayaati.texteFonce
        : (v.numero.isEven ? PaletteHayaati.vertProfond : PaletteHayaati.vertClair);
    final selectionne = selection != null && selection.sourate == sourate && selection.verset == v.numero;
    final fond = selectionne ? surlignage : null;
    final g = geste?.call(sourate, v.numero);
    spans.addAll(spansTexte(
      texte: v.texte,
      annotations: v.tajweed,
      couleurBase: base,
      tajweed: etat.tajweed,
      taille: taille,
      fond: fond,
      geste: g,
    ));
    spans.add(TextSpan(
      text: marqueurVerset(v.numero),
      recognizer: g,
      style: TextStyle(
        color: etat.estSignetVerset(sourate, v.numero) ? couleurNumeroSignet : couleurNumero,
        backgroundColor: fond,
        fontSize: taille * rapportNumero,
      ),
    ));
  }
  return spans;
}
