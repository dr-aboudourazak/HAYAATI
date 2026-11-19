/// Un titre dont le pictogramme de tête a été séparé du texte.
class TitreSepare {
  const TitreSepare(this.emoji, this.titre);

  /// Pictogramme(s) qui précédaient le titre (« 🏫 »), ou null s'il n'y en avait pas.
  final String? emoji;

  /// Le titre seul, sans pictogramme ni espaces autour.
  final String titre;
}

bool _pictogramme(int r) =>
    (r >= 0x1F000 && r <= 0x1FAFF) || // émojis, drapeaux, pictogrammes
    (r >= 0x2600 && r <= 0x27BF) || // symboles divers, dingbats
    (r >= 0x2B00 && r <= 0x2BFF) || // flèches et symboles divers
    (r >= 0x2300 && r <= 0x23FF) || // symboles techniques
    r == 0xFE0F || // sélecteur de variante émoji
    r == 0x200D; // liaison de séquence émoji

/// « 🏫 Madrassa » donne l'émoji « 🏫 » et le titre « Madrassa ». Sert à montrer le pictogramme à côté du titre
/// de la page, mais pas dans la liste des rubriques. Un texte qui n'est QUE un pictogramme est laissé tel quel.
TitreSepare separerEmoji(String texte) {
  final runes = texte.runes.toList();
  var i = 0;
  while (i < runes.length && _pictogramme(runes[i])) {
    i++;
  }
  if (i == 0) return TitreSepare(null, texte.trim());
  final emoji = String.fromCharCodes(runes.sublist(0, i));
  final reste = String.fromCharCodes(runes.sublist(i)).trim();
  if (reste.isEmpty) return TitreSepare(null, texte.trim());
  return TitreSepare(emoji, reste);
}
