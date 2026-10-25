import 'i18n_donnees.dart';

/// Textes de l'interface. Les tables viennent de traductions/al_ansar.json (fichier généré
/// i18n_donnees.dart) : toutes les langues sont complètes, imposé par outils/generer_traductions.py
/// et par test/traductions_test.dart. Le français sert seulement de repli pour une langue inconnue.
class Textes {
  const Textes(this.langue, {this.surcharge = const <String, String>{}});

  final String langue;

  /// Textes fournis par l'application hôte, prioritaires sur ceux du module.
  final Map<String, String> surcharge;

  bool get rtl => langue == 'ar';

  /// Tables par langue (utile aux tests de complétude).
  static Map<String, Map<String, String>> get tables => chainesGenerees;

  String call(String cle) =>
      surcharge[cle] ?? chainesGenerees[langue]?[cle] ?? chainesGenerees['fr']![cle] ?? cle;
}

/// Choisit un texte dans un dictionnaire par langue : langue active, puis fr, en,
/// puis la première langue disponible.
String choisir(Map<String, String> textes, String langue) {
  if (textes.isEmpty) return '';
  return textes[langue] ?? textes['fr'] ?? textes['en'] ?? textes.values.first;
}
