import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:hayaati_ui/hayaati_ui.dart';

import '../controleur.dart';
import '../etat_lecture.dart';
import '../moteur_coran.dart';
import '../textes.dart';
import 'ecran_liste.dart';

/// Configuration reçue de l'hôte (Flet aujourd'hui, une application Flutter complète demain).
class ConfigCoran {
  const ConfigCoran({
    this.textes = const TextesCoran(),
    this.etatBrut,
    this.surSauverEtat,
    this.surProfondeur,
  });

  /// Textes traduits et sens d'écriture de l'interface.
  final TextesCoran textes;

  /// Contenu brut de coran_lecture.json (réglages, signets, progression) tel que l'hôte l'a enregistré.
  final Object? etatBrut;

  /// Appelé (avec un court délai) à chaque changement de l'état de lecture : l'hôte l'enregistre.
  final void Function(Map<String, dynamic> etat)? surSauverEtat;

  /// Nombre d'écrans empilés dans le module, pour que l'hôte sache s'il doit lui laisser le bouton « retour ».
  final void Function(int profondeur)? surProfondeur;
}

/// Lit les fichiers du Coran embarqués dans le paquet.
Future<String> lecteurFichiersEmbarques(String nom) => rootBundle.loadString('packages/hayaati_coran/assets/coran/$nom');

class _ObservateurProfondeur extends NavigatorObserver {
  _ObservateurProfondeur(this.surChangement);

  final void Function(int profondeur)? surChangement;
  int _n = 0;

  @override
  void didPush(Route<dynamic> route, Route<dynamic>? previousRoute) {
    if (previousRoute == null) return;
    _n++;
    surChangement?.call(_n);
  }

  @override
  void didPop(Route<dynamic> route, Route<dynamic>? previousRoute) {
    if (_n > 0) _n--;
    surChangement?.call(_n);
  }

  @override
  void didRemove(Route<dynamic> route, Route<dynamic>? previousRoute) {
    if (_n > 0) _n--;
    surChangement?.call(_n);
  }
}

/// Point d'entrée : un Navigator interne, indépendant de l'application hôte (même principe qu'AlAnsarModule).
/// Bouton « retour » d'Android : l'hôte connaît la profondeur par [ConfigCoran.surProfondeur] et, si elle dépasse 0,
/// demande au module de revenir d'un écran avec [navigatorKey] (`navigatorKey.currentState?.maybePop()`).
class ModuleCoran extends StatefulWidget {
  const ModuleCoran({super.key, required this.config, this.navigatorKey, this.lecteur = lecteurFichiersEmbarques});

  final ConfigCoran config;
  final GlobalKey<NavigatorState>? navigatorKey;

  /// Source des fichiers du Coran ; remplaçable dans les tests.
  final LecteurFichier lecteur;

  @override
  State<ModuleCoran> createState() => _ModuleCoranState();
}

class _ModuleCoranState extends State<ModuleCoran> {
  ControleurCoran? _controleur;
  Widget? _navigateur;
  Object? _erreur;

  @override
  void initState() {
    super.initState();
    _preparer();
  }

  Future<void> _preparer() async {
    try {
      final moteur = await MoteurCoran.ouvrir(widget.lecteur, journal: (m) => debugPrint(m));
      final config = widget.config;
      final c = ControleurCoran(
        moteur: moteur,
        textes: config.textes,
        depot: DepotHote(initial: config.etatBrut, surSauver: (etat) => widget.config.surSauverEtat?.call(etat)),
      );
      await c.init();
      if (!mounted) {
        c.dispose();
        return;
      }
      final observateur = _ObservateurProfondeur((n) => widget.config.surProfondeur?.call(n));
      setState(() {
        _controleur = c;
        _navigateur = Navigator(
          key: widget.navigatorKey,
          observers: <NavigatorObserver>[observateur],
          onGenerateRoute: (_) => MaterialPageRoute<void>(builder: (_) => EcranListeSourates(controleur: c)),
        );
      });
    } catch (e) {
      if (mounted) setState(() => _erreur = e);
    }
  }

  @override
  void didUpdateWidget(covariant ModuleCoran ancien) {
    super.didUpdateWidget(ancien);
    // Langue ou textes modifiés par l'hôte : on les applique sans reconstruire le module ni toucher à l'état de lecture.
    final c = _controleur;
    if (c != null && !identical(ancien.config.textes, widget.config.textes)) {
      WidgetsBinding.instance.addPostFrameCallback((_) => c.definirTextes(widget.config.textes));
    }
  }

  @override
  void dispose() {
    _controleur?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final c = _controleur;
    final navigateur = _navigateur;
    if (_erreur != null) {
      return Theme(
        data: themeHayaati(),
        child: Center(child: Text('Le Coran n\'est pas disponible : $_erreur', textAlign: TextAlign.center)),
      );
    }
    if (c == null || navigateur == null) {
      return Theme(
        data: themeHayaati(),
        child: const Center(child: CircularProgressIndicator(color: PaletteHayaati.vertProfond)),
      );
    }
    return ListenableBuilder(
      listenable: c,
      builder: (context, nav) => Theme(
        data: themeHayaati(arabe: c.textes.rtl),
        child: Directionality(textDirection: c.textes.rtl ? TextDirection.rtl : TextDirection.ltr, child: nav!),
      ),
      child: navigateur,
    );
  }
}
