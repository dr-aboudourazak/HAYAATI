import 'config.dart';

typedef Json = Map<String, dynamic>;

Map<String, String> _i18n(Object? v) {
  if (v is Map) {
    return v.map((k, x) => MapEntry(k.toString(), x.toString()));
  }
  return const <String, String>{};
}

List<String> _liste(Object? v) =>
    v is List ? v.map((e) => e.toString()).toList() : const <String>[];

Coord? _coord(Object? v) {
  if (v is Map && v['lat'] is num && v['lon'] is num) {
    return Coord((v['lat'] as num).toDouble(), (v['lon'] as num).toDouble());
  }
  return null;
}

class Ville {
  const Ville({required this.id, required this.nom, this.region, this.gps});

  final String id;
  final Map<String, String> nom;
  final String? region;
  final Coord? gps;

  factory Ville.fromJson(Json j) => Ville(
        id: j['id'] as String,
        nom: _i18n(j['nom']),
        region: j['region'] as String?,
        gps: _coord(j['gps']),
      );
}

class ZoneService {
  const ZoneService({
    this.paysEntier = false,
    this.villes = const <String>[],
    this.international = false,
  });

  final bool paysEntier;
  final List<String> villes;
  final bool international;

  factory ZoneService.fromJson(Object? v) {
    if (v is! Map) return const ZoneService();
    return ZoneService(
      paysEntier: v['pays_entier'] == true,
      villes: _liste(v['villes']),
      international: v['international'] == true,
    );
  }
}

class BlocMadrassa {
  const BlocMadrassa({
    this.publics = const <String>[],
    this.disciplines = const <String>[],
    this.modalite,
  });

  final List<String> publics;
  final List<String> disciplines;
  final String? modalite;

  factory BlocMadrassa.fromJson(Object? v) {
    if (v is! Map) return const BlocMadrassa();
    return BlocMadrassa(
      publics: _liste(v['publics']),
      disciplines: _liste(v['disciplines']),
      modalite: v['modalite'] as String?,
    );
  }
}

class BlocMosquee {
  const BlocMosquee({
    this.jumua = 'inconnu',
    this.jumuaHeure,
    this.langueKhutba = const <String>[],
    this.femmes = 'inconnu',
    this.ablutions = 'inconnu',
  });

  final String jumua;
  final String? jumuaHeure;
  final List<String> langueKhutba;
  final String femmes;
  final String ablutions;

  factory BlocMosquee.fromJson(Object? v) {
    if (v is! Map) return const BlocMosquee();
    return BlocMosquee(
      jumua: (v['jumua'] as String?) ?? 'inconnu',
      jumuaHeure: v['jumua_heure'] as String?,
      langueKhutba: _liste(v['langue_khutba']),
      femmes: (v['femmes'] as String?) ?? 'inconnu',
      ablutions: (v['ablutions'] as String?) ?? 'inconnu',
    );
  }
}

class Agrement {
  const Agrement({required this.numero, this.autorite, this.valideJusqua});

  final String numero;
  final String? autorite;

  /// Date ISO jusqu'à laquelle l'agrément est valable.
  final String? valideJusqua;

  factory Agrement.fromJson(Json j) => Agrement(
        numero: j['numero'] as String,
        autorite: j['autorite'] as String?,
        valideJusqua: j['valide_jusqua'] as String?,
      );
}

class BlocAgence {
  const BlocAgence({this.agrement, this.services = const <String>[]});

  final Agrement? agrement;
  final List<String> services;

  factory BlocAgence.fromJson(Object? v) {
    if (v is! Map) return const BlocAgence();
    return BlocAgence(
      agrement: v['agrement'] is Map ? Agrement.fromJson(v['agrement'] as Json) : null,
      services: _liste(v['services']),
    );
  }
}

class Fiche {
  const Fiche({
    required this.id,
    required this.type,
    required this.nom,
    required this.villeId,
    required this.niveau,
    required this.statut,
    this.description = const <String, String>{},
    this.quartier,
    this.gps,
    this.gpsPrecisionM,
    this.gpsSource = 'estimee',
    this.gpsVerifiee = false,
    this.whatsapp,
    this.langues = const <String>[],
    this.zone = const ZoneService(),
    this.madrassa = const BlocMadrassa(),
    this.mosquee = const BlocMosquee(),
    this.agence = const BlocAgence(),
  });

  final String id;
  final String type;
  final String nom;
  final String villeId;
  final int niveau;
  final String statut;
  final Map<String, String> description;
  final String? quartier;
  final Coord? gps;

  /// Précision du relevé GPS en mètres, si connue.
  final double? gpsPrecisionM;

  /// releve_sur_place, communaute, openstreetmap ou estimee.
  final String gpsSource;

  /// Vrai quand un responsable a confirmé la position.
  final bool gpsVerifiee;
  final String? whatsapp;
  final List<String> langues;
  final ZoneService zone;
  final BlocMadrassa madrassa;
  final BlocMosquee mosquee;
  final BlocAgence agence;

  factory Fiche.fromJson(Json j) {
    final lieu = j['lieu'] as Json;
    final contacts = (j['contacts'] as Json?) ?? const <String, dynamic>{};
    final verification = j['verification'] as Json;
    final blocGps = lieu['gps'];
    return Fiche(
      id: j['id'] as String,
      type: j['type'] as String,
      nom: j['nom'] as String,
      villeId: lieu['ville_id'] as String,
      niveau: (verification['niveau'] as num).toInt(),
      statut: j['statut'] as String,
      description: _i18n(j['description']),
      quartier: lieu['quartier'] as String?,
      gps: _coord(blocGps),
      gpsPrecisionM: blocGps is Map ? (blocGps['precision_m'] as num?)?.toDouble() : null,
      gpsSource: blocGps is Map ? ((blocGps['source'] as String?) ?? 'estimee') : 'estimee',
      gpsVerifiee: blocGps is Map && blocGps['verifiee'] == true,
      whatsapp: contacts['whatsapp'] as String?,
      langues: _liste(j['langues_parlees']),
      zone: ZoneService.fromJson(j['zone_service']),
      madrassa: BlocMadrassa.fromJson(j['madrassa']),
      mosquee: BlocMosquee.fromJson(j['mosquee']),
      agence: BlocAgence.fromJson(j['agence']),
    );
  }
}

class Cours {
  const Cours({
    required this.id,
    required this.ficheId,
    required this.sujet,
    required this.jours,
    required this.debut,
    required this.fin,
    required this.periodicite,
    required this.statut,
    this.publics = const <String>[],
    this.modalite,
    this.noteHoraire = const <String, String>{},
    this.montant,
    this.devise,
    this.seuilMin,
    this.capaciteMax,
    this.dateLimite,
    this.preinscrits,
    this.preinscritsMajLe,
  });

  final String id;
  final String ficheId;
  final Map<String, String> sujet;
  final List<String> jours;
  final String debut;
  final String fin;
  final String periodicite;
  final String statut;
  final List<String> publics;
  final String? modalite;
  final Map<String, String> noteHoraire;
  final double? montant;
  final String? devise;
  final int? seuilMin;
  final int? capaciteMax;
  final String? dateLimite;
  final int? preinscrits;
  final String? preinscritsMajLe;

  bool get gratuit => periodicite == 'gratuit';

  factory Cours.fromJson(Json j) {
    final horaire = j['horaire'] as Json;
    final tarif = j['tarif'] as Json;
    final pre = j['preinscrits'] as Json?;
    return Cours(
      id: j['id'] as String,
      ficheId: j['fiche_id'] as String,
      sujet: _i18n(j['sujet']),
      jours: _liste(j['jours']),
      debut: horaire['debut'] as String,
      fin: horaire['fin'] as String,
      periodicite: tarif['periodicite'] as String,
      statut: j['statut'] as String,
      publics: _liste(j['publics']),
      modalite: j['modalite'] as String?,
      noteHoraire: _i18n(j['note_horaire']),
      montant: (tarif['montant'] as num?)?.toDouble(),
      devise: tarif['devise'] as String?,
      seuilMin: (j['seuil_min'] as num?)?.toInt(),
      capaciteMax: (j['capacite_max'] as num?)?.toInt(),
      dateLimite: j['date_limite'] as String?,
      preinscrits: (pre?['nombre'] as num?)?.toInt(),
      preinscritsMajLe: pre?['maj_le'] as String?,
    );
  }
}

class Article {
  const Article({
    required this.id,
    required this.ficheId,
    required this.nom,
    required this.categorie,
    required this.disponibilite,
    this.montant,
    this.devise,
    this.avertissementSante = false,
  });

  final String id;
  final String ficheId;
  final Map<String, String> nom;
  final String categorie;
  final String disponibilite;
  final double? montant;
  final String? devise;
  final bool avertissementSante;

  factory Article.fromJson(Json j) {
    final prix = j['prix'] as Json?;
    return Article(
      id: j['id'] as String,
      ficheId: j['fiche_id'] as String,
      nom: _i18n(j['nom']),
      categorie: j['categorie'] as String,
      disponibilite: j['disponibilite'] as String,
      montant: (prix?['montant'] as num?)?.toDouble(),
      devise: prix?['devise'] as String?,
      avertissementSante: j['avertissement_sante'] == true,
    );
  }
}

class Prestation {
  const Prestation({
    required this.id,
    required this.ficheId,
    required this.besoin,
    required this.modalites,
    required this.typeTarif,
    this.description = const <String, String>{},
    this.min,
    this.max,
    this.devise,
  });

  final String id;
  final String ficheId;
  final String besoin;
  final List<String> modalites;
  final String typeTarif;
  final Map<String, String> description;
  final double? min;
  final double? max;
  final String? devise;

  factory Prestation.fromJson(Json j) {
    final tarif = j['tarif'] as Json;
    return Prestation(
      id: j['id'] as String,
      ficheId: j['fiche_id'] as String,
      besoin: j['besoin'] as String,
      modalites: _liste(j['modalites']),
      typeTarif: tarif['type'] as String,
      description: _i18n(j['description']),
      min: (tarif['min'] as num?)?.toDouble(),
      max: (tarif['max'] as num?)?.toDouble(),
      devise: tarif['devise'] as String?,
    );
  }
}

bool? _bool(Object? v) => v is bool ? v : null;

class Hotel {
  const Hotel({this.nom, this.etoiles, this.distanceM});

  final String? nom;
  final int? etoiles;

  /// Distance à pied jusqu'au Haram (La Mecque) ou à la mosquée du Prophète (Médine).
  final int? distanceM;

  static Hotel? fromJson(Object? v, String cleDistance) {
    if (v is! Map) return null;
    return Hotel(
      nom: v['hotel'] as String?,
      etoiles: (v['etoiles'] as num?)?.toInt(),
      distanceM: (v[cleDistance] as num?)?.toInt(),
    );
  }
}

/// Forfait Hadj ou Omra avec fiche de coûts standardisée (section 8 de la spécification).
class Forfait {
  const Forfait({
    required this.id,
    required this.ficheId,
    required this.type,
    required this.intitule,
    required this.dateDepart,
    required this.dateRetour,
    required this.montant,
    required this.devise,
    required this.statut,
    this.villeDepartId,
    this.acompte,
    this.volInclus,
    this.volDetail,
    this.hotelMakkah,
    this.hotelMadina,
    this.repas,
    this.visaInclus,
    this.transportInclus,
    this.guidePresent,
    this.guideLangues = const <String>[],
    this.encadrementMedical,
    this.groupeMin,
    this.groupeMax,
    this.assuranceIncluse,
    this.annulation = const <String, String>{},
    this.fraisNonInclus,
    this.placesRestantes,
    this.dateLimite,
  });

  final String id;
  final String ficheId;

  /// « hadj » ou « omra ».
  final String type;
  final Map<String, String> intitule;
  final String dateDepart;
  final String dateRetour;
  final double montant;
  final String devise;
  final String statut;
  final String? villeDepartId;
  final double? acompte;
  final bool? volInclus;
  final String? volDetail;
  final Hotel? hotelMakkah;
  final Hotel? hotelMadina;
  final String? repas;
  final bool? visaInclus;
  final bool? transportInclus;
  final bool? guidePresent;
  final List<String> guideLangues;
  final bool? encadrementMedical;
  final int? groupeMin;
  final int? groupeMax;
  final bool? assuranceIncluse;
  final Map<String, String> annulation;

  /// null = rubrique non renseignée ; liste vide = « aucun frais supplémentaire » déclaré.
  final List<Map<String, String>>? fraisNonInclus;
  final int? placesRestantes;
  final String? dateLimite;

  /// Nombre de jours entre le départ et le retour, départ et retour compris.
  int get dureeJours {
    final d = DateTime.tryParse(dateDepart);
    final r = DateTime.tryParse(dateRetour);
    if (d == null || r == null) return 0;
    return r.difference(d).inDays + 1;
  }

  /// Part des 11 rubriques de la fiche de coûts renseignées, de 0 à 100.
  int get scoreTransparence {
    final criteres = <bool>[
      volInclus != null,
      hotelMakkah?.distanceM != null,
      hotelMadina?.distanceM != null,
      repas != null,
      visaInclus != null,
      transportInclus != null,
      guidePresent != null,
      groupeMax != null,
      assuranceIncluse != null,
      annulation.isNotEmpty,
      fraisNonInclus != null,
    ];
    return (100 * criteres.where((c) => c).length / criteres.length).round();
  }

  factory Forfait.fromJson(Json j) {
    final prix = j['prix'] as Json;
    final acompte = j['acompte'] as Json?;
    final vol = j['vol'] as Json?;
    final heb = j['hebergement'] as Json?;
    final guide = j['guide'] as Json?;
    final groupe = j['taille_groupe'] as Json?;
    final assurance = j['assurance'] as Json?;
    final frais = j['frais_non_inclus'];
    return Forfait(
      id: j['id'] as String,
      ficheId: j['fiche_id'] as String,
      type: j['type'] as String,
      intitule: _i18n(j['intitule']),
      dateDepart: j['date_depart'] as String,
      dateRetour: j['date_retour'] as String,
      montant: (prix['montant'] as num).toDouble(),
      devise: prix['devise'] as String,
      statut: j['statut'] as String,
      villeDepartId: j['ville_depart_id'] as String?,
      acompte: (acompte?['montant'] as num?)?.toDouble(),
      volInclus: _bool(vol?['inclus']),
      volDetail: vol?['detail'] as String?,
      hotelMakkah: Hotel.fromJson(heb?['makkah'], 'distance_haram_m'),
      hotelMadina: Hotel.fromJson(heb?['madina'], 'distance_masjid_m'),
      repas: j['repas'] as String?,
      visaInclus: _bool(j['visa_inclus']),
      transportInclus: _bool(j['transport_inclus']),
      guidePresent: _bool(guide?['present']),
      guideLangues: _liste(guide?['langues']),
      encadrementMedical: _bool(guide?['encadrement_medical']),
      groupeMin: (groupe?['min'] as num?)?.toInt(),
      groupeMax: (groupe?['max'] as num?)?.toInt(),
      assuranceIncluse: _bool(assurance?['incluse']),
      annulation: _i18n(j['politique_annulation']),
      fraisNonInclus: frais is List ? frais.map((e) => _i18n(e)).toList() : null,
      placesRestantes: (j['places_restantes'] as num?)?.toInt(),
      dateLimite: j['date_limite_inscription'] as String?,
    );
  }
}

/// Contenu d'un fichier annuaire_XX.json ou mosquees_XX.json.
class Annuaire {
  const Annuaire({
    required this.pays,
    required this.version,
    required this.villes,
    required this.fiches,
    this.cours = const <Cours>[],
    this.articles = const <Article>[],
    this.prestations = const <Prestation>[],
    this.forfaits = const <Forfait>[],
    this.modulesActifs = const <String>[],
    this.attribution,
    this.moderationWhatsapp,
    this.demonstration = false,
  });

  final String pays;
  final int version;
  final List<Ville> villes;
  final List<Fiche> fiches;
  final List<Cours> cours;
  final List<Article> articles;
  final List<Prestation> prestations;
  final List<Forfait> forfaits;
  final List<String> modulesActifs;
  final String? attribution;

  /// Vrai pour un fichier d'exemple : ses fiches fictives s'affichent en démonstration.
  final bool demonstration;

  /// Numéro WhatsApp du responsable qui reçoit les propositions.
  final String? moderationWhatsapp;

  factory Annuaire.fromJson(Json j) {
    List<T> lire<T>(String cle, T Function(Json) f) {
      final v = j[cle];
      if (v is! List) return <T>[];
      return v.map((e) => f(e as Json)).toList();
    }

    return Annuaire(
      pays: j['pays'] as String,
      version: (j['version_donnees'] as num).toInt(),
      villes: lire('villes', Ville.fromJson),
      fiches: lire('fiches', Fiche.fromJson),
      cours: lire('cours', Cours.fromJson),
      articles: lire('articles', Article.fromJson),
      prestations: lire('prestations', Prestation.fromJson),
      forfaits: lire('forfaits_hadj_omra', Forfait.fromJson),
      modulesActifs: _liste(j['modules_actifs']),
      attribution: j['attribution'] as String?,
      demonstration: j['demonstration'] == true,
      moderationWhatsapp:
          j['moderation'] is Map ? (j['moderation'] as Map)['whatsapp'] as String? : null,
    );
  }
}
