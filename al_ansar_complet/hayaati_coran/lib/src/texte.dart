/// Préparation du texte coranique à l'affichage. Port de core/quran_engine.py (fonctions sans accès aux fichiers).
///
/// Dart compte en unités UTF-16 et Python en points de code : les positions des annotations de tajweed
/// restent valables parce que tout le texte de Tanzil est dans le plan multilingue de base (vérifié par
/// outils/generer_golden_coran.py, qui refuse de produire le fichier de référence sinon).
library;

import 'tajweed.dart';

const int nbPages = 604;

const String signeSajda = '\u06e9'; // ۩ (déjà présent dans le texte Tanzil des 15 versets de prosternation)
const String signeHizb = '\u06de'; // ۞
const String signesPause = '\u06d6\u06d7\u06d8\u06d9\u06da\u06db'; // ۖ ۗ ۘ ۙ ۚ ۛ
const String espaceInsecable = '\u00a0';

/// Signes dessinés avec une police dédiée (HayaatiSignes) : la police du texte dessine ۩ comme une fleur,
/// alors que le signe connu des lecteurs est l'arche (niche).
const String signesOrnementaux = '\u06e9\u06de';

/// Parenthèses ornées du numéro de verset, dans l'ORDRE LOGIQUE de la chaîne : en lecture de droite à gauche, le
/// premier caractère s'affiche à DROITE. On voit donc « ﴾ ١٢ ﴿ » : ouvrante à gauche, fermante à droite comme dans
/// un mushaf. Si un appareil affichait l'inverse, échanger ces deux constantes est la SEULE modification à faire.
const String marqueurPremier = '\ufd3f'; // ﴿ affiché à droite en RTL
const String marqueurDernier = '\ufd3e'; // ﴾ affiché à gauche en RTL

/// 12 -> ١٢ (chiffres arabes-indiens, comme dans un mushaf).
String chiffresArabes(int nombre) {
  final sortie = StringBuffer();
  for (final u in nombre.toString().codeUnits) {
    sortie.writeCharCode((u >= 0x30 && u <= 0x39) ? 0x0660 + (u - 0x30) : u);
  }
  return sortie.toString();
}

/// Marqueur de fin de verset : espace insécable devant (le numéro ne se retrouve jamais seul en début de ligne),
/// parenthèses ornées autour du numéro en chiffres arabes-indiens, espace normale derrière.
String marqueurVerset(int numero) => '$espaceInsecable$marqueurPremier${chiffresArabes(numero)}$marqueurDernier ';

/// Anti-orphelins, À L'AFFICHAGE SEULEMENT (le texte stocké reste verbatim) : l'espace qui précède un signe de pause
/// ou ۩, et celle qui suit ۞, devient insécable. Remplacement d'un caractère par un autre : les positions des
/// annotations de tajweed restent valables.
String preparerTexteAffichage(String texte) {
  final c = texte.codeUnits.toList();
  final pause = signesPause.codeUnits;
  final sajda = signeSajda.codeUnitAt(0);
  final hizb = signeHizb.codeUnitAt(0);
  for (var i = 0; i < c.length; i++) {
    if (c[i] != 0x20) continue;
    final suivant = i + 1 < c.length ? c[i + 1] : -1;
    final precedent = i > 0 ? c[i - 1] : -1;
    if (suivant != -1 && (pause.contains(suivant) || suivant == sajda)) {
      c[i] = 0xA0;
    } else if (precedent == hizb) {
      c[i] = 0xA0;
    }
  }
  return String.fromCharCodes(c);
}

class MorceauTexte {
  const MorceauTexte(this.texte, this.estSigne);

  final String texte;
  final bool estSigne;
}

/// Sépare les signes ornementaux du reste. Le texte n'est pas modifié, seulement découpé (la concaténation redonne
/// l'original). Sans signe : un seul morceau.
List<MorceauTexte> decouperSignes(String texte) {
  final morceaux = <MorceauTexte>[];
  var debut = 0;
  for (var i = 0; i < texte.length; i++) {
    if (signesOrnementaux.contains(texte[i])) {
      if (i > debut) morceaux.add(MorceauTexte(texte.substring(debut, i), false));
      morceaux.add(MorceauTexte(texte[i], true));
      debut = i + 1;
    }
  }
  if (debut < texte.length) morceaux.add(MorceauTexte(texte.substring(debut), false));
  return morceaux.isEmpty ? <MorceauTexte>[MorceauTexte(texte, false)] : morceaux;
}

class SegmentTexte {
  const SegmentTexte(this.texte, this.famille);

  final String texte;

  /// Indice de couleur du tajweed (0-4), ou -1 pour le texte ordinaire.
  final int famille;
}

/// Annotations de tajweed lues d'un JSON : [[debut, fin, code], ...].
List<List<int>> annotationsDepuisJson(Object? brut) {
  if (brut is! List) return const <List<int>>[];
  final sortie = <List<int>>[];
  for (final a in brut) {
    if (a is List && a.length >= 3 && a[0] is int && a[1] is int && a[2] is int) {
      sortie.add(<int>[a[0] as int, a[1] as int, a[2] as int]);
    }
  }
  return sortie;
}

/// Découpe le texte (déjà préparé pour l'affichage) en segments par famille de couleur. Sans tajweed : un seul
/// segment. Chevauchements : la première annotation (par position dans la liste) l'emporte.
List<SegmentTexte> segmentsVerset(String texte, List<List<int>>? annotations, bool avecTajweed) {
  if (!avecTajweed || annotations == null || annotations.isEmpty) {
    return <SegmentTexte>[SegmentTexte(texte, -1)];
  }
  final familles = List<int>.filled(texte.length, -1);
  for (final a in annotations) {
    final fam = indiceFamille(a[2]);
    if (fam < 0) continue;
    final debut = a[0] < 0 ? 0 : a[0];
    final fin = a[1] > texte.length ? texte.length : a[1];
    for (var i = debut; i < fin; i++) {
      if (familles[i] == -1) familles[i] = fam;
    }
  }
  final segments = <SegmentTexte>[];
  var debut = 0;
  for (var i = 1; i <= texte.length; i++) {
    if (i == texte.length || familles[i] != familles[debut]) {
      segments.add(SegmentTexte(texte.substring(debut, i), familles[debut]));
      debut = i;
    }
  }
  return segments;
}
