// Enregistre le contrôle visuel HayaatiAlAnsar (patron officiel Flet :
// createWidget(Key?, Control) retourne un Widget pour un contrôle visuel,
// à la différence de hayaati_alarm qui est un Service sans interface).

import 'package:flet/flet.dart';
import 'package:flutter/widgets.dart';

import 'control.dart';

class Extension extends FletExtension {
  @override
  Widget? createWidget(Key? key, Control control) {
    switch (control.type) {
      case "HayaatiAlAnsar":
        return HayaatiAlAnsarControl(key: key, control: control);
      default:
        return null;
    }
  }
}
