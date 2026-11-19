import 'dart:convert';
import 'dart:io';

import 'package:al_ansar/al_ansar.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('un forfait Hadj et Omra porte ses médias, un autre n\'en a pas', () {
    final json = jsonDecode(File('example/assets/al_ansar/annuaire_TG.json').readAsStringSync()) as Json;
    final forfaits = json['forfaits_hadj_omra'] as List<dynamic>;
    expect(forfaits.length, greaterThanOrEqualTo(2));
    (forfaits.first as Map<String, dynamic>)['medias'] = <String, dynamic>{
      'image': <String, dynamic>{'url': 'https://exemple.org/offre.jpg', 'genre': 'affiche'},
      'video': <String, dynamic>{'youtube': 'https://youtu.be/jNQXAC9IVRw'},
    };
    final a = Annuaire.fromJson(json);
    final m = a.forfaits.first.medias!;
    expect(m.image!.estAffiche, isTrue);
    expect(m.video!.youtube, 'jNQXAC9IVRw');
    expect(a.forfaits.last.medias, isNull);
  });

  test('des médias invalides sur un forfait sont ignorés sans casser le chargement', () {
    final json = jsonDecode(File('example/assets/al_ansar/annuaire_TG.json').readAsStringSync()) as Json;
    final forfaits = json['forfaits_hadj_omra'] as List<dynamic>;
    (forfaits.first as Map<String, dynamic>)['medias'] = <String, dynamic>{
      'image': <String, dynamic>{'url': 'http://exemple.org/offre.jpg'},
      'video': <String, dynamic>{'youtube': 'https://evil.example/watch?v=jNQXAC9IVRw'},
    };
    final a = Annuaire.fromJson(json);
    expect(a.forfaits.first.medias, isNull);
  });
}
