import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:al_ansar/al_ansar.dart' as ansar;
import 'package:app_links/app_links.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:hayaati_coran/hayaati_coran.dart' as coran;
import 'package:hayaati_ui/hayaati_ui.dart' as ui;
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import 'lecteur_youtube.dart';

/// Application d'exemple en Flutter pur : les mêmes modules que HAYAATI (Al Ansâr, Madrassa, Le Coran), sans Flet ni
/// Python. Elle sert à tester vite (flutter run, rechargement à chaud) avant de reconstruire l'application complète.
///
/// L'hôte fait ici ce que fait page_alansar.py / page_coran_native.py côté Python : il fournit la langue, les textes
/// traduits (fichiers de langue de HAYAATI copiés dans assets/locales), la progression et l'état de lecture.
void main() => runApp(const HayaatiExemple());

const List<String> langues = <String>['fr', 'en', 'ar', 'ha'];
const List<String> sectionsMadrassa = <String>['madrassa', 'interface_savoir', 'encyclopedie', 'langue_arabe', 'sciences_islamiques'];

class HayaatiExemple extends StatefulWidget {
  const HayaatiExemple({super.key, this.ecouterLiens = true});

  /// Faux dans les tests : sans plateforme réelle, l'écoute des liens n'a pas de canal à interroger.
  final bool ecouterLiens;

  @override
  State<HayaatiExemple> createState() => _HayaatiExempleState();
}

class _HayaatiExempleState extends State<HayaatiExemple> {
  String _langue = 'fr';
  Map<String, dynamic>? _dic;
  final Map<String, dynamic> _progres = <String, dynamic>{};
  Object? _etatCoran;
  Object? _erreur;

  /// Apparence choisie (arrière-plan et couleur principale), enregistrée dans apparence.json.
  final ValueNotifier<ui.ApparenceHayaati> _apparence = ValueNotifier<ui.ApparenceHayaati>(ui.ApparenceHayaati.defaut);

  final GlobalKey<NavigatorState> _nav = GlobalKey<NavigatorState>();
  final AppLinks _liensApp = AppLinks();
  StreamSubscription<Uri>? _abonnementLiens;

  /// Publication demandée par un lien reçu avant la fin du chargement : elle s'ouvre dès que l'application est prête.
  String? _idEnAttente;

  @override
  void initState() {
    super.initState();
    _chargerApparence();
    _charger();
    if (widget.ecouterLiens) _ecouterLiens();
  }

  @override
  void dispose() {
    _abonnementLiens?.cancel();
    _apparence.dispose();
    super.dispose();
  }

  /// Écoute les liens hayaati://a/<identifiant> (application déjà ouverte, ou ouverte par le lien).
  Future<void> _ecouterLiens() async {
    try {
      _abonnementLiens = _liensApp.uriLinkStream.listen((uri) => _recevoirLien(uri.toString()));
      final premier = await _liensApp.getInitialLink();
      if (premier != null) _recevoirLien(premier.toString());
    } catch (e) {
      // Plateforme sans réception de liens : l'application fonctionne sans.
      debugPrint('Réception de liens indisponible ($e)');
    }
  }

  /// Vrai si le texte est un lien de publication reconnu. Seul l'identifiant est retenu (voir idFicheDepuisLien).
  bool _recevoirLien(String lien) {
    final id = ansar.idFicheDepuisLien(lien);
    if (id == null) return false;
    if (_dic == null) {
      _idEnAttente = id;
    } else {
      _ouvrirFicheDemandee(id);
    }
    return true;
  }

  void _ouvrirFicheDemandee(String id) {
    final nav = _nav.currentState;
    if (nav == null) {
      _idEnAttente = id;
      return;
    }
    _pousserAlAnsar(nav, ficheInitiale: id);
  }

  Future<void> _collerLien(BuildContext contexte) async {
    final saisie = TextEditingController();
    final lien = await showDialog<String>(
      context: contexte,
      builder: (ctx) => AlertDialog(
        title: const Text('Ouvrir une publication par lien'),
        content: TextField(
          controller: saisie,
          autofocus: true,
          keyboardType: TextInputType.url,
          decoration: const InputDecoration(hintText: 'hayaati://a/tg-lome-mad-001'),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(), child: const Text('Annuler')),
          FilledButton(onPressed: () => Navigator.of(ctx).pop(saisie.text), child: const Text('Ouvrir')),
        ],
      ),
    );
    if (lien == null || lien.trim().isEmpty || !contexte.mounted) return;
    if (!_recevoirLien(lien)) {
      ScaffoldMessenger.of(contexte).showSnackBar(const SnackBar(content: Text('Lien non reconnu')));
    }
  }

  Future<File> _fichierEtatCoran() async {
    final dossier = await getApplicationDocumentsDirectory();
    return File('${dossier.path}${Platform.pathSeparator}coran_lecture.json');
  }

  Future<File> _fichierApparence() async {
    final dossier = await getApplicationDocumentsDirectory();
    return File('${dossier.path}${Platform.pathSeparator}apparence.json');
  }

  Future<void> _chargerApparence() async {
    try {
      final f = await _fichierApparence();
      if (await f.exists()) _apparence.value = ui.ApparenceHayaati.depuisJson(jsonDecode(await f.readAsString()));
    } catch (_) {
      // Fichier illisible : l'apparence par défaut s'applique.
    }
  }

  Future<void> _changerApparence(ui.ApparenceHayaati a) async {
    _apparence.value = a;
    try {
      await (await _fichierApparence()).writeAsString(jsonEncode(a.toJson()));
    } catch (_) {
      // Un enregistrement impossible ne doit pas empêcher d'essayer les thèmes.
    }
  }

  Future<void> _charger({String? langue}) async {
    try {
      final code = langue ?? _langue;
      final dic = Map<String, dynamic>.from(jsonDecode(await rootBundle.loadString('assets/locales/$code.json')) as Map);
      Object? etat = _etatCoran;
      if (etat == null) {
        try {
          final f = await _fichierEtatCoran();
          if (await f.exists()) etat = jsonDecode(await f.readAsString());
        } catch (_) {
          etat = null;
        }
      }
      if (!mounted) return;
      setState(() {
        _langue = code;
        _dic = dic;
        _etatCoran = etat;
        _erreur = null;
      });
      final enAttente = _idEnAttente;
      if (enAttente != null) {
        _idEnAttente = null;
        WidgetsBinding.instance.addPostFrameCallback((_) => _ouvrirFicheDemandee(enAttente));
      }
    } catch (e) {
      if (mounted) setState(() => _erreur = e);
    }
  }

  Future<void> _sauverEtatCoran(Map<String, dynamic> etat) async {
    _etatCoran = etat;
    try {
      await (await _fichierEtatCoran()).writeAsString(jsonEncode(etat));
    } catch (_) {
      // L'exemple continue même si l'enregistrement est impossible.
    }
  }

  Map<String, String> _textes(String section) {
    final s = _dic?[section];
    if (s is! Map) return const <String, String>{};
    return s.map((k, v) => MapEntry(k.toString(), v.toString()));
  }

  ansar.AlAnsarConfig _configAlAnsar({String? ecranInitial, String? ficheInitiale, required ValueChanged<int> surProfondeur}) {
    final dic = _dic!;
    return ansar.AlAnsarConfig(
      baseUrl: '',
      langue: _langue,
      pays: 'TG',
      modeDemo: true,
      ecranInitial: ecranInitial,
      textes: _textes('al_ansar'),
      apparence: _apparence.value,
      // Adresse fictive : aucun site de partage n'existe encore. Sans baseLien, le bouton Partager n'est pas proposé.
      baseLien: 'https://exemple.org/a/',
      surPartager: (texte) => SharePlus.instance.share(ShareParams(text: texte)),
      // Lecture des vidéos dans l'application (Android, iOS, macOS, web) ; ailleurs, YouTube s'ouvre à l'extérieur.
      lecteurVideo: lecteurYoutubeDisponible
          ? (contexte, idYoutube) => LecteurYoutube(idYoutube: idYoutube, langue: _langue)
          : null,
      ficheInitiale: ficheInitiale,
      madrassa: ansar.MadrassaHote(
        contenu: <String, dynamic>{for (final k in sectionsMadrassa) k: dic[k] ?? const <String, dynamic>{}},
        progres: _progres,
        visiteur: true,
        surSauver: (module, donnees) => _progres[module] = donnees,
      ),
      surProfondeur: surProfondeur,
    );
  }

  /// Choix de l'apparence : le thème de toute l'application change en direct, derrière la feuille.
  void _ouvrirApparence(BuildContext contexte) {
    showModalBottomSheet<void>(
      context: contexte,
      showDragHandle: true,
      builder: (_) => ValueListenableBuilder<ui.ApparenceHayaati>(
        valueListenable: _apparence,
        builder: (context, apparence, _) => SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
            child: ui.SelecteurApparence(apparence: apparence, surChangement: _changerApparence),
          ),
        ),
      ),
    );
  }

  void _ouvrirAlAnsar(BuildContext contexte, {String? ecranInitial}) =>
      _pousserAlAnsar(Navigator.of(contexte), ecranInitial: ecranInitial);

  void _pousserAlAnsar(NavigatorState nav, {String? ecranInitial, String? ficheInitiale}) {
    nav.push(MaterialPageRoute<void>(
      builder: (_) => _EcranModule(
        construire: (cle, surProfondeur) => ansar.AlAnsarModule(
          config: _configAlAnsar(ecranInitial: ecranInitial, ficheInitiale: ficheInitiale, surProfondeur: surProfondeur),
          navigatorKey: cle,
        ),
      ),
    ));
  }

  void _ouvrirCoran(BuildContext contexte) {
    Navigator.of(contexte).push(MaterialPageRoute<void>(
      builder: (_) => _EcranModule(
        construire: (cle, surProfondeur) => coran.ModuleCoran(
          navigatorKey: cle,
          config: coran.ConfigCoran(
            textes: coran.TextesCoran(_textes('coran'), _langue == 'ar'),
            etatBrut: _etatCoran,
            apparence: _apparence.value,
            surSauverEtat: _sauverEtatCoran,
            surProfondeur: surProfondeur,
          ),
        ),
      ),
    ));
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<ui.ApparenceHayaati>(
      valueListenable: _apparence,
      builder: (context, apparence, _) => MaterialApp(
        navigatorKey: _nav,
        title: 'HAYAATI exemple',
        debugShowCheckedModeBanner: false,
        theme: ui.themeHayaati(arabe: _langue == 'ar', apparence: apparence),
        home: Builder(builder: (contexte) => _accueil(contexte)),
      ),
    );
  }

  Widget _accueil(BuildContext contexte) {
    final dic = _dic;
    return Scaffold(
      appBar: ansar.barreHayaati(
        'HAYAATI · exemple',
        avecIcone: true,
        actions: [
          IconButton(
            tooltip: 'Apparence',
            icon: const Icon(Icons.palette_outlined),
            onPressed: () => _ouvrirApparence(contexte),
          ),
          PopupMenuButton<String>(
            tooltip: 'Langue',
            icon: const Icon(Icons.language),
            onSelected: (code) => _charger(langue: code),
            itemBuilder: (_) => [
              for (final l in langues) CheckedPopupMenuItem<String>(value: l, checked: l == _langue, child: Text(l.toUpperCase())),
            ],
          ),
        ],
      ),
      body: _erreur != null
          ? Padding(
              padding: const EdgeInsets.all(24),
              child: Text(
                'Chargement impossible : $_erreur\n\nVérifiez que assets/locales contient fr.json, en.json, ar.json et ha.json '
                '(ils sont copiés par appliquer_lot_c.py).',
              ),
            )
          : dic == null
              ? const Center(child: CircularProgressIndicator())
              : ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    _Tuile(icone: Icons.explore, titre: 'Al Ansâr', onTap: () => _ouvrirAlAnsar(contexte)),
                    _Tuile(icone: Icons.school, titre: 'Madrassa (ouvert directement)', onTap: () => _ouvrirAlAnsar(contexte, ecranInitial: 'madrassa')),
                    _Tuile(icone: Icons.menu_book, titre: 'Le Coran', onTap: () => _ouvrirCoran(contexte)),
                    _Tuile(icone: Icons.link, titre: 'Ouvrir une publication par lien', onTap: () => _collerLien(contexte)),
                    const Padding(
                      padding: EdgeInsets.only(top: 16),
                      child: Text(
                        'Mêmes modules que dans HAYAATI, sans Flet ni Python : flutter run, puis « r » pour recharger à chaud.',
                        style: TextStyle(fontSize: 12),
                      ),
                    ),
                  ],
                ),
    );
  }
}

class _Tuile extends StatelessWidget {
  const _Tuile({required this.icone, required this.titre, required this.onTap});

  final IconData icone;
  final String titre;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        minVerticalPadding: 20,
        leading: Icon(icone, size: 32),
        title: Text(titre, style: Theme.of(context).textTheme.titleMedium),
        trailing: const Icon(Icons.chevron_right),
        onTap: onTap,
      ),
    );
  }
}

/// Écran qui héberge un module et lui laisse le bouton « retour » tant qu'il a des écrans empilés (comme le fait
/// l'hôte Python dans HAYAATI).
class _EcranModule extends StatefulWidget {
  const _EcranModule({required this.construire});

  final Widget Function(GlobalKey<NavigatorState> cle, ValueChanged<int> surProfondeur) construire;

  @override
  State<_EcranModule> createState() => _EcranModuleState();
}

class _EcranModuleState extends State<_EcranModule> {
  final GlobalKey<NavigatorState> _cle = GlobalKey<NavigatorState>();
  final ValueNotifier<int> _profondeur = ValueNotifier<int>(0);

  @override
  void dispose() {
    _profondeur.dispose();
    super.dispose();
  }

  void _surProfondeur(int n) {
    // Après la construction : le module signale sa profondeur pendant qu'il se met à jour.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _profondeur.value = n;
    });
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<int>(
      valueListenable: _profondeur,
      builder: (context, profondeur, _) => PopScope(
        canPop: profondeur == 0,
        onPopInvokedWithResult: (didPop, _) {
          if (!didPop) _cle.currentState?.maybePop();
        },
        child: Scaffold(body: SafeArea(child: widget.construire(_cle, _surProfondeur))),
      ),
    );
  }
}
