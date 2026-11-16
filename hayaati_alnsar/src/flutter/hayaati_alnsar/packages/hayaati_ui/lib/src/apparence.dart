/// Apparence de HAYAATI choisie par l'utilisateur : un arrière-plan (clair, papier ou sombre) et une couleur principale
/// (vert, terracotta ou ocre, toutes trois de la charte). Ce fichier ne dépend pas de Flutter : les valeurs des couleurs
/// y sont des entiers ARGB, ce qui permet de CONTRÔLER automatiquement les contrastes de lisibilité (voir les tests).
///
/// Le thème « clair » avec la couleur « vert » est la charte officielle de HAYAATI, à l'identique de palette_hayaati.py.
/// « Papier » en garde les teintes chaudes sur un fond de papier ancien. « Sombre » est la seule adaptation libre de la
/// charte : mêmes teintes (vert, terracotta, ocre), éclaircies pour rester lisibles sur fond sombre.
library;

import 'dart:math' as math;

const List<String> fondsApparence = <String>['clair', 'papier', 'sombre'];
const List<String> couleursApparence = <String>['vert', 'terracotta', 'ocre'];

/// Choix de l'utilisateur, enregistré tel quel (JSON) et validé à la lecture comme les réglages de lecture du Coran.
class ApparenceHayaati {
  const ApparenceHayaati({this.fond = 'clair', this.couleur = 'vert'});

  static const int version = 1;

  final String fond;
  final String couleur;

  static const ApparenceHayaati defaut = ApparenceHayaati();

  /// Ramène un contenu brut (fichier édité, ancien ou illisible) à des valeurs sûres.
  factory ApparenceHayaati.depuisJson(Object? brut) {
    if (brut is! Map) return defaut;
    final f = brut['fond'];
    final c = brut['couleur'];
    return ApparenceHayaati(
      fond: f is String && fondsApparence.contains(f) ? f : 'clair',
      couleur: c is String && couleursApparence.contains(c) ? c : 'vert',
    );
  }

  Map<String, dynamic> toJson() => <String, dynamic>{'version': version, 'fond': fond, 'couleur': couleur};

  ApparenceHayaati avec({String? fond, String? couleur}) =>
      ApparenceHayaati(fond: fond ?? this.fond, couleur: couleur ?? this.couleur);

  bool get sombre => fond == 'sombre';

  @override
  bool operator ==(Object autre) => autre is ApparenceHayaati && autre.fond == fond && autre.couleur == couleur;

  @override
  int get hashCode => Object.hash(fond, couleur);
}

/// Luminance relative WCAG d'une couleur ARGB (0 = noir, 1 = blanc).
double luminance(int argb) {
  double canal(int v) {
    final s = v / 255.0;
    return s <= 0.03928 ? s / 12.92 : math.pow((s + 0.055) / 1.055, 2.4).toDouble();
  }

  return 0.2126 * canal((argb >> 16) & 0xFF) + 0.7152 * canal((argb >> 8) & 0xFF) + 0.0722 * canal(argb & 0xFF);
}

/// Rapport de contraste WCAG entre deux couleurs (de 1 à 21). 4,5 : texte courant lisible ; 7 : très confortable ;
/// 3 : éléments d'interface et grands textes.
double contraste(int a, int b) {
  final la = luminance(a);
  final lb = luminance(b);
  final haut = math.max(la, lb);
  final bas = math.min(la, lb);
  return (haut + 0.05) / (bas + 0.05);
}

/// Toutes les couleurs d'une apparence, sous les mêmes noms que la palette officielle (PaletteHayaati) : un écran qui
/// lisait `vertProfond` ou `sable` lit simplement la valeur de l'apparence en cours.
///  - sable : fond de page ; blanc : fond des cartes et des zones ; grisClair : fond discret ;
///  - texteFonce : texte de corps ; grisTexte : texte secondaire ;
///  - vertProfond et vertClair : couleur d'accentuation du texte et des icônes (le vert, ou la couleur principale choisie) ;
///  - primaire et surPrimaire : bandeaux et boutons pleins, et le texte qui s'y trouve.
class ValeursCharte {
  const ValeursCharte({
    required this.sombre,
    required this.primaire,
    required this.surPrimaire,
    required this.vertProfond,
    required this.vertClair,
    required this.terracotta,
    required this.terracottaClair,
    required this.terracottaFonce,
    required this.ocre,
    required this.ocreClair,
    required this.ocreFonce,
    required this.texteFonce,
    required this.sable,
    required this.blanc,
    required this.grisTexte,
    required this.grisClair,
    required this.bordure,
    required this.vertSucces,
    required this.rougeErreur,
    required this.ambreAttente,
    required this.fondPage,
    required this.surlignage,
    required this.numeroVerset,
    required this.numeroSignet,
    required this.tajweed,
    required this.tajweedSurSurlignage,
  });

  final bool sombre;
  final int primaire, surPrimaire;
  final int vertProfond, vertClair;
  final int terracotta, terracottaClair, terracottaFonce;
  final int ocre, ocreClair, ocreFonce;
  final int texteFonce, sable, blanc, grisTexte, grisClair, bordure;
  final int vertSucces, rougeErreur, ambreAttente;

  /// Page du mushaf : fond, surlignage d'un verset, numéros de verset (ordinaire et signet).
  final int fondPage, surlignage, numeroVerset, numeroSignet;

  /// Cinq familles de couleurs du tajweed (madd, ghunna et idgham, ikhfa et iqlab, qalqala, lettres muettes), sur la
  /// page et sur le surlignage d'un verset (l'orange et le gris y prennent une variante plus foncée ou plus claire).
  final List<int> tajweed, tajweedSurSurlignage;

  /// Valeurs d'une apparence.
  factory ValeursCharte.pour(ApparenceHayaati a) {
    final base = switch (a.fond) {
      'papier' => _papier,
      'sombre' => _sombre,
      _ => _clair,
    };
    return base._avecCouleur(a.couleur);
  }

  ValeursCharte _avecCouleur(String couleur) {
    if (couleur == 'vert') return this;
    // Couleur principale de rechange : bandeaux et accents passent du vert à la terracotta ou à l'ocre.
    final t = sombre ? _teintesSombre[couleur]! : (identical(this, _papier) ? _teintesPapier[couleur]! : _teintesClair[couleur]!);
    return ValeursCharte(
      sombre: sombre,
      primaire: t[0],
      surPrimaire: t[1],
      vertProfond: t[2],
      vertClair: t[3],
      terracotta: terracotta,
      terracottaClair: terracottaClair,
      terracottaFonce: terracottaFonce,
      ocre: ocre,
      ocreClair: ocreClair,
      ocreFonce: ocreFonce,
      texteFonce: texteFonce,
      sable: sable,
      blanc: blanc,
      grisTexte: grisTexte,
      grisClair: grisClair,
      bordure: bordure,
      vertSucces: vertSucces,
      rougeErreur: rougeErreur,
      ambreAttente: ambreAttente,
      fondPage: fondPage,
      surlignage: surlignage,
      numeroVerset: numeroVerset,
      numeroSignet: numeroSignet,
      tajweed: tajweed,
      tajweedSurSurlignage: tajweedSurSurlignage,
    );
  }
}

// Couleur principale de rechange : [primaire, surPrimaire, vertProfond (accentuation), vertClair (accentuation 2)].
const Map<String, List<int>> _teintesClair = <String, List<int>>{
  'terracotta': <int>[0xFFA8431F, 0xFFFFFFFF, 0xFF7A2F14, 0xFFA8431F],
  'ocre': <int>[0xFFD9A441, 0xFF2B1607, 0xFF6B4A0C, 0xFF8A5F10],
};
// Sur le papier, le fond est plus foncé que le sable : les accentuations sont un peu plus profondes.
const Map<String, List<int>> _teintesPapier = <String, List<int>>{
  'terracotta': <int>[0xFFA8431F, 0xFFFFFFFF, 0xFF7A2F14, 0xFF9C3D1B],
  'ocre': <int>[0xFFD9A441, 0xFF2B1607, 0xFF6B4A0C, 0xFF74500C],
};
const Map<String, List<int>> _teintesSombre = <String, List<int>>{
  'terracotta': <int>[0xFF6B2712, 0xFFFBEDE6, 0xFFF2AA90, 0xFFE2805F],
  'ocre': <int>[0xFF5A4310, 0xFFFBF0DA, 0xFFE8C27A, 0xFFD9A441],
};

// ---------------------------------------------------------------- clair : la charte officielle, à l'identique
const ValeursCharte _clair = ValeursCharte(
  sombre: false,
  primaire: 0xFF064E3B,
  surPrimaire: 0xFFFFFFFF,
  vertProfond: 0xFF064E3B,
  vertClair: 0xFF0F766E,
  terracotta: 0xFFC1502E,
  terracottaClair: 0xFFF4E4DC,
  terracottaFonce: 0xFF6B2712,
  ocre: 0xFFD9A441,
  ocreClair: 0xFFFBF0DA,
  ocreFonce: 0xFF7A5510,
  texteFonce: 0xFF2B1607,
  sable: 0xFFFBF6EE,
  blanc: 0xFFFFFFFF,
  grisTexte: 0xFF374151,
  grisClair: 0xFFF3F4F6,
  bordure: 0xFFE5E7EB,
  vertSucces: 0xFF27500A,
  rougeErreur: 0xFF791F1F,
  ambreAttente: 0xFFD97706,
  fondPage: 0xFFFFFDF8,
  surlignage: 0xFFFFE082,
  numeroVerset: 0xFF7B4F00,
  numeroSignet: 0xFF9B1C1C,
  tajweed: <int>[0xFFC62828, 0xFF2E7D32, 0xFFEF6C00, 0xFF1565C0, 0xFF9E9E9E],
  tajweedSurSurlignage: <int>[0xFFC62828, 0xFF2E7D32, 0xFFBF360C, 0xFF1565C0, 0xFF616161],
);

// ---------------------------------------------------------------- papier : mêmes teintes chaudes, fond de papier ancien
const ValeursCharte _papier = ValeursCharte(
  sombre: false,
  primaire: 0xFF064E3B,
  surPrimaire: 0xFFFFFFFF,
  vertProfond: 0xFF064E3B,
  vertClair: 0xFF0B615B,
  terracotta: 0xFFC1502E,
  terracottaClair: 0xFFEBD3C3,
  terracottaFonce: 0xFF6B2712,
  ocre: 0xFFD9A441,
  ocreClair: 0xFFF3DFB0,
  ocreFonce: 0xFF7A5510,
  texteFonce: 0xFF2B1607,
  sable: 0xFFF1E6CB,
  blanc: 0xFFF9F1DD,
  grisTexte: 0xFF463C2E,
  grisClair: 0xFFE7DABA,
  bordure: 0xFFD6C6A0,
  vertSucces: 0xFF27500A,
  rougeErreur: 0xFF791F1F,
  ambreAttente: 0xFFB45309,
  fondPage: 0xFFF7EED8,
  surlignage: 0xFFF0D27C,
  numeroVerset: 0xFF6B4300,
  numeroSignet: 0xFF8E1B1B,
  tajweed: <int>[0xFFB71C1C, 0xFF2A7530, 0xFFA84D00, 0xFF1565C0, 0xFF757575],
  tajweedSurSurlignage: <int>[0xFFA61919, 0xFF1B5E20, 0xFF8A3B00, 0xFF0D47A1, 0xFF4E4E4E],
);

// ---------------------------------------------------------------- sombre : mêmes teintes, éclaircies
const ValeursCharte _sombre = ValeursCharte(
  sombre: true,
  primaire: 0xFF0D3B2E,
  surPrimaire: 0xFFEAF3EE,
  vertProfond: 0xFF7FD8B0,
  vertClair: 0xFF5BBFAE,
  terracotta: 0xFFE2805F,
  terracottaClair: 0xFF3F2A22,
  terracottaFonce: 0xFFF2AA90,
  ocre: 0xFFD9A441,
  ocreClair: 0xFF3A3018,
  ocreFonce: 0xFFE8C27A,
  texteFonce: 0xFFEDE8DC,
  sable: 0xFF121A17,
  blanc: 0xFF1B2723,
  grisTexte: 0xFFB8C2BC,
  grisClair: 0xFF24332E,
  bordure: 0xFF2E3F39,
  vertSucces: 0xFF8BD17C,
  rougeErreur: 0xFFF28B82,
  ambreAttente: 0xFFF0A63A,
  fondPage: 0xFF0F1613,
  surlignage: 0xFF443A19,
  numeroVerset: 0xFFE3B968,
  numeroSignet: 0xFFF28B82,
  tajweed: <int>[0xFFFF8A80, 0xFF81C784, 0xFFFFB74D, 0xFF64B5F6, 0xFF9E9E9E],
  tajweedSurSurlignage: <int>[0xFFFF8A80, 0xFF81C784, 0xFFFFB74D, 0xFF64B5F6, 0xFFBDBDBD],
);
