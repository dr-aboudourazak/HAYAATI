import 'package:flutter/foundation.dart';

import 'contenu.dart';
import 'moteurs.dart';

/// État de la progression de Madrassa. La progression est conservée par l'application hôte
/// (SyncEngine de HAYAATI) : chaque changement lui est signalé par [MadrassaHote.surSauver].
class ControleurMadrassa extends ChangeNotifier {
  ControleurMadrassa(MadrassaHote hote)
      : contenu = ContenuMadrassa.depuisJson(hote.contenu),
        visiteur = hote.visiteur,
        _surSauver = hote.surSauver {
    jeu = normaliserProgresJeu(hote.progres[cleModuleJeu]);
    langue = normaliserProgresLangue(hote.progres[cleModuleLangueArabe]);
    sciences = normaliserProgresLangue(hote.progres[cleModuleSciencesIslamiques]);
  }

  final ContenuMadrassa contenu;
  final bool visiteur;
  final void Function(String module, Map<String, dynamic> donnees)? _surSauver;

  late ProgresJeu jeu;
  late ProgresLangue langue;
  late ProgresLangue sciences;

  /// Progression de langue arabe et de sciences islamiques réunies (entrée de la Caravane).
  ProgresLangue get combine => <String, Map<String, List<String>>>{...langue, ...sciences};

  int get perles => compterPerles(jeu);

  int get pointsARevoir => compterPointsARevoir(combine);

  static int _acquis(ProgresLangue p) => p.entries
      .where((e) => e.key != 'caravane')
      .fold(0, (a, e) => a + e.value['connues']!.length);

  int get acquisLangue => _acquis(langue);

  int get acquisSciences => _acquis(sciences);

  void _sauver(String module, Map<String, dynamic> donnees) {
    if (!visiteur) _surSauver?.call(module, donnees);
  }

  void marquerLu(int indexCategorie, bool lu) {
    jeu = basculerLu(jeu, indexCategorie, lu);
    _sauver(cleModuleJeu, jeu.versJson());
    notifyListeners();
  }

  void repondre(int indexCategorie, int indexQuestion, bool correcte) {
    jeu = enregistrerReponse(jeu, indexCategorie, indexQuestion, correcte);
    _sauver(cleModuleJeu, jeu.versJson());
    notifyListeners();
  }

  void marquerLangue(String cleEtape, String identifiant, bool connu) {
    langue = marquerItem(langue, cleEtape, identifiant, connu);
    _sauver(cleModuleLangueArabe, langue);
    notifyListeners();
  }

  void marquerSciences(String cleEtape, String identifiant, bool connu) {
    sciences = marquerItem(sciences, cleEtape, identifiant, connu);
    _sauver(cleModuleSciencesIslamiques, sciences);
    notifyListeners();
  }

  /// Marque un point depuis la Caravane : il retourne dans le module d'origine.
  void marquerCaravane(ItemCaravane item, bool connu) {
    if (item.cleEtape.startsWith('sciences_')) {
      marquerSciences(item.cleEtape, item.identifiant, connu);
    } else {
      marquerLangue(item.cleEtape, item.identifiant, connu);
    }
  }

  String etatLangue(String cleEtape, Object id) => etatItem(langue, cleEtape, id);

  String etatSciences(String cleEtape, Object id) => etatItem(sciences, cleEtape, id);
}
