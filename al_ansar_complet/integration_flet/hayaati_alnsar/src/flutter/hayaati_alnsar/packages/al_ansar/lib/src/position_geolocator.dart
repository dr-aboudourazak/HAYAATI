import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:geolocator/geolocator.dart';

import 'config.dart';

/// Flux de positions basé sur le paquet geolocator (Android, iOS, Windows).
///
/// Cause probable des échecs sur téléphone avec un relevé unique en haute
/// précision : en intérieur, le GPS met souvent plus de 30 secondes à obtenir
/// un premier point. Ce flux répond donc en deux temps :
///  - precis = false : dernière position si elle date de moins de 10 minutes,
///    puis première position en précision moyenne (réseau, quelques secondes) ;
///  - precis = true : positions successives de précision croissante, jusqu'à
///    ce que l'appelant arrête l'écoute.
/// Chaque échec est renvoyé avec sa cause, pour que l'écran puisse l'expliquer.
Stream<ResultatPosition> fluxPositionGeolocator({required bool precis}) async* {
  try {
    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    if (permission == LocationPermission.deniedForever) {
      yield const ResultatPosition.echec(ErreurPosition.permissionRefuseeDefinitivement);
      return;
    }
    if (permission == LocationPermission.denied) {
      yield const ResultatPosition.echec(ErreurPosition.permissionRefusee);
      return;
    }
    if (!await Geolocator.isLocationServiceEnabled()) {
      yield const ResultatPosition.echec(ErreurPosition.serviceDesactive);
      return;
    }
  } on PermissionDefinitionsNotFoundException {
    // Cas des applications d'essai : AndroidManifest.xml sans ACCESS_FINE_LOCATION.
    yield const ResultatPosition.echec(ErreurPosition.permissionNonDeclaree);
    return;
  } catch (e) {
    debugPrint('Al Ansâr : permission de localisation impossible à vérifier ($e)');
    yield const ResultatPosition.echec(ErreurPosition.indisponible);
    return;
  }

  if (!precis) {
    try {
      final derniere = await Geolocator.getLastKnownPosition();
      if (derniere != null && DateTime.now().difference(derniere.timestamp).inMinutes < 10) {
        yield ResultatPosition.ok(_vers(derniere));
        return;
      }
    } catch (_) {
      // Plateforme sans dernière position connue : on continue avec le flux.
    }
  }

  var recu = false;
  try {
    final reglages = LocationSettings(
      accuracy: precis ? LocationAccuracy.best : LocationAccuracy.medium,
      distanceFilter: 0,
    );
    await for (final p in Geolocator.getPositionStream(locationSettings: reglages)
        .timeout(Duration(seconds: precis ? 60 : 25))) {
      recu = true;
      yield ResultatPosition.ok(_vers(p));
      if (!precis) return;
    }
  } on TimeoutException {
    if (!recu) yield const ResultatPosition.echec(ErreurPosition.delaiDepasse);
  } catch (e) {
    debugPrint('Al Ansâr : flux de position interrompu ($e)');
    if (!recu) yield const ResultatPosition.echec(ErreurPosition.indisponible);
  }
}

PositionPrecise _vers(Position p) =>
    PositionPrecise(Coord(p.latitude, p.longitude), precisionM: p.accuracy);
