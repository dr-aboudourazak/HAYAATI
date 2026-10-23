import 'package:flutter/material.dart';

import '../config.dart';
import '../controleur.dart';
import '../depot.dart';
import '../theme/theme_hayaati.dart';
import 'ecrans.dart';

/// Compte les écrans empilés dans le Navigator interne du module, pour que
/// l'hôte sache s'il doit laisser le bouton « retour » au module.
class _ObservateurProfondeur extends NavigatorObserver {
  _ObservateurProfondeur(this.surChangement);

  final void Function(int profondeur)? surChangement;
  int _n = 0;

  void _notifier() => surChangement?.call(_n);

  @override
  void didPush(Route<dynamic> route, Route<dynamic>? previousRoute) {
    if (previousRoute == null) return;
    _n++;
    _notifier();
  }

  @override
  void didPop(Route<dynamic> route, Route<dynamic>? previousRoute) {
    if (_n > 0) _n--;
    _notifier();
  }

  @override
  void didRemove(Route<dynamic> route, Route<dynamic>? previousRoute) {
    if (_n > 0) _n--;
    _notifier();
  }
}

/// Point d'entrée : un Navigator interne, indépendant de l'application hôte.
///
/// Bouton « retour » d'Android dans HAYAATI : l'hôte intercepte le retour système
/// (page.views[0].can_pop = False). Il connaît la profondeur du module grâce à
/// [AlAnsarConfig.surProfondeur] et, si elle est supérieure à 0, demande au module
/// de revenir d'un écran avec [navigatorKey] (`navigatorKey.currentState?.maybePop()`).
class AlAnsarModule extends StatefulWidget {
  const AlAnsarModule({super.key, required this.config, this.depot, this.navigatorKey});

  final AlAnsarConfig config;
  final DepotAnnuaire? depot;
  final GlobalKey<NavigatorState>? navigatorKey;

  @override
  State<AlAnsarModule> createState() => _AlAnsarModuleState();
}

class _AlAnsarModuleState extends State<AlAnsarModule> {
  late final ControleurAlAnsar _c;
  late final _ObservateurProfondeur _observateur;
  late final Widget _navigateur;

  @override
  void initState() {
    super.initState();
    _c = ControleurAlAnsar(config: widget.config, depot: widget.depot);
    _c.init();
    _observateur = _ObservateurProfondeur(widget.config.surProfondeur);
    _navigateur = Navigator(
      key: widget.navigatorKey,
      observers: <NavigatorObserver>[_observateur],
      onGenerateRoute: (_) => MaterialPageRoute<void>(
        builder: (_) => EcranAccueil(c: _c),
      ),
    );
  }

  @override
  void didUpdateWidget(covariant AlAnsarModule oldWidget) {
    super.didUpdateWidget(oldWidget);
    final nouvelle = widget.config;
    WidgetsBinding.instance.addPostFrameCallback((_) => _c.mettreAJourHote(nouvelle));
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: _c,
      builder: (context, navigateur) => Theme(
        data: themeHayaati(arabe: _c.t.rtl),
        child: Directionality(
          textDirection: _c.t.rtl ? TextDirection.rtl : TextDirection.ltr,
          child: navigateur!,
        ),
      ),
      child: _navigateur,
    );
  }
}
