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
import 'package:flutter/foundation.dart' show debugPrint;
import 'package:flutter/services.dart' show rootBundle;
import 'package:flet/flet.dart';
import 'package:alarm/alarm.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:path_provider/path_provider.dart';

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
  Future<String> _ensureAudioFileExtracted(String assetKey) async {
    final dir = await getApplicationSupportDirectory();
    final fileName = assetKey.split('/').last;
    final file = File('${dir.path}/$fileName');

    if (await file.exists() && await file.length() > 0) {
      return file.path;
    }

    final byteData = await rootBundle.load(assetKey);
    await file.writeAsBytes(
      byteData.buffer.asUint8List(
        byteData.offsetInBytes,
        byteData.lengthInBytes,
      ),
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
        final resolvedAudioPath = await _ensureAudioFileExtracted(
          args["assetAudioPath"] as String,
        );

        final settings = AlarmSettings(
          id: args["id"] as int,
          dateTime: DateTime.parse(args["dateTime"] as String),
          assetAudioPath: resolvedAudioPath,
          loopAudio: args["loopAudio"] as bool? ?? true,
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
