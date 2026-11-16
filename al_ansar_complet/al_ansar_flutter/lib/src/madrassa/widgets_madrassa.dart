import 'package:flutter/material.dart';
import 'package:hayaati_ui/hayaati_ui.dart' show familleArabe, reserveArabe, styleCorps, styleArabe, TexteArabe;

import 'package:hayaati_ui/hayaati_ui.dart' show CharteHayaati;
import '../theme/palette.dart';
import '../theme/theme_hayaati.dart';
import 'moteurs.dart';

// La police arabe et les composants de texte arabe vivent dans le paquet commun hayaati_ui ; ils restent
// accessibles d'ici pour les écrans de Madrassa.
export 'package:hayaati_ui/hayaati_ui.dart' show familleArabe, reserveArabe, styleCorps, styleArabe, TexteArabe;

void ouvrirEcran(BuildContext context, Widget ecran) {
  Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => ecran));
}

/// Tuile d'un module dans un hub.
class TuileMadrassa extends StatelessWidget {
  const TuileMadrassa({
    super.key,
    required this.icone,
    required this.titre,
    required this.onTap,
    this.description = '',
    this.info = '',
  });

  final IconData icone;
  final String titre;
  final String description;
  final String info;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final ch = CharteHayaati.of(context);
    final theme = Theme.of(context);
    return CarteHayaati(
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            children: [
              Icon(icone, size: 30, color: ch.vertProfond),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(titre, style: theme.textTheme.titleMedium?.copyWith(fontFamilyFallback: reserveArabe)),
                    if (description.isNotEmpty) Text(description, style: theme.textTheme.bodySmall),
                    if (info.isNotEmpty)
                      Padding(
                        padding: const EdgeInsets.only(top: 4),
                        child: Text(
                          info,
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: ch.ocreFonce,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right),
            ],
          ),
        ),
      ),
    );
  }
}

/// Boutons « je connais » / « à revoir » : l'état courant est coloré, les deux sont exclusifs.
class BoutonsMarquage extends StatelessWidget {
  const BoutonsMarquage({
    super.key,
    required this.etat,
    required this.surOui,
    required this.surNon,
    required this.tooltipOui,
    required this.tooltipNon,
  });

  /// connu, a_revoir ou non_vu.
  final String etat;
  final VoidCallback surOui;
  final VoidCallback surNon;
  final String tooltipOui;
  final String tooltipNon;

  @override
  Widget build(BuildContext context) {
    final ch = CharteHayaati.of(context);
    final connu = etat == 'connu';
    final aRevoir = etat == 'a_revoir';
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        IconButton(
          tooltip: tooltipOui,
          onPressed: surOui,
          icon: Icon(
            connu ? Icons.check_circle : Icons.check_circle_outline,
            color: connu ? ch.vertClair : ch.grisTexte,
          ),
        ),
        IconButton(
          tooltip: tooltipNon,
          onPressed: surNon,
          icon: Icon(
            aRevoir ? Icons.help : Icons.help_outline,
            color: aRevoir ? ch.ambreAttente : ch.grisTexte,
          ),
        ),
      ],
    );
  }
}

/// « 12 connu(e)s · 3 à revoir · 13 pas encore vu(e)s ».
class BandeauResume extends StatelessWidget {
  const BandeauResume({
    super.key,
    required this.resume,
    required this.libelleConnues,
    required this.libelleARevoir,
    required this.libelleNonVues,
  });

  final ResumeEtape resume;
  final String libelleConnues;
  final String libelleARevoir;
  final String libelleNonVues;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 6,
      runSpacing: 4,
      children: [
        Chip(label: Text('✅ ${resume.connues} $libelleConnues'), visualDensity: VisualDensity.compact),
        Chip(label: Text('🔁 ${resume.aRevoir} $libelleARevoir'), visualDensity: VisualDensity.compact),
        Chip(label: Text('⚪ ${resume.nonVues} $libelleNonVues'), visualDensity: VisualDensity.compact),
      ],
    );
  }
}

/// Bloc d'exemples : arabe, translittération, sens.
class BlocExemples extends StatelessWidget {
  const BlocExemples({super.key, required this.exemples});

  final List<Map<String, dynamic>> exemples;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final ex in exemples)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 6),
            child: CarteHayaati(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    TexteArabe('${ex['arabe'] ?? ''}', taille: 24),
                    if ('${ex['translitteration'] ?? ''}'.isNotEmpty)
                      Align(
                        alignment: AlignmentDirectional.centerStart,
                        child: Text('${ex['translitteration']}', style: theme.textTheme.bodyMedium?.copyWith(fontStyle: FontStyle.italic)),
                      ),
                    if ('${ex['sens'] ?? ''}'.isNotEmpty)
                      Align(
                        alignment: AlignmentDirectional.centerStart,
                        child: Text('${ex['sens']}', style: styleCorps(context)),
                      ),
                  ],
                ),
              ),
            ),
          ),
      ],
    );
  }
}
