import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';

import 'package:hayaati_ui/hayaati_ui.dart' show CharteHayaati;

import '../controleur.dart';
import '../moteur_coran.dart';
import 'constructeur_spans.dart';
import 'justification.dart';

/// Texte continu des versets d'une page (ou d'un bloc du mode liste), justifié de droite à gauche. Un toucher sur un
/// verset le sélectionne (surlignage jaune) ; le texte se reconstruit seul quand les réglages ou la sélection changent.
///
/// [justifierFin] : chaque ligne du bloc, y compris la dernière (fin de sourate ou fin de page), finit exactement au bout
/// de la ligne, comme dans un mushaf imprimé. Les coupures de lignes sont choisies pour cela (mise_en_lignes.dart) et
/// chaque ligne est affichée seule ; si le bloc est trop court pour cela, l'ancienne méthode, puis l'affichage normal,
/// prennent le relais.
class TexteVersets extends StatefulWidget {
  const TexteVersets({super.key, required this.controleur, required this.blocs, this.justifierFin = false});

  final ControleurCoran controleur;
  final List<BlocPage> blocs;
  final bool justifierFin;

  @override
  State<TexteVersets> createState() => _TexteVersetsState();
}

class _TexteVersetsState extends State<TexteVersets> {
  CharteHayaati get ch => CharteHayaati.of(context);

  // Un reconnaisseur par verset, remplacés à chaque reconstruction : il faut les libérer.
  final List<TapGestureRecognizer> _gestes = <TapGestureRecognizer>[];

  // Réglages de justification : ne dépendent que de la largeur, de la taille, de la police et du texte, donc
  // recalculés seulement quand l'un d'eux change (pas à chaque sélection de verset ni changement de couleur).
  String? _cleJustification;
  PlanJustification _plan = PlanJustification.aucun;

  void _liberer() {
    for (final g in _gestes) {
      g.dispose();
    }
    _gestes.clear();
  }

  @override
  void dispose() {
    _liberer();
    super.dispose();
  }

  List<InlineSpan> _spans(double echelle, double taille, {required bool gestes}) {
    final c = widget.controleur;
    final spans = <InlineSpan>[];
    for (final bloc in widget.blocs) {
      spans.addAll(spansVersets(
        ch: ch,
        sourate: bloc.sourate,
        versets: bloc.versets,
        etat: c.etat,
        taille: taille * echelle,
        selection: c.selection,
        geste: gestes
            ? (sourate, verset) {
                final g = TapGestureRecognizer()..onTap = () => c.toucherVerset(sourate, verset);
                _gestes.add(g);
                return g;
              }
            : null,
      ));
    }
    return spans;
  }

  Widget _corps(BuildContext context, double largeur) {
    _liberer();
    final c = widget.controleur;
    final police = c.police;
    final taille = c.etat.taille * police.rapport;

    var plan = PlanJustification.aucun;
    if (widget.justifierFin) {
      final echelleSysteme = MediaQuery.textScalerOf(context);
      final premier = widget.blocs.first.versets.isEmpty ? 0 : widget.blocs.first.versets.first.numero;
      final dernier = widget.blocs.last.versets.isEmpty ? 0 : widget.blocs.last.versets.last.numero;
      final cle = '${largeur.toStringAsFixed(1)}|${c.etat.taille}|${police.cle}|${echelleSysteme.scale(14)}'
          '|${widget.blocs.first.sourate}:$premier-$dernier';
      if (cle != _cleJustification) {
        _cleJustification = cle;
        _plan = calculerPlan(
          construireSpans: (e) => _spans(e, taille, gestes: false),
          construireStyle: (e) => styleTexteCoran(police, taille * e, ch),
          largeur: largeur,
          echelleSysteme: echelleSysteme,
        );
      }
      plan = _plan;
    }

    final dispo = plan.disposition;
    if (dispo != null) {
      // Une ligne par Text : chaque ligne est justifiée à sa propre largeur, sans coupure automatique.
      final spans = sansEspaceFinal(_spans(dispo.echelle, taille, gestes: true));
      final style = styleTexteCoran(police, taille * dispo.echelle, ch);
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          for (final l in dispo.lignes)
            Text.rich(
              TextSpan(children: extraireSpans(spans, l.debut, l.fin)),
              softWrap: false,
              overflow: TextOverflow.visible,
              textAlign: TextAlign.start,
              textDirection: TextDirection.rtl,
              style: style.copyWith(wordSpacing: l.espace),
            ),
        ],
      );
    }

    final params = plan.params;
    var spans = _spans(params.echelle, taille, gestes: true);
    var style = styleTexteCoran(police, taille * params.echelle, ch);
    if (params.actif) {
      spans = sansEspaceFinal(spans);
      spans = espacerFin(spans, params.debutFin, params.espaceGlobal, params.espaceFin);
      style = style.copyWith(wordSpacing: params.espaceGlobal);
    }
    return Text.rich(
      TextSpan(children: spans),
      textAlign: TextAlign.justify,
      textDirection: TextDirection.rtl,
      style: style,
    );
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: widget.controleur,
      builder: (context, _) => LayoutBuilder(builder: (context, contraintes) => _corps(context, contraintes.maxWidth)),
    );
  }
}
