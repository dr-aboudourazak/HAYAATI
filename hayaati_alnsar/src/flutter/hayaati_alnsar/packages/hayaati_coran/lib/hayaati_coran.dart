/// Module Coran de HAYAATI : lecture par pages du mushaf de Médine (604 pages), tajweed en couleurs,
/// signets de page ou de verset, progression de lecture.
///
/// Le cœur (tajweed, texte, moteur, état de lecture) ne dépend pas de Flutter : il est testé contre
/// le moteur Python (core/quran_engine.py) à l'aide de test/golden/golden_coran.json.
library;

export 'src/controleur.dart';
export 'src/etat_lecture.dart';
export 'src/moteur_coran.dart';
export 'src/polices.dart';
export 'src/tajweed.dart';
export 'src/texte.dart';
export 'src/textes.dart';
export 'src/ui/module_coran.dart';
