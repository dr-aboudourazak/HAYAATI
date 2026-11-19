import 'dart:convert';
import 'dart:io';

import 'package:al_ansar/al_ansar.dart';
import 'package:flutter_test/flutter_test.dart';

class DepotFactice extends DepotAnnuaire {
  DepotFactice(this.donnees) : super(baseUrl: '', assetPrefix: '');

  final Annuaire donnees;

  @override
  Future<Manifeste?> manifeste() async => null;

  @override
  Future<Annuaire?> charger(String pays, String role, {Manifeste? manifeste}) async => donnees;
}

void main() {
  late Annuaire annuaire;
  const types = <String>{'madrassa', 'librairie', 'specialiste'};

  setUpAll(() {
    annuaire = Annuaire.fromJson(
      jsonDecode(File('example/assets/al_ansar/annuaire_TG.json').readAsStringSync()) as Json,
    );
  });

  Future<ControleurAlAnsar> creer({Coord? position, FournisseurPosition? fournisseur}) async {
    final c = ControleurAlAnsar(
      config: AlAnsarConfig(
        baseUrl: '',
        pays: 'TG',
        villeId: 'tg-dapaong',
        position: position,
        fournisseurPosition: fournisseur,
        modeDemo: true,
      ),
      depot: DepotFactice(annuaire),
    );
    await c.init();
    return c;
  }

  test('position fournie : mode « autour de moi », classement par distance', () async {
    final c = await creer(position: const Coord(10.8627, 0.2076));
    expect(c.mode, ModeLieu.autourDeMoi);

    final r50 = c.fiches(types, rayonKm: 50);
    expect(r50.map((e) => e.fiche.type).toList(), <String>['madrassa', 'librairie', 'specialiste']);
    expect(r50.first.distanceM, lessThan(100));
    expect(r50[1].distanceM, closeTo(27500, 2000));
    expect(r50.last.aDistance, isTrue);

    final r10 = c.fiches(types, rayonKm: 10);
    expect(r10.map((e) => e.fiche.type).toList(), <String>['madrassa', 'specialiste']);
  });

  test('choix d\'une ville : filtre par ville, services à distance conservés', () async {
    final c = await creer(position: const Coord(10.8627, 0.2076));
    await c.changerLieu(villeId: 'tg-kara');
    expect(c.mode, ModeLieu.ville);
    expect(c.lieuManuel, isTrue);
    expect(c.fiches(types).map((e) => e.fiche.type).toList(), <String>['specialiste']);

    await c.changerLieu(toutesVilles: true);
    expect(c.mode, ModeLieu.pays);
    expect(c.positionEffective, isNull);
    expect(c.fiches(types).length, 3);
  });

  test('« autour de moi » relève la position et efface le choix manuel', () async {
    final c = await creer(
      fournisseur: ({required bool precis}) => Stream<ResultatPosition>.value(
        const ResultatPosition.ok(PositionPrecise(Coord(6.1319, 1.2228), precisionM: 20)),
      ),
    );
    expect(c.mode, ModeLieu.ville);
    await c.choisirAutourDeMoi();
    expect(c.mode, ModeLieu.autourDeMoi);
    expect(c.lieuManuel, isFalse);
    expect(c.positionGps?.precisionM, 20);
    expect(c.erreurPosition, isNull);
    expect(c.fiches(types, rayonKm: 50).first.fiche.type, 'specialiste');
  });

  test('« autour de moi » : la cause de l\'échec est conservée', () async {
    final c = await creer(
      fournisseur: ({required bool precis}) => Stream<ResultatPosition>.value(
        const ResultatPosition.echec(ErreurPosition.permissionRefusee),
      ),
    );
    await c.choisirAutourDeMoi();
    expect(c.mode, ModeLieu.autourDeMoi);
    expect(c.positionGps, isNull);
    expect(c.erreurPosition, ErreurPosition.permissionRefusee);
    expect(c.positionEffective, isNull);
  });

  test('textes injectés par l\'hôte prioritaires, repli sur le français', () async {
    final c = await creer();
    c.mettreAJourHote(const AlAnsarConfig(
      baseUrl: '',
      langue: 'ha',
      textes: <String, String>{'apprendre': 'Karatu'},
    ));
    expect(c.t('apprendre'), 'Karatu');
    expect(c.t('boutique'), 'Kasuwa');
  });
}
