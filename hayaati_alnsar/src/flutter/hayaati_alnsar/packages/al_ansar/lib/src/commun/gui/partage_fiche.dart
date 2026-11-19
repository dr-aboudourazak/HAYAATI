import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../fonctionnalites/annuaire/core/controleur.dart';
import '../core/liens_publication.dart';
import '../../fonctionnalites/annuaire/core/modeles.dart';

/// Bouton Partager d'une publication (fiche, forfait...). Il n'apparaît que si AlAnsarConfig.baseLien est une adresse sûre
/// terminée par « /a/ ». Avec une feuille de partage fournie par l'hôte (surPartager) il l'appelle ; sinon il copie le lien.
class BoutonPartager extends StatelessWidget {
  const BoutonPartager({super.key, required this.c, required this.id, required this.titre});

  final ControleurAlAnsar c;
  final String id;

  /// Texte qui accompagne le lien dans le message partagé.
  final String titre;

  @override
  Widget build(BuildContext context) {
    final lien = lienPartage(c.config.baseLien, id);
    if (lien.isEmpty) return const SizedBox.shrink();
    final t = c.t;
    return Padding(
      padding: const EdgeInsets.only(top: 8, bottom: 4),
      child: Align(
        alignment: AlignmentDirectional.centerStart,
        child: OutlinedButton.icon(
          icon: const Icon(Icons.share_outlined),
          label: Text(t('pub_partager')),
          onPressed: () async {
            final hote = c.config.surPartager;
            if (hote != null) {
              hote('$titre\n$lien');
              return;
            }
            await Clipboard.setData(ClipboardData(text: lien));
            if (context.mounted) {
              ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(t('pub_lien_copie'))));
            }
          },
        ),
      ),
    );
  }
}

/// Bouton Partager d'une fiche.
class BoutonPartagerFiche extends StatelessWidget {
  const BoutonPartagerFiche({super.key, required this.c, required this.fiche});

  final ControleurAlAnsar c;
  final Fiche fiche;

  @override
  Widget build(BuildContext context) => BoutonPartager(c: c, id: fiche.id, titre: fiche.nom);
}
