import 'package:flutter_test/flutter_test.dart';
import 'package:hayaati_ui/hayaati_ui.dart';

void main() {
  test('sépare le pictogramme de tête du titre', () {
    final t = separerEmoji('🏫 Madrassa');
    expect(t.emoji, '🏫');
    expect(t.titre, 'Madrassa');
  });

  test('titre arabe, haoussa, avec séquence émoji', () {
    expect(separerEmoji('🏫 المدرسة الشرعية').titre, 'المدرسة الشرعية');
    expect(separerEmoji('🏫 Makaranta').titre, 'Makaranta');
    final t = separerEmoji('👨‍👩‍👧 Famille');
    expect(t.titre, 'Famille');
    expect(t.emoji, isNotNull);
    expect(separerEmoji('✨ 12 perles').titre, '12 perles');
  });

  test('sans pictogramme : titre inchangé', () {
    expect(separerEmoji('Madrassa').emoji, isNull);
    expect(separerEmoji('  Apprendre ').titre, 'Apprendre');
    expect(separerEmoji('').titre, '');
  });

  test('un texte qui n\'est qu\'un pictogramme est conservé', () {
    final t = separerEmoji('🏫');
    expect(t.emoji, isNull);
    expect(t.titre, '🏫');
  });

  test('un pictogramme au milieu du texte n\'est pas touché', () {
    expect(separerEmoji('Madrassa 🏫 du soir').titre, 'Madrassa 🏫 du soir');
  });
}
