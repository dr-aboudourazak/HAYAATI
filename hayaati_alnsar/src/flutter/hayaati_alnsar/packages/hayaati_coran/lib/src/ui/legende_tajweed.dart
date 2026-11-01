import 'package:flutter/material.dart';
import 'package:hayaati_ui/hayaati_ui.dart';

import '../tajweed.dart';
import '../textes.dart';

/// Légende des cinq couleurs du tajweed, avec l'avertissement : ces annotations sont automatiques, elles aident la
/// lecture sans remplacer l'apprentissage auprès d'un enseignant qualifié.
Future<void> montrerLegendeTajweed(BuildContext context, TextesCoran t) {
  return showModalBottomSheet<void>(
    context: context,
    backgroundColor: PaletteHayaati.blanc,
    builder: (_) => SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              t('tajweed_legende_titre', 'Légende du tajweed'),
              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: PaletteHayaati.vertProfond),
            ),
            const SizedBox(height: 8),
            for (final f in famillesTajweed)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 3),
                child: Row(
                  children: [
                    Container(
                      width: 16,
                      height: 16,
                      decoration: BoxDecoration(color: couleurDepuisHex(f.couleur), shape: BoxShape.circle),
                    ),
                    const SizedBox(width: 10),
                    Expanded(child: Text(t(f.cleLibelle, f.cle), style: const TextStyle(fontSize: 13))),
                  ],
                ),
              ),
            const SizedBox(height: 8),
            Text(
              t(
                'tajweed_avertissement',
                "Annotations automatiques, à titre d'aide à la lecture : elles ne remplacent pas l'apprentissage auprès d'un enseignant qualifié.",
              ),
              style: const TextStyle(fontSize: 11.5, fontStyle: FontStyle.italic, color: PaletteHayaati.grisTexte),
            ),
            const SizedBox(height: 6),
            Text(
              t('source_tajweed', 'Tajweed : annotations cpfair/quran-tajweed (CC BY 4.0)'),
              style: const TextStyle(fontSize: 10, color: PaletteHayaati.grisTexte),
            ),
          ],
        ),
      ),
    ),
  );
}
