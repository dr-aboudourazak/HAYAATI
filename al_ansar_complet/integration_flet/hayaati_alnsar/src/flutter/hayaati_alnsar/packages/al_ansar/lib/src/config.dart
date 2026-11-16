import 'madrassa/contenu.dart';

/// Version du module Al Ansâr (affichée en mode démo pour savoir quel code tourne vraiment).
const String versionModuleAlAnsar = '0.4.0';

/// Coordonnées géographiques en degrés décimaux.
class Coord {
  const Coord(this.lat, this.lon);

  final double lat;
  final double lon;
}

/// Position avec précision estimée par le GPS, en mètres.
class PositionPrecise {
  const PositionPrecise(this.coord, {this.precisionM});

  final Coord coord;
  final double? precisionM;
}

/// Raison pour laquelle aucune position n'a pu être obtenue.
enum ErreurPosition {
  /// Les permissions de localisation ne sont pas déclarées dans le manifeste Android de l'application.
  permissionNonDeclaree,
  permissionRefusee,
  permissionRefuseeDefinitivement,
  serviceDesactive,
  delaiDepasse,
  indisponible,
}

/// Une position, ou la raison de son absence.
class ResultatPosition {
  const ResultatPosition.ok(PositionPrecise this.position) : erreur = null;
  const ResultatPosition.echec(ErreurPosition this.erreur) : position = null;

  final PositionPrecise? position;
  final ErreurPosition? erreur;
}

/// Flux de positions fourni par l'hôte. Avec precis = false : réponse rapide
/// (dernière position récente, puis précision moyenne). Avec precis = true :
/// précision croissante jusqu'à l'arrêt de l'écoute (relevé sur place).
typedef FournisseurPosition = Stream<ResultatPosition> Function({required bool precis});

/// Raccourci de l'application hôte affiché sur l'accueil du module
/// (par exemple l'écran Madrassa de HAYAATI).
class RaccourciHote {
  const RaccourciHote({required this.cle, required this.titre, this.icone = 'apps'});

  final String cle;
  final String titre;

  /// Nom d'une icône Material connue du module (voir ecrans.dart).
  final String icone;
}

/// Réglages transmis par l'application hôte (HAYAATI/Flet) ou par l'exemple.
///
/// La position GPS vient de l'hôte : HAYAATI la connaît déjà pour les heures
/// de prière, donc Al Ansâr ne redemande aucune permission et n'ajoute aucune
/// dépendance de localisation.
class AlAnsarConfig {
  const AlAnsarConfig({
    required this.baseUrl,
    this.langue = 'fr',
    this.pays = 'TG',
    this.villeId,
    this.position,
    this.assetPrefix = 'assets/al_ansar/',
    this.modeDemo,
    this.madrassa,
    this.ecranInitial,
    this.fournisseurPosition,
    this.textes = const <String, String>{},
    this.raccourcisHote = const <RaccourciHote>[],
    this.surOuvrirHote,
    this.surProfondeur,
    this.integre = false,
  });

  /// Adresse de publication des fichiers, terminée par « / ».
  final String baseUrl;
  final String langue;

  /// Code ISO du pays d'origine de l'utilisateur.
  final String pays;
  final String? villeId;
  final Coord? position;
  final String assetPrefix;

  /// Fiches « brouillon » et d'exemple : true les affiche, false les masque, null suit les données
  /// (un fichier marqué `demonstration: true` est affiché en démonstration).
  final bool? modeDemo;

  /// Contenu pédagogique et progression fournis par l'hôte (Madrassa). Absent : pas de Madrassa.
  final MadrassaHote? madrassa;

  /// « madrassa » : le module s'ouvre directement sur le hub Madrassa.
  final String? ecranInitial;

  /// Sert à relever la position sur place (propositions de mosquées).
  final FournisseurPosition? fournisseurPosition;

  /// Textes de l'interface déjà traduits par l'hôte (priorité sur les textes intégrés).
  final Map<String, String> textes;
  final List<RaccourciHote> raccourcisHote;

  /// Appelé quand l'utilisateur touche un raccourci de l'hôte.
  final void Function(String cle)? surOuvrirHote;

  /// Appelé à chaque changement de profondeur de la navigation interne.
  final void Function(int profondeur)? surProfondeur;

  /// Vrai quand le module est affiché dans HAYAATI : pas de second bandeau vert
  /// (l'hôte a déjà le sien), titres de page discrets.
  final bool integre;

  AlAnsarConfig copyWith({
    String? langue,
    String? pays,
    String? villeId,
    bool effacerVille = false,
    Coord? position,
    Map<String, String>? textes,
    List<RaccourciHote>? raccourcisHote,
    bool? modeDemo,
    bool definirModeDemo = false,
  }) {
    return AlAnsarConfig(
      baseUrl: baseUrl,
      langue: langue ?? this.langue,
      pays: pays ?? this.pays,
      villeId: effacerVille ? null : (villeId ?? this.villeId),
      position: position ?? this.position,
      assetPrefix: assetPrefix,
      modeDemo: definirModeDemo ? modeDemo : this.modeDemo,
      madrassa: madrassa,
      ecranInitial: ecranInitial,
      fournisseurPosition: fournisseurPosition,
      textes: textes ?? this.textes,
      raccourcisHote: raccourcisHote ?? this.raccourcisHote,
      surOuvrirHote: surOuvrirHote,
      surProfondeur: surProfondeur,
      integre: integre,
    );
  }
}
