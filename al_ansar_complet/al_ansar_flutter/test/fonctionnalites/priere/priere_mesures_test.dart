import 'dart:convert';
import 'dart:io';

import 'package:al_ansar/al_ansar.dart';
import 'package:flutter_test/flutter_test.dart';

/// Les trois mesures du moteur : minute de précaution (et ajustements manuels), règle des hautes latitudes (et soleil de minuit),
/// décalage horaire réel du jour. Les valeurs attendues de la section « mesures » de test/fixtures/priere_reference.json sont
/// recalculées par outils/generer_references_priere.py avec une seconde écriture, indépendante, des mêmes règles.
void main() {
  final ref = jsonDecode(File('test/fixtures/priere_reference.json').readAsStringSync()) as Map<String, dynamic>;
  List<Map<String, dynamic>> liste(String cle) => (ref[cle] as List<dynamic>).cast<Map<String, dynamic>>();

  int minutes(String hhmm) {
    final p = hhmm.split(':');
    return int.parse(p[0]) * 60 + int.parse(p[1]);
  }

  group('formaterHeure', () {
    test('mêmes résultats que la référence, y compris autour de minuit et sur les valeurs exactes', () {
      for (final c in liste('formats')) {
        final r = formaterHeure((c['heures'] as num).toDouble(), versLeHaut: c['haut'] as bool, ajustementMinutes: c['ajust'] as int);
        expect(r, c['attendu'], reason: '${c['heures']} haut=${c['haut']} ajust=${c['ajust']}');
      }
    });
  });

  group('moteur prudent : mêmes horaires que la référence', () {
    test('le jeu de référence est complet', () {
      expect(liste('mesures').length, greaterThan(400));
    });

    test('précaution, ajustements, hautes latitudes, soleil de minuit et nuit polaire', () {
      final ecarts = <String>[];
      for (final c in liste('mesures')) {
        final ajustements = (c['ajustements'] as Map<String, dynamic>).map((k, v) => MapEntry(k, (v as num).toInt()));
        final calcul = CalculateurHoraires(
          latitude: (c['lat'] as num).toDouble(),
          longitude: (c['lon'] as num).toDouble(),
          fuseau: (c['fuseau'] as num).toDouble(),
        );
        final h = calcul.calculer(
          DateTime.parse(c['date'] as String),
          methode: MethodeCalcul.depuisCle(c['methode'] as String)!,
          asrHanafi: c['hanafi'] as bool,
          precaution: PrecautionHoraires(arrondi: ArrondiHoraires.values.byName(c['arrondi'] as String), ajustementsMinutes: ajustements),
          regleHautesLatitudes: RegleHautesLatitudes.values.byName(c['regle'] as String),
        );
        final attendu = (c['attendu'] as Map<String, dynamic>).cast<String, String>();
        final obtenu = h.toMap();
        final id = "${c['ville']} ${c['date']} ${c['methode']} hanafi=${c['hanafi']} ${c['regle']} ${c['arrondi']} $ajustements";
        for (final k in attendu.keys) {
          if (obtenu[k] != attendu[k]) ecarts.add('$id $k : attendu ${attendu[k]}, obtenu ${obtenu[k]}');
        }
        if (h.situation.name != c['situation']) ecarts.add('$id situation : attendu ${c['situation']}, obtenu ${h.situation.name}');
        if (h.hautesLatitudesAppliquees != c['hautes_latitudes']) ecarts.add('$id hautes latitudes : attendu ${c['hautes_latitudes']}');
      }
      expect(ecarts, isEmpty, reason: '${ecarts.length} écart(s), par exemple :\n${ecarts.take(12).join('\n')}');
    });
  });

  group('minute de précaution', () {
    test('elle ne s\'écarte jamais de plus d\'une minute de la minute tronquée, et jamais pour le lever', () {
      for (final c in liste('horaires')) {
        if (!<String>{'dapaong', 'lome', 'la_mecque', 'jakarta', 'karachi'}.contains(c['ville'])) continue;
        final calcul = CalculateurHoraires(
          latitude: (c['lat'] as num).toDouble(),
          longitude: (c['lon'] as num).toDouble(),
          fuseau: (c['fuseau'] as num).toDouble(),
        );
        final methode = MethodeCalcul.depuisCle(c['methode'] as String)!;
        final h = calcul.calculer(DateTime.parse(c['date'] as String), methode: methode, asrHanafi: c['hanafi'] as bool);
        final attendu = (c['attendu'] as Map<String, dynamic>).cast<String, String>();
        final obtenu = h.toMap();
        for (final k in attendu.keys) {
          final ecart = (minutes(obtenu[k]!) - minutes(attendu[k]!)) % 1440;
          expect(ecart, k == 'sunrise' ? 0 : inInclusiveRange(0, 1), reason: "${c['ville']} ${c['date']} ${c['methode']} $k");
        }
      }
    });

    test('un ajustement manuel déplace l\'horaire demandé et lui seul', () {
      final calcul = CalculateurHoraires(latitude: 10.8627, longitude: 0.2076, fuseau: 0.0);
      final base = calcul.calculer(DateTime(2026, 9, 8), precaution: PrecautionHoraires.aucune);
      final ajuste = calcul.calculer(
        DateTime(2026, 9, 8),
        precaution: PrecautionHoraires.aucune.avecAjustement('fajr', 2).avecAjustement('isha', -3),
      );
      expect(minutes(ajuste.fajr) - minutes(base.fajr), 2);
      expect(minutes(ajuste.isha) - minutes(base.isha), -3);
      expect(ajuste.dhuhr, base.dhuhr);
      expect(ajuste.maghrib, base.maghrib);
    });

    test('un ajustement est borné à 30 minutes ; PrecautionHoraires est immuable', () {
      const p = PrecautionHoraires(ajustementsMinutes: <String, int>{'fajr': 500, 'isha': -500});
      expect(p.ajustement('fajr'), 30);
      expect(p.ajustement('isha'), -30);
      expect(p.ajustement('asr'), 0);
      final q = p.avecAjustement('asr', 4);
      expect(q.ajustement('asr'), 4);
      expect(p.ajustement('asr'), 0);
      expect(PrecautionHoraires.prudente.aUnAjustement, isFalse);
      expect(q.aUnAjustement, isTrue);
    });

    test('le comportement par défaut est prudent', () {
      expect(PrecautionHoraires.prudente.arrondi, ArrondiHoraires.prudent);
      expect(PrecautionHoraires.aucune.arrondi, ArrondiHoraires.tronque);
    });
  });

  group('hautes latitudes et soleil de minuit', () {
    test('Togo, toute l\'année : six horaires, dans l\'ordre, sans règle de hautes latitudes', () {
      final calcul = CalculateurHoraires(latitude: 10.8627, longitude: 0.2076, fuseau: 0.0);
      for (var jour = 0; jour < 366; jour++) {
        final d = DateTime(2024, 1, 1 + jour);
        final h = calcul.calculer(d);
        final ordre = <String>[h.fajr, h.lever, h.dhuhr, h.asr, h.maghrib, h.isha];
        expect(ordre.every(HorairesJour.estDisponible), isTrue, reason: '$d');
        expect(List<String>.of(ordre)..sort(), ordre, reason: '$d : $ordre');
        expect(h.situation, SituationSolaire.normale);
        expect(h.hautesLatitudesAppliquees, isFalse, reason: '$d');
      }
    });

    test('Paris au solstice d\'été : l\'ancien moteur donne des heures aberrantes, le moteur prudent des heures cohérentes', () {
      final calcul = CalculateurHoraires(latitude: 48.8566, longitude: 2.3522, fuseau: 2.0);
      final d = DateTime(2026, 6, 21);
      final ancien = calcul.calculer(d, precaution: PrecautionHoraires.aucune, regleHautesLatitudes: RegleHautesLatitudes.aucune);
      expect(HorairesJour.estDisponible(ancien.fajr), isFalse, reason: ancien.fajr);
      final h = calcul.calculer(d);
      expect(h.hautesLatitudesAppliquees, isTrue);
      final ordre = <String>[h.fajr, h.lever, h.dhuhr, h.asr, h.maghrib, h.isha];
      expect(ordre.every(HorairesJour.estDisponible), isTrue);
      expect(List<String>.of(ordre)..sort(), ordre, reason: '$ordre');
    });

    test('Tromsø : soleil de minuit en juin, nuit polaire en décembre, Dhuhr toujours présent', () {
      final calcul = CalculateurHoraires(latitude: 69.6492, longitude: 18.9553, fuseau: 2.0);
      final ete = calcul.calculer(DateTime(2026, 6, 21));
      expect(ete.situation, SituationSolaire.soleilDeMinuit);
      for (final v in <String>[ete.fajr, ete.lever, ete.maghrib, ete.isha]) {
        expect(v, HorairesJour.indisponible);
      }
      expect(HorairesJour.estDisponible(ete.dhuhr), isTrue);
      final hiver = calcul.calculer(DateTime(2026, 12, 21), decalageUtc: 1.0);
      expect(hiver.situation, SituationSolaire.nuitPolaire);
      expect(hiver.lever, HorairesJour.indisponible);
    });

    test('prochaine prière : les horaires indisponibles sont sautés', () {
      final calcul = CalculateurHoraires(latitude: 69.6492, longitude: 18.9553, fuseau: 2.0);
      final r = calcul.prochainePriere(DateTime(2026, 6, 21), 0.0);
      expect(r.nom, 'dhuhr');
      expect(HorairesJour.estDisponible(r.heure), isTrue);
    });
  });

  group('décalage horaire réel', () {
    test('sans fuseau fixe, le moteur prend le décalage que l\'appareil applique ce jour-là', () {
      final sansFuseau = CalculateurHoraires(latitude: 48.8566, longitude: 2.3522);
      for (final d in <DateTime>[DateTime(2026, 1, 15), DateTime(2026, 7, 15), DateTime(2026, 3, 29), DateTime(2026, 10, 25)]) {
        final attendu = CalculateurHoraires(latitude: 48.8566, longitude: 2.3522, fuseau: CalculateurHoraires.decalageLocalDu(d)).calculer(d);
        expect(sansFuseau.calculer(d).toMap(), attendu.toMap(), reason: '$d');
      }
    });

    test('decalageUtc remplace le fuseau fixe pour le jour demandé', () {
      final calcul = CalculateurHoraires(latitude: 10.8627, longitude: 0.2076, fuseau: 0.0);
      final utc = calcul.calculer(DateTime(2026, 9, 8), precaution: PrecautionHoraires.aucune);
      final plusUn = calcul.calculer(DateTime(2026, 9, 8), precaution: PrecautionHoraires.aucune, decalageUtc: 1.0);
      expect(minutes(plusUn.dhuhr) - minutes(utc.dhuhr), 60);
    });
  });
}
