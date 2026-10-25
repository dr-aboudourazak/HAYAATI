import 'dart:convert';

import 'package:al_ansar/al_ansar.dart';
import 'package:flet/flet.dart';
import 'package:flutter/material.dart';

/// Pont entre le contrôle Python HayaatiAlAnsar et le module Flutter al_ansar.
class HayaatiAlAnsarControl extends StatefulWidget {
  const HayaatiAlAnsarControl({super.key, required this.control});

  final Control control;

  @override
  State<HayaatiAlAnsarControl> createState() => _HayaatiAlAnsarControlState();
}

class _HayaatiAlAnsarControlState extends State<HayaatiAlAnsarControl> {
  final GlobalKey<NavigatorState> _cleNavigateur = GlobalKey<NavigatorState>();

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
        throw Exception("Méthode inconnue pour HayaatiAlAnsar : $nom");
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

  static List<RaccourciHote> _lireRaccourcis(String? json) {
    if (json == null || json.isEmpty) return const <RaccourciHote>[];
    try {
      final l = jsonDecode(json) as List;
      return l
          .map((e) => RaccourciHote(
                cle: (e as Map)["cle"].toString(),
                titre: e["titre"].toString(),
                icone: (e["icone"] ?? "apps").toString(),
              ))
          .toList();
    } catch (_) {
      return const <RaccourciHote>[];
    }
  }

  @override
  Widget build(BuildContext context) {
    final c = widget.control;
    final lat = c.get<double>("latitude");
    final lon = c.get<double>("longitude");
    final config = AlAnsarConfig(
      baseUrl: c.get<String>("base_url") ?? "",
      assetPrefix: c.get<String>("asset_prefix") ?? "packages/hayaati_alnsar/assets/al_ansar/",
      langue: c.get<String>("langue") ?? "fr",
      pays: c.get<String>("pays") ?? "TG",
      villeId: c.get<String>("ville_id"),
      position: (lat != null && lon != null) ? Coord(lat, lon) : null,
      modeDemo: c.get<bool>("mode_demo") ?? false,
      integre: c.get<bool>("integre") ?? true,
      textes: _lireTextes(c.get<String>("textes_json")),
      raccourcisHote: _lireRaccourcis(c.get<String>("raccourcis_json")),
      fournisseurPosition: fluxPositionGeolocator,
      surOuvrirHote: (cle) => c.triggerEvent("ouvrir_hote", cle),
      surProfondeur: (n) => c.triggerEvent("profondeur", n),
    );
    return LayoutControl(
      control: c,
      child: AlAnsarModule(config: config, navigatorKey: _cleNavigateur),
    );
  }
}
