import 'package:flutter/material.dart';

import '../controleur.dart';
import '../theme/palette.dart';
import '../theme/theme_hayaati.dart';
import 'contenu.dart';
import 'ecrans_savoir.dart';
import 'moteurs.dart';
import 'widgets_madrassa.dart';

/// Hub Madrassa : Encyclopédie, Langue arabe, Sciences islamiques, Caravane du Savoir, Coran.
class EcranMadrassaHub extends StatelessWidget {
  const EcranMadrassaHub({super.key, required this.ac});

  final ControleurAlAnsar ac;

  @override
  Widget build(BuildContext context) {
    final m = ac.madrassa!;
    final c = m.contenu;
    return Scaffold(
      appBar: barreHayaati(c.m('titre_hub', 'Madrassa'), integre: ac.config.integre),
      body: ListenableBuilder(
        listenable: m,
        builder: (context, _) {
          final pasCommence = c.m('lbl_pas_commence');
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              if (m.visiteur)
                CarteHayaati(
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Text(c.m('msg_mode_visiteur')),
                  ),
                ),
              if (c.m('soustitre_hub').isNotEmpty)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  child: Text(c.m('soustitre_hub')),
                ),
              TuileMadrassa(
                icone: Icons.account_balance,
                titre: c.m('titre_encyclopedie'),
                description: c.m('desc_encyclopedie'),
                info: m.perles > 0 ? '✨ ${m.perles} ${c.m('lbl_perles')}' : pasCommence,
                onTap: () => ouvrirEcran(context, EcranEncyclopedie(ac: ac)),
              ),
              TuileMadrassa(
                icone: Icons.translate,
                titre: c.m('titre_langue_arabe'),
                description: c.m('desc_langue_arabe'),
                info: m.acquisLangue > 0 ? '✅ ${m.acquisLangue} ${c.m('lbl_acquis')}' : pasCommence,
                onTap: () => ouvrirEcran(context, EcranLangueArabe(ac: ac)),
              ),
              TuileMadrassa(
                icone: Icons.auto_stories,
                titre: c.m('titre_sciences_islamiques'),
                description: c.m('desc_sciences_islamiques'),
                info: m.acquisSciences > 0 ? '✅ ${m.acquisSciences} ${c.m('lbl_acquis')}' : pasCommence,
                onTap: () => ouvrirEcran(context, EcranSciences(ac: ac)),
              ),
              TuileMadrassa(
                icone: Icons.explore,
                titre: c.m('titre_caravane'),
                description: c.m('desc_caravane'),
                info: m.pointsARevoir > 0 ? '🔁 ${m.pointsARevoir} ${c.s('lbl_points_a_revoir_total')}' : pasCommence,
                onTap: () => ouvrirEcran(context, EcranCaravane(ac: ac)),
              ),
              if (ac.config.surOuvrirHote != null)
                TuileMadrassa(
                  icone: Icons.menu_book,
                  titre: c.m('titre_coran'),
                  description: c.m('desc_coran'),
                  onTap: () => ac.config.surOuvrirHote!('CORAN'),
                ),
            ],
          );
        },
      ),
    );
  }
}

// ------------------------------------------------------------- Encyclopédie

class EcranEncyclopedie extends StatelessWidget {
  const EcranEncyclopedie({super.key, required this.ac});

  final ControleurAlAnsar ac;

  @override
  Widget build(BuildContext context) {
    final m = ac.madrassa!;
    final c = m.contenu;
    final categories = c.categories;
    final badges = mapDe(c.encyclopedie['badges']);
    return Scaffold(
      appBar: barreHayaati(c.m('titre_encyclopedie', 'Encyclopédie'), integre: ac.config.integre),
      body: ListenableBuilder(
        listenable: m,
        builder: (context, _) {
          final theme = Theme.of(context);
          final badge = badgeActuel(m.perles);
          final prochain = prochainPalier(m.perles);
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text(c.e('titre'), style: theme.textTheme.titleMedium?.copyWith(fontFamilyFallback: reserveArabe)),
              if (c.e('consigne').isNotEmpty) Padding(padding: const EdgeInsets.only(top: 6), child: Text(c.e('consigne'))),
              const SizedBox(height: 12),
              CarteHayaati(
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(texteDe(badges[badge.cle], badge.libelle), style: theme.textTheme.titleSmall),
                      Text('✨ ${m.perles} ${c.m('lbl_perles')}'),
                      Text(formaterGabarit(c.e('progres_lecture'), <Object>[m.jeu.lus.length, categories.length])),
                      if (prochain != null)
                        Text(
                          formaterGabarit(
                            c.e('lbl_encore_x_bonnes_reponses'),
                            <Object>[prochain.manque, texteDe(badges[prochain.palier.cle], prochain.palier.libelle)],
                          ),
                          style: theme.textTheme.bodySmall,
                        ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 8),
              for (var i = 0; i < categories.length; i++)
                CarteHayaati(
                  margin: const EdgeInsets.symmetric(vertical: 4),
                  child: ListTile(
                    title: Text(texteDe(categories[i]['titre']), style: styleCorps(context)),
                    subtitle: Text(
                      '${c.e('lbl_quiz')} : ${questionsMaitriseesCategorie(m.jeu, i).length}/${listeDe(categories[i]['quiz']).length}',
                    ),
                    trailing: m.jeu.lus.contains(i)
                        ? const Icon(Icons.check_circle, color: PaletteHayaati.vertClair)
                        : const Icon(Icons.chevron_right),
                    onTap: () => ouvrirEcran(context, EcranCategorie(ac: ac, index: i)),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}

/// Un thème : texte, case « j'ai lu » et quiz de trois questions.
class EcranCategorie extends StatefulWidget {
  const EcranCategorie({super.key, required this.ac, required this.index});

  final ControleurAlAnsar ac;
  final int index;

  @override
  State<EcranCategorie> createState() => _EcranCategorieState();
}

class _EcranCategorieState extends State<EcranCategorie> {
  bool _quizVisible = false;
  final Map<int, int> _reponses = <int, int>{};

  @override
  Widget build(BuildContext context) {
    final m = widget.ac.madrassa!;
    final c = m.contenu;
    final categorie = c.categories[widget.index];
    final questions = listeDe(categorie['quiz']).map(mapDe).toList();
    return Scaffold(
      appBar: barreHayaati(texteDe(categorie['titre']), integre: widget.ac.config.integre),
      body: ListenableBuilder(
        listenable: m,
        builder: (context, _) {
          final theme = Theme.of(context);
          final maitrisees = questionsMaitriseesCategorie(m.jeu, widget.index);
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              SelectableText(texteDe(categorie['texte']), style: styleCorps(context)),
              CheckboxListTile(
                contentPadding: EdgeInsets.zero,
                value: m.jeu.lus.contains(widget.index),
                title: Text(c.s('tooltip_jai_lu', "J'ai lu ce texte")),
                onChanged: (v) => m.marquerLu(widget.index, v ?? false),
              ),
              if (questions.isNotEmpty)
                TextButton.icon(
                  icon: Icon(_quizVisible ? Icons.expand_less : Icons.quiz),
                  label: Text(_quizVisible ? c.e('lbl_masquer_quiz') : c.e('lbl_quiz')),
                  onPressed: () => setState(() => _quizVisible = !_quizVisible),
                ),
              if (_quizVisible)
                for (var q = 0; q < questions.length; q++)
                  CarteHayaati(
                    margin: const EdgeInsets.symmetric(vertical: 6),
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: _question(context, m, theme, q, questions[q], maitrisees.contains(q)),
                    ),
                  ),
            ],
          );
        },
      ),
    );
  }

  Widget _question(
    BuildContext context,
    dynamic m,
    ThemeData theme,
    int q,
    Map<String, dynamic> question,
    bool dejaMaitrisee,
  ) {
    final choix = listeDe(question['choix']).map((e) => e.toString()).toList();
    final bonne = int.tryParse('${question['reponse']}') ?? -1;
    final choisi = _reponses[q];
    final repondu = choisi != null || dejaMaitrisee;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text('${q + 1}. ${texteDe(question['question'])}', style: theme.textTheme.titleSmall?.copyWith(fontFamilyFallback: reserveArabe)),
        const SizedBox(height: 8),
        for (var i = 0; i < choix.length; i++)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 3),
            child: OutlinedButton(
              style: OutlinedButton.styleFrom(
                alignment: AlignmentDirectional.centerStart,
                backgroundColor: repondu && i == bonne
                    ? PaletteHayaati.vertClair
                    : (choisi == i ? PaletteHayaati.terracottaClair : null),
                foregroundColor: repondu && i == bonne ? PaletteHayaati.blanc : PaletteHayaati.texteFonce,
              ),
              onPressed: repondu
                  ? null
                  : () {
                      setState(() => _reponses[q] = i);
                      m.repondre(widget.index, q, i == bonne);
                    },
              child: Text(choix[i], textAlign: TextAlign.start),
            ),
          ),
        if (repondu && texteDe(question['explication']).isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Text(texteDe(question['explication']), style: theme.textTheme.bodySmall),
          ),
      ],
    );
  }
}
