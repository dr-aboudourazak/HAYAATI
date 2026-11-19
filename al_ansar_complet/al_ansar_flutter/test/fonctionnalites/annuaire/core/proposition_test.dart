import 'dart:convert';

import 'package:al_ansar/al_ansar.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  final nouvelle = Proposition(
    type: TypeProposition.nouvelleMosquee,
    pays: 'TG',
    villeId: 'tg-dapaong',
    nom: 'Mosquée Al Fath',
    position: const PositionPrecise(Coord(10.8700004, 0.2150004), precisionM: 8.6),
    commentaire: "Près du château d'eau",
    creeLe: DateTime.utc(2026, 10, 21, 10, 32),
  );

  test('JSON : champs, arrondis et précision entière', () {
    final j = nouvelle.toJson();
    expect(j['schema'], 'al_ansar_proposition_v1');
    expect(j['type'], 'nouvelle_mosquee');
    expect(j['ville_id'], 'tg-dapaong');
    expect(j.containsKey('fiche_id'), isFalse);
    final pos = j['position'] as Map<String, dynamic>;
    expect(pos['lat'], 10.87);
    expect(pos['lon'], 0.215);
    expect(pos['precision_m'], 9);
    expect(pos['source'], 'releve_sur_place');
    expect(j['cree_le'], '2026-10-21T10:32:00.000Z');
  });

  test('message : lignes lisibles puis ligne JSON identique au JSON', () {
    final msg = nouvelle.versMessage(const Textes('fr'));
    expect(msg, contains('Al Ansâr · Nouvelle mosquée'));
    expect(msg, contains('Position : 10.870000, 0.215000 (±9 m)'));
    expect(
      msg,
      contains('https://www.openstreetmap.org/?mlat=10.870000&mlon=0.215000#map=19/10.870000/0.215000'),
    );
    final ligne = msg.split('\n').firstWhere((l) => l.startsWith('AL-ANSAR-JSON '));
    expect(jsonDecode(ligne.substring('AL-ANSAR-JSON '.length)), equals(nouvelle.toJson()));
  });

  test('correction : identifiant de fiche, sans précision si inconnue', () {
    final correction = Proposition(
      type: TypeProposition.correctionPosition,
      pays: 'TG',
      villeId: 'tg-dapaong',
      ficheId: 'tg-dapaong-msq-002',
      nom: 'Mosquée de la gare',
      position: const PositionPrecise(Coord(10.86, 0.2051)),
      creeLe: DateTime.utc(2026, 10, 21, 11),
    );
    final j = correction.toJson();
    expect(j['type'], 'correction_position');
    expect(j['fiche_id'], 'tg-dapaong-msq-002');
    expect((j['position'] as Map<String, dynamic>).containsKey('precision_m'), isFalse);
    expect(correction.versMessage(const Textes('en')), contains('Position correction'));
  });
}
