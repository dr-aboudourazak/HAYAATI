import 'dart:convert';
import 'dart:io';

/// Résultats de référence figés par outils/generer_golden_coran.py à partir du moteur Python.
/// `flutter test` s'exécute depuis la racine du paquet : les chemins sont relatifs à celle-ci.
Map<String, dynamic> golden() =>
    Map<String, dynamic>.from(jsonDecode(File('test/golden/golden_coran.json').readAsStringSync()) as Map);

/// Lit les fichiers du Coran sur le disque, comme rootBundle le fait dans l'application.
Future<String> lireDisque(String nom) => File('assets/coran/$nom').readAsString();
