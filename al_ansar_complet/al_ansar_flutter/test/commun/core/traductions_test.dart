import 'package:al_ansar/al_ansar.dart';
import 'package:flutter_test/flutter_test.dart';

/// Zéro dette de traduction : ce test échoue dès qu'une langue n'a pas toutes les clés.
void main() {
  final tables = Textes.tables;

  test('langues attendues présentes', () {
    expect(tables.keys, containsAll(<String>['fr', 'en', 'ar', 'ha']));
  });

  test('chaque langue a exactement les clés du français, sans texte vide', () {
    final cles = tables['fr']!.keys.toSet();
    for (final e in tables.entries) {
      expect(e.value.keys.toSet(), cles, reason: 'langue ${e.key}');
      for (final t in e.value.entries) {
        expect(t.value.trim(), isNotEmpty, reason: '${e.key} / ${t.key}');
      }
    }
  });

  test('le marqueur {nom} est conservé dans toutes les langues', () {
    for (final e in tables.entries) {
      expect(e.value['msg_contact'], contains('{nom}'), reason: 'langue ${e.key}');
    }
  });
}
