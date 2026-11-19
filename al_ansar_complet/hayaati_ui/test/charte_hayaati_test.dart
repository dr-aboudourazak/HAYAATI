import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hayaati_ui/hayaati_ui.dart';

void main() {
  group('CharteHayaati', () {
    test('la charte par défaut est la palette officielle, couleur par couleur', () {
      final c = CharteHayaati.defaut;
      expect(c.vertProfond, PaletteHayaati.vertProfond);
      expect(c.vertClair, PaletteHayaati.vertClair);
      expect(c.terracotta, PaletteHayaati.terracotta);
      expect(c.terracottaClair, PaletteHayaati.terracottaClair);
      expect(c.terracottaFonce, PaletteHayaati.terracottaFonce);
      expect(c.ocre, PaletteHayaati.ocre);
      expect(c.ocreClair, PaletteHayaati.ocreClair);
      expect(c.ocreFonce, PaletteHayaati.ocreFonce);
      expect(c.texteFonce, PaletteHayaati.texteFonce);
      expect(c.sable, PaletteHayaati.sable);
      expect(c.blanc, PaletteHayaati.blanc);
      expect(c.grisTexte, PaletteHayaati.grisTexte);
      expect(c.grisClair, PaletteHayaati.grisClair);
      expect(c.vertSucces, PaletteHayaati.vertSucces);
      expect(c.rougeErreur, PaletteHayaati.rougeErreur);
      expect(c.ambreAttente, PaletteHayaati.ambreAttente);
      expect(c.primaire, PaletteHayaati.vertProfond);
      expect(c.sombre, isFalse);
    });

    test('tajweed : cinq couleurs, variante sur surlignage, hors limites nul', () {
      final c = CharteHayaati.defaut;
      expect(c.tajweed(0), const Color(0xFFC62828));
      expect(c.tajweed(2), const Color(0xFFEF6C00));
      expect(c.tajweed(2, surSurlignage: true), const Color(0xFFBF360C));
      expect(c.tajweed(-1), isNull);
      expect(c.tajweed(5), isNull);
    });

    test('copyWith change d\'apparence, lerp bascule à mi-parcours', () {
      final sombre = CharteHayaati.defaut.copyWith(apparence: const ApparenceHayaati(fond: 'sombre'));
      expect(sombre.sombre, isTrue);
      expect(CharteHayaati.defaut.copyWith(), same(CharteHayaati.defaut));
      expect(CharteHayaati.defaut.lerp(sombre, 0.2), same(CharteHayaati.defaut));
      expect(CharteHayaati.defaut.lerp(sombre, 0.8), same(sombre));
      expect(CharteHayaati.defaut.lerp(null, 0.8), same(CharteHayaati.defaut));
    });
  });

  group('themeHayaati', () {
    test('par défaut : identique au thème d\'avant (bandeau vert, fond sable, cartes blanches)', () {
      final t = themeHayaati();
      expect(t.brightness, Brightness.light);
      expect(t.colorScheme.primary, PaletteHayaati.vertProfond);
      expect(t.colorScheme.onPrimary, PaletteHayaati.blanc);
      expect(t.colorScheme.secondary, PaletteHayaati.terracotta);
      expect(t.colorScheme.tertiary, PaletteHayaati.ocre);
      expect(t.colorScheme.surface, PaletteHayaati.blanc);
      expect(t.scaffoldBackgroundColor, PaletteHayaati.sable);
      expect(t.appBarTheme.backgroundColor, PaletteHayaati.vertProfond);
      expect(t.appBarTheme.foregroundColor, PaletteHayaati.blanc);
      expect(t.appBarTheme.toolbarHeight, 60);
      expect(t.chipTheme.selectedColor, PaletteHayaati.ocre);
      expect(t.extension<CharteHayaati>(), isNotNull);
    });

    test('toutes les apparences produisent un thème cohérent avec leur charte', () {
      for (final f in fondsApparence) {
        for (final c in couleursApparence) {
          final a = ApparenceHayaati(fond: f, couleur: c);
          final t = themeHayaati(apparence: a);
          final ch = t.extension<CharteHayaati>()!;
          expect(ch.apparence, a);
          expect(t.brightness, f == 'sombre' ? Brightness.dark : Brightness.light, reason: '$f/$c');
          expect(t.scaffoldBackgroundColor, ch.sable, reason: '$f/$c');
          expect(t.appBarTheme.backgroundColor, ch.primaire, reason: '$f/$c');
          expect(t.appBarTheme.foregroundColor, ch.surPrimaire, reason: '$f/$c');
          expect(t.colorScheme.onSurface, ch.texteFonce, reason: '$f/$c');
          expect(t.colorScheme.surface, ch.blanc, reason: '$f/$c');
        }
      }
    });

    test('la police arabe est celle du paquet', () {
      expect(themeHayaati(arabe: true).textTheme.bodyMedium?.fontFamily, policeArabe);
      expect(policeArabe, 'packages/hayaati_ui/NotoSansArabic');
    });
  });

  group('dans une application', () {
    testWidgets('CharteHayaati.of lit le thème, et la charte officielle sans thème HAYAATI', (tester) async {
      Color? lu;
      await tester.pumpWidget(MaterialApp(
        theme: themeHayaati(apparence: const ApparenceHayaati(fond: 'papier')),
        home: Builder(builder: (c) {
          lu = CharteHayaati.of(c).sable;
          return const SizedBox();
        }),
      ));
      expect(lu, const Color(0xFFF1E6CB));

      await tester.pumpWidget(MaterialApp(
        home: Builder(builder: (c) {
          lu = CharteHayaati.of(c).sable;
          return const SizedBox();
        }),
      ));
      expect(lu, PaletteHayaati.sable);
    });

    testWidgets('barreHayaati : titre et illustration, barre intégrée aux couleurs de la charte', (tester) async {
      await tester.pumpWidget(MaterialApp(
        theme: themeHayaati(apparence: const ApparenceHayaati(fond: 'sombre')),
        home: Scaffold(
          appBar: barreHayaati('Madrassa', integre: true, illustration: const Icon(Icons.school)),
          body: const SizedBox(),
        ),
      ));
      expect(find.text('Madrassa'), findsOneWidget);
      expect(find.byIcon(Icons.school), findsOneWidget);
      final barre = tester.widget<AppBar>(find.byType(AppBar));
      expect(barre.backgroundColor, ValeursCharteSombre.sable);
    });

    testWidgets('le sélecteur propose les trois fonds et les trois couleurs, et signale le choix', (tester) async {
      ApparenceHayaati? recu;
      await tester.pumpWidget(MaterialApp(
        theme: themeHayaati(),
        home: Scaffold(
          body: SingleChildScrollView(
            child: SelecteurApparence(apparence: ApparenceHayaati.defaut, surChangement: (a) => recu = a),
          ),
        ),
      ));
      for (final t in <String>['Clair', 'Papier', 'Sombre', 'Vert', 'Terracotta', 'Ocre']) {
        expect(find.text(t), findsOneWidget, reason: t);
      }
      await tester.tap(find.text('Papier'));
      expect(recu, const ApparenceHayaati(fond: 'papier'));
      await tester.tap(find.text('Ocre'));
      expect(recu, const ApparenceHayaati(couleur: 'ocre'));
    });

    testWidgets('le sélecteur utilise les textes traduits fournis', (tester) async {
      await tester.pumpWidget(MaterialApp(
        home: Scaffold(
          body: SelecteurApparence(
            apparence: ApparenceHayaati.defaut,
            surChangement: (_) {},
            libelle: (cle, defaut) => cle == 'apparence_sombre' ? 'Dark' : defaut,
          ),
        ),
      ));
      expect(find.text('Dark'), findsOneWidget);
      expect(find.text('Sombre'), findsNothing);
    });
  });
}

/// Couleurs de l'arrière-plan sombre, pour les vérifications ci-dessus.
class ValeursCharteSombre {
  static final Color sable = Color(ValeursCharte.pour(const ApparenceHayaati(fond: 'sombre')).sable);
}
