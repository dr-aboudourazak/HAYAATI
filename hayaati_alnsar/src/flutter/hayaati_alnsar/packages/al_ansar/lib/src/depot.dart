import 'dart:convert';
import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';

import 'config.dart';
import 'modeles.dart';

class FichierRef {
  const FichierRef({
    required this.fichier,
    required this.version,
    required this.sha256,
  });

  final String fichier;
  final int version;
  final String sha256;

  factory FichierRef.fromJson(Json j) => FichierRef(
        fichier: j['fichier'] as String,
        version: (j['version_donnees'] as num).toInt(),
        sha256: (j['sha256'] as String?) ?? '',
      );
}

class PaysRef {
  const PaysRef({
    required this.code,
    required this.nom,
    this.bbox,
    this.annuaire,
    this.mosquees,
  });

  final String code;
  final Map<String, String> nom;

  /// [latMin, lonMin, latMax, lonMax], rectangle approximatif du pays.
  final List<double>? bbox;
  final FichierRef? annuaire;
  final FichierRef? mosquees;

  bool contient(Coord c) {
    final b = bbox;
    if (b == null || b.length != 4) return false;
    return c.lat >= b[0] && c.lat <= b[2] && c.lon >= b[1] && c.lon <= b[3];
  }

  factory PaysRef.fromJson(Json j) {
    final bb = j['bbox'];
    return PaysRef(
      code: j['code'] as String,
      nom: (j['nom'] is Map)
          ? (j['nom'] as Map).map((k, v) => MapEntry(k.toString(), v.toString()))
          : const <String, String>{},
      bbox: bb is List ? bb.map((e) => (e as num).toDouble()).toList() : null,
      annuaire: j['annuaire'] is Map ? FichierRef.fromJson(j['annuaire'] as Json) : null,
      mosquees: j['mosquees'] is Map ? FichierRef.fromJson(j['mosquees'] as Json) : null,
    );
  }
}

class Manifeste {
  const Manifeste(this.pays);

  final List<PaysRef> pays;

  factory Manifeste.fromJson(Json j) {
    final l = (j['pays'] as List?) ?? const <dynamic>[];
    return Manifeste(l.map((e) => PaysRef.fromJson(e as Json)).toList());
  }

  PaysRef? parCode(String code) {
    for (final p in pays) {
      if (p.code == code) return p;
    }
    return null;
  }

  PaysRef? paysDe(Coord c) {
    for (final p in pays) {
      if (p.contient(c)) return p;
    }
    return null;
  }
}

/// Accès aux données : réseau (seulement si la version a augmenté), puis cache
/// local, puis fichiers embarqués (démonstration). Une seule version d'un pays
/// est gardée en mémoire par le contrôleur.
///
/// Limite connue : dart:io et path_provider ciblent Android et Windows, pas le web.
class DepotAnnuaire {
  DepotAnnuaire({
    required this.baseUrl,
    required this.assetPrefix,
    http.Client? client,
  }) : _client = client ?? http.Client();

  final String baseUrl;
  final String assetPrefix;
  final http.Client _client;

  Future<Manifeste?> manifeste() async {
    try {
      final r = await _client
          .get(Uri.parse('${baseUrl}manifest.json'))
          .timeout(const Duration(seconds: 6));
      if (r.statusCode != 200) return null;
      return Manifeste.fromJson(jsonDecode(utf8.decode(r.bodyBytes)) as Json);
    } catch (e) {
      debugPrint('Al Ansâr : manifeste indisponible ($e)');
      return null;
    }
  }

  /// [role] vaut « annuaire » ou « mosquees ».
  Future<Annuaire?> charger(String pays, String role, {Manifeste? manifeste}) async {
    final nom = '${role}_$pays.json';
    final local = await _lireCache(nom);
    final ref = role == 'mosquees'
        ? manifeste?.parCode(pays)?.mosquees
        : manifeste?.parCode(pays)?.annuaire;

    if (ref != null && (local == null || local.version < ref.version)) {
      final frais = await _telecharger(nom, ref);
      if (frais != null) return frais;
    }
    if (local != null) return local;
    return _lireAsset(nom);
  }

  Future<Annuaire?> _telecharger(String nom, FichierRef ref) async {
    try {
      final r = await _client
          .get(Uri.parse('$baseUrl${ref.fichier}'))
          .timeout(const Duration(seconds: 15));
      if (r.statusCode != 200) return null;
      final octets = r.bodyBytes;
      final attendu = ref.sha256.toLowerCase();
      if (RegExp(r'^[0-9a-f]{64}$').hasMatch(attendu)) {
        if (sha256.convert(octets).toString() != attendu) {
          debugPrint('Al Ansâr : empreinte invalide pour ${ref.fichier}, fichier rejeté');
          return null;
        }
      } else {
        debugPrint('Al Ansâr : empreinte non renseignée, vérification ignorée');
      }
      final annuaire = Annuaire.fromJson(jsonDecode(utf8.decode(octets)) as Json);
      await _ecrireCache(nom, octets);
      return annuaire;
    } catch (e) {
      debugPrint('Al Ansâr : téléchargement impossible ($e)');
      return null;
    }
  }

  Future<File> _fichierCache(String nom) async {
    final base = await getApplicationDocumentsDirectory();
    final dossier = Directory('${base.path}/al_ansar');
    if (!await dossier.exists()) await dossier.create(recursive: true);
    return File('${dossier.path}/$nom');
  }

  Future<Annuaire?> _lireCache(String nom) async {
    try {
      final f = await _fichierCache(nom);
      if (!await f.exists()) return null;
      return Annuaire.fromJson(jsonDecode(utf8.decode(await f.readAsBytes())) as Json);
    } catch (e) {
      debugPrint('Al Ansâr : cache illisible ($e)');
      return null;
    }
  }

  Future<void> _ecrireCache(String nom, List<int> octets) async {
    try {
      await (await _fichierCache(nom)).writeAsBytes(octets, flush: true);
    } catch (e) {
      debugPrint('Al Ansâr : écriture du cache impossible ($e)');
    }
  }

  Future<Annuaire?> _lireAsset(String nom) async {
    try {
      final texte = await rootBundle.loadString('$assetPrefix$nom');
      return Annuaire.fromJson(jsonDecode(texte) as Json);
    } catch (e) {
      return null;
    }
  }
}
