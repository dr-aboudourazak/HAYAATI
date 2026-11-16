import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hayaati_coran/src/ui/justification.dart';

/// Ces tests utilisent la police de test de Flutter (Ahem : chaque caractère est un carré de la taille de la police),
/// donc les largeurs sont exactes et reproductibles.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  String texteDe(List<InlineSpan> spans) => TextSpan(children: spans).toPlainText(includeSemanticsLabels: false);

  group('découpe des spans', () {
    const rouge = TextStyle(color: Color(0xFFFF0000));
    const bleu = TextStyle(color: Color(0xFF0000FF));
    final spans = <InlineSpan>[const TextSpan(text: 'abcdef', style: rouge), const TextSpan(text: 'ghi', style: bleu)];

    test('couper au milieu d\'un span garde le texte, les styles et l\'ordre', () {
      final c = couperSpans(spans, 4);
      expect(texteDe(c.avant), 'abcd');
      expect(texteDe(c.apres), 'efghi');
      expect((c.avant.last as TextSpan).style, rouge);
      expect((c.apres.first as TextSpan).style, rouge);
      expect((c.apres.last as TextSpan).style, bleu);
    });

    test('couper à une frontière de span, au début et à la fin', () {
      expect(texteDe(couperSpans(spans, 6).avant), 'abcdef');
      expect(texteDe(couperSpans(spans, 6).apres), 'ghi');
      expect(texteDe(couperSpans(spans, 0).avant), '');
      expect(texteDe(couperSpans(spans, 0).apres), 'abcdefghi');
      expect(texteDe(couperSpans(spans, 9).apres), '');
    });

    test('espacerFin n\'élargit que les espaces après le point de coupe', () {
      final r = espacerFin(spans, 4, 1.0, 2.5);
      expect(texteDe(r), 'abcdefghi');
      expect((r.first as TextSpan).style?.wordSpacing, isNull); // « abcd » : avant la coupe
      expect((r[1] as TextSpan).style?.wordSpacing, 3.5); // « ef » : espaceGlobal + espaceFin
      expect((r.last as TextSpan).style?.wordSpacing, 3.5);
      expect(identical(espacerFin(spans, 4, 1.0, 0), spans), isTrue);
    });

    test('sansEspaceFinal retire l\'espace qui suit le dernier numéro de verset', () {
      expect(texteDe(sansEspaceFinal(<InlineSpan>[const TextSpan(text: 'abc'), const TextSpan(text: ' ﴿٣﴾ ')])), 'abc ﴿٣﴾');
      expect(texteDe(sansEspaceFinal(<InlineSpan>[const TextSpan(text: 'abc')])), 'abc');
    });
  });

  test('calculerJustification : la dernière ligne finit au bout de la ligne, sans débordement', () {
    const taille = 10.0;
    final texte = <String>[for (var i = 0; i < 45; i++) 'a' * (3 + (i * 7) % 6)].join(' ');
    List<InlineSpan> spans(double e) => <InlineSpan>[TextSpan(text: '$texte ')];
    TextStyle style(double e) => TextStyle(fontFamily: 'Ahem', fontSize: taille * e, height: 1.0);
    const largeur = 330.0;

    double fin(List<InlineSpan> s, TextStyle st) {
      final p = TextPainter(text: TextSpan(style: st, children: s), textDirection: TextDirection.rtl)
        ..layout(maxWidth: largeur);
      final l = p.computeLineMetrics();
      p.dispose();
      expect(l.length, greaterThan(1));
      return l.last.width;
    }

    final avant = fin(sansEspaceFinal(spans(1.0)), style(1.0)) / largeur;
    final p = calculerJustification(
      construireSpans: spans,
      construireStyle: style,
      largeur: largeur,
      echelleSysteme: TextScaler.noScaling,
    );
    expect(p.actif || avant >= 0.97, isTrue, reason: 'dernière ligne à $avant sans réglage, aucun réglage trouvé');
    final s = espacerFin(sansEspaceFinal(spans(p.echelle)), p.debutFin, p.espaceGlobal, p.espaceFin);
    final apres = fin(s, style(p.echelle).copyWith(wordSpacing: p.espaceGlobal)) / largeur;
    expect(apres, lessThanOrEqualTo(1.0));
    expect(apres, greaterThanOrEqualTo(avant - 1e-6));
    expect(apres, greaterThanOrEqualTo(0.85));
    expect(p.echelle, inInclusiveRange(0.91, 1.09));
  });

  test('calculerJustification : texte d\'une seule ligne ou largeur absurde : aucun réglage', () {
    List<InlineSpan> court(double e) => <InlineSpan>[const TextSpan(text: 'aaa aaa ')];
    TextStyle style(double e) => TextStyle(fontFamily: 'Ahem', fontSize: 10 * e);
    expect(
      calculerJustification(construireSpans: court, construireStyle: style, largeur: 330, echelleSysteme: TextScaler.noScaling).actif,
      isFalse,
    );
    expect(
      calculerJustification(construireSpans: court, construireStyle: style, largeur: 20, echelleSysteme: TextScaler.noScaling).actif,
      isFalse,
    );
    expect(
      calculerJustification(construireSpans: court, construireStyle: style, largeur: double.infinity, echelleSysteme: TextScaler.noScaling).actif,
      isFalse,
    );
  });

  group('mise en lignes justifiées (chaque ligne finit au bout de la ligne)', () {
    const taille = 10.0;
    const largeur = 330.0;
    TextStyle style(double e) => TextStyle(fontFamily: 'Ahem', fontSize: taille * e, height: 1.0);

    // Police de test Ahem : chaque caractère, espace comprise, est un carré de 10 px.
    List<InlineSpan> spansDe(String texte) => <InlineSpan>[TextSpan(text: '$texte ')];
    String texteLong(int nb) => <String>[for (var i = 0; i < nb; i++) 'a' * (3 + (i * 7) % 6)].join(' ');

    double largeurDe(List<InlineSpan> spans, TextStyle st) {
      final p = TextPainter(text: TextSpan(style: st, children: spans), textDirection: TextDirection.rtl)..layout();
      final w = p.computeLineMetrics().first.width;
      p.dispose();
      return w;
    }

    test('chaque ligne, la dernière comprise, atteint le bout de la ligne', () {
      final texte = texteLong(60);
      final d = calculerDisposition(
        construireSpans: (e) => spansDe(texte),
        construireStyle: style,
        largeur: largeur,
        echelleSysteme: TextScaler.noScaling,
      );
      expect(d, isNotNull);
      expect(d!.lignes.length, greaterThan(2));
      final spans = sansEspaceFinal(spansDe(texte));
      for (final l in d.lignes) {
        final contenu = extraireSpans(spans, l.debut, l.fin);
        final w = largeurDe(contenu, style(d.echelle).copyWith(wordSpacing: l.espace));
        expect(w, closeTo(largeur - 0.5, 1.5), reason: 'ligne ${l.debut}-${l.fin}');
      }
      expect(d.echelle, inInclusiveRange(0.88, 1.12));
    });

    test('les lignes reconstituent exactement le texte, sans perte ni doublon', () {
      final texte = texteLong(45);
      final d = calculerDisposition(
        construireSpans: (e) => spansDe(texte),
        construireStyle: style,
        largeur: largeur,
        echelleSysteme: TextScaler.noScaling,
      )!;
      final spans = sansEspaceFinal(spansDe(texte));
      final lignes = <String>[for (final l in d.lignes) texteDe(extraireSpans(spans, l.debut, l.fin))];
      expect(lignes.join(' '), texte);
      expect(d.lignes.first.debut, 0);
      expect(d.lignes.last.fin, texte.length);
    });

    test('un bloc trop court pour remplir une ligne : pas de mise en lignes, repli sans erreur', () {
      List<InlineSpan> court(double e) => spansDe('aa aa');
      expect(
        calculerDisposition(construireSpans: court, construireStyle: style, largeur: largeur, echelleSysteme: TextScaler.noScaling),
        isNull,
      );
      final plan = calculerPlan(construireSpans: court, construireStyle: style, largeur: largeur, echelleSysteme: TextScaler.noScaling);
      expect(plan.disposition, isNull);
      expect(plan.params.actif, isFalse);
    });

    test('calculerPlan privilégie la mise en lignes quand elle est possible', () {
      final texte = texteLong(60);
      final plan = calculerPlan(
        construireSpans: (e) => spansDe(texte),
        construireStyle: style,
        largeur: largeur,
        echelleSysteme: TextScaler.noScaling,
      );
      expect(plan.disposition, isNotNull);
    });

    test('largeur absurde : aucun calcul', () {
      final texte = texteLong(20);
      for (final l in <double>[10, double.infinity, double.nan]) {
        expect(
          calculerDisposition(construireSpans: (e) => spansDe(texte), construireStyle: style, largeur: l, echelleSysteme: TextScaler.noScaling),
          isNull,
        );
      }
    });
  });
}
