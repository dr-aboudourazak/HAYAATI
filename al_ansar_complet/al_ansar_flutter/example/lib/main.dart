import 'dart:convert';

import 'package:al_ansar/al_ansar.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;

/// Lancement :
///   flutter run -d <identifiant>                                   (GPS réel au toucher de « Autour de moi »)
///   flutter run -d <identifiant> --dart-define=POS=10.8627,0.2076  (position simulée à Dapaong)
///   flutter run -d <identifiant> --dart-define=LANGUE=en
///   flutter run -d <identifiant> --dart-define=ECRAN=madrassa      (ouvre directement le hub Madrassa)
void main() => runApp(const ExempleApp());

class ExempleApp extends StatelessWidget {
  const ExempleApp({super.key});

  static const String _pos = String.fromEnvironment('POS');
  static const String _langue = String.fromEnvironment('LANGUE', defaultValue: 'fr');
  static const String _ecran = String.fromEnvironment('ECRAN');

  Coord? _positionSimulee() {
    final p = _pos.split(',');
    if (p.length != 2) return null;
    final lat = double.tryParse(p[0]);
    final lon = double.tryParse(p[1]);
    if (lat == null || lon == null) return null;
    return Coord(lat, lon);
  }

  /// Contenu de Madrassa : dans HAYAATI il vient des fichiers de langue ; ici, une copie française de démonstration.
  /// La progression n'est pas conservée par l'exemple : elle est seulement affichée dans la console.
  Future<MadrassaHote?> _madrassa() async {
    try {
      final texte = await rootBundle.loadString('assets/al_ansar/madrassa_demo.json');
      return MadrassaHote(
        contenu: Map<String, dynamic>.from(jsonDecode(texte) as Map),
        surSauver: (module, donnees) => debugPrint('Progression $module : ${jsonEncode(donnees)}'),
      );
    } catch (_) {
      return null;
    }
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'HAYAATI · Al Ansâr',
      debugShowCheckedModeBanner: false,
      theme: themeHayaati(arabe: _langue == 'ar'),
      home: FutureBuilder<MadrassaHote?>(
        future: _madrassa(),
        builder: (context, instantane) {
          if (instantane.connectionState != ConnectionState.done) {
            return const Scaffold(body: Center(child: CircularProgressIndicator()));
          }
          return AlAnsarModule(
            config: AlAnsarConfig(
              // Adresse injoignable : repli sur les fichiers embarqués.
              baseUrl: 'https://exemple.invalid/al-ansar/',
              langue: _langue,
              pays: 'TG',
              villeId: 'tg-dapaong',
              position: _positionSimulee(),
              // Relevé GPS réel : dans HAYAATI, c'est le même flux (paquet geolocator).
              fournisseurPosition: fluxPositionGeolocator,
              // modeDemo non renseigné : les fichiers d'exemple portent « demonstration: true ».
              madrassa: instantane.data,
              ecranInitial: _ecran.isEmpty ? null : _ecran,
            ),
          );
        },
      ),
    );
  }
}
