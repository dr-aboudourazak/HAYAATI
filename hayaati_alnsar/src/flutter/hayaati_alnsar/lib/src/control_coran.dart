import 'dart:convert';

import 'package:flet/flet.dart';
import 'package:flutter/material.dart';
import 'package:hayaati_coran/hayaati_coran.dart';

/// Pont entre le contrôle Python HayaatiCoran et le module Flutter hayaati_coran.
///
/// Python ne transmet que la langue, les textes déjà traduits et l'état de lecture enregistré (coran_lecture.json) ;
/// le texte du Coran (2,6 Mo) est embarqué dans le paquet Flutter et ne transite jamais par Flet. Le module signale
/// chaque changement d'état de lecture (événement « sauver_etat ») et la profondeur de sa navigation interne
/// (événement « profondeur », pour le bouton « retour » d'Android).
class HayaatiCoranControl extends StatefulWidget {
  const HayaatiCoranControl({super.key, required this.control});

  final Control control;

  @override
  State<HayaatiCoranControl> createState() => _HayaatiCoranControlState();
}

class _HayaatiCoranControlState extends State<HayaatiCoranControl> {
  final GlobalKey<NavigatorState> _cleNavigateur = GlobalKey<NavigatorState>();

  // Décodés seulement si le contenu change : le module compare les textes par identité pour savoir s'il doit se mettre à jour.
  String? _clefTextes;
  TextesCoran _textes = const TextesCoran();
  String? _etatBrut;
  Object? _etat;

  @override
  void initState() {
    super.initState();
    widget.control.addInvokeMethodListener(_invoquer);
  }

  @override
  void dispose() {
    widget.control.removeInvokeMethodListener(_invoquer);
    super.dispose();
  }

  /// Méthodes appelables depuis Python.
  Future<dynamic> _invoquer(String nom, dynamic args) async {
    switch (nom) {
      case "retour":
        // Revient d'un écran dans la navigation interne ; renvoie vrai si un écran a été fermé.
        return await _cleNavigateur.currentState?.maybePop() ?? false;
      default:
        throw Exception("Méthode inconnue pour HayaatiCoran : $nom");
    }
  }

  static Map<String, String> _lireTextes(String? json) {
    if (json == null || json.isEmpty) return const <String, String>{};
    try {
      final m = jsonDecode(json) as Map;
      return m.map((k, v) => MapEntry(k.toString(), v.toString()));
    } catch (_) {
      return const <String, String>{};
    }
  }

  @override
  Widget build(BuildContext context) {
    final c = widget.control;
    final langue = (c.get<String>("langue") ?? "fr").toLowerCase();
    final brutTextes = c.get<String>("textes_json");
    final clef = "$langue|${brutTextes ?? ''}";
    if (clef != _clefTextes) {
      _clefTextes = clef;
      _textes = TextesCoran(_lireTextes(brutTextes), langue == "ar");
    }
    final brutEtat = c.get<String>("etat_json");
    if (brutEtat != _etatBrut) {
      _etatBrut = brutEtat;
      try {
        _etat = (brutEtat == null || brutEtat.isEmpty) ? null : jsonDecode(brutEtat);
      } catch (_) {
        _etat = null; // illisible : le module part des valeurs par défaut
      }
    }
    final config = ConfigCoran(
      textes: _textes,
      etatBrut: _etat,
      surSauverEtat: (etat) => c.triggerEvent("sauver_etat", jsonEncode(etat)),
      surProfondeur: (n) => c.triggerEvent("profondeur", n),
    );
    return LayoutControl(
      control: c,
      child: ModuleCoran(config: config, navigatorKey: _cleNavigateur),
    );
  }
}
