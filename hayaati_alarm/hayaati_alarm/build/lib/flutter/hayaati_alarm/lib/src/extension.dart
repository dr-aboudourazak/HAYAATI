// extension.dart
//
// Enregistre HayaatiAlarmService comme Service Flet, suivant exactement le
// patron officiel documenté par l'équipe Flet (voir flet.dev/blog/introducing-
// flet-1-0-alpha, exemple InterstitialAdService) : createService(Control)
// retourne un FletService, pas un Widget — cette alarme n'a pas d'interface
// visuelle propre, uniquement des méthodes invocables depuis Python.

import 'package:flet/flet.dart';
import 'hayaati_alarm.dart';

class Extension extends FletExtension {
  @override
  FletService? createService(Control control) {
    switch (control.type) {
      case "HayaatiAlarm":
        return HayaatiAlarmService(control: control);
      default:
        return null;
    }
  }
}
