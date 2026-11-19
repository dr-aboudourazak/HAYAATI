import 'package:flutter/material.dart';

import '../justification_calcul.dart';
import '../mise_en_lignes.dart';

/// Réglages retenus pour qu'un bloc de versets finisse exactement au bout de sa dernière ligne.
class ParamsJustification {
  const ParamsJustification({this.echelle = 1.0, this.espaceGlobal = 0.0, this.espaceFin = 0.0, this.debutFin = -1});

  /// Facteur appliqué à la taille du texte (de 0,91 à 1,09).
  final double echelle;

  /// Pixels ajoutés à chaque espace de tout le texte.
  final double espaceGlobal;

  /// Pixels ajoutés, en plus, aux espaces de la dernière ligne seule.
  final double espaceFin;

  /// Position du premier caractère de la dernière ligne (unités UTF-16).
  final int debutFin;

  static const ParamsJustification aucun = ParamsJustification();

  bool get actif => echelle != 1.0 || espaceGlobal != 0.0 || espaceFin != 0.0;
}

/// Spans du texte à une échelle donnée, SANS reconnaisseur de geste (pour les mesures).
typedef ConstruireSpans = List<InlineSpan> Function(double echelle);

/// Style racine du texte à une échelle donnée.
typedef ConstruireStyle = TextStyle Function(double echelle);

/// Retire l'espace qui suit le dernier numéro de verset : il ne doit pas compter dans la dernière ligne.
List<InlineSpan> sansEspaceFinal(List<InlineSpan> spans) {
  if (spans.isEmpty) return spans;
  final dernier = spans.last;
  if (dernier is TextSpan && dernier.text != null && dernier.text!.endsWith(' ')) {
    return <InlineSpan>[
      ...spans.sublist(0, spans.length - 1),
      TextSpan(text: dernier.text!.trimRight(), style: dernier.style, recognizer: dernier.recognizer),
    ];
  }
  return spans;
}

/// Coupe une liste de TextSpan plats à [position] (unités UTF-16 du texte concaténé). Un span qui chevauche la
/// position est coupé en deux, avec le même style et le même reconnaisseur de geste.
({List<InlineSpan> avant, List<InlineSpan> apres}) couperSpans(List<InlineSpan> spans, int position) {
  final avant = <InlineSpan>[];
  final apres = <InlineSpan>[];
  var decalage = 0;
  for (final s in spans) {
    if (s is! TextSpan || s.text == null) {
      (decalage < position ? avant : apres).add(s);
      continue;
    }
    final texte = s.text!;
    final fin = decalage + texte.length;
    if (fin <= position) {
      avant.add(s);
    } else if (decalage >= position) {
      apres.add(s);
    } else {
      final k = position - decalage;
      avant.add(TextSpan(text: texte.substring(0, k), style: s.style, recognizer: s.recognizer));
      apres.add(TextSpan(text: texte.substring(k), style: s.style, recognizer: s.recognizer));
    }
    decalage = fin;
  }
  return (avant: avant, apres: apres);
}

/// Élargit de [espaceFin] pixels les espaces de la dernière ligne (à partir de [debutFin]), en plus de [espaceGlobal]
/// déjà appliqué à tout le texte par le style racine.
List<InlineSpan> espacerFin(List<InlineSpan> spans, int debutFin, double espaceGlobal, double espaceFin) {
  if (espaceFin == 0 || debutFin < 0) return spans;
  final c = couperSpans(spans, debutFin);
  return <InlineSpan>[
    ...c.avant,
    for (final s in c.apres)
      if (s is TextSpan)
        TextSpan(
          text: s.text,
          recognizer: s.recognizer,
          children: s.children,
          style: (s.style ?? const TextStyle()).copyWith(wordSpacing: espaceGlobal + espaceFin),
        )
      else
        s,
  ];
}

class _MesureReelle {
  const _MesureReelle(this.nbLignes, this.largeurFin, this.debutFin);

  final int nbLignes;
  final double largeurFin;
  final int debutFin;
}

TextPainter _peintre(List<InlineSpan> spans, TextStyle style, TextScaler echelle) => TextPainter(
      text: TextSpan(style: style, children: spans),
      textDirection: TextDirection.rtl,
      textScaler: echelle,
    );

/// Vraie mise en page : nombre de lignes, largeur de la dernière et position de son premier caractère.
_MesureReelle _mesurer(List<InlineSpan> spans, TextStyle style, double largeur, TextScaler echelle) {
  final p = _peintre(spans, style, echelle)..layout(maxWidth: largeur);
  try {
    final lignes = p.computeLineMetrics();
    final longueur = TextSpan(children: spans).toPlainText(includeSemanticsLabels: false).length;
    final debut = longueur > 0 ? p.getLineBoundary(TextPosition(offset: longueur - 1)).start : 0;
    return _MesureReelle(lignes.length, lignes.isEmpty ? 0.0 : lignes.last.width, debut);
  } finally {
    p.dispose();
  }
}

double _largeurPlage(TextPainter p, int a, int b) {
  var somme = 0.0;
  for (final box in p.getBoxesForSelection(TextSelection(baseOffset: a, extentOffset: b))) {
    somme += box.right - box.left;
  }
  return somme;
}

/// Modèle d'un paragraphe et position (unités UTF-16) du début et de la fin de chaque mot.
class _ModeleDetaille {
  const _ModeleDetaille(this.modele, this.debuts, this.fins);

  final ModeleParagraphe modele;
  final List<int> debuts;
  final List<int> fins;
}

/// Largeur de chaque mot et de chaque espace, mesurée une fois sur une seule ligne. Les mots sont séparés par
/// l'espace ordinaire ; l'espace insécable reste dans le mot, comme dans la vraie coupure de lignes.
_ModeleDetaille _modeleDetaille(List<InlineSpan> spans, TextStyle style, TextScaler echelle) {
  final p = _peintre(spans, style, echelle)..layout();
  try {
    final texte = TextSpan(children: spans).toPlainText(includeSemanticsLabels: false);
    final mots = <double>[];
    final espaces = <double>[];
    final debuts = <int>[];
    final fins = <int>[];
    var gap = 0.0;
    var debut = 0;
    for (var i = 0; i <= texte.length; i++) {
      final fin = i == texte.length;
      if (fin || texte.codeUnitAt(i) == 0x20) {
        if (i > debut) {
          if (mots.isNotEmpty) espaces.add(gap);
          mots.add(_largeurPlage(p, debut, i));
          debuts.add(debut);
          fins.add(i);
          gap = 0.0;
        }
        if (!fin) gap += _largeurPlage(p, i, i + 1);
        debut = i + 1;
      }
    }
    return _ModeleDetaille(ModeleParagraphe(mots, espaces), debuts, fins);
  } finally {
    p.dispose();
  }
}

ModeleParagraphe _modele(List<InlineSpan> spans, TextStyle style, TextScaler echelle) =>
    _modeleDetaille(spans, style, echelle).modele;

/// Les spans entre les positions [a] (inclus) et [b] (exclu) du texte concaténé.
List<InlineSpan> extraireSpans(List<InlineSpan> spans, int a, int b) => couperSpans(couperSpans(spans, b).avant, a).apres;

/// Une ligne de la mise en page : texte de [debut] à [fin] (positions UTF-16), [espace] pixels ajoutés à chaque espace.
class LigneRendue {
  const LigneRendue(this.debut, this.fin, this.espace);

  final int debut;
  final int fin;
  final double espace;
}

/// Mise en page ligne par ligne : chaque ligne, y compris la dernière du bloc, finit au bout de la ligne.
class DispositionLignes {
  const DispositionLignes(this.echelle, this.lignes);

  final double echelle;
  final List<LigneRendue> lignes;
}

double _largeurLigne(List<InlineSpan> spans, TextStyle style, TextScaler echelle, double espace) {
  final p = _peintre(spans, style.copyWith(wordSpacing: espace), echelle)..layout();
  try {
    final lignes = p.computeLineMetrics();
    return lignes.isEmpty ? 0.0 : lignes.first.width;
  } finally {
    p.dispose();
  }
}

/// Choisit les coupures de lignes (mise_en_lignes.dart) puis VÉRIFIE chaque ligne par une vraie mesure : l'espacement
/// de chaque ligne est calibré sur la largeur réelle, pas sur le modèle. Retourne null si le bloc ne peut pas être mis
/// en lignes justifiées (par exemple une fin de sourate de deux mots) ou si la mesure réelle s'écarte trop du modèle.
DispositionLignes? calculerDisposition({
  required ConstruireSpans construireSpans,
  required ConstruireStyle construireStyle,
  required double largeur,
  required TextScaler echelleSysteme,
}) {
  try {
    if (!largeur.isFinite || largeur < 80) return null;
    final detail = _modeleDetaille(sansEspaceFinal(construireSpans(1.0)), construireStyle(1.0), echelleSysteme);
    if (detail.modele.mots.length < 2) return null;
    final mise = calculerMiseEnLignesAvecRepli(detail.modele, largeur);
    if (mise == null) return null;

    final spans = sansEspaceFinal(construireSpans(mise.echelle));
    final style = construireStyle(mise.echelle);
    final tri = List<double>.of(detail.modele.espaces)..sort();
    final espaceRef = (tri[tri.length ~/ 2] > 0.5 ? tri[tri.length ~/ 2] : 5.0) * mise.echelle;
    const marge = 0.5;
    final lignes = <LigneRendue>[];
    for (final l in mise.lignes) {
      final a = detail.debuts[l.debut];
      final b = detail.fins[l.fin - 1];
      final contenu = extraireSpans(spans, a, b);
      final w0 = _largeurLigne(contenu, style, echelleSysteme, 0);
      var ws = 0.0;
      if (l.nbEspaces > 0) {
        final k = _largeurLigne(contenu, style, echelleSysteme, 1) - w0;
        if (k < 0.5) return null; // aucun espace élargissable : le modèle ne correspond pas à la réalité
        ws = (largeur - marge - w0) / k;
        // Mêmes limites que le modèle, avec un peu de tolérance pour l'écart entre le modèle et la mesure réelle.
        if (ws / espaceRef > 10.5 || ws / espaceRef < -0.7) return null;
        for (var i = 0; i < 3 && _largeurLigne(contenu, style, echelleSysteme, ws) > largeur + 0.75; i++) {
          ws -= 0.05 * espaceRef;
        }
        if (_largeurLigne(contenu, style, echelleSysteme, ws) > largeur + 0.75) return null;
      } else if (w0 > largeur + 0.75) {
        return null;
      }
      lignes.add(LigneRendue(a, b, ws));
    }
    return DispositionLignes(mise.echelle, lignes);
  } catch (_) {
    return null;
  }
}

/// Résultat du calcul : une mise en lignes justifiées si elle est possible, sinon les réglages de l'ancienne méthode
/// (légère variation de taille et d'espacement, dernière ligne comblée), sinon rien (affichage normal).
class PlanJustification {
  const PlanJustification({this.disposition, this.params = ParamsJustification.aucun});

  final DispositionLignes? disposition;
  final ParamsJustification params;

  static const PlanJustification aucun = PlanJustification();
}

PlanJustification calculerPlan({
  required ConstruireSpans construireSpans,
  required ConstruireStyle construireStyle,
  required double largeur,
  required TextScaler echelleSysteme,
}) {
  final d = calculerDisposition(
    construireSpans: construireSpans,
    construireStyle: construireStyle,
    largeur: largeur,
    echelleSysteme: echelleSysteme,
  );
  if (d != null) return PlanJustification(disposition: d);
  return PlanJustification(
    params: calculerJustification(
      construireSpans: construireSpans,
      construireStyle: construireStyle,
      largeur: largeur,
      echelleSysteme: echelleSysteme,
    ),
  );
}

/// Calcule les réglages qui font finir le texte exactement au bout de sa dernière ligne.
///
/// 1. mesure une fois la largeur de chaque mot ;
/// 2. cherche par simulation les combinaisons (légère échelle, espacement) qui remplissent la dernière ligne ;
/// 3. vérifie la meilleure par une VRAIE mise en page (le simulateur peut différer du moteur de texte) et passe à la
///    suivante si elle ne tient pas ;
/// 4. comble le petit manque restant en élargissant les seuls espaces de la dernière ligne.
/// En cas de doute ou d'erreur : [ParamsJustification.aucun], c'est-à-dire l'affichage normal.
ParamsJustification calculerJustification({
  required ConstruireSpans construireSpans,
  required ConstruireStyle construireStyle,
  required double largeur,
  required TextScaler echelleSysteme,
}) {
  try {
    if (!largeur.isFinite || largeur < 80) return ParamsJustification.aucun;
    final modele = _modele(sansEspaceFinal(construireSpans(1.0)), construireStyle(1.0), echelleSysteme);
    if (modele.mots.length < 2) return ParamsJustification.aucun;
    for (final c in chercherCandidats(modele, largeur).take(4)) {
      final spans = sansEspaceFinal(construireSpans(c.echelle));
      final style = construireStyle(c.echelle).copyWith(wordSpacing: c.espaceMots);
      final m0 = _mesurer(spans, style, largeur, echelleSysteme);
      if (m0.nbLignes < 2 || m0.largeurFin > largeur - 0.5) continue;
      if (m0.largeurFin / largeur < c.remplissage - 0.08) continue; // la mise en page réelle s'écarte trop du modèle
      var fin = 0.0;
      final m1 = _mesurer(espacerFin(spans, m0.debutFin, c.espaceMots, 1.0), style, largeur, echelleSysteme);
      if (m1.nbLignes == m0.nbLignes) {
        fin = espaceFinPour(largeur: largeur, w0: m0.largeurFin, w1: m1.largeurFin);
      }
      for (var i = 0; i < 6 && fin > 0; i++) {
        final v = _mesurer(espacerFin(spans, m0.debutFin, c.espaceMots, fin), style, largeur, echelleSysteme);
        if (v.nbLignes == m0.nbLignes && v.largeurFin <= largeur - 0.5) break;
        fin = i == 5 ? 0.0 : fin * 0.85;
      }
      return ParamsJustification(echelle: c.echelle, espaceGlobal: c.espaceMots, espaceFin: fin, debutFin: m0.debutFin);
    }
  } catch (_) {
    // Une mesure impossible ne doit jamais empêcher d'afficher le texte.
  }
  return ParamsJustification.aucun;
}
