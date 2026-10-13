// hayaati_alarm.dart (src/)
//
// Implémentation du Service : reçoit les appels invoke_method() venant de
// Python et pilote le paquet Flutter 'alarm' (https://pub.dev/packages/alarm),
// activement maintenu, API vérifiée en date d'aujourd'hui sur sa page pub.dev.
//
// ── Journal des corrections (30/08/2026) ────────────────────────────
// v1.1 :
//  • fadeDuration et warningNotificationOnKill sont désormais lus dans
//    args et transmis à VolumeSettings / AlarmSettings, pour suivre
//    l'évolution du côté Python (hayaati_alarm.py v1.1).
//  • Le cas "isAlarmActive" a été retiré : il n'était de toute façon
//    jamais atteint avec succès côté Python, et son rôle (éviter les
//    doublons) est déjà couvert par cancel_all_prayer_alarms() avant
//    chaque reschedule_all().
//  • bypassDnd n'a jamais existé dans ce fichier ni dans l'API connue
//    du paquet alarm : rien à faire ici, juste ne pas l'ajouter côté
//    Python sans vérification préalable sur pub.dev.
//
// ── Journal des corrections (08/09/2026) ────────────────────────────
// v1.2 :
//  • Ajout de _ensureAudioFileExtracted(). Le paquet 'alarm' échouait
//    silencieusement à extraire lui-même l'asset audio quand celui-ci
//    vit dans un package tiers (hayaati_alarm) plutôt que dans l'app
//    principale : la clé d'asset qu'il résout en interne ne correspond
//    pas à la clé réelle dans flutter_assets. Confirmé en inspectant
//    l'APK décompressé : le fichier se trouve à
//    assets/flutter_assets/packages/hayaati_alarm/assets/sounds/adhan.mp3
//    On extrait donc l'asset nous-mêmes vers un fichier réel sur disque
//    avant d'appeler Alarm.set(), et on transmet ce chemin de fichier
//    plutôt que la clé d'asset brute.
//  • args["assetAudioPath"] envoyé par Python doit maintenant contenir
//    la clé d'asset complète avec sous-dossier, ex. :
//    "packages/hayaati_alarm/assets/sounds/adhan.mp3"
//
// ⚠️ À VÉRIFIER avant de lancer un build complet sur ta machine :
// 1. Que 'path_provider' figure bien dans pubspec.yaml de ce package
//    (hayaati_alarm/pubspec.yaml). Si absent : flutter pub add path_provider
// 2. Le nom exact du champ "warningNotificationOnKill" sur AlarmSettings,
//    et la signature de VolumeSettings.fade(...), peuvent varier d'une
//    version à l'autre du paquet 'alarm'. Lance d'abord :
//        cd hayaati_alarm/src/flutter/hayaati_alarm
//        flutter analyze
//    C'est net plus rapide qu'un build APK complet et ça suffit à repérer
//    un nom de champ qui aurait changé entre deux versions du paquet.
//
// ⚠️ Les noms exacts addInvokeMethodListener / removeInvokeMethodListener
// n'ont pas été modifiés : puisque l'app compile et s'installe déjà
// avec ce fichier, ces méthodes existent bien dans cette version de Flet.

// ⚠️ 09/09/2026 : import 'dart:io' retiré. `flutter analyze` signale
// (niveau info, pas une erreur) qu'il est redondant : package:flet/flet.dart
// réexporte déjà File, seule classe de dart:io utilisée dans ce fichier
// (_ensureAudioFileExtracted). Aucun changement de comportement.
import 'dart:typed_data';
import 'package:flutter/foundation.dart' show debugPrint;
import 'package:flutter/services.dart' show rootBundle;
import 'package:flet/flet.dart';
import 'package:alarm/alarm.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:path_provider/path_provider.dart';

// ---------------------------------------------------------------------------
// 10/10/2026 : « N sonneries ».
//
// Le paquet 'alarm' sait seulement jouer un son UNE fois ou EN BOUCLE SANS FIN. Une alarme non
// bouclée (loopAudio: false) s'arrête d'elle-même quand son audio se termine : le paquet coupe
// alors le son, la vibration et la notification, comme le bouton « Arrêter ». Pour obtenir « 3
// sonneries puis silence », même si l'application est tuée, on joue donc UN fichier qui contient
// le son répété N fois : tout est géré par le service natif, sans minuteur Dart (qui ne survivrait
// pas à l'arrêt de l'application).
//
// Pour que les raccords soient propres, l'étiquette ID3v2 du début n'est conservée qu'une seule
// fois et l'étiquette ID3v1 de fin n'est pas recopiée. Testé : adhan.mp3 x3 et adhan_fajr.mp3 x3
// se décodent en entier, sans erreur, avec exactement 3 fois la durée d'origine.
int _debutAudioMp3(Uint8List b) {
  if (b.length > 10 && b[0] == 0x49 && b[1] == 0x44 && b[2] == 0x33) {
    final int taille = ((b[6] & 0x7f) << 21) |
        ((b[7] & 0x7f) << 14) |
        ((b[8] & 0x7f) << 7) |
        (b[9] & 0x7f);
    final bool pied = (b[5] & 0x10) != 0;
    final int fin = 10 + taille + (pied ? 10 : 0);
    if (fin < b.length) {
      return fin;
    }
  }
  return 0;
}

int _finAudioMp3(Uint8List b) {
  if (b.length > 128 &&
      b[b.length - 128] == 0x54 &&
      b[b.length - 127] == 0x41 &&
      b[b.length - 126] == 0x47) {
    return b.length - 128;
  }
  return b.length;
}

Uint8List _repeterMp3(Uint8List original, int fois) {
  if (fois <= 1) {
    return original;
  }
  final int debut = _debutAudioMp3(original);
  final int fin = _finAudioMp3(original);
  final int longueur = fin - debut;
  final Uint8List sortie = Uint8List(debut + longueur * fois);
  sortie.setRange(0, debut, original, 0);
  for (int i = 0; i < fois; i++) {
    sortie.setRange(
      debut + i * longueur,
      debut + (i + 1) * longueur,
      original,
      debut,
    );
  }
  return sortie;
}

int _borner(int valeur, int minimum, int maximum) {
  if (valeur < minimum) {
    return minimum;
  }
  if (valeur > maximum) {
    return maximum;
  }
  return valeur;
}

class HayaatiAlarmService extends FletService {
  HayaatiAlarmService({required super.control});

  @override
  void init() {
    super.init();
    // ⚠️ DIAGNOSTIC 02/09/2026 : trace non filtrée, pour confirmer que le
    // service est bien créé une seule fois et n'est pas détruit puis
    // recréé entre l'enregistrement du listener et l'appel de Python.
    debugPrint(
      '[HayaatiAlarm][DIAG] init() — instance=${identityHashCode(this)} '
      'control.id=${control.id}',
    );
    Alarm.init().then((_) {
      debugPrint('[HayaatiAlarm][DIAG] Alarm.init() terminé avec succès');
    }).catchError((err, stack) {
      debugPrint('[HayaatiAlarm][DIAG] Alarm.init() a échoué : $err\n$stack');
    });
    control.addInvokeMethodListener(_onInvokeMethod);
    debugPrint(
      '[HayaatiAlarm][DIAG] addInvokeMethodListener enregistré pour '
      'instance=${identityHashCode(this)}',
    );
  }

  @override
  void dispose() {
    // ⚠️ DIAGNOSTIC : si cette ligne apparaît peu après init(), le service
    // est détruit avant que Python n'ait eu le temps d'appeler quoi que
    // ce soit, ce qui expliquerait un timeout systématique.
    debugPrint(
      '[HayaatiAlarm][DIAG] dispose() — instance=${identityHashCode(this)}',
    );
    control.removeInvokeMethodListener(_onInvokeMethod);
    super.dispose();
  }

  /// Copie un asset embarqué dans le bundle Flutter vers un fichier réel
  /// sur disque, une seule fois, puis renvoie le chemin absolu.
  ///
  /// [assetKey] est la clé complète telle qu'elle existe dans
  /// flutter_assets, par exemple :
  /// "packages/hayaati_alarm/assets/sounds/adhan.mp3"
  ///
  /// Le fichier est mis en cache dans le dossier de support de l'app.
  /// Au démarrage suivant, s'il existe déjà et n'est pas vide, on le
  /// réutilise directement sans relire le bundle.
  Future<String> _ensureAudioFileExtracted(
    String assetKey, {
    int repeat = 1,
  }) async {
    final dir = await getApplicationSupportDirectory();
    final fileName = assetKey.split('/').last;
    // 10/10/2026 : repeat > 1 => on écrit un fichier qui contient le son répété `repeat` fois
    // (adhan_x3_v1.mp3 pour 3). Le nom change avec le nombre de répétitions, donc un ancien fichier
    // d'un seul passage n'est jamais réutilisé par erreur.
    String targetName = fileName;
    if (repeat > 1) {
      final int point = fileName.lastIndexOf('.');
      final String base = point > 0 ? fileName.substring(0, point) : fileName;
      final String ext = point > 0 ? fileName.substring(point) : '';
      targetName = '${base}_x${repeat}_v1$ext';
    }
    final file = File('${dir.path}/$targetName');

    if (await file.exists() && await file.length() > 0) {
      return file.path;
    }

    final byteData = await rootBundle.load(assetKey);
    Uint8List bytes = byteData.buffer.asUint8List(
      byteData.offsetInBytes,
      byteData.lengthInBytes,
    );
    if (repeat > 1) {
      bytes = _repeterMp3(bytes, repeat);
    }
    await file.writeAsBytes(
      bytes,
      flush: true,
    );
    debugPrint(
      '[HayaatiAlarm][DIAG] Audio extrait vers ${file.path} '
      '(${await file.length()} octets)',
    );
    return file.path;
  }

  Future<dynamic> _onInvokeMethod(String name, dynamic args) async {
    // ⚠️ DIAGNOSTIC : première ligne, inconditionnelle, avant tout switch
    // ou try. Si cette trace n'apparaît jamais dans le logcat pendant
    // qu'un timeout se produit côté Python, la fonction n'est simplement
    // jamais appelée : le problème est dans l'enregistrement du listener,
    // pas dans la logique métier ci-dessous.
    debugPrint(
      '[HayaatiAlarm][DIAG] _onInvokeMethod APPELÉ — name=$name '
      'instance=${identityHashCode(this)}',
    );
    try {
      switch (name) {
      case "setAlarm":
        final double volume = (args["volume"] as num?)?.toDouble() ?? 1.0;
        final num? fadeDurationSeconds = args["fadeDuration"] as num?;

        final volumeSettings = fadeDurationSeconds != null
            ? VolumeSettings.fade(
                volume: volume,
                fadeDuration: Duration(
                  milliseconds: (fadeDurationSeconds.toDouble() * 1000).round(),
                ),
              )
            : VolumeSettings.fixed(volume: volume);

        // ⚠️ CORRECTION 08/09/2026 : args["assetAudioPath"] contient la
        // clé d'asset brute envoyée par Python, pas un chemin de fichier
        // réel. On extrait le fichier nous-mêmes avant de le transmettre
        // à AlarmSettings, plutôt que de laisser le paquet 'alarm' tenter
        // (et rater) cette extraction de son côté.
        // 10/10/2026 : nombre de sonneries (1 = une seule). Au-delà de 1, le son est répété dans
        // le fichier et loopAudio est forcé à false : l'alarme s'arrête seule à la fin.
        final int repeatCount = _borner(
          (args["repeatCount"] as num?)?.toInt() ?? 1,
          1,
          10,
        );
        final resolvedAudioPath = await _ensureAudioFileExtracted(
          args["assetAudioPath"] as String,
          repeat: repeatCount,
        );

        final settings = AlarmSettings(
          id: args["id"] as int,
          dateTime: DateTime.parse(args["dateTime"] as String),
          assetAudioPath: resolvedAudioPath,
          loopAudio: repeatCount > 1 ? false : (args["loopAudio"] as bool? ?? true),
          vibrate: args["vibrate"] as bool? ?? true,
          androidFullScreenIntent:
              args["androidFullScreenIntent"] as bool? ?? true,
          volumeSettings: volumeSettings,
          warningNotificationOnKill:
              args["warningNotificationOnKill"] as bool? ?? false,
          notificationSettings: NotificationSettings(
            title: args["title"] as String? ?? "HAYAATI",
            body: args["body"] as String? ?? "",
            stopButton: args["stopButton"] as String? ?? "Arrêter",
          ),
        );
        await Alarm.set(alarmSettings: settings);
        return true;

      case "cancelAlarm":
        await Alarm.stop(args["id"] as int);
        return true;

      case "stopAll":
        await Alarm.stopAll();
        return true;

      case "requestPermissions":
        // POST_NOTIFICATIONS (Android 13+). Vérifié via permission_handler,
        // package déjà associé au paquet 'alarm' dans la documentation
        // de la communauté pour ce cas d'usage précis.
        final notifStatus = await Permission.notification.status;
        if (notifStatus.isDenied) {
          await Permission.notification.request();
        }
        return true;

      case "requestExactAlarmPermission":
        // SCHEDULE_EXACT_ALARM (Android 12+).
        final exactStatus = await Permission.scheduleExactAlarm.status;
        if (exactStatus.isDenied) {
          await Permission.scheduleExactAlarm.request();
        }
        return true;

      case "requestFullScreenIntentPermission":
        // ⚠️ Non implémenté : permission_handler ne couvre pas
        // USE_FULL_SCREEN_INTENT (demande fermée "not planned" par les
        // mainteneurs). Une vraie implémentation demanderait du code
        // natif Android (Kotlin) appelant
        // Settings.ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT, non écrit
        // pour l'instant. Les apps avec fonction d'alarme reçoivent
        // normalement cette permission par défaut à l'installation.
        // ignore: avoid_print
        print(
          '[HayaatiAlarm] requestFullScreenIntentPermission : non implémenté '
          '(voir commentaire dans hayaati_alarm.py). Vérifier manuellement '
          'sur le téléphone : Réglages > Apps > Hayaati > Autorisations spéciales.',
        );
        return true;

      default:
        return null;
      }
    } catch (err, stack) {
      // ⚠️ DIAGNOSTIC : sans ce catch, une exception ici (par exemple dans
      // Alarm.set() ou permission_handler) disparaissait silencieusement
      // côté Dart, sans jamais renvoyer d'erreur à Python — d'où le
      // timeout de 10s côté Python plutôt qu'un message d'échec net.
      debugPrint('[HayaatiAlarm][DIAG] Exception dans $name : $err\n$stack');
      rethrow;
    }
  }
}
