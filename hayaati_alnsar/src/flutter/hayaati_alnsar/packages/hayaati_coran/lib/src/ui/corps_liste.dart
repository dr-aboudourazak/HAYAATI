import 'package:flutter/material.dart';
import 'package:hayaati_ui/hayaati_ui.dart';

import '../controleur.dart';
import '../moteur_coran.dart';
import '../texte.dart';
import 'constructeur_spans.dart';
import 'texte_versets.dart';

/// Mode liste : la sourate se lit en défilement continu vers le bas, une page de mushaf après l'autre. La lecture
/// commence à la page active ; un bouton renvoie au début de la sourate si l'on est parti du milieu. La page suivie
/// pour la progression est estimée d'après la position de défilement.
class CorpsListe extends StatefulWidget {
  const CorpsListe({super.key, required this.controleur, required this.barre});

  final ControleurCoran controleur;

  /// Barre d'actions du verset sélectionné, sous la liste.
  final Widget barre;

  @override
  State<CorpsListe> createState() => _CorpsListeState();
}

class _Donnees {
  const _Donnees(this.pages, this.sourate);

  final List<int> pages;
  final SourateCoran? sourate;
}

class _CorpsListeState extends State<CorpsListe> {
  late int _debut = widget.controleur.pageActive;
  Key _cle = UniqueKey();
  late Future<_Donnees> _donnees = _charger();
  int _derniereEstimee = -1;

  Future<_Donnees> _charger() async {
    final c = widget.controleur;
    final n = c.sourateActive;
    return _Donnees(await c.moteur.pagesDeSourate(n), await c.moteur.sourate(n));
  }

  @override
  void initState() {
    super.initState();
    widget.controleur.saut.addListener(_surSaut);
  }

  @override
  void dispose() {
    widget.controleur.saut.removeListener(_surSaut);
    super.dispose();
  }

  /// Recherche de verset ou changement de sourate : la liste est reconstruite à partir de la page demandée.
  void _surSaut() {
    final d = widget.controleur.saut.value;
    if (d == null) return;
    setState(() {
      _debut = d.page;
      _cle = UniqueKey();
      _donnees = _charger();
      _derniereEstimee = -1;
    });
  }

  bool _surDefilement(ScrollNotification n, List<int> pages, int indexDebut) {
    final m = n.metrics;
    if (m.axis != Axis.vertical || m.maxScrollExtent <= 0) return false;
    final nb = pages.length - indexDebut;
    final fraction = (m.pixels / m.maxScrollExtent).clamp(0.0, 0.999);
    final page = pages[indexDebut + (fraction * nb).floor()];
    if (page != _derniereEstimee) {
      _derniereEstimee = page;
      // Après la mise en page : un défilement ne doit pas modifier l'état pendant qu'il est dessiné.
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted && widget.controleur.pageActive != page) widget.controleur.pageAffichee(page);
      });
    }
    return false;
  }

  @override
  Widget build(BuildContext context) {
    final c = widget.controleur;
    final t = c.textes;
    return Column(
      children: [
        Expanded(
          child: FutureBuilder<_Donnees>(
            key: _cle,
            future: _donnees,
            builder: (context, instantane) {
              if (instantane.connectionState != ConnectionState.done) {
                return const Center(child: CircularProgressIndicator(color: PaletteHayaati.vertProfond));
              }
              final donnees = instantane.data;
              if (donnees == null || donnees.pages.isEmpty) {
                return Center(
                  child: Text(
                    t('texte_indisponible', 'Le texte est indisponible.'),
                    style: const TextStyle(color: PaletteHayaati.rougeErreur, fontSize: 12),
                  ),
                );
              }
              final pages = donnees.pages;
              final trouve = pages.indexOf(_debut);
              final indexDebut = trouve < 0 ? 0 : trouve;
              final nb = pages.length - indexDebut;
              return NotificationListener<ScrollNotification>(
                onNotification: (n) => _surDefilement(n, pages, indexDebut),
                child: ListView.builder(
                  itemCount: nb + 2, // entête + pages + pied
                  itemBuilder: (context, i) {
                    if (i == 0) return _entete(c, pages, indexDebut, donnees.sourate);
                    if (i == nb + 1) return _pied(t.call('source_attribution', 'Source : Tanzil.net'));
                    return _BlocListe(
                      key: ValueKey<String>('${c.sourateActive}|${pages[indexDebut + i - 1]}|$_debut'),
                      controleur: c,
                      page: pages[indexDebut + i - 1],
                    );
                  },
                ),
              );
            },
          ),
        ),
        widget.barre,
      ],
    );
  }

  Widget _entete(ControleurCoran c, List<int> pages, int indexDebut, SourateCoran? sourate) {
    if (indexDebut > 0) {
      return TextButton(
        onPressed: () => c.ouvrirSourate(c.sourateActive),
        child: Text(
          c.textes('debut_sourate', '↑ Début de la sourate'),
          style: const TextStyle(fontSize: 12, color: PaletteHayaati.vertProfond),
        ),
      );
    }
    final basmalah = sourate?.basmalah;
    if (basmalah == null) return const SizedBox(height: 4);
    return ListenableBuilder(
      listenable: c,
      builder: (context, _) {
        final taille = c.etat.taille * c.police.rapport;
        return Padding(
          padding: const EdgeInsets.fromLTRB(8, 8, 8, 6),
          child: Text.rich(
            TextSpan(children: spansTexte(
              texte: basmalah,
              annotations: sourate?.basmalahTajweed,
              couleurBase: PaletteHayaati.vertProfond,
              tajweed: c.etat.tajweed,
              taille: taille,
            )),
            textAlign: TextAlign.center,
            textDirection: TextDirection.rtl,
            style: styleTexteCoran(c.police, taille),
          ),
        );
      },
    );
  }

  Widget _pied(String attribution) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(0, 12, 0, 12),
      child: Text(
        attribution,
        textAlign: TextAlign.center,
        style: const TextStyle(fontSize: 9, color: PaletteHayaati.grisTexte),
      ),
    );
  }
}

/// Une page de mushaf dans la liste : les versets de la sourate lue, puis « Page n · Juz j ». Une page peut contenir
/// la fin d'une autre sourate : elle n'apparaît pas dans cette vue.
class _BlocListe extends StatefulWidget {
  const _BlocListe({super.key, required this.controleur, required this.page});

  final ControleurCoran controleur;
  final int page;

  @override
  State<_BlocListe> createState() => _BlocListeState();
}

class _BlocListeState extends State<_BlocListe> {
  late final Future<List<BlocPage>> _blocs = _charger();

  Future<List<BlocPage>> _charger() async {
    final c = widget.controleur;
    final n = c.sourateActive;
    final tous = await c.moteur.versetsDePage(widget.page);
    return <BlocPage>[for (final b in tous) if (b.sourate == n) b];
  }

  @override
  Widget build(BuildContext context) {
    final c = widget.controleur;
    return FutureBuilder<List<BlocPage>>(
      future: _blocs,
      builder: (context, instantane) {
        if (instantane.connectionState != ConnectionState.done) return const SizedBox(height: 320);
        final blocs = instantane.data ?? const <BlocPage>[];
        if (blocs.isEmpty) return const SizedBox.shrink();
        final t = c.textes;
        final juz = c.moteur.juzDePage(widget.page);
        var pied = '${t('mot_page', 'Page')} ${chiffresArabes(widget.page)}';
        if (juz != null) pied += '  ·  ${t('mot_juz', 'Juz')} ${chiffresArabes(juz)}';
        return Container(
          padding: const EdgeInsets.fromLTRB(8, 10, 8, 8),
          decoration: const BoxDecoration(border: Border(bottom: BorderSide(color: PaletteHayaati.grisClair))),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              TexteVersets(controleur: c, blocs: blocs),
              const SizedBox(height: 6),
              Text(
                pied,
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 10, color: PaletteHayaati.grisTexte),
              ),
            ],
          ),
        );
      },
    );
  }
}
