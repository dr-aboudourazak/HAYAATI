import 'dart:convert';
import 'dart:io';

import 'package:al_ansar/al_ansar.dart';
import 'package:flutter_test/flutter_test.dart';

/// Rejoue les cas générés par les moteurs Python eux-mêmes (référence de vérité).
Map<String, dynamic> _json(String chemin) =>
    jsonDecode(File(chemin).readAsStringSync()) as Map<String, dynamic>;

void main() {
  final v = _json('test/fixtures/madrassa_vecteurs.json');
  final contenu = _json('test/fixtures/contenu_fr.json');
  final langue = contenu['langue_arabe'] as Map<String, dynamic>;
  final sciences = contenu['sciences_islamiques'] as Map<String, dynamic>;

  group('jeu éducatif', () {
    final jeu = v['jeu'] as Map<String, dynamic>;

    test('normalisation tolérante (valeurs invalides ignorées)', () {
      final cas = jeu['normaliser'] as Map<String, dynamic>;
      expect(normaliserProgresJeu(cas['entree']).versJson(), cas['attendu']);
    });

    test('suite de réponses : mêmes états que Python à chaque étape', () {
      final cas = jeu['sequence'] as Map<String, dynamic>;
      var p = normaliserProgresJeu(cas['depart']);
      final actions = cas['actions'] as List;
      final etats = cas['etats'] as List;
      for (var i = 0; i < actions.length; i++) {
        final a = actions[i] as Map<String, dynamic>;
        p = enregistrerReponse(p, a['cat'] as int, a['q'] as int, a['correct'] as bool);
        expect(p.versJson(), etats[i], reason: 'action $i');
      }
    });

    test('badges et prochain palier', () {
      for (final c in jeu['badges'] as List) {
        final n = (c as Map)['n'] as int;
        final b = badgeActuel(n);
        expect([b.cle, b.libelle], c['badge'], reason: 'perles $n');
        final prochain = prochainPalier(n);
        if (c['prochain'] == null) {
          expect(prochain, isNull, reason: 'perles $n');
        } else {
          expect([prochain!.manque, prochain.palier.cle, prochain.palier.libelle], c['prochain'], reason: 'perles $n');
        }
      }
    });

    test('compte des perles', () {
      for (final c in jeu['perles'] as List) {
        expect(compterPerles(normaliserProgresJeu((c as Map)['progres'])), c['perles']);
      }
    });

    test('marquer un thème comme lu puis non lu', () {
      var p = const ProgresJeu();
      p = basculerLu(p, 3, true);
      p = basculerLu(p, 1, true);
      expect(p.lus, [1, 3]);
      expect(basculerLu(p, 3, false).lus, [1]);
    });
  });

  group('langue arabe', () {
    final l = v['langue'] as Map<String, dynamic>;

    test('migration de l\'ancienne structure à plat', () {
      final cas = l['migration'] as Map<String, dynamic>;
      expect(normaliserProgresLangue(cas['entree']), cas['attendu']);
    });

    test('marquage exclusif connu / à revoir, état à chaque étape', () {
      final cas = l['sequence'] as Map<String, dynamic>;
      var p = normaliserProgresLangue(cas['depart']);
      final actions = cas['actions'] as List;
      final etats = cas['etats'] as List;
      for (var i = 0; i < actions.length; i++) {
        final a = actions[i] as Map<String, dynamic>;
        p = marquerItem(p, a['etape'] as String, a['id'] as String, a['connu'] as bool);
        expect(p, etats[i], reason: 'action $i');
      }
    });

    test('état d\'un item', () {
      for (final c in l['etats_items'] as List) {
        final m = c as Map<String, dynamic>;
        expect(etatItem(normaliserProgresLangue(m['progres']), m['etape'] as String, m['id'] as String), m['etat']);
      }
    });

    test('résumé d\'étape', () {
      for (final c in l['resumes'] as List) {
        final m = c as Map<String, dynamic>;
        expect(resumeEtape(normaliserProgresLangue(m['progres']), m['etape'] as String, m['total'] as int).toMap(), m['resume']);
      }
    });
  });

  group('caravane du savoir', () {
    final c = v['caravane'] as Map<String, dynamic>;
    final progres = normaliserProgresLangue(c['progres']);

    test('résolution d\'un point depuis le contenu', () {
      for (final r in c['resolutions'] as List) {
        final m = r as Map<String, dynamic>;
        final item = resoudreItem(langue, m['etape'] as String, m['id'] as String, contenuSciences: sciences);
        if (m['item'] == null) {
          expect(item, isNull, reason: '${m['etape']} ${m['id']}');
        } else {
          final attendu = Map<String, dynamic>.from(m['item'] as Map);
          final obtenu = item!.toMap()
            ..remove('cle_etape')
            ..remove('identifiant')
            ..remove('complement');
          expect(obtenu, attendu, reason: '${m['etape']} ${m['id']}');
        }
      }
    });

    test('séances de révision identiques à Python (taille 10, 3 et 40)', () {
      for (final cas in c['cas'] as List) {
        final m = cas as Map<String, dynamic>;
        final session = construireSessionRevision(progres, langue, tailleMax: m['taille'] as int, contenuSciences: sciences);
        expect(session.map((i) => i.toMap()).toList(), m['session'], reason: 'taille ${m['taille']}');
      }
    });

    test('points à revoir et séance vide', () {
      expect(compterPointsARevoir(progres), c['points_a_revoir']);
      final vide = c['vide'] as Map<String, dynamic>;
      expect(construireSessionRevision(<String, Map<String, List<String>>>{}, langue, contenuSciences: sciences), isEmpty);
      expect(compterPointsARevoir(<String, Map<String, List<String>>>{}), vide['points']);
    });
  });
}
