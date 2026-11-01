/// Règles de tajweed annotées dans assets/coran/surah_NNN.json (champ « tajweed » : [[debut, fin, code], ...])
/// et leur regroupement en 5 familles de couleurs. Port de core/quran_tajweed.py.
///
/// Les codes sont écrits dans les fichiers de données : l'ORDRE de [reglesTajweed] ne doit jamais changer.
/// Annotations AUTOMATIQUES (https://github.com/cpfair/quran-tajweed, CC BY 4.0), destinées à aider la lecture :
/// elles ne remplacent pas l'apprentissage auprès d'un enseignant qualifié.
library;

const List<String> reglesTajweed = <String>[
  'ghunnah', 'idghaam_ghunnah', 'idghaam_no_ghunnah', 'idghaam_shafawi',
  'idghaam_mutajanisayn', 'idghaam_mutaqaribayn', 'ikhfa', 'ikhfa_shafawi', 'iqlab',
  'qalqalah', 'madd_2', 'madd_246', 'madd_6', 'madd_muttasil', 'madd_munfasil',
  'hamzat_wasl', 'lam_shamsiyyah', 'silent',
];

class FamilleTajweed {
  const FamilleTajweed(this.cle, this.couleur, this.cleLibelle);

  final String cle;

  /// « #RRGGBB » en majuscules, identique à Python.
  final String couleur;

  /// Clé du libellé dans la section « coran » des fichiers de langue.
  final String cleLibelle;
}

const List<FamilleTajweed> famillesTajweed = <FamilleTajweed>[
  FamilleTajweed('madd', '#C62828', 'famille_madd'),
  FamilleTajweed('ghunna_idgham', '#2E7D32', 'famille_ghunna_idgham'),
  FamilleTajweed('ikhfa_iqlab', '#EF6C00', 'famille_ikhfa_iqlab'),
  FamilleTajweed('qalqala', '#1565C0', 'famille_qalqala'),
  FamilleTajweed('muettes', '#9E9E9E', 'famille_muettes'),
];

// Même ordre que [reglesTajweed] : index = code - 1  ->  indice de famille.
const List<int> _familleParCode = <int>[1, 1, 1, 1, 1, 1, 2, 2, 2, 3, 0, 0, 0, 0, 0, 4, 4, 4];

/// Indice (0-4) de la famille d'un code de règle (1-18) ; -1 si le code est inconnu.
int indiceFamille(int code) => (code >= 1 && code <= _familleParCode.length) ? _familleParCode[code - 1] : -1;

// Variantes plus foncées, utilisées sur le fond jaune d'un verset surligné : l'orange et le gris n'y atteignent
// pas un contraste lisible (2,4 et 2,1 pour 1), leurs variantes y atteignent ~4,5.
const Map<String, String> _varianteSurSurlignage = <String, String>{'#EF6C00': '#BF360C', '#9E9E9E': '#616161'};
const Map<String, String> _varianteInverse = <String, String>{'#BF360C': '#EF6C00', '#616161': '#9E9E9E'};

String? couleurFamille(int indice, {bool surSurlignage = false}) {
  if (indice < 0 || indice >= famillesTajweed.length) return null;
  final c = famillesTajweed[indice].couleur;
  return surSurlignage ? (_varianteSurSurlignage[c] ?? c) : c;
}

/// Couleur à utiliser pour un texte de cette couleur lorsqu'il passe sur le surlignage.
String avecSurlignage(String couleur) => _varianteSurSurlignage[couleur] ?? couleur;

/// Opération inverse : retrouve la couleur d'origine quand le surlignage disparaît.
String sansSurlignage(String couleur) => _varianteInverse[couleur] ?? couleur;
