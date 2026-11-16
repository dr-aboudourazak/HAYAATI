import 'package:flutter/foundation.dart';

import 'config.dart';
import 'depot.dart';
import 'filtres.dart';
import 'geo.dart';
import 'i18n.dart';
import 'madrassa/controleur_madrassa.dart';
import 'modeles.dart';

/// Comment le lieu de recherche est défini.
enum ModeLieu {
  /// Position GPS de l'utilisateur : les services sont classés par distance.
  autourDeMoi,

  /// Une ville choisie dans la liste.
  ville,

  /// Tout le pays, sans point de référence.
  pays,
}

/// État partagé du module : lieu choisi, données du pays chargé, position GPS.
///
/// Un seul pays est gardé en mémoire à la fois (téléphones de 1 à 2 Go de RAM).
class ControleurAlAnsar extends ChangeNotifier {
  ControleurAlAnsar({required AlAnsarConfig config, DepotAnnuaire? depot})
      : _config = config,
        _depot = depot ??
            DepotAnnuaire(baseUrl: config.baseUrl, assetPrefix: config.assetPrefix) {
    final p = config.position;
    _positionGps = p == null ? null : PositionPrecise(p);
    _mode = p != null
        ? ModeLieu.autourDeMoi
        : (config.villeId != null ? ModeLieu.ville : ModeLieu.pays);
    final hote = config.madrassa;
    if (hote != null && hote.contenu.isNotEmpty) madrassa = ControleurMadrassa(hote);
  }

  AlAnsarConfig _config;
  final DepotAnnuaire _depot;

  Manifeste? manifeste;
  Annuaire? annuaire;
  Annuaire? mosquees;
  bool chargement = false;
  bool indisponible = false;

  late ModeLieu _mode;

  /// Madrassa (apprentissage), si l'hôte en fournit le contenu.
  ControleurMadrassa? madrassa;
  PositionPrecise? _positionGps;
  bool chargementPosition = false;
  ErreurPosition? erreurPosition;
  bool _lieuManuel = false;

  AlAnsarConfig get config => _config;
  Textes get t => Textes(_config.langue, surcharge: _config.textes);
  ModeLieu get mode => _mode;
  PositionPrecise? get positionGps => _positionGps;

  /// Vrai si l'utilisateur a choisi lui-même une ville ou un pays.
  bool get lieuManuel => _lieuManuel;

  /// Pays proposés dans le sélecteur. Sans manifeste (hors ligne), le pays courant.
  List<String> get paysDisponibles {
    final m = manifeste;
    if (m == null || m.pays.isEmpty) return <String>[_config.pays];
    return m.pays.map((p) => p.code).toList();
  }

  String nomPays(String code) {
    final p = manifeste?.parCode(code);
    return p == null ? code : choisir(p.nom, _config.langue);
  }

  Ville? ville(String? id) {
    if (id == null) return null;
    for (final v in annuaire?.villes ?? const <Ville>[]) {
      if (v.id == id) return v;
    }
    return null;
  }

  String nomVille(String id) {
    final v = ville(id);
    return v == null ? id : choisir(v.nom, _config.langue);
  }

  /// Responsable qui reçoit les propositions (mosquées proposées ou corrigées).
  String? get numeroModeration => mosquees?.moderationWhatsapp ?? annuaire?.moderationWhatsapp;

  /// Ligne technique : version du module et provenance des données (mode démo).
  String get resumeDonnees {
    final a = annuaire;
    final donnees = a == null
        ? 'aucune donnée lue'
        : '${_depot.sourceAnnuaire ?? '?'} v${a.version} · ${a.fiches.length} fiches (${a.fiches.where(visible).length} visibles) · ${a.forfaits.length} forfaits';
    return 'Module $versionModuleAlAnsar · données : $donnees · démo : ${demoActif ? 'oui' : 'non'}';
  }

  /// Cause technique si les données n'ont pas pu être lues.
  String? get diagnostic => _depot.diagnostic;

  /// Mode démonstration : réglage de l'hôte s'il existe, sinon indication des données.
  bool get demoActif =>
      _config.modeDemo ?? ((annuaire?.demonstration ?? false) || (mosquees?.demonstration ?? false));

  bool visible(Fiche f) => f.statut == 'publie' || demoActif;

  /// Nombre de fiches de ces types masquées parce qu'elles ne sont pas publiées.
  int brouillonsMasques(Set<String> types) {
    if (demoActif) return 0;
    return (annuaire?.fiches ?? const <Fiche>[]).where((f) => types.contains(f.type) && f.statut != 'publie').length;
  }

  /// Point de référence des recherches « proches ».
  Coord? get positionEffective {
    switch (_mode) {
      case ModeLieu.autourDeMoi:
        return _positionGps?.coord ?? _config.position;
      case ModeLieu.ville:
        return ville(_config.villeId)?.gps;
      case ModeLieu.pays:
        return null;
    }
  }

  bool get positionEstVille => _mode == ModeLieu.ville;

  Future<void> init() async {
    manifeste = await _depot.manifeste();
    // Voyageur : si la position fournie par l'hôte tombe dans un autre pays du
    // manifeste, on charge directement ce pays-là.
    final pos = _config.position;
    final m = manifeste;
    if (pos != null && m != null) {
      final p = m.paysDe(pos);
      if (p != null && p.code != _config.pays) {
        _config = _config.copyWith(pays: p.code, effacerVille: true);
      }
    }
    await _chargerPays(_config.pays);
  }

  Future<void> _chargerPays(String pays) async {
    chargement = true;
    notifyListeners();
    annuaire = await _depot.charger(pays, 'annuaire', manifeste: manifeste);
    mosquees = null; // libère la mémoire de l'ancien pays
    indisponible = annuaire == null;
    chargement = false;
    notifyListeners();
  }

  Future<void> chargerMosquees() async {
    if (mosquees != null) return;
    chargement = true;
    notifyListeners();
    mosquees = await _depot.charger(_config.pays, 'mosquees', manifeste: manifeste);
    chargement = false;
    notifyListeners();
  }

  /// Choisit un pays et/ou une ville (recherche pour un proche vivant ailleurs).
  Future<void> changerLieu({String? pays, String? villeId, bool toutesVilles = false}) async {
    final autrePays = pays != null && pays != _config.pays;
    _config = _config.copyWith(
      pays: pays,
      villeId: villeId,
      effacerVille: toutesVilles || (autrePays && villeId == null),
    );
    _mode = (villeId != null && !toutesVilles) ? ModeLieu.ville : ModeLieu.pays;
    _lieuManuel = true;
    erreurPosition = null;
    if (autrePays) {
      await _chargerPays(_config.pays);
    } else {
      notifyListeners();
    }
  }

  /// « Autour de moi » : relève la position (réponse rapide), classe les services
  /// par distance et charge automatiquement le pays où se trouve l'utilisateur.
  Future<void> choisirAutourDeMoi() async {
    _mode = ModeLieu.autourDeMoi;
    _lieuManuel = false;
    erreurPosition = null;
    chargementPosition = true;
    notifyListeners();

    PositionPrecise? pos;
    ErreurPosition? echec;
    final fournisseur = _config.fournisseurPosition;
    if (fournisseur != null) {
      await for (final r in fournisseur(precis: false)) {
        if (r.position != null) {
          pos = r.position;
          break;
        }
        echec ??= r.erreur;
      }
    }
    final repli = _config.position;
    pos ??= repli == null ? null : PositionPrecise(repli);

    _positionGps = pos;
    erreurPosition = pos == null ? (echec ?? ErreurPosition.indisponible) : null;
    chargementPosition = false;

    final m = manifeste;
    if (pos != null && m != null) {
      final p = m.paysDe(pos.coord);
      if (p != null && p.code != _config.pays) {
        _config = _config.copyWith(pays: p.code, effacerVille: true);
        await _chargerPays(p.code);
        return;
      }
    }
    notifyListeners();
  }

  /// Reprend les réglages de l'hôte (langue, textes, raccourcis) sans perdre l'état.
  void mettreAJourHote(AlAnsarConfig nouvelle) {
    final change = nouvelle.langue != _config.langue ||
        !mapEquals(nouvelle.textes, _config.textes) ||
        nouvelle.raccourcisHote.length != _config.raccourcisHote.length ||
        nouvelle.modeDemo != _config.modeDemo;
    if (!change) return;
    _config = _config.copyWith(
      langue: nouvelle.langue,
      textes: nouvelle.textes,
      raccourcisHote: nouvelle.raccourcisHote,
      modeDemo: nouvelle.modeDemo,
      definirModeDemo: true,
    );
    notifyListeners();
  }

  /// Fiches des types demandés, classées par distance en mode « autour de moi »
  /// (les services à distance suivent, puis ceux sans position connue).
  List<EntreeFiche> fiches(Set<String> types, {FiltreFiches filtre = const FiltreFiches(), double? rayonKm}) {
    final base = (annuaire?.fiches ?? const <Fiche>[])
        .where((f) => types.contains(f.type) && visible(f));
    final origine = positionEffective;
    if (_mode == ModeLieu.autourDeMoi && origine != null) {
      final proches = <EntreeFiche>[];
      final distants = <EntreeFiche>[];
      final sansPosition = <EntreeFiche>[];
      for (final f in base) {
        if (!filtre.accepte(f)) continue;
        final coord = f.gps ?? ville(f.villeId)?.gps;
        if (coord == null) {
          sansPosition.add(EntreeFiche(f, null));
          continue;
        }
        final d = distanceM(origine, coord);
        if (rayonKm == null || d <= rayonKm * 1000) {
          proches.add(EntreeFiche(f, d));
        } else if (f.zone.paysEntier || f.zone.international) {
          distants.add(EntreeFiche(f, null, aDistance: true));
        }
      }
      proches.sort((a, b) => a.distanceM!.compareTo(b.distanceM!));
      return <EntreeFiche>[...proches, ...distants, ...sansPosition];
    }
    final avecVille = FiltreFiches(
      villeId: _mode == ModeLieu.ville ? _config.villeId : null,
      niveauMin: filtre.niveauMin,
      aDistance: filtre.aDistance,
      langue: filtre.langue,
    );
    return base.where(avecVille.accepte).map((f) => EntreeFiche(f, null)).toList();
  }
}
