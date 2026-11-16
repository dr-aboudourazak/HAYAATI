import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../controleur.dart';
import '../theme/palette.dart';
import '../theme/theme_hayaati.dart';
import 'contenu.dart';
import 'controleur_madrassa.dart';
import 'moteurs.dart';
import 'widgets_madrassa.dart';

BandeauResume _bandeau(ContenuMadrassa c, ResumeEtape r, {bool compris = false}) => BandeauResume(
      resume: r,
      libelleConnues: c.s(compris ? 'resume_compris' : 'resume_connues'),
      libelleARevoir: c.s('resume_a_revoir'),
      libelleNonVues: c.s('resume_non_vues'),
    );

/// Additionne la progression de plusieurs clés (ex. un temps de conjugaison, une rubrique de grammaire).
ResumeEtape _agreger(ProgresLangue p, Map<String, int> totaux) {
  var c = 0, r = 0, t = 0;
  totaux.forEach((cle, total) {
    final e = p[cle];
    if (e != null) {
      c += e['connues']!.length;
      r += e['a_revoir']!.length;
    }
    t += total;
  });
  return ResumeEtape(c, r, math.max(0, t - c - r), t);
}

/// Clés de progression et nombre de leçons de chaque rubrique d'une étape à leçons.
Map<String, int> _totauxLecons(Map<String, dynamic> etape, String prefixe) {
  final res = <String, int>{};
  final cle = texteDe(etape['cle']);
  final directes = listeDe(etape['lecons']);
  if (directes.isNotEmpty) res['$prefixe$cle'] = directes.length;
  for (final sr in listeDe(etape['sous_rubriques']).map(mapDe)) {
    res['$prefixe${cle}_${texteDe(sr['cle'])}'] = listeDe(sr['lecons']).length;
  }
  return res;
}

// ------------------------------------------------------------- Langue arabe

class EcranLangueArabe extends StatelessWidget {
  const EcranLangueArabe({super.key, required this.ac});

  final ControleurAlAnsar ac;

  ResumeEtape? _stats(ControleurMadrassa m, Map<String, dynamic> e) {
    switch (e['cle']) {
      case 'alphabet':
        return resumeEtape(m.langue, 'alphabet', listeDe(e['lettres']).length);
      case 'vocabulaire':
        final total = listeDe(e['listes']).fold<int>(0, (a, l) => a + listeDe(mapDe(l)['mots']).length);
        return resumeEtape(m.langue, 'vocabulaire', total);
      case 'lecture':
        return resumeEtape(m.langue, 'lecture', listeDe(e['textes']).length);
      case 'conjugaison':
        return _agreger(m.langue, <String, int>{
          for (final t in listeDe(e['temps']).map(mapDe))
            'conjugaison_${texteDe(t['cle'])}': listeDe(t['conjugaisons']).length,
        });
      case 'grammaire':
        final totaux = <String, int>{};
        for (final b in listeDe(e['babs']).map(mapDe)) {
          totaux.addAll(_totauxLecons(b, 'grammaire_'));
        }
        return _agreger(m.langue, totaux);
    }
    return null;
  }

  Widget? _ecran(Map<String, dynamic> e) {
    switch (e['cle']) {
      case 'alphabet':
        return EcranAlphabet(ac: ac, etape: e);
      case 'vocabulaire':
        return EcranVocabulaire(ac: ac, etape: e);
      case 'conjugaison':
        return EcranConjugaison(ac: ac, etape: e);
      case 'grammaire':
        return EcranGrammaire(ac: ac, etape: e);
      case 'lecture':
        return EcranLecture(ac: ac, etape: e);
      case 'caravane':
        return EcranCaravane(ac: ac);
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final m = ac.madrassa!;
    final c = m.contenu;
    return Scaffold(
      appBar: barreHayaati(c.m('titre_langue_arabe', 'Langue arabe'), integre: ac.config.integre),
      body: ListenableBuilder(
        listenable: m,
        builder: (context, _) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(texteDe(c.langueArabe['titre']), style: Theme.of(context).textTheme.titleMedium),
            if (texteDe(c.langueArabe['sous_titre']).isNotEmpty)
              Padding(padding: const EdgeInsets.only(top: 4), child: Text(texteDe(c.langueArabe['sous_titre']))),
            const SizedBox(height: 8),
            for (final e in c.etapesLangue)
              _CarteEtape(
                titre: texteDe(e['titre']),
                resume: _stats(m, e),
                contenu: c,
                onTap: () {
                  final ecran = e['disponible'] == true ? _ecran(e) : null;
                  if (ecran == null) {
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(c.s('etape_bientot_disponible'))));
                  } else {
                    ouvrirEcran(context, ecran);
                  }
                },
              ),
          ],
        ),
      ),
    );
  }
}

class _CarteEtape extends StatelessWidget {
  const _CarteEtape({required this.titre, required this.resume, required this.contenu, required this.onTap});

  final String titre;
  final ResumeEtape? resume;
  final ContenuMadrassa contenu;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return CarteHayaati(
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(titre, style: Theme.of(context).textTheme.titleSmall?.copyWith(fontFamilyFallback: reserveArabe)),
              if (resume != null) ...[
                const SizedBox(height: 6),
                _bandeau(contenu, resume!),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

// --------------------------------------------------------------- Alphabet

class EcranAlphabet extends StatelessWidget {
  const EcranAlphabet({super.key, required this.ac, required this.etape});

  final ControleurAlAnsar ac;
  final Map<String, dynamic> etape;

  @override
  Widget build(BuildContext context) {
    final m = ac.madrassa!;
    final c = m.contenu;
    final lettres = listeDe(etape['lettres']).map(mapDe).toList();
    return Scaffold(
      appBar: barreHayaati(texteDe(etape['titre']), integre: ac.config.integre),
      body: ListenableBuilder(
        listenable: m,
        builder: (context, _) => Column(
          children: [
            Padding(
              padding: const EdgeInsets.all(12),
              child: _bandeau(c, resumeEtape(m.langue, 'alphabet', lettres.length)),
            ),
            Expanded(
              child: GridView.builder(
                padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 4,
                  mainAxisSpacing: 8,
                  crossAxisSpacing: 8,
                  childAspectRatio: 0.85,
                ),
                itemCount: lettres.length,
                itemBuilder: (context, i) {
                  final etat = m.etatLangue('alphabet', i);
                  final fond = etat == 'connu'
                      ? PaletteHayaati.vertClair
                      : (etat == 'a_revoir' ? PaletteHayaati.ocreClair : PaletteHayaati.blanc);
                  final encre = etat == 'connu' ? PaletteHayaati.blanc : PaletteHayaati.texteFonce;
                  return InkWell(
                    borderRadius: BorderRadius.circular(10),
                    onTap: () => ouvrirEcran(context, EcranLettre(ac: ac, lettres: lettres, index: i)),
                    child: Ink(
                      decoration: BoxDecoration(
                        color: fond,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: const Color(0xFFE5E7EB)),
                      ),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          TexteArabe(texteDe(lettres[i]['lettre']), taille: 34, centre: true, couleur: encre),
                          Text(
                            texteDe(lettres[i]['nom']),
                            style: TextStyle(fontSize: 11, color: encre),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class EcranLettre extends StatefulWidget {
  const EcranLettre({super.key, required this.ac, required this.lettres, required this.index});

  final ControleurAlAnsar ac;
  final List<Map<String, dynamic>> lettres;
  final int index;

  @override
  State<EcranLettre> createState() => _EcranLettreState();
}

class _EcranLettreState extends State<EcranLettre> {
  late int _i = widget.index;

  @override
  Widget build(BuildContext context) {
    final m = widget.ac.madrassa!;
    final c = m.contenu;
    final l = widget.lettres[_i];
    final theme = Theme.of(context);
    final occurrences = listeDe(l['occurrences']).map(mapDe).toList();
    return Scaffold(
      appBar: barreHayaati(texteDe(l['nom']), integre: widget.ac.config.integre),
      body: ListenableBuilder(
        listenable: m,
        builder: (context, _) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Center(child: TexteArabe(texteDe(l['lettre']), taille: 96, centre: true)),
            Center(child: BoutonsMarquage(
              etat: m.etatLangue('alphabet', _i),
              surOui: () => m.marquerLangue('alphabet', '$_i', true),
              surNon: () => m.marquerLangue('alphabet', '$_i', false),
              tooltipOui: c.s('tooltip_je_connais'),
              tooltipNon: c.s('tooltip_a_revoir'),
            )),
            _ligne(c.s('label_translitteration'), texteDe(l['translitteration']), theme),
            _ligne(c.s('label_connexion'), texteDe(l['connexion']), theme),
            _ligne('', texteDe(l['son']), theme),
            if (texteDe(c.langueArabe['avertissement_audio']).isNotEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 8),
                child: Text(texteDe(c.langueArabe['avertissement_audio']), style: theme.textTheme.bodySmall),
              ),
            for (final o in occurrences)
              ListTile(
                dense: true,
                contentPadding: EdgeInsets.zero,
                leading: Text(texteDe(o['position']), style: theme.textTheme.bodySmall),
                title: Align(alignment: AlignmentDirectional.centerStart, child: TexteArabe(texteDe(o['mot']), taille: 22)),
                subtitle: Text('${texteDe(o['translitteration'])} · ${texteDe(o['sens'])}'),
              ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                IconButton(
                  onPressed: _i > 0 ? () => setState(() => _i--) : null,
                  icon: const Icon(Icons.chevron_left),
                ),
                Text('${_i + 1} / ${widget.lettres.length}'),
                IconButton(
                  onPressed: _i < widget.lettres.length - 1 ? () => setState(() => _i++) : null,
                  icon: const Icon(Icons.chevron_right),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _ligne(String libelle, String valeur, ThemeData theme) {
    if (valeur.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Text.rich(
        TextSpan(
          children: [
            if (libelle.isNotEmpty) TextSpan(text: '$libelle : ', style: const TextStyle(fontWeight: FontWeight.w600)),
            TextSpan(text: valeur),
          ],
        ),
        style: styleCorps(context),
      ),
    );
  }
}

// ------------------------------------------------------------- Vocabulaire

class EcranVocabulaire extends StatelessWidget {
  const EcranVocabulaire({super.key, required this.ac, required this.etape});

  final ControleurAlAnsar ac;
  final Map<String, dynamic> etape;

  @override
  Widget build(BuildContext context) {
    final m = ac.madrassa!;
    final c = m.contenu;
    final listes = listeDe(etape['listes']).map(mapDe).toList();
    final total = listes.fold<int>(0, (a, l) => a + listeDe(l['mots']).length);
    return Scaffold(
      appBar: barreHayaati(texteDe(etape['titre']), integre: ac.config.integre),
      body: ListenableBuilder(
        listenable: m,
        builder: (context, _) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _bandeau(c, resumeEtape(m.langue, 'vocabulaire', total)),
            for (var i = 0; i < listes.length; i++) ...[
              Padding(
                padding: const EdgeInsets.only(top: 16, bottom: 4),
                child: Text(texteDe(listes[i]['titre']), style: Theme.of(context).textTheme.titleSmall),
              ),
              for (var j = 0; j < listeDe(listes[i]['mots']).length; j++)
                _MotVocabulaire(
                  m: m,
                  mot: mapDe(listeDe(listes[i]['mots'])[j]),
                  identifiant: 'liste${i}_mot$j',
                ),
            ],
          ],
        ),
      ),
    );
  }
}

class _MotVocabulaire extends StatelessWidget {
  const _MotVocabulaire({required this.m, required this.mot, required this.identifiant});

  final ControleurMadrassa m;
  final Map<String, dynamic> mot;
  final String identifiant;

  @override
  Widget build(BuildContext context) {
    final c = m.contenu;
    return CarteHayaati(
      margin: const EdgeInsets.symmetric(vertical: 3),
      child: ListTile(
        leading: Text(texteDe(mot['icone']), style: const TextStyle(fontSize: 24)),
        title: Align(alignment: AlignmentDirectional.centerStart, child: TexteArabe(texteDe(mot['arabe']), taille: 24)),
        subtitle: Text('${texteDe(mot['translitteration'])} · ${texteDe(mot['sens'])}'),
        trailing: BoutonsMarquage(
          etat: m.etatLangue('vocabulaire', identifiant),
          surOui: () => m.marquerLangue('vocabulaire', identifiant, true),
          surNon: () => m.marquerLangue('vocabulaire', identifiant, false),
          tooltipOui: c.s('tooltip_je_connais'),
          tooltipNon: c.s('tooltip_a_revoir'),
        ),
      ),
    );
  }
}

// ------------------------------------------------------------- Conjugaison

class EcranConjugaison extends StatefulWidget {
  const EcranConjugaison({super.key, required this.ac, required this.etape});

  final ControleurAlAnsar ac;
  final Map<String, dynamic> etape;

  @override
  State<EcranConjugaison> createState() => _EcranConjugaisonState();
}

class _EcranConjugaisonState extends State<EcranConjugaison> {
  int _temps = 0;

  @override
  Widget build(BuildContext context) {
    final m = widget.ac.madrassa!;
    final c = m.contenu;
    final etape = widget.etape;
    final temps = listeDe(etape['temps']).map(mapDe).toList();
    final modele = mapDe(etape['verbe_modele']);
    final theme = Theme.of(context);
    return Scaffold(
      appBar: barreHayaati(texteDe(etape['titre']), integre: widget.ac.config.integre),
      body: ListenableBuilder(
        listenable: m,
        builder: (context, _) {
          final t = temps.isEmpty ? <String, dynamic>{} : temps[_temps];
          final cleEtape = 'conjugaison_${texteDe(t['cle'])}';
          final lignes = listeDe(t['conjugaisons']).map(mapDe).toList();
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              if (modele.isNotEmpty)
                CarteHayaati(
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        TexteArabe(texteDe(modele['forme_base']), taille: 30),
                        Text('${texteDe(modele['racine'])} · ${texteDe(modele['sens'])}', style: styleCorps(context)),
                        if (texteDe(etape['source']).isNotEmpty)
                          Text(texteDe(etape['source']), style: theme.textTheme.bodySmall),
                      ],
                    ),
                  ),
                ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 6,
                children: [
                  for (var i = 0; i < temps.length; i++)
                    ChoiceChip(
                      label: Text(texteDe(temps[i]['titre'])),
                      selected: i == _temps,
                      onSelected: (_) => setState(() => _temps = i),
                    ),
                ],
              ),
              const SizedBox(height: 8),
              _bandeau(c, _agreger(m.langue, <String, int>{cleEtape: lignes.length})),
              for (var i = 0; i < lignes.length; i++)
                CarteHayaati(
                  margin: const EdgeInsets.symmetric(vertical: 3),
                  child: ListTile(
                    title: Row(
                      children: [
                        Expanded(child: TexteArabe(texteDe(lignes[i]['pronom']), taille: 20)),
                        Expanded(child: TexteArabe(texteDe(lignes[i]['forme']), taille: 22)),
                      ],
                    ),
                    subtitle: Text(
                      '${texteDe(lignes[i]['pronom_translitteration'])} ${texteDe(lignes[i]['translitteration'])} · ${texteDe(lignes[i]['sens'])}',
                    ),
                    trailing: BoutonsMarquage(
                      etat: m.etatLangue(cleEtape, '${cleEtape}_$i'),
                      surOui: () => m.marquerLangue(cleEtape, '${cleEtape}_$i', true),
                      surNon: () => m.marquerLangue(cleEtape, '${cleEtape}_$i', false),
                      tooltipOui: c.s('tooltip_je_connais'),
                      tooltipNon: c.s('tooltip_a_revoir'),
                    ),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}

// ---------------------------------------------------------------- Grammaire

class EcranGrammaire extends StatelessWidget {
  const EcranGrammaire({super.key, required this.ac, required this.etape});

  final ControleurAlAnsar ac;
  final Map<String, dynamic> etape;

  @override
  Widget build(BuildContext context) {
    final m = ac.madrassa!;
    final c = m.contenu;
    final babs = listeDe(etape['babs']).map(mapDe).toList();
    return Scaffold(
      appBar: barreHayaati(texteDe(etape['titre']), integre: ac.config.integre),
      body: ListenableBuilder(
        listenable: m,
        builder: (context, _) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            if (texteDe(etape['avertissement_source']).isNotEmpty)
              Text(texteDe(etape['avertissement_source']), style: Theme.of(context).textTheme.bodySmall),
            for (final b in babs)
              _CarteEtape(
                titre: texteDe(b['titre']),
                resume: _agreger(m.langue, _totauxLecons(b, 'grammaire_')),
                contenu: c,
                onTap: () {
                  final sous = listeDe(b['sous_rubriques']).map(mapDe).toList();
                  if (sous.isNotEmpty) {
                    ouvrirEcran(
                      context,
                      EcranSousRubriques(ac: ac, titre: texteDe(b['titre']), sous: sous, cleBase: 'grammaire_${texteDe(b['cle'])}', sciences: false),
                    );
                  } else {
                    ouvrirEcran(
                      context,
                      EcranLecons(ac: ac, titre: texteDe(b['titre']), lecons: listeDe(b['lecons']).map(mapDe).toList(), cleProgres: 'grammaire_${texteDe(b['cle'])}', sciences: false),
                    );
                  }
                },
              ),
          ],
        ),
      ),
    );
  }
}

/// Liste de rubriques (grammaire : sous-catégories d'un bab ; sciences : sous-rubriques du Tawhid).
class EcranSousRubriques extends StatelessWidget {
  const EcranSousRubriques({
    super.key,
    required this.ac,
    required this.titre,
    required this.sous,
    required this.cleBase,
    required this.sciences,
    this.avertissement = '',
  });

  final ControleurAlAnsar ac;
  final String titre;
  final List<Map<String, dynamic>> sous;
  final String cleBase;
  final bool sciences;
  final String avertissement;

  @override
  Widget build(BuildContext context) {
    final m = ac.madrassa!;
    final c = m.contenu;
    final progres = sciences ? m.sciences : m.langue;
    return Scaffold(
      appBar: barreHayaati(titre, integre: ac.config.integre),
      body: ListenableBuilder(
        listenable: m,
        builder: (context, _) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            if (avertissement.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text(avertissement, style: Theme.of(context).textTheme.bodySmall),
              ),
            for (final sr in sous)
              CarteHayaati(
                margin: const EdgeInsets.symmetric(vertical: 4),
                child: InkWell(
                  borderRadius: BorderRadius.circular(12),
                  onTap: () => ouvrirEcran(
                    context,
                    EcranLecons(
                      ac: ac,
                      titre: texteDe(sr['titre']),
                      lecons: listeDe(sr['lecons']).map(mapDe).toList(),
                      cleProgres: '${cleBase}_${texteDe(sr['cle'])}',
                      sciences: sciences,
                    ),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(texteDe(sr['titre']), style: Theme.of(context).textTheme.titleSmall?.copyWith(fontFamilyFallback: reserveArabe)),
                        if (texteDe(sr['description']).isNotEmpty) Text(texteDe(sr['description']), style: Theme.of(context).textTheme.bodySmall),
                        const SizedBox(height: 6),
                        _bandeau(
                          c,
                          resumeEtape(progres, '${cleBase}_${texteDe(sr['cle'])}', listeDe(sr['lecons']).length),
                          compris: true,
                        ),
                      ],
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

/// Leçons une par une (grammaire et sciences islamiques) : explication, chronologie, exemples.
class EcranLecons extends StatefulWidget {
  const EcranLecons({
    super.key,
    required this.ac,
    required this.titre,
    required this.lecons,
    required this.cleProgres,
    required this.sciences,
  });

  final ControleurAlAnsar ac;
  final String titre;
  final List<Map<String, dynamic>> lecons;
  final String cleProgres;

  /// Vrai : progression de sciences islamiques ; faux : progression de langue arabe.
  final bool sciences;

  @override
  State<EcranLecons> createState() => _EcranLeconsState();
}

class _EcranLeconsState extends State<EcranLecons> {
  int _i = 0;

  @override
  Widget build(BuildContext context) {
    final m = widget.ac.madrassa!;
    final c = m.contenu;
    final lecons = widget.lecons;
    final theme = Theme.of(context);
    return Scaffold(
      appBar: barreHayaati(widget.titre, integre: widget.ac.config.integre),
      body: lecons.isEmpty
          ? Center(child: Text(c.s('aucune_lecon')))
          : ListenableBuilder(
              listenable: m,
              builder: (context, _) {
                final l = lecons[_i];
                final progres = widget.sciences ? m.sciences : m.langue;
                final etat = widget.sciences
                    ? m.etatSciences(widget.cleProgres, _i)
                    : m.etatLangue(widget.cleProgres, _i);
                void marquer(bool oui) {
                  if (widget.sciences) {
                    m.marquerSciences(widget.cleProgres, '$_i', oui);
                  } else {
                    m.marquerLangue(widget.cleProgres, '$_i', oui);
                  }
                }
                final chrono = listeDe(l['chronologie']).map(mapDe).toList();
                return ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    _bandeau(c, resumeEtape(progres, widget.cleProgres, lecons.length), compris: true),
                    const SizedBox(height: 8),
                    Text(texteDe(l['titre']), style: theme.textTheme.titleMedium?.copyWith(fontFamilyFallback: reserveArabe)),
                    const SizedBox(height: 8),
                    SelectableText(texteDe(l['explication']), style: styleCorps(context)),
                    if (chrono.isNotEmpty) ...[
                      const SizedBox(height: 12),
                      for (final e in chrono)
                        Padding(
                          padding: const EdgeInsets.symmetric(vertical: 4),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                decoration: BoxDecoration(color: PaletteHayaati.ocreClair, borderRadius: BorderRadius.circular(8)),
                                child: Text(texteDe(e['date']), style: const TextStyle(fontWeight: FontWeight.w600)),
                              ),
                              const SizedBox(width: 8),
                              Expanded(child: Text(texteDe(e['evenement']), style: styleCorps(context))),
                            ],
                          ),
                        ),
                    ],
                    const SizedBox(height: 8),
                    BlocExemples(exemples: listeDe(l['exemples']).map(mapDe).toList()),
                    const SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        IconButton(
                          onPressed: _i > 0 ? () => setState(() => _i--) : null,
                          icon: const Icon(Icons.chevron_left),
                        ),
                        BoutonsMarquage(
                          etat: etat,
                          surOui: () => marquer(true),
                          surNon: () => marquer(false),
                          tooltipOui: c.s('tooltip_jai_compris'),
                          tooltipNon: c.s('tooltip_a_revoir'),
                        ),
                        Text('${_i + 1} / ${lecons.length}'),
                        IconButton(
                          onPressed: _i < lecons.length - 1 ? () => setState(() => _i++) : null,
                          icon: const Icon(Icons.chevron_right),
                        ),
                      ],
                    ),
                  ],
                );
              },
            ),
    );
  }
}

// ------------------------------------------------------------------ Lecture

class EcranLecture extends StatelessWidget {
  const EcranLecture({super.key, required this.ac, required this.etape});

  final ControleurAlAnsar ac;
  final Map<String, dynamic> etape;

  @override
  Widget build(BuildContext context) {
    final m = ac.madrassa!;
    final c = m.contenu;
    final textes = listeDe(etape['textes']).map(mapDe).toList();
    return Scaffold(
      appBar: barreHayaati(texteDe(etape['titre']), integre: ac.config.integre),
      body: ListenableBuilder(
        listenable: m,
        builder: (context, _) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            if (texteDe(etape['consigne']).isNotEmpty) Text(texteDe(etape['consigne'])),
            const SizedBox(height: 8),
            _bandeau(c, resumeEtape(m.langue, 'lecture', textes.length), compris: true),
            for (var i = 0; i < textes.length; i++)
              CarteHayaati(
                margin: const EdgeInsets.symmetric(vertical: 4),
                child: ListTile(
                  title: Text(texteDe(textes[i]['titre']), style: styleCorps(context)),
                  subtitle: Text('${c.s('label_niveau')} : ${texteDe(textes[i]['niveau'])}'),
                  trailing: Icon(
                    m.etatLangue('lecture', i) == 'connu' ? Icons.check_circle : Icons.chevron_right,
                    color: m.etatLangue('lecture', i) == 'connu' ? PaletteHayaati.vertClair : null,
                  ),
                  onTap: () => ouvrirEcran(context, EcranTexte(ac: ac, texte: textes[i], index: i)),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class EcranTexte extends StatelessWidget {
  const EcranTexte({super.key, required this.ac, required this.texte, required this.index});

  final ControleurAlAnsar ac;
  final Map<String, dynamic> texte;
  final int index;

  @override
  Widget build(BuildContext context) {
    final m = ac.madrassa!;
    final c = m.contenu;
    final lignes = listeDe(texte['lignes']).map(mapDe).toList();
    final vocab = listeDe(texte['vocabulaire_nouveau']).map(mapDe).toList();
    final theme = Theme.of(context);
    return Scaffold(
      appBar: barreHayaati(texteDe(texte['titre']), integre: ac.config.integre),
      body: ListenableBuilder(
        listenable: m,
        builder: (context, _) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Center(
              child: BoutonsMarquage(
                etat: m.etatLangue('lecture', index),
                surOui: () => m.marquerLangue('lecture', '$index', true),
                surNon: () => m.marquerLangue('lecture', '$index', false),
                tooltipOui: c.s('tooltip_jai_lu'),
                tooltipNon: c.s('tooltip_a_relire'),
              ),
            ),
            for (final l in lignes)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 6),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    if (texteDe(l['locuteur']).isNotEmpty) Text(texteDe(l['locuteur']), style: theme.textTheme.bodySmall),
                    TexteArabe(texteDe(l['arabe']), taille: 24),
                    Text(texteDe(l['traduction']), style: styleCorps(context)),
                  ],
                ),
              ),
            if (vocab.isNotEmpty) ...[
              const Divider(height: 28),
              Text(c.s('label_vocabulaire_nouveau'), style: theme.textTheme.titleSmall),
              for (final v in vocab)
                ListTile(
                  dense: true,
                  contentPadding: EdgeInsets.zero,
                  title: Align(alignment: AlignmentDirectional.centerStart, child: TexteArabe(texteDe(v['arabe']), taille: 22)),
                  subtitle: Text('${texteDe(v['translitteration'])} · ${texteDe(v['sens'])}'),
                ),
            ],
          ],
        ),
      ),
    );
  }
}

// ------------------------------------------------------- Sciences islamiques

class EcranSciences extends StatelessWidget {
  const EcranSciences({super.key, required this.ac});

  final ControleurAlAnsar ac;

  @override
  Widget build(BuildContext context) {
    final m = ac.madrassa!;
    final c = m.contenu;
    return Scaffold(
      appBar: barreHayaati(c.m('titre_sciences_islamiques', 'Sciences islamiques'), integre: ac.config.integre),
      body: ListenableBuilder(
        listenable: m,
        builder: (context, _) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(texteDe(c.sciences['titre']), style: Theme.of(context).textTheme.titleMedium),
            if (texteDe(c.sciences['sous_titre']).isNotEmpty)
              Padding(padding: const EdgeInsets.only(top: 4), child: Text(texteDe(c.sciences['sous_titre']))),
            if (texteDe(c.sciences['avertissement']).isNotEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 8),
                child: Text(texteDe(c.sciences['avertissement']), style: Theme.of(context).textTheme.bodySmall),
              ),
            for (final e in c.etapesSciences)
              _CarteEtape(
                titre: texteDe(e['titre']),
                resume: _agreger(m.sciences, _totauxLecons(e, 'sciences_')),
                contenu: c,
                onTap: () {
                  if (e['disponible'] != true) {
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(c.s('etape_bientot_disponible'))));
                    return;
                  }
                  final cle = texteDe(e['cle']);
                  final sous = listeDe(e['sous_rubriques']).map(mapDe).toList();
                  if (sous.isNotEmpty) {
                    ouvrirEcran(
                      context,
                      EcranSousRubriques(
                        ac: ac,
                        titre: texteDe(e['titre']),
                        sous: sous,
                        cleBase: 'sciences_$cle',
                        sciences: true,
                        avertissement: '${texteDe(e['avertissement_source'])}\n${texteDe(e['source'])}'.trim(),
                      ),
                    );
                  } else {
                    ouvrirEcran(
                      context,
                      EcranLecons(
                        ac: ac,
                        titre: texteDe(e['titre']),
                        lecons: listeDe(e['lecons']).map(mapDe).toList(),
                        cleProgres: 'sciences_$cle',
                        sciences: true,
                      ),
                    );
                  }
                },
              ),
          ],
        ),
      ),
    );
  }
}

// -------------------------------------------------------- Caravane du Savoir

class EcranCaravane extends StatefulWidget {
  const EcranCaravane({super.key, required this.ac});

  final ControleurAlAnsar ac;

  @override
  State<EcranCaravane> createState() => _EcranCaravaneState();
}

class _EcranCaravaneState extends State<EcranCaravane> {
  late final List<ItemCaravane> _session;
  int _i = 0;
  bool _revele = false;

  @override
  void initState() {
    super.initState();
    final m = widget.ac.madrassa!;
    _session = construireSessionRevision(
      m.combine,
      m.contenu.langueArabe,
      tailleMax: 10,
      contenuSciences: m.contenu.sciences,
    );
  }

  @override
  Widget build(BuildContext context) {
    final m = widget.ac.madrassa!;
    final c = m.contenu;
    final theme = Theme.of(context);
    final termine = _i >= _session.length;
    return Scaffold(
      appBar: barreHayaati(c.m('titre_caravane', 'Caravane du Savoir'), integre: widget.ac.config.integre),
      body: ListenableBuilder(
        listenable: m,
        builder: (context, _) {
          if (_session.isEmpty) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(c.s('msg_caravane_vide_titre'), style: theme.textTheme.titleMedium, textAlign: TextAlign.center),
                    const SizedBox(height: 8),
                    Text(c.s('msg_caravane_vide_corps'), textAlign: TextAlign.center),
                  ],
                ),
              ),
            );
          }
          if (termine) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text(
                  '🔁 ${m.pointsARevoir} ${c.s('lbl_points_a_revoir_total')}',
                  style: theme.textTheme.titleMedium,
                  textAlign: TextAlign.center,
                ),
              ),
            );
          }
          final item = _session[_i];
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text('${_i + 1} / ${_session.length}', textAlign: TextAlign.center, style: theme.textTheme.bodySmall),
              const SizedBox(height: 8),
              Chip(
                label: Text(item.complement ? c.s('badge_deja_connu') : c.s('badge_a_consolider')),
                backgroundColor: item.complement ? PaletteHayaati.ocreClair : PaletteHayaati.terracottaClair,
              ),
              CarteHayaati(
                child: InkWell(
                  borderRadius: BorderRadius.circular(12),
                  onTap: () => setState(() => _revele = true),
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      children: [
                        TexteArabe(item.arabe, taille: 56, centre: true),
                        if (_revele) ...[
                          const SizedBox(height: 12),
                          if (item.translitteration.isNotEmpty)
                            Text(item.translitteration, style: theme.textTheme.titleMedium?.copyWith(fontStyle: FontStyle.italic)),
                          Text(item.sens, style: styleCorps(context, taille: 17), textAlign: TextAlign.center),
                          const SizedBox(height: 6),
                          Text(item.module, style: theme.textTheme.bodySmall),
                        ] else
                          const Padding(padding: EdgeInsets.only(top: 16), child: Icon(Icons.touch_app, color: PaletteHayaati.grisTexte)),
                      ],
                    ),
                  ),
                ),
              ),
              if (_revele)
                Padding(
                  padding: const EdgeInsets.only(top: 12),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      FilledButton.icon(
                        onPressed: () => _repondre(m, item, true),
                        icon: const Icon(Icons.check_circle),
                        label: Text(c.s('tooltip_je_maitrise')),
                      ),
                      const SizedBox(width: 12),
                      FilledButton.tonalIcon(
                        onPressed: () => _repondre(m, item, false),
                        icon: const Icon(Icons.help),
                        label: Text(c.s('tooltip_encore_a_revoir')),
                      ),
                    ],
                  ),
                ),
            ],
          );
        },
      ),
    );
  }

  void _repondre(ControleurMadrassa m, ItemCaravane item, bool connu) {
    m.marquerCaravane(item, connu);
    setState(() {
      _i++;
      _revele = false;
    });
  }
}
