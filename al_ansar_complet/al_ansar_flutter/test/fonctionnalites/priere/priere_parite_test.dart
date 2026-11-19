import 'dart:convert';
import 'dart:io';

import 'package:al_ansar/al_ansar.dart';
import 'package:flutter_test/flutter_test.dart';

/// Parité avec le moteur Python de HAYAATI (core/prayertimes.py et core/qibla_engine.py) : les valeurs attendues viennent de
/// test/fixtures/priere_reference.json, produit par outils/generer_references_priere.py.
///
/// Le moteur est désormais plus prudent par défaut (minute de précaution, hautes latitudes) : pour comparer avec l'ancien moteur, ces tests
/// demandent explicitement l'ancien comportement. Le comportement prudent est vérifié dans priere_mesures_test.dart.
const _ancien = PrecautionHoraires.aucune;
const _sansRegle = RegleHautesLatitudes.aucune;

void main() {
  final ref = jsonDecode(File('test/fixtures/priere_reference.json').readAsStringSync()) as Map<String, dynamic>;
  List<Map<String, dynamic>> liste(String cle) => (ref[cle] as List<dynamic>).cast<Map<String, dynamic>>();

  group('horaires : mêmes minutes que le moteur Python', () {
    test('le jeu de référence est complet', () {
      expect(liste('horaires').length, greaterThan(700));
    });

    test('chaque cas (ville, date, méthode, école) donne les six mêmes heures', () {
      final ecarts = <String>[];
      for (final c in liste('horaires')) {
        final calcul = CalculateurHoraires(
          latitude: (c['lat'] as num).toDouble(),
          longitude: (c['lon'] as num).toDouble(),
          fuseau: (c['fuseau'] as num).toDouble(),
        );
        final h = calcul.calculer(
          DateTime.parse(c['date'] as String),
          methode: MethodeCalcul.depuisCle(c['methode'] as String)!,
          asrHanafi: c['hanafi'] as bool,
          precaution: _ancien,
          regleHautesLatitudes: _sansRegle,
        );
        final attendu = (c['attendu'] as Map<String, dynamic>).cast<String, String>();
        final obtenu = h.toMap();
        for (final k in attendu.keys) {
          if (obtenu[k] != attendu[k]) {
            ecarts.add("${c['ville']} ${c['date']} ${c['methode']} hanafi=${c['hanafi']} $k : attendu ${attendu[k]}, obtenu ${obtenu[k]}");
          }
        }
      }
      expect(ecarts, isEmpty, reason: '${ecarts.length} écart(s), par exemple :\n${ecarts.take(12).join('\n')}');
    });

    test('fuseau déduit de la longitude : arrondi « au pair » comme Python', () {
      for (final c in liste('fuseaux_deduits')) {
        final lon = (c['lon'] as num).toDouble();
        expect(CalculateurHoraires.fuseauDeduitDeLongitude(lon), (c['fuseau'] as num).toDouble(), reason: 'longitude $lon');
      }
    });

    test('prochaine prière : mêmes réponses que Python, y compris le Fajr du lendemain', () {
      final calcul = CalculateurHoraires(latitude: 10.8627, longitude: 0.2076, fuseau: 0.0);
      for (final c in liste('prochaines')) {
        final r = calcul.prochainePriere(DateTime(2026, 9, 8), (c['heure'] as num).toDouble(), precaution: _ancien, regleHautesLatitudes: _sansRegle);
        expect(r.nom, c['nom'], reason: 'heure ${c['heure']}');
        expect(r.heure, c['valeur'], reason: 'heure ${c['heure']}');
      }
    });
  });

  group('horaires : cohérence', () {
    test('Dapaong, 8 septembre 2026 : l\'ordre de la journée est respecté', () {
      final h = CalculateurHoraires(latitude: 10.8627, longitude: 0.2076, fuseau: 0.0).calculer(DateTime(2026, 9, 8));
      final ordre = <String>[h.fajr, h.lever, h.dhuhr, h.asr, h.maghrib, h.isha];
      final tries = List<String>.of(ordre)..sort();
      expect(ordre, tries);
    });

    test('l\'Asr hanafite tombe après l\'Asr standard', () {
      final calcul = CalculateurHoraires(latitude: 10.8627, longitude: 0.2076, fuseau: 0.0);
      final standard = calcul.calculer(DateTime(2026, 9, 8)).asr;
      final hanafite = calcul.calculer(DateTime(2026, 9, 8), asrHanafi: true).asr;
      expect(hanafite.compareTo(standard), greaterThan(0));
    });

    test('Umm Al-Qura : l\'Isha tombe 90 minutes après le Maghrib', () {
      final h = CalculateurHoraires(latitude: 21.4225, longitude: 39.8262, fuseau: 3.0)
          .calculer(DateTime(2026, 6, 21), methode: MethodeCalcul.oummAlQoura);
      final ecart = h.instant(h.isha)!.difference(h.instant(h.maghrib)!).inMinutes;
      expect(ecart, inInclusiveRange(89, 91)); // chaque minute est arrondie séparément
    });

    test('les six méthodes existent sous les clés du moteur Python', () {
      expect(MethodeCalcul.toutes.map((e) => e.cle), <String>['MWL', 'ISNA', 'EGYPT', 'KARACHI', 'UMM_AL_QURA', 'GULF']);
      expect(MethodeCalcul.depuisCle('MWL'), same(MethodeCalcul.mwl));
      expect(MethodeCalcul.depuisCle('inconnue'), isNull);
      expect(MethodeCalcul.depuisCle(null), isNull);
    });

    test('instant() reconstruit la date et l\'heure locales du jour demandé', () {
      final h = CalculateurHoraires(latitude: 10.8627, longitude: 0.2076, fuseau: 0.0).calculer(DateTime(2026, 9, 8, 23, 59));
      final i = h.instant(h.dhuhr)!;
      expect((i.year, i.month, i.day), (2026, 9, 8));
      expect('${i.hour.toString().padLeft(2, '0')}:${i.minute.toString().padLeft(2, '0')}', h.dhuhr);
      expect(h.instant(HorairesJour.indisponible), isNull);
    });
  });

  group('qibla : mêmes valeurs que le moteur Python', () {
    test('direction et distance', () {
      for (final c in liste('qibla')) {
        final lat = (c['lat'] as num).toDouble();
        final lon = (c['lon'] as num).toDouble();
        expect(calculerDirectionQibla(lat, lon), closeTo((c['direction'] as num).toDouble(), 1e-9), reason: '$lat,$lon');
        expect(calculerDistanceKaabaKm(lat, lon), closeTo((c['distance_km'] as num).toDouble(), 1e-6), reason: '$lat,$lon');
      }
    });

    test('angle relatif de l\'aiguille', () {
      for (final c in liste('relatifs')) {
        final boussole = c['boussole'] == null ? null : (c['boussole'] as num).toDouble();
        expect(angleRelatifAiguille((c['qibla'] as num).toDouble(), boussole), closeTo((c['attendu'] as num).toDouble(), 1e-9));
      }
    });

    test('Dapaong : la qibla est à l\'est-nord-est, à plus de 4 000 km', () {
      final d = calculerDirectionQibla(10.8627, 0.2076);
      expect(d, inInclusiveRange(60, 80));
      expect(calculerDistanceKaabaKm(10.8627, 0.2076), greaterThan(4000));
    });
  });
}
