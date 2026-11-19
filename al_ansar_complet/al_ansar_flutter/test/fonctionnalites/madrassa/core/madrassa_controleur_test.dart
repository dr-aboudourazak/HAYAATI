import 'dart:convert';
import 'dart:io';

import 'package:al_ansar/al_ansar.dart';
import 'package:flutter_test/flutter_test.dart';

Map<String, dynamic> _contenu() =>
    jsonDecode(File('test/fixtures/contenu_fr.json').readAsStringSync()) as Map<String, dynamic>;

void main() {
  test('contenu : six étapes de langue arabe et six de sciences islamiques', () {
    final c = ContenuMadrassa.depuisJson(_contenu());
    expect(c.etapesLangue.length, 6);
    expect(c.etapesSciences.length, 6);
    expect(c.etapeLangue('alphabet')['lettres'], isNotEmpty);
    expect(c.etapeLangue('inconnue'), isEmpty);
  });

  test('gabarit « {} » rempli dans l\'ordre, comme str.format de Python', () {
    expect(formaterGabarit('{} / {}', <Object>[3, 10]), '3 / 10');
    expect(formaterGabarit('encore {} pour {}', <Object>[2, 'Savant']), 'encore 2 pour Savant');
    expect(formaterGabarit('sans marqueur', <Object>[1]), 'sans marqueur');
  });

  test('chaque changement est signalé à l\'hôte avec le bon module ; rien en mode visiteur', () {
    final appels = <String>[];
    final connecte = ControleurMadrassa(MadrassaHote(contenu: _contenu(), surSauver: (m, d) => appels.add(m)));
    connecte.marquerLangue('alphabet', '3', true);
    connecte.marquerSciences('sciences_coran', '0', true);
    connecte.repondre(0, 1, true);
    connecte.marquerLu(2, true);
    expect(appels, <String>[cleModuleLangueArabe, cleModuleSciencesIslamiques, cleModuleJeu, cleModuleJeu]);
    expect(connecte.acquisLangue, 1);
    expect(connecte.acquisSciences, 1);
    expect(connecte.perles, 1);
    expect(connecte.etatLangue('alphabet', 3), 'connu');

    final visiteur = ControleurMadrassa(MadrassaHote(
      contenu: _contenu(),
      visiteur: true,
      surSauver: (m, d) => appels.add('visiteur'),
    ));
    visiteur.marquerLangue('alphabet', '1', false);
    expect(appels.contains('visiteur'), isFalse);
    expect(visiteur.pointsARevoir, 1);
  });

  test('la progression de l\'hôte est reprise et un point de la Caravane retourne dans son module', () {
    final c = ControleurMadrassa(MadrassaHote(
      contenu: _contenu(),
      progres: <String, dynamic>{
        cleModuleLangueArabe: <String, dynamic>{'alphabet': <String, dynamic>{'connues': <String>['0'], 'a_revoir': <String>['1']}},
        cleModuleSciencesIslamiques: <String, dynamic>{'sciences_coran': <String, dynamic>{'connues': <String>[], 'a_revoir': <String>['2']}},
        cleModuleJeu: <String, dynamic>{'lus': <int>[4], 'quiz_reussis': <String, dynamic>{'0': <int>[0, 1]}},
      },
    ));
    expect(c.pointsARevoir, 2);
    expect(c.perles, 2);
    expect(c.jeu.lus, <int>[4]);

    final session = construireSessionRevision(c.combine, c.contenu.langueArabe, contenuSciences: c.contenu.sciences);
    final sciences = session.firstWhere((i) => i.cleEtape == 'sciences_coran');
    c.marquerCaravane(sciences, true);
    expect(c.etatSciences('sciences_coran', '2'), 'connu');
    expect(c.pointsARevoir, 1);
    expect(c.langue.containsKey('sciences_coran'), isFalse);
  });
}
