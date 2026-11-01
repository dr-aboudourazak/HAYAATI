import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';

import '../controleur.dart';
import '../moteur_coran.dart';
import 'constructeur_spans.dart';

/// Texte continu des versets d'une page (ou d'un bloc du mode liste), justifié de droite à gauche. Un toucher sur un
/// verset le sélectionne (surlignage jaune) ; le texte se reconstruit seul quand les réglages ou la sélection changent.
class TexteVersets extends StatefulWidget {
  const TexteVersets({super.key, required this.controleur, required this.blocs});

  final ControleurCoran controleur;
  final List<BlocPage> blocs;

  @override
  State<TexteVersets> createState() => _TexteVersetsState();
}

class _TexteVersetsState extends State<TexteVersets> {
  // Un reconnaisseur par verset, remplacés à chaque reconstruction : il faut les libérer.
  final List<TapGestureRecognizer> _gestes = <TapGestureRecognizer>[];

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

  @override
  Widget build(BuildContext context) {
    final c = widget.controleur;
    return ListenableBuilder(
      listenable: c,
      builder: (context, _) {
        _liberer();
        final police = c.police;
        final taille = c.etat.taille * police.rapport;
        final spans = <InlineSpan>[];
        for (final bloc in widget.blocs) {
          spans.addAll(spansVersets(
            sourate: bloc.sourate,
            versets: bloc.versets,
            etat: c.etat,
            taille: taille,
            selection: c.selection,
            geste: (sourate, verset) {
              final g = TapGestureRecognizer()..onTap = () => c.toucherVerset(sourate, verset);
              _gestes.add(g);
              return g;
            },
          ));
        }
        return Text.rich(
          TextSpan(children: spans),
          textAlign: TextAlign.justify,
          textDirection: TextDirection.rtl,
          style: styleTexteCoran(police, taille),
        );
      },
    );
  }
}
