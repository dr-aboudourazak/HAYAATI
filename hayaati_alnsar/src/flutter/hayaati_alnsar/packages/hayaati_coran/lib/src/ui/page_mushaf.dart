import 'package:flutter/material.dart';
import 'package:hayaati_ui/hayaati_ui.dart';

import '../controleur.dart';
import '../moteur_coran.dart';
import '../texte.dart';
import 'constantes_ui.dart';
import 'constructeur_spans.dart';
import 'texte_versets.dart';

/// Une page du mushaf de Médine : cadre ornemental (double bordure verte puis ocre, quatre rosettes), en-tête
/// (juz, sourate), bannière et basmala des sourates qui commencent ici, versets, numéro de page.
///
/// Le contenu est chargé une seule fois par page ; seuls les réglages (taille, police, tajweed, signets) la
/// reconstruisent.
class PageMushaf extends StatefulWidget {
  const PageMushaf({super.key, required this.controleur, required this.page});

  final ControleurCoran controleur;
  final int page;

  @override
  State<PageMushaf> createState() => _PageMushafState();
}

class _PageMushafState extends State<PageMushaf> {
  late final Future<List<BlocPage>> _blocs = widget.controleur.moteur.versetsDePage(widget.page);

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<BlocPage>>(
      future: _blocs,
      builder: (context, instantane) {
        if (instantane.connectionState != ConnectionState.done) {
          return const Center(child: CircularProgressIndicator(color: PaletteHayaati.vertProfond));
        }
        final blocs = instantane.data ?? const <BlocPage>[];
        if (blocs.isEmpty) {
          return Center(
            child: Text(
              widget.controleur.textes('texte_indisponible', 'Le texte est indisponible.'),
              style: const TextStyle(color: PaletteHayaati.rougeErreur, fontSize: 12),
            ),
          );
        }
        return ListenableBuilder(
          listenable: widget.controleur,
          builder: (context, _) => _construire(context, blocs),
        );
      },
    );
  }

  Widget _construire(BuildContext context, List<BlocPage> blocs) {
    final c = widget.controleur;
    final police = c.police;
    final taille = c.etat.taille * police.rapport;
    final styleCoran = styleTexteCoran(police, taille);

    final corps = <Widget>[];
    for (final bloc in blocs) {
      if (bloc.debut) {
        corps.add(_banniere(bloc.nomArabe, styleCoran, taille));
        if (bloc.basmalah != null) {
          corps.add(Padding(
            padding: const EdgeInsets.only(top: 2, bottom: 6),
            child: Text.rich(
              TextSpan(children: spansTexte(
                texte: bloc.basmalah!,
                annotations: bloc.basmalahTajweed,
                couleurBase: PaletteHayaati.vertProfond,
                tajweed: c.etat.tajweed,
                taille: taille,
              )),
              textAlign: TextAlign.center,
              textDirection: TextDirection.rtl,
              style: styleCoran,
            ),
          ));
        }
      }
      corps.add(TexteVersets(controleur: c, blocs: <BlocPage>[bloc]));
    }

    final juz = c.moteur.juzDePage(widget.page);
    final motJuz = c.textes('mot_juz', 'Juz');
    const styleEntete = TextStyle(fontFamily: familleArabe, fontSize: 11, color: PaletteHayaati.grisTexte);
    // Page lue de droite à gauche : le premier enfant d'une Row s'affiche à droite (nom de la sourate), le juz à gauche.
    final entete = Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          blocs.first.nomArabe,
          style: const TextStyle(
            fontFamily: familleArabe, fontSize: 12, fontWeight: FontWeight.bold, color: PaletteHayaati.vertProfond,
          ),
        ),
        Text(juz == null ? '' : '$motJuz ${chiffresArabes(juz)}', style: styleEntete),
      ],
    );
    final pied = Padding(
      padding: const EdgeInsets.only(top: 2),
      child: Center(
        child: Text(
          chiffresArabes(widget.page),
          style: TextStyle(
            fontFamily: police.famille, fontSize: 12, fontWeight: FontWeight.bold, color: PaletteHayaati.vertProfond,
          ),
        ),
      ),
    );

    final interieur = Container(
      decoration: BoxDecoration(border: Border.all(color: PaletteHayaati.ocre), borderRadius: BorderRadius.circular(6)),
      padding: const EdgeInsets.fromLTRB(10, 10, 10, 4),
      child: Column(
        children: [
          entete,
          const Divider(height: 6, color: PaletteHayaati.ocre),
          Expanded(child: SingleChildScrollView(child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: corps))),
          pied,
        ],
      ),
    );
    final exterieur = Container(
      decoration: BoxDecoration(
        color: fondPage,
        border: Border.all(color: PaletteHayaati.vertProfond, width: 3),
        borderRadius: BorderRadius.circular(10),
      ),
      padding: const EdgeInsets.all(3),
      child: interieur,
    );
    return Padding(
      padding: const EdgeInsets.fromLTRB(4, 8, 4, 4),
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          Positioned.fill(child: exterieur),
          _rosette(left: -2, top: -2),
          _rosette(right: -2, top: -2),
          _rosette(left: -2, bottom: -2),
          _rosette(right: -2, bottom: -2),
        ],
      ),
    );
  }

  Widget _banniere(String nom, TextStyle styleCoran, double taille) {
    const rosette = Text('۞', style: TextStyle(fontFamily: familleSignes, fontSize: 18, color: PaletteHayaati.ocre));
    return Container(
      margin: const EdgeInsets.only(top: 4, bottom: 6),
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: PaletteHayaati.ocreClair,
        border: Border.all(color: PaletteHayaati.ocre),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          rosette,
          const SizedBox(width: 10),
          Text(
            'سورة $nom',
            style: styleCoran.copyWith(fontSize: taille * 0.9, fontWeight: FontWeight.bold, color: PaletteHayaati.vertProfond),
          ),
          const SizedBox(width: 10),
          rosette,
        ],
      ),
    );
  }

  Widget _rosette({double? left, double? right, double? top, double? bottom}) {
    return Positioned(
      left: left,
      right: right,
      top: top,
      bottom: bottom,
      child: Container(
        width: 24,
        height: 24,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: PaletteHayaati.blanc,
          shape: BoxShape.circle,
          border: Border.all(color: PaletteHayaati.ocre, width: 1.5),
        ),
        child: const Text('۞', style: TextStyle(fontFamily: familleSignes, fontSize: 17, color: PaletteHayaati.ocre)),
      ),
    );
  }
}
