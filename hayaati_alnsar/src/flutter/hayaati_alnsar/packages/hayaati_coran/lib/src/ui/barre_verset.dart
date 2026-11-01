import 'package:flutter/material.dart';
import 'package:hayaati_ui/hayaati_ui.dart';

import '../controleur.dart';

/// Actions du verset sélectionné : copier, poser ou retirer un signet, fermer. Invisible tant qu'aucun verset
/// n'est sélectionné.
class BarreVerset extends StatelessWidget {
  const BarreVerset({super.key, required this.controleur, required this.surCopier});

  final ControleurCoran controleur;
  final Future<void> Function() surCopier;

  @override
  Widget build(BuildContext context) {
    final c = controleur;
    final sel = c.selection;
    if (sel == null) return const SizedBox.shrink();
    final t = c.textes;
    return Container(
      decoration: const BoxDecoration(
        color: PaletteHayaati.sable,
        border: Border(top: BorderSide(color: PaletteHayaati.ocre)),
      ),
      padding: const EdgeInsets.only(left: 6, right: 10),
      child: Row(
        children: [
          IconButton(
            tooltip: t('fermer', 'Fermer'),
            icon: const Icon(Icons.close_rounded, size: 18),
            color: PaletteHayaati.grisTexte,
            onPressed: c.effacerSelection,
          ),
          IconButton(
            tooltip: t('signet_verset', 'Signet sur ce verset'),
            icon: Icon(c.selectionEstSignet ? Icons.bookmark_added : Icons.bookmark_add_outlined, size: 22),
            color: PaletteHayaati.ocre,
            onPressed: c.basculerSignetVerset,
          ),
          IconButton(
            tooltip: t('copier_verset', 'Copier le verset'),
            icon: const Icon(Icons.content_copy_rounded, size: 20),
            color: PaletteHayaati.vertProfond,
            onPressed: surCopier,
          ),
          Expanded(
            child: Text(
              '${c.moteur.nomSourate(sel.sourate)} · ${t('mot_verset', 'verset')} ${sel.verset}',
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontFamily: familleArabe, fontSize: 12, color: PaletteHayaati.texteFonce),
            ),
          ),
        ],
      ),
    );
  }
}
