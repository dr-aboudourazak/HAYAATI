import 'package:flutter_test/flutter_test.dart';
import 'package:hayaati_exemple/main.dart';

void main() {
  testWidgets('l\'application démarre et affiche une erreur claire sans fichiers de langue', (tester) async {
    await tester.pumpWidget(const HayaatiExemple(ecouterLiens: false));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));
    // Sans assets/locales dans le banc d'essai : soit la liste (assets présents), soit le message d'erreur lisible.
    final ok = find.text('Al Ansâr').evaluate().isNotEmpty || find.textContaining('Chargement impossible').evaluate().isNotEmpty;
    expect(ok, isTrue);
  });
}
