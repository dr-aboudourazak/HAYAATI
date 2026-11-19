/// Mise en lignes justifiées d'un bloc de versets : les coupures de lignes sont CHOISIES (et non laissées au moteur
/// de texte) pour que chaque ligne, y compris la dernière du bloc, finisse exactement au bout de la ligne, comme dans
/// un mushaf imprimé. Cela vaut pour la fin d'une sourate au milieu d'une page comme pour la fin d'une page.
///
/// Ce fichier ne dépend pas de Flutter : il travaille sur le MODÈLE du paragraphe (largeur de chaque mot et de chaque
/// espace, mesurées une fois). La méthode est celle des bons logiciels de composition (coupures optimales par
/// programmation dynamique) : on minimise l'étirement des espaces sur l'ensemble du bloc, avec en plus une très légère
/// variation de taille (au plus 9 %) pour que le texte « tombe juste ».
library;

import 'justification_calcul.dart' show ModeleParagraphe;

/// Limites de ce que l'on accepte pour justifier une ligne.
class ReglagesLignes {
  const ReglagesLignes({
    this.etirementMax = 6.0,
    this.compressionMax = 0.5,
    this.echelleMin = 0.91,
    this.echelleMax = 1.09,
    this.pasEchelle = 0.01,
    this.marge = 0.5,
  });

  /// Étirement maximal d'un espace, en multiples de l'espace normal (6 : l'espace devient 7 fois plus large). À titre de
  /// comparaison, la coupure ordinaire d'un moteur de texte étire en moyenne de 2,3 fois et jusqu'à 10 fois.
  final double etirementMax;

  /// Compression maximale d'un espace, en multiples de l'espace normal (0,5 : l'espace perd la moitié).
  final double compressionMax;

  final double echelleMin;
  final double echelleMax;
  final double pasEchelle;

  /// Pixels laissés au bout de la ligne (chaque ligne est affichée seule, sans coupure possible : un écart de mesure
  /// d'un pixel ne peut donc pas faire passer un mot à la ligne, il déborde seulement de moins d'un pixel).
  final double marge;
}

/// Une ligne : mots [debut] inclus à [fin] exclu, [espace] pixels ajoutés à chacun de ses espaces.
class LigneCalculee {
  const LigneCalculee(this.debut, this.fin, this.espace);

  final int debut;
  final int fin;
  final double espace;

  int get nbMots => fin - debut;
  int get nbEspaces => fin - debut - 1;
}

class MiseEnLignes {
  const MiseEnLignes(this.echelle, this.lignes, this.cout);

  /// Facteur appliqué à la taille du texte (de 0,91 à 1,09).
  final double echelle;
  final List<LigneCalculee> lignes;

  /// Étirement total (plus il est petit, plus les espaces sont réguliers).
  final double cout;
}

/// Calcule les lignes d'un paragraphe. Retourne null s'il n'existe aucune mise en lignes acceptable (texte trop court
/// pour remplir une ligne, par exemple une fin de sourate de deux mots) : l'appelant garde alors l'affichage normal.
MiseEnLignes? calculerMiseEnLignes(ModeleParagraphe m, double largeur, {ReglagesLignes reglages = const ReglagesLignes()}) {
  final n = m.mots.length;
  if (n < 2 || largeur <= 0 || m.espaces.length != n - 1) return null;

  // Sommes cumulées : largeur d'une ligne en O(1).
  final pm = List<double>.filled(n + 1, 0);
  for (var i = 0; i < n; i++) {
    pm[i + 1] = pm[i] + m.mots[i];
  }
  final pe = List<double>.filled(n, 0);
  for (var i = 0; i < n - 1; i++) {
    pe[i + 1] = pe[i] + m.espaces[i];
  }
  final tri = List<double>.of(m.espaces)..sort();
  final espaceRef = tri[tri.length ~/ 2] > 0.5 ? tri[tri.length ~/ 2] : 5.0;
  final cible = largeur - reglages.marge;

  MiseEnLignes? meilleur;
  final nbEchelles = ((reglages.echelleMax - reglages.echelleMin) / reglages.pasEchelle).round();
  for (var e = 0; e <= nbEchelles; e++) {
    final s = reglages.echelleMin + e * reglages.pasEchelle;
    final ref = espaceRef * s;
    final cout = List<double>.filled(n + 1, double.infinity);
    final prec = List<int>.filled(n + 1, -1);
    final esp = List<double>.filled(n + 1, 0);
    cout[0] = 0;
    for (var i = 0; i < n; i++) {
      if (cout[i].isInfinite) continue;
      for (var j = i + 1; j <= n; j++) {
        final k = j - i - 1; // nombre d'espaces de la ligne
        final naturel = (pm[j] - pm[i] + pe[j - 1] - pe[i]) * s;
        // Même en comprimant au maximum, la ligne est trop large : les suivantes le seront encore plus.
        if (naturel - k * ref * reglages.compressionMax > cible) break;
        double c;
        double ws = 0;
        if (k == 0) {
          // Un seul mot : rien à étirer. Accepté seulement s'il remplit déjà la ligne.
          if ((cible - naturel) / largeur > 0.03) continue;
          c = 0;
        } else {
          ws = (cible - naturel) / k;
          final r = ws / ref;
          if (r > reglages.etirementMax || r < -reglages.compressionMax) continue;
          c = r >= 0 ? r * r : 4 * r * r;
        }
        final total = cout[i] + c + 0.1; // 0,1 par ligne : préfère peu de lignes à égalité
        if (total < cout[j]) {
          cout[j] = total;
          prec[j] = i;
          esp[j] = ws;
        }
      }
    }
    if (cout[n].isInfinite) continue;
    final lignes = <LigneCalculee>[];
    for (var j = n; j > 0; j = prec[j]) {
      lignes.add(LigneCalculee(prec[j], j, esp[j]));
    }
    final ordonnees = lignes.reversed.toList();
    // Une taille qui s'écarte de celle choisie par l'utilisateur est légèrement pénalisée.
    final penalise = cout[n] + 4 * (s - 1).abs() * ordonnees.length;
    if (meilleur == null || penalise < meilleur.cout) {
      meilleur = MiseEnLignes(s, ordonnees, penalise);
    }
  }
  return meilleur;
}

/// Réglages un peu plus souples (étirement et variation de taille plus larges), pour les blocs courts dont la mise en
/// lignes n'a pas abouti avec les réglages ordinaires.
const ReglagesLignes reglagesLignesSouples = ReglagesLignes(
  etirementMax: 9.0,
  compressionMax: 0.6,
  echelleMin: 0.88,
  echelleMax: 1.12,
);

/// Essaie les réglages ordinaires, puis les réglages souples. Null si aucun ne convient.
MiseEnLignes? calculerMiseEnLignesAvecRepli(ModeleParagraphe m, double largeur) =>
    calculerMiseEnLignes(m, largeur) ?? calculerMiseEnLignes(m, largeur, reglages: reglagesLignesSouples);
