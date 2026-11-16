import 'dart:convert';

import 'config.dart';
import 'i18n.dart';

enum TypeProposition { nouvelleMosquee, correctionPosition }

/// Proposition d'un utilisateur : nouvelle mosquée ou correction de position.
///
/// Phase 0 (sans serveur) : la proposition part sous forme de message WhatsApp
/// lisible par une personne, avec une ligne JSON lisible par le script
/// traiter_proposition.py. Un responsable vérifie avant toute publication.
class Proposition {
  const Proposition({
    required this.type,
    required this.pays,
    required this.nom,
    required this.position,
    this.villeId,
    this.ficheId,
    this.commentaire = '',
    this.creeLe,
  });

  final TypeProposition type;
  final String pays;
  final String? villeId;
  final String? ficheId;
  final String nom;
  final PositionPrecise position;
  final String commentaire;
  final DateTime? creeLe;

  String get codeType =>
      type == TypeProposition.nouvelleMosquee ? 'nouvelle_mosquee' : 'correction_position';

  Map<String, dynamic> toJson() {
    final precision = position.precisionM;
    return <String, dynamic>{
      'schema': 'al_ansar_proposition_v1',
      'type': codeType,
      'pays': pays,
      if (villeId != null) 'ville_id': villeId,
      if (ficheId != null) 'fiche_id': ficheId,
      'nom': nom,
      'position': <String, dynamic>{
        'lat': double.parse(position.coord.lat.toStringAsFixed(6)),
        'lon': double.parse(position.coord.lon.toStringAsFixed(6)),
        if (precision != null) 'precision_m': precision.round(),
        'source': 'releve_sur_place',
      },
      if (commentaire.isNotEmpty) 'commentaire': commentaire,
      'cree_le': (creeLe ?? DateTime.now()).toUtc().toIso8601String(),
    };
  }

  /// Message à envoyer : lignes lisibles, lien de carte, puis la ligne JSON.
  String versMessage(Textes t) {
    final lat = position.coord.lat.toStringAsFixed(6);
    final lon = position.coord.lon.toStringAsFixed(6);
    final precision = position.precisionM;
    final precisionTxt = precision == null ? '' : ' (±${precision.round()} m)';
    final titre = t(type == TypeProposition.nouvelleMosquee ? 'type_nouvelle' : 'type_correction');
    final lignes = <String>[
      'Al Ansâr · $titre',
      nom,
      if (ficheId != null) 'Fiche : $ficheId',
      'Position : $lat, $lon$precisionTxt',
      'Carte : https://www.openstreetmap.org/?mlat=$lat&mlon=$lon#map=19/$lat/$lon',
      if (commentaire.isNotEmpty) 'Commentaire : $commentaire',
      '',
      'AL-ANSAR-JSON ${jsonEncode(toJson())}',
    ];
    return lignes.join('\n');
  }
}
