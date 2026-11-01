/// Textes de l'interface déjà traduits par l'hôte (section « coran » des fichiers de langue de HAYAATI).
/// Le module ne garde aucune traduction : une clé absente retombe sur le texte français par défaut.
library;

class TextesCoran {
  const TextesCoran([this._textes = const <String, String>{}, this.rtl = false]);

  final Map<String, String> _textes;

  /// Vrai si la langue de l'interface s'écrit de droite à gauche (arabe).
  final bool rtl;

  String call(String cle, [String defaut = '']) => _textes[cle] ?? defaut;

  /// Remplace {n}, {total}, {verset}, {page}... dans un gabarit, comme le font les fichiers de langue.
  String modele(String cle, Map<String, Object> valeurs, [String defaut = '']) {
    var s = _textes[cle] ?? defaut;
    valeurs.forEach((k, v) => s = s.replaceAll('{$k}', v.toString()));
    return s;
  }
}
