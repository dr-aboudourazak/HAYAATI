import 'dart:convert';
import 'dart:io';

import 'package:al_ansar/al_ansar.dart';
import 'package:flutter_test/flutter_test.dart';

Json _lire(String chemin) =>
    jsonDecode(File(chemin).readAsStringSync()) as Json;

void main() {
  late Annuaire annuaire;
  late Annuaire mosquees;

  setUpAll(() {
    annuaire = Annuaire.fromJson(_lire('example/assets/al_ansar/annuaire_TG.json'));
    mosquees = Annuaire.fromJson(_lire('example/assets/al_ansar/mosquees_TG.json'));
  });

  test('lecture de l\'annuaire d\'exemple', () {
    expect(annuaire.pays, 'TG');
    expect(annuaire.villes.length, 4);
    expect(annuaire.fiches.length, 4);
    expect(annuaire.forfaits.length, 2);
    expect(annuaire.cours.length, 2);
    expect(annuaire.articles.length, 2);
    expect(annuaire.prestations.length, 1);
    expect(annuaire.fiches.first.type, 'madrassa');
    expect(annuaire.fiches.first.niveau, 1);
  });

  test('un cours en cours n\'a ni seuil ni date limite', () {
    final enCours = annuaire.cours.firstWhere((c) => c.statut == 'confirme');
    expect(enCours.seuilMin, isNull);
    expect(enCours.dateLimite, isNull);
    expect(enCours.noteHoraire['fr'], isNotEmpty);
  });

  test('lecture du fichier de mosquées', () {
    expect(mosquees.fiches.length, 4);
    expect(mosquees.fiches.every((f) => f.type == 'mosquee' && f.gps != null), isTrue);
    expect(mosquees.attribution, contains('OpenStreetMap'));
    expect(mosquees.fiches.first.mosquee.jumuaHeure, '13:30');
  });

  test('regroupement des classes par jour puis par public', () {
    final cours = annuaire.cours.where((c) => c.ficheId == 'tg-dapaong-mad-001').toList();
    expect(grouperCours(cours, GroupeCours.parJour).keys.toList(), <String>['mar', 'jeu', 'sam', 'dim']);
    expect(grouperCours(cours, GroupeCours.parPublic).keys.toList(), <String>['adultes', 'enfants']);
  });

  test('filtres : ville, distance, niveau', () {
    final madrassa = annuaire.fiches.firstWhere((f) => f.type == 'madrassa');
    final librairie = annuaire.fiches.firstWhere((f) => f.type == 'librairie');
    final cabinet = annuaire.fiches.firstWhere((f) => f.type == 'specialiste');

    const dapaong = FiltreFiches(villeId: 'tg-dapaong');
    expect(dapaong.accepte(madrassa), isTrue);
    expect(dapaong.accepte(librairie), isTrue); // livre à Dapaong
    expect(dapaong.accepte(cabinet), isTrue); // pays entier

    const kara = FiltreFiches(villeId: 'tg-kara');
    expect(kara.accepte(madrassa), isFalse);
    expect(kara.accepte(librairie), isFalse);
    expect(kara.accepte(cabinet), isTrue);

    const distance = FiltreFiches(aDistance: true);
    expect(<Fiche>[madrassa, librairie, cabinet].map(distance.accepte).toList(), <bool>[false, false, true]);
    expect(const FiltreFiches(niveauMin: 2).accepte(madrassa), isFalse);
    expect(const FiltreFiches(niveauMin: 2).accepte(cabinet), isTrue);
  });

  test('créneaux et filtre de cours', () {
    expect(creneauDe('08:00'), 'matin');
    expect(creneauDe('14:30'), 'apres_midi');
    expect(creneauDe('19:30'), 'soir');
    const soir = FiltreCours(creneau: 'soir');
    expect(annuaire.cours.where(soir.accepte).length, 1);
  });

  test('manifeste : pays détecté par la position', () {
    final m = Manifeste.fromJson(_lire('test/fixtures/manifest.exemple.json'));
    expect(m.paysDe(const Coord(10.86, 0.20))?.code, 'TG');
    expect(m.paysDe(const Coord(6.37, 2.39))?.code, 'BJ');
    expect(m.paysDe(const Coord(48.85, 2.35)), isNull);
    expect(m.parCode('TG')?.mosquees?.version, 1);
  });

  test('textes : repli sur le français et sur la clé', () {
    const ha = Textes('ha');
    const en = Textes('en');
    const fr = Textes('fr');
    const ar = Textes('ar');
    expect(ha('apprendre'), 'Koyo');
    expect(const Textes('xx')('apprendre'), 'Apprendre');
    expect(en('apprendre'), 'Learn');
    expect(fr('cle_inconnue'), 'cle_inconnue');
    expect(choisir(<String, String>{'en': 'Hello'}, 'fr'), 'Hello');
    expect(ar.rtl, isTrue);
  });
}
