import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:hayaati_coran/hayaati_coran.dart';

import 'aide_tests.dart';

Future<ControleurCoran> _controleur(DepotMemoire depot, {Duration lue = const Duration(milliseconds: 30)}) async {
  final moteur = await MoteurCoran.ouvrir(lireDisque);
  final c = ControleurCoran(
    moteur: moteur,
    depot: depot,
    delaiPageLue: lue,
    delaiSauvegarde: const Duration(milliseconds: 10),
    delaiRecherche: const Duration(milliseconds: 20),
  );
  await c.init();
  return c;
}

void main() {
  final g = golden();

  group('EtatLecture : nettoyage identique à Python', () {
    test('valeurs par défaut', () {
      expect(EtatLecture.defauts().toJson(), equals(g['etat_defauts']));
    });

    test('contenus bruts de toute sorte', () {
      for (final e in g['etat_lecture'] as List) {
        expect(EtatLecture.depuisJson(e[0]).toJson(), equals(e[1]), reason: jsonEncode(e[0]));
      }
    });

    test('tailles valides', () => expect(taillesValides, equals(g['tailles_valides'])));
  });

  group('EtatLecture : modifications', () {
    test('réglages validés', () {
      final e = EtatLecture.defauts();
      expect(e.definirTaille(24), isTrue);
      expect(e.definirTaille(24), isFalse); // inchangé
      expect(e.definirTaille(21), isFalse); // invalide
      expect(e.taille, 24);
      expect(e.definirPolice('arial'), isFalse);
      expect(e.definirPolice('naskh'), isTrue);
      expect(e.definirMode('carte'), isFalse);
      expect(e.definirDernierePage(605), isFalse);
      expect(e.definirDernierePage(12), isTrue);
      expect(e.definirDernierePage(null), isTrue);
    });

    test('signets de page et de verset, triés, sans doublon', () {
      final e = EtatLecture.defauts();
      expect(e.basculerSignet(20), isTrue);
      expect(e.basculerSignetVerset(2, 10, 20), isTrue);
      expect(e.basculerSignet(4), isTrue);
      expect(e.basculerSignet(700), isFalse); // page invalide : rien n'est ajouté
      expect([for (final s in e.signets) s.toJson()], [
        {'p': 4},
        {'p': 20},
        {'p': 20, 's': 2, 'v': 10},
      ]);
      expect(e.estSignet(20), isTrue);
      expect(e.estSignetVerset(2, 10), isTrue);
      expect(e.basculerSignet(20), isFalse); // retiré
      expect(e.estSignet(20), isFalse);
      expect(e.estSignetVerset(2, 10), isTrue); // le signet de verset reste
    });

    test('progression', () {
      final e = EtatLecture.defauts();
      expect(e.marquerPageLue(5), isTrue);
      expect(e.marquerPageLue(5), isFalse);
      expect(e.marquerPageLue(3), isTrue);
      expect(e.marquerPageLue(0), isFalse);
      expect(e.pagesLues, [3, 5]);
      expect(e.progression(), (2, 604));
      e.basculerSignet(9);
      e.definirDernierePage(7);
      e.reinitialiserProgression();
      expect(e.pagesLues, isEmpty);
      expect(e.dernierePage, isNull);
      expect(e.estSignet(9), isTrue); // les signets sont conservés
    });

    test('toJson puis depuisJson ne change rien', () {
      final e = EtatLecture.defauts()
        ..definirTaille(28)
        ..definirTajweed(true)
        ..basculerSignetVerset(36, 1, 440)
        ..marquerPageLue(440);
      expect(EtatLecture.depuisJson(jsonDecode(jsonEncode(e.toJson()))).toJson(), equals(e.toJson()));
    });
  });

  group('ControleurCoran', () {
    test('reprend là où la lecture s\'était arrêtée', () async {
      final depot = DepotMemoire({'derniere_page': 77, 'taille': 24, 'tajweed': true});
      final c = await _controleur(depot);
      expect(c.pageActive, 77);
      expect(c.etat.taille, 24);
      expect(c.etat.tajweed, isTrue);
      c.dispose();
    });

    test('un contenu illisible donne les valeurs par défaut', () async {
      final c = await _controleur(DepotMemoire('n\'importe quoi'));
      expect(c.pageActive, 1);
      expect(c.etat.toJson(), equals(EtatLecture.defauts().toJson()));
      c.dispose();
    });

    test('taille : bornée aux tailles valides', () async {
      final c = await _controleur(DepotMemoire());
      for (var i = 0; i < 20; i++) {
        c.changerTaille(1);
      }
      expect(c.etat.taille, taillesValides.last);
      expect(c.peutAgrandir, isFalse);
      for (var i = 0; i < 20; i++) {
        c.changerTaille(-1);
      }
      expect(c.etat.taille, taillesValides.first);
      expect(c.peutReduire, isFalse);
      c.dispose();
    });

    test('une page n\'est lue qu\'après un temps d\'affichage', () async {
      final depot = DepotMemoire();
      final c = await _controleur(depot);
      c.pageAffichee(10);
      c.pageAffichee(11); // on passe vite : la page 10 ne compte pas
      await Future<void>.delayed(const Duration(milliseconds: 120));
      expect(c.etat.pagesLues, [11]);
      expect(c.etat.dernierePage, 11);
      expect((depot.contenu as Map)['pages_lues'], [11]);
      c.dispose();
    });

    test('les changements sont enregistrés, et à la fermeture ce qui attend l\'est aussi', () async {
      final depot = DepotMemoire();
      final c = await _controleur(depot);
      c.basculerTajweed();
      await Future<void>.delayed(const Duration(milliseconds: 60));
      expect((depot.contenu as Map)['tajweed'], isTrue);
      final avant = depot.nbSauvegardes;
      c.changerPolice('naskh');
      c.dispose(); // avant l'échéance du délai
      await Future<void>.delayed(const Duration(milliseconds: 5));
      expect(depot.nbSauvegardes, avant + 1);
      expect((depot.contenu as Map)['police'], 'naskh');
    });

    test('signet de la page affichée', () async {
      final c = await _controleur(DepotMemoire());
      c.pageAffichee(48);
      expect(c.pageEstSignet, isFalse);
      c.basculerSignetPage();
      expect(c.pageEstSignet, isTrue);
      c.dispose();
    });
  });

  group('ControleurCoran : sélection, recherche et navigation', () {
    test('toucher un verset le sélectionne, le retoucher le désélectionne', () async {
      final c = await _controleur(DepotMemoire());
      c.toucherVerset(2, 255);
      expect(c.selection, const VersetRef(2, 255));
      c.toucherVerset(2, 256);
      expect(c.selection, const VersetRef(2, 256));
      c.toucherVerset(2, 256);
      expect(c.selection, isNull);
      c.dispose();
    });

    test('recherche d\'un verset : sélection, message et saut vers sa page', () async {
      final c = await _controleur(DepotMemoire());
      c.ouvrirLecture(2, 1);
      c.pageAffichee(1);
      final attendue = (await c.moteur.pageDeVerset(2, 255))!;
      c.saisirVerset('255');
      await Future<void>.delayed(const Duration(milliseconds: 120));
      expect(c.selection, const VersetRef(2, 255));
      expect(c.pageActive, attendue);
      expect(c.saut.value?.page, attendue);
      expect(c.messageRecherche, 'Verset 255 - page $attendue du mushaf');
      c.dispose();
    });

    test('recherche : chiffres arabes-indiens acceptés, numéro inexistant refusé, champ vidé', () async {
      final c = await _controleur(DepotMemoire());
      c.ouvrirLecture(2, 1);
      c.saisirVerset('٢٥٥');
      await Future<void>.delayed(const Duration(milliseconds: 120));
      expect(c.selection, const VersetRef(2, 255));
      c.saisirVerset('9999');
      await Future<void>.delayed(const Duration(milliseconds: 120));
      expect(c.selection, isNull);
      expect(c.messageRecherche, 'Aucun verset ne correspond à ce numéro.');
      c.saisirVerset('abc');
      await Future<void>.delayed(const Duration(milliseconds: 120));
      expect(c.selection, isNull);
      c.saisirVerset('');
      await Future<void>.delayed(const Duration(milliseconds: 120));
      expect(c.messageRecherche, isNull);
      c.dispose();
    });

    test('recherche d\'un verset déjà à l\'écran : pas de saut', () async {
      final c = await _controleur(DepotMemoire());
      c.ouvrirLecture(1, 1);
      c.pageAffichee(1);
      c.saisirVerset('3');
      await Future<void>.delayed(const Duration(milliseconds: 120));
      expect(c.selection, const VersetRef(1, 3));
      expect(c.saut.value, isNull);
      c.dispose();
    });

    test('signet de verset : pose, retrait, message et page enregistrée', () async {
      final c = await _controleur(DepotMemoire());
      c.toucherVerset(2, 255);
      await c.basculerSignetVerset();
      expect(c.selectionEstSignet, isTrue);
      final page = (await c.moteur.pageDeVerset(2, 255))!;
      expect([for (final s in c.etat.signets) s.toJson()], [
        {'p': page, 's': 2, 'v': 255},
      ]);
      expect(c.messages.value?.texte, 'Signet ajouté : ${c.moteur.nomSourate(2)} 255');
      await c.basculerSignetVerset();
      expect(c.etat.signets, isEmpty);
      expect(c.messages.value?.texte, 'Signet retiré : ${c.moteur.nomSourate(2)} 255');
      c.dispose();
    });

    test('texte copié : verset entre parenthèses ornées, puis référence', () async {
      final c = await _controleur(DepotMemoire());
      expect(await c.contenuACopier(), isNull);
      c.toucherVerset(112, 1);
      final texte = (await c.moteur.texteVerset(112, 1))!;
      expect(await c.contenuACopier(), '$marqueurPremier$texte$marqueurDernier\n[سورة ${c.moteur.nomSourate(112)} : 1]');
      c.dispose();
    });

    test('ouvrir une sourate : première page, sourate active, saut demandé', () async {
      final c = await _controleur(DepotMemoire());
      await c.ouvrirSourate(36);
      final page = (await c.moteur.premierePageSourate(36))!;
      expect(c.sourateActive, 36);
      expect(c.pageActive, page);
      expect(c.saut.value?.page, page);
      await c.ouvrirSourate(0); // hors limites : sans effet
      await c.ouvrirSourate(115);
      expect(c.sourateActive, 36);
      c.dispose();
    });

    test('feuilleter : la sourate affichée suit la page', () async {
      final c = await _controleur(DepotMemoire());
      final p = (await c.moteur.premierePageSourate(18))!;
      c.pageFeuilletee(p);
      expect(c.sourateActive, c.moteur.sourateDePage(p));
      c.dispose();
    });

    test('quitter la lecture trop vite : la page n\'est pas comptée comme lue', () async {
      final c = await _controleur(DepotMemoire());
      c.pageAffichee(10);
      c.quitterLecture();
      await Future<void>.delayed(const Duration(milliseconds: 120));
      expect(c.etat.pagesLues, isEmpty);
      c.dispose();
    });

    test('mode, en-tête replié, signet de page et retrait depuis la liste', () async {
      final depot = DepotMemoire();
      final c = await _controleur(depot);
      c.changerMode('liste');
      c.basculerEntete();
      c.pageAffichee(48);
      c.basculerSignetPage();
      await Future<void>.delayed(const Duration(milliseconds: 80));
      expect((depot.contenu as Map)['mode'], 'liste');
      expect((depot.contenu as Map)['entete_replie'], isTrue);
      expect(c.messages.value?.texte, 'Signet ajouté : page 48');
      c.retirerSignet(c.etat.signets.first);
      expect(c.etat.signets, isEmpty);
      c.dispose();
    });
  });
}
