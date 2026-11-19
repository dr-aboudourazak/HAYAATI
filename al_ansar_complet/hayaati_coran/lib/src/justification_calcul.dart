/// Choix des réglages qui font finir le dernier verset d'une page exactement au bout de sa dernière ligne, comme
/// dans un mushaf imprimé. Ce fichier ne dépend pas de Flutter : il travaille sur un MODÈLE du paragraphe (la largeur
/// de chaque mot et de chaque espace, mesurées une fois), ce qui le rend instantané et testable.
///
/// Principe : le texte est composé en lignes justifiées, donc seule la dernière ligne reste « libre ». Un léger
/// ajustement de la taille du texte (au plus 9 %, moins qu'un cran de A+ ou A-, 4 à 5 % en moyenne) et de l'espace entre les mots déplace
/// les coupures de lignes. On simule des centaines de combinaisons et l'on retient la plus discrète qui remplit la
/// dernière ligne. L'appelant vérifie ensuite le résultat par une vraie mise en page, puis comble le petit manque
/// restant en élargissant les seuls espaces de la dernière ligne.
library;

/// Largeur de chaque mot et de chaque espace qui les sépare (un mot de moins que de mots), en pixels logiques à la
/// taille de référence. Un mot est un bloc de texte entre deux espaces ordinaires ; l'espace insécable reste dans le mot.
class ModeleParagraphe {
  const ModeleParagraphe(this.mots, this.espaces);

  final List<double> mots;
  final List<double> espaces;
}

/// Résultat d'une simulation : nombre de lignes et largeur de la dernière, en pixels logiques.
class MesureParagraphe {
  const MesureParagraphe(this.nbLignes, this.largeurFin);

  final int nbLignes;
  final double largeurFin;
}

/// Une combinaison retenue : taille multipliée par [echelle], [espaceMots] pixels ajoutés à chaque espace.
class CandidatJustification {
  const CandidatJustification(this.echelle, this.espaceMots, this.remplissage, this.cout);

  final double echelle;
  final double espaceMots;

  /// Largeur de la dernière ligne divisée par la largeur disponible.
  final double remplissage;

  /// Discrétion du changement : plus il est petit, moins le texte s'écarte de ce que l'utilisateur a choisi.
  final double cout;
}

/// Marge laissée au bout de la ligne : une mesure et un affichage peuvent différer de moins d'un pixel ; sans marge,
/// un mot de trop passerait seul à la ligne suivante.
const double margeJustification = 2.0;

/// Paliers de remplissage de la dernière ligne, du meilleur au moins bon. Le manque restant est comblé en élargissant
/// les espaces de cette ligne (jusqu'à environ 14 px par espace, du même ordre que les lignes justifiées voisines).
const List<double> paliersRemplissage = <double>[0.97, 0.93, 0.88, 0.80];

/// Une dernière ligne remplie à ce taux ou plus est considérée comme pleine.
const double seuilRemplissage = 0.88;

int _palier(double remplissage) {
  for (var i = 0; i < paliersRemplissage.length; i++) {
    if (remplissage >= paliersRemplissage[i]) return paliersRemplissage.length - i;
  }
  return 0;
}

/// Coupe le paragraphe en lignes comme le fait un moteur de texte (coupure gloutonne aux espaces) et retourne le
/// nombre de lignes et la largeur de la dernière.
MesureParagraphe simuler(ModeleParagraphe m, double largeur, {double echelle = 1.0, double espaceMots = 0.0}) {
  if (m.mots.isEmpty) return const MesureParagraphe(0, 0);
  var lignes = 1;
  var courant = m.mots[0] * echelle;
  for (var i = 1; i < m.mots.length; i++) {
    final w = m.mots[i] * echelle;
    final g = m.espaces[i - 1] * echelle + espaceMots;
    if (courant + g + w <= largeur) {
      courant += g + w;
    } else {
      lignes++;
      courant = w;
    }
  }
  return MesureParagraphe(lignes, courant);
}

/// Cherche les combinaisons qui remplissent la dernière ligne. Elles sont classées par palier de remplissage
/// (le plus plein d'abord), puis, à palier égal, du changement le plus discret au moins discret.
/// Retourne une liste vide si le texte tient en une ligne.
List<CandidatJustification> chercherCandidats(
  ModeleParagraphe m,
  double largeur, {
  double echelleMin = 0.91,
  double echelleMax = 1.09,
  double pasEchelle = 0.004,
  double espaceMin = -2.0,
  double espaceMax = 8.0,
  double pasEspace = 0.25,
  int maxResultats = 6,
}) {
  if (m.mots.length < 2 || largeur <= 0) return const <CandidatJustification>[];
  final plafond = (largeur - margeJustification) / largeur;
  final tous = <CandidatJustification>[];
  final nbEchelles = ((echelleMax - echelleMin) / pasEchelle).round();
  final nbEspaces = ((espaceMax - espaceMin) / pasEspace).round();
  for (var i = 0; i <= nbEchelles; i++) {
    final s = echelleMin + i * pasEchelle;
    for (var j = 0; j <= nbEspaces; j++) {
      final ws = espaceMin + j * pasEspace;
      final r = simuler(m, largeur, echelle: s, espaceMots: ws);
      if (r.nbLignes < 2) continue;
      final remplissage = r.largeurFin / largeur;
      if (remplissage > plafond) continue; // déborderait : un mot passerait seul à la ligne
      tous.add(CandidatJustification(s, ws, remplissage, 6 * (s - 1).abs() + ws.abs() / 12));
    }
  }
  tous.sort((a, b) {
    final c = _palier(b.remplissage).compareTo(_palier(a.remplissage));
    if (c != 0) return c;
    // à palier égal : au meilleur palier, le plus discret ; sinon (aucun palier atteint), le plus rempli
    return _palier(a.remplissage) > 0 ? a.cout.compareTo(b.cout) : b.remplissage.compareTo(a.remplissage);
  });
  return tous.take(maxResultats).toList();
}

/// Espacement à ajouter aux espaces de la dernière ligne pour qu'elle atteigne le bout de la ligne.
/// [w0] : largeur de la dernière ligne telle quelle ; [w1] : sa largeur avec [pas] pixels ajoutés à chaque espace
/// (la différence donne le nombre d'espaces qui s'élargissent vraiment). Le résultat est borné par [maximum] ;
/// il vaut 0 si la ligne n'a pas d'espace à élargir ou si elle est déjà assez remplie.
double espaceFinPour({
  required double largeur,
  required double w0,
  required double w1,
  double pas = 1.0,
  double maximum = 14.0,
}) {
  final k = (w1 - w0) / pas;
  if (k < 0.5) return 0;
  final manque = largeur - margeJustification - w0;
  if (manque <= 0) return 0;
  final ws = manque / k;
  return ws > maximum ? maximum : ws;
}
