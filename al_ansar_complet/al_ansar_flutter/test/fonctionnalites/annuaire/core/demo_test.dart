import 'dart:convert';
import 'dart:io';

import 'package:al_ansar/al_ansar.dart';
import 'package:flutter_test/flutter_test.dart';

class _Depot extends DepotAnnuaire {
  _Depot(this.donnees) : super(baseUrl: '', assetPrefix: '');

  final Annuaire donnees;

  @override
  Future<Manifeste?> manifeste() async => null;

  @override
  Future<Annuaire?> charger(String pays, String role, {Manifeste? manifeste}) async => donnees;
}

void main() {
  const types = <String>{'madrassa', 'librairie', 'specialiste'};
  late Annuaire annuaire;

  setUpAll(() {
    annuaire = Annuaire.fromJson(
      jsonDecode(File('example/assets/al_ansar/annuaire_TG.json').readAsStringSync()) as Json,
    );
  });

  Future<ControleurAlAnsar> creer(bool? modeDemo) async {
    final c = ControleurAlAnsar(
      config: AlAnsarConfig(baseUrl: '', pays: 'TG', modeDemo: modeDemo),
      depot: _Depot(annuaire),
    );
    await c.init();
    return c;
  }

  test('le fichier d\'exemple se déclare lui-même en démonstration', () {
    expect(annuaire.demonstration, isTrue);
  });

  test('mode démo non décidé par l\'hôte : on suit les données', () async {
    final c = await creer(null);
    expect(c.demoActif, isTrue);
    expect(c.fiches(types).length, 3);
    expect(c.resumeDonnees, contains('démo : oui'));
  });

  test('l\'hôte peut forcer le masquage ; les brouillons masqués sont comptés', () async {
    final c = await creer(false);
    expect(c.demoActif, isFalse);
    expect(c.fiches(types), isEmpty);
    expect(c.brouillonsMasques(types), 3);
  });

  test('l\'hôte peut forcer l\'affichage', () async {
    final c = await creer(true);
    expect(c.fiches(types).length, 3);
    expect(c.brouillonsMasques(types), 0);
  });
}
