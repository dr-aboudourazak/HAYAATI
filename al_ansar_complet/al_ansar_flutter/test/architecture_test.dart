import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

/// Garde-fou d'architecture : la structure en core / gui par fonctionnalité ne doit pas se déliter avec le temps.
///
/// Règles (sur les import/export de lib/src) :
///  A. un dossier core/ ne dépend d'aucun écran : ni widgets Flutter (material, widgets, cupertino), ni dossier gui/ ;
///  B. commun/ ne dépend d'aucune fonctionnalité ni de app/ (c'est lui que les fonctionnalités utilisent, pas l'inverse) ;
///  C. une fonctionnalité ne dépend pas d'une autre fonctionnalité (la coquille app/ les assemble) ;
///  D. priere/core est du Dart pur : uniquement dart:* et ses propres fichiers.
///
/// Les écarts qui existaient AVANT la mise en place de ces règles sont listés ci-dessous (« dettes connues »). Le test échoue
/// si un NOUVEL écart apparaît, et aussi si une dette est réglée sans avoir été retirée de la liste : la liste ne peut que
/// raccourcir. Elles disparaîtront avec l'extraction d'un contexte commun (langue, configuration, textes) et le déplacement de
/// l'écran d'accueil dans app/.
const List<String> dettesConnues = <String>[
  'commun/core/config.dart -> fonctionnalites/madrassa/core/contenu.dart',
  'commun/core/config.dart -> package:flutter/widgets.dart',
  'commun/gui/medias_fiche.dart -> fonctionnalites/annuaire/core/controleur.dart',
  'commun/gui/medias_fiche.dart -> fonctionnalites/annuaire/core/modeles.dart',
  'commun/gui/partage_fiche.dart -> fonctionnalites/annuaire/core/controleur.dart',
  'commun/gui/partage_fiche.dart -> fonctionnalites/annuaire/core/modeles.dart',
  'fonctionnalites/annuaire/core/controleur.dart -> fonctionnalites/madrassa/core/controleur_madrassa.dart',
  'fonctionnalites/annuaire/gui/ecrans.dart -> fonctionnalites/hadj_omra/gui/ecran_hadj_omra.dart',
  'fonctionnalites/annuaire/gui/ecrans.dart -> fonctionnalites/madrassa/gui/ecrans_madrassa.dart',
  'fonctionnalites/hadj_omra/gui/ecran_hadj_omra.dart -> fonctionnalites/annuaire/core/controleur.dart',
  'fonctionnalites/hadj_omra/gui/ecran_hadj_omra.dart -> fonctionnalites/annuaire/core/modeles.dart',
  'fonctionnalites/hadj_omra/gui/ecran_hadj_omra.dart -> fonctionnalites/annuaire/gui/ecrans.dart',
  'fonctionnalites/madrassa/gui/ecrans_madrassa.dart -> fonctionnalites/annuaire/core/controleur.dart',
  'fonctionnalites/madrassa/gui/ecrans_savoir.dart -> fonctionnalites/annuaire/core/controleur.dart',
];

final RegExp _directive = RegExp(r'''^\s*(?:import|export)\s+(['"])([^'"]+)\1''', multiLine: true);

String _normaliser(String chemin) {
  final parties = <String>[];
  for (final p in chemin.split('/')) {
    if (p.isEmpty || p == '.') continue;
    if (p == '..') {
      if (parties.isNotEmpty) parties.removeLast();
    } else {
      parties.add(p);
    }
  }
  return parties.join('/');
}

/// Pour chaque fichier de lib/src : ses dépendances (« dart:... », « package:... » ou chemin relatif à lib/src).
Map<String, List<String>> _dependances() {
  final resultat = <String, List<String>>{};
  for (final f in Directory('lib/src').listSync(recursive: true).whereType<File>()) {
    final chemin = f.path.replaceAll('\\', '/');
    if (!chemin.endsWith('.dart')) continue;
    final rel = chemin.substring(chemin.indexOf('lib/src/') + 'lib/src/'.length);
    final dossier = rel.contains('/') ? rel.substring(0, rel.lastIndexOf('/')) : '';
    final cibles = <String>[];
    for (final m in _directive.allMatches(f.readAsStringSync())) {
      final c = m.group(2)!;
      cibles.add(c.startsWith('dart:') || c.startsWith('package:') ? c : _normaliser('$dossier/$c'));
    }
    resultat[rel] = cibles;
  }
  return resultat;
}

String? _fonctionnalite(String chemin) {
  final m = RegExp(r'^fonctionnalites/([^/]+)/').firstMatch(chemin);
  return m?.group(1);
}

void main() {
  final dependances = _dependances();

  test('l\'arborescence attendue existe', () {
    for (final d in <String>['app', 'commun/core', 'commun/gui', 'services', 'fonctionnalites/annuaire', 'fonctionnalites/priere/core']) {
      expect(Directory('lib/src/$d').existsSync(), isTrue, reason: d);
    }
  });

  test('aucun écart nouveau aux règles A, B et C, aucune dette oubliée dans la liste', () {
    final ecarts = <String>{};
    dependances.forEach((rel, cibles) {
      for (final cible in cibles) {
        if (cible.startsWith('dart:')) continue;
        final widgets = cible == 'package:flutter/material.dart' ||
            cible == 'package:flutter/widgets.dart' ||
            cible == 'package:flutter/cupertino.dart';
        final a = '/$rel'.contains('/core/') && (widgets || '/$cible'.contains('/gui/'));
        final b = rel.startsWith('commun/') && (cible.startsWith('fonctionnalites/') || cible.startsWith('app/'));
        final fo = _fonctionnalite(rel);
        final fc = _fonctionnalite(cible);
        final c = fo != null && fc != null && fo != fc;
        if (a || b || c) ecarts.add('$rel -> $cible');
      }
    });
    final nouveaux = ecarts.difference(dettesConnues.toSet()).toList()..sort();
    final reglees = dettesConnues.toSet().difference(ecarts).toList()..sort();
    expect(nouveaux, isEmpty, reason: 'Nouveaux écarts d\'architecture (voir les règles en tête de ce fichier) :\n${nouveaux.join('\n')}');
    expect(reglees, isEmpty, reason: 'Dettes réglées : retirez-les de dettesConnues :\n${reglees.join('\n')}');
  });

  test('D : priere/core est du Dart pur', () {
    dependances.forEach((rel, cibles) {
      if (!rel.startsWith('fonctionnalites/priere/core/')) return;
      for (final cible in cibles) {
        final ok = cible.startsWith('dart:') || cible.startsWith('fonctionnalites/priere/core/');
        expect(ok, isTrue, reason: '$rel dépend de $cible');
      }
    });
  });
}
