import 'package:flutter/material.dart';

import '../commun/core/config.dart';
import '../fonctionnalites/annuaire/core/controleur.dart';
import '../fonctionnalites/annuaire/core/depot.dart';
import '../commun/gui/theme/theme_hayaati.dart';
import '../fonctionnalites/madrassa/gui/ecrans_madrassa.dart';
import '../fonctionnalites/annuaire/gui/ecrans.dart';
import '../fonctionnalites/annuaire/core/modeles.dart';
import '../fonctionnalites/hadj_omra/gui/ecran_hadj_omra.dart' show EcranForfait;

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

  /// Clé du Navigator interne : celle de l'hôte si elle est fournie, sinon la nôtre (pour ouvrir une publication).
  late final GlobalKey<NavigatorState> _cle = widget.navigatorKey ?? GlobalKey<NavigatorState>();

  /// Ouvre la publication d'un lien partagé dès que l'annuaire est chargé (20 secondes d'attente au plus). Une
  /// publication non publiée n'est ouverte que si le mode démonstration est actif.
  Future<void> _ouvrirFichePubliee(String id) async {
    final limite = DateTime.now().add(const Duration(seconds: 20));
    Fiche? fiche;
    Forfait? forfait;
    while (mounted && DateTime.now().isBefore(limite)) {
      final a = _c.annuaire;
      if (a != null) {
        fiche = a.fiches.where((f) => f.id == id && _c.visible(f)).firstOrNull;
        if (fiche == null) {
          // Un forfait Hadj et Omra n'est ouvert que si l'agence qui le propose est visible.
          final candidat = a.forfaits.where((f) => f.id == id).firstOrNull;
          if (candidat != null && a.fiches.any((f) => f.id == candidat.ficheId && _c.visible(f))) forfait = candidat;
        }
        break;
      }
      await Future<void>.delayed(const Duration(milliseconds: 150));
    }
    final nav = _cle.currentState;
    if (!mounted || nav == null) return;
    final trouve = forfait;
    if (fiche != null) {
      nav.push(routeFiche(_c, fiche));
    } else if (trouve != null) {
      nav.push(MaterialPageRoute<void>(builder: (_) => EcranForfait(c: _c, forfait: trouve)));
    }
  }

  @override
  void initState() {
    super.initState();
    _c = ControleurAlAnsar(config: widget.config, depot: widget.depot);
    _c.init();
    final demandee = widget.config.ficheInitiale;
    if (demandee != null) _ouvrirFichePubliee(demandee);
    _observateur = _ObservateurProfondeur(widget.config.surProfondeur);
    _navigateur = Navigator(
      key: _cle,
      observers: <NavigatorObserver>[_observateur],
      onGenerateRoute: (_) => MaterialPageRoute<void>(
        builder: (_) => (widget.config.ecranInitial == 'madrassa' && _c.madrassa != null)
            ? EcranMadrassaHub(ac: _c)
            : EcranAccueil(c: _c),
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
        data: themeHayaati(arabe: _c.t.rtl, apparence: widget.config.apparence),
        child: Directionality(
          textDirection: _c.t.rtl ? TextDirection.rtl : TextDirection.ltr,
          child: navigateur!,
        ),
      ),
      child: _navigateur,
    );
  }
}
