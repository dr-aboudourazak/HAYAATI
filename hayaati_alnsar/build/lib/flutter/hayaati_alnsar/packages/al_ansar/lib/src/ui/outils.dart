import '../config.dart';
import '../i18n.dart';
import 'package:flutter/foundation.dart';
import 'package:url_launcher/url_launcher.dart';

/// Ouvre WhatsApp avec un message pré-rempli. Renvoie faux si impossible.
Future<bool> ouvrirWhatsApp(String numeroE164, String message) async {
  final numero = numeroE164.replaceAll('+', '');
  final uri = Uri.parse('https://wa.me/$numero?text=${Uri.encodeComponent(message)}');
  try {
    return await launchUrl(uri, mode: LaunchMode.externalApplication);
  } catch (e) {
    debugPrint('Al Ansâr : WhatsApp indisponible ($e)');
    return false;
  }
}

/// Ouvre l'application de cartes (même hors ligne si OsmAnd ou Maps.me est installée).
Future<bool> ouvrirItineraire(double lat, double lon, String nom) async {
  final uri = Uri.parse('geo:$lat,$lon?q=$lat,$lon(${Uri.encodeComponent(nom)})');
  try {
    return await launchUrl(uri, mode: LaunchMode.externalApplication);
  } catch (e) {
    debugPrint('Al Ansâr : application de cartes indisponible ($e)');
    return false;
  }
}

String formaterMontant(double m) =>
    m == m.roundToDouble() ? m.toInt().toString() : m.toStringAsFixed(2);

/// Explique pourquoi la position n'a pas pu être obtenue.
String messageErreurPosition(Textes t, ErreurPosition erreur) {
  switch (erreur) {
    case ErreurPosition.permissionNonDeclaree:
      return t('pos_manifeste');
    case ErreurPosition.permissionRefusee:
      return t('pos_permission');
    case ErreurPosition.permissionRefuseeDefinitivement:
      return t('pos_permission_def');
    case ErreurPosition.serviceDesactive:
      return t('pos_service');
    case ErreurPosition.delaiDepasse:
      return t('pos_delai');
    case ErreurPosition.indisponible:
      return t('position_echec');
  }
}
