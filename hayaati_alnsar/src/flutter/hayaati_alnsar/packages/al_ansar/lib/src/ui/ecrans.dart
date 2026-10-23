import 'package:flutter/material.dart';

import '../controleur.dart';
import '../filtres.dart';
import '../geo.dart';
import '../i18n.dart';
import '../modeles.dart';
import '../theme/palette.dart';
import '../theme/theme_hayaati.dart';
import 'ecran_hadj_omra.dart';
import 'ecran_proposition.dart';
import 'outils.dart';

void _pousser(BuildContext context, WidgetBuilder builder) {
  Navigator.of(context).push(MaterialPageRoute<void>(builder: builder));
}

String _lieu(ControleurAlAnsar c, Fiche f) => <String>[
      c.nomVille(f.villeId),
      if (f.quartier != null) f.quartier!,
    ].join(' · ');

// ---------------------------------------------------------------- Accueil

const Map<String, IconData> _icones = <String, IconData>{
  'apps': Icons.apps,
  'menu_book': Icons.menu_book,
  'school': Icons.school,
  'mosque': Icons.mosque,
  'explore': Icons.explore,
  'flight': Icons.flight_takeoff,
};

class EcranAccueil extends StatelessWidget {
  const EcranAccueil({super.key, required this.c});

  final ControleurAlAnsar c;

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: c,
      builder: (context, _) {
        final t = c.t;
        final a = c.annuaire;
        final hadjActif = a != null && (a.modulesActifs.contains('hadj_omra') || a.forfaits.isNotEmpty);
        return Scaffold(
          appBar: c.config.integre ? null : barreHayaati('HAYAATI', avecIcone: true),
          body: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text(
                  t('titre'),
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                        color: PaletteHayaati.vertProfond,
                        fontWeight: FontWeight.bold,
                      ),
                ),
              ),
              BandeauLieu(c: c),
              if (c.chargement) const LinearProgressIndicator(),
              if (c.indisponible && !c.chargement)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  child: Text(t('hors_ligne')),
                ),
              const SizedBox(height: 8),
              for (final r in c.config.raccourcisHote)
                _Tuile(
                  icone: _icones[r.icone] ?? Icons.apps,
                  titre: r.titre,
                  onTap: () => c.config.surOuvrirHote?.call(r.cle),
                ),
              _Tuile(
                icone: Icons.menu_book,
                titre: t('apprendre'),
                onTap: () => _pousser(
                  context,
                  (_) => EcranListe(c: c, titre: t('apprendre'), types: const {'madrassa'}),
                ),
              ),
              _Tuile(
                icone: Icons.storefront,
                titre: t('boutique'),
                onTap: () => _pousser(
                  context,
                  (_) => EcranListe(
                    c: c,
                    titre: t('boutique'),
                    types: const {'librairie', 'boutique', 'artisan'},
                  ),
                ),
              ),
              _Tuile(
                icone: Icons.support_agent,
                titre: t('accompagnement'),
                onTap: () => _pousser(
                  context,
                  (_) => EcranListe(c: c, titre: t('accompagnement'), types: const {'specialiste'}),
                ),
              ),
              if (hadjActif)
                _Tuile(
                  icone: Icons.flight_takeoff,
                  titre: t('hadj_omra'),
                  onTap: () => _pousser(context, (_) => EcranHadjOmra(c: c)),
                ),
              _Tuile(
                icone: Icons.mosque,
                titre: t('mosquees'),
                onTap: () => _pousser(context, (_) => EcranMosquees(c: c)),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _Tuile extends StatelessWidget {
  const _Tuile({required this.icone, required this.titre, required this.onTap});

  final IconData icone;
  final String titre;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return CarteHayaati(
      child: ListTile(
        minVerticalPadding: 20,
        leading: Icon(icone, size: 32, color: PaletteHayaati.vertProfond),
        title: Text(titre, style: Theme.of(context).textTheme.titleMedium),
        trailing: const Icon(Icons.chevron_right),
        onTap: onTap,
      ),
    );
  }
}

// ------------------------------------------------------- Lieu (« ailleurs »)

/// Bandeau du lieu de recherche : « Autour de moi », une ville ou tout le pays.
class BandeauLieu extends StatelessWidget {
  const BandeauLieu({super.key, required this.c});

  final ControleurAlAnsar c;

  @override
  Widget build(BuildContext context) {
    final t = c.t;
    final String lieu;
    if (c.mode == ModeLieu.autourDeMoi) {
      final precision = c.positionGps?.precisionM;
      lieu = precision == null
          ? t('autour_de_moi')
          : '${t('autour_de_moi')} · ±${precision.round()} m';
    } else if (c.mode == ModeLieu.ville && c.config.villeId != null) {
      lieu = c.nomVille(c.config.villeId!);
    } else {
      lieu = t('toutes_villes');
    }
    final erreur = c.erreurPosition;
    String? sousTitre;
    if (c.chargementPosition) {
      sousTitre = t('chargement');
    } else if (erreur != null) {
      sousTitre = messageErreurPosition(t, erreur);
    }
    return CarteHayaati(
      child: ListTile(
        leading: Icon(
          c.mode == ModeLieu.autourDeMoi ? Icons.my_location : Icons.place,
          color: PaletteHayaati.vertProfond,
        ),
        title: Text('$lieu · ${c.nomPays(c.config.pays)}'),
        subtitle: sousTitre == null ? null : Text(sousTitre),
        trailing: TextButton(
          onPressed: () => showModalBottomSheet<void>(
            context: context,
            isScrollControlled: true,
            useRootNavigator: false,
            builder: (_) => SelecteurLieu(c: c),
          ),
          child: Text(t('changer')),
        ),
      ),
    );
  }
}

class SelecteurLieu extends StatelessWidget {
  const SelecteurLieu({super.key, required this.c});

  final ControleurAlAnsar c;

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: c,
      builder: (context, _) {
        final t = c.t;
        final villes = c.annuaire?.villes ?? const <Ville>[];
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(t('chercher_ailleurs'), style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 12),
                Text(t('pays')),
                DropdownButton<String>(
                  isExpanded: true,
                  value: c.paysDisponibles.contains(c.config.pays) ? c.config.pays : null,
                  items: <DropdownMenuItem<String>>[
                    for (final p in c.paysDisponibles)
                      DropdownMenuItem<String>(value: p, child: Text(c.nomPays(p))),
                  ],
                  onChanged: (p) {
                    if (p != null) c.changerLieu(pays: p);
                  },
                ),
                const SizedBox(height: 12),
                Text(t('ville')),
                if (c.chargement) const LinearProgressIndicator(),
                Flexible(
                  child: ListView(
                    shrinkWrap: true,
                    children: [
                      ListTile(
                        leading: const Icon(Icons.my_location, color: PaletteHayaati.vertProfond),
                        title: Text(t('autour_de_moi')),
                        selected: c.mode == ModeLieu.autourDeMoi,
                        onTap: () {
                          c.choisirAutourDeMoi();
                          Navigator.of(context).pop();
                        },
                      ),
                      ListTile(
                        title: Text(t('toutes_villes')),
                        selected: c.mode == ModeLieu.pays,
                        onTap: () {
                          c.changerLieu(toutesVilles: true);
                          Navigator.of(context).pop();
                        },
                      ),
                      for (final v in villes)
                        ListTile(
                          title: Text(choisir(v.nom, c.config.langue)),
                          subtitle: v.region == null ? null : Text(v.region!),
                          selected: c.mode == ModeLieu.ville && c.config.villeId == v.id,
                          onTap: () {
                            c.changerLieu(villeId: v.id);
                            Navigator.of(context).pop();
                          },
                        ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

// ------------------------------------------------------------------ Listes

class EcranListe extends StatefulWidget {
  const EcranListe({super.key, required this.c, required this.titre, required this.types});

  final ControleurAlAnsar c;
  final String titre;
  final Set<String> types;

  @override
  State<EcranListe> createState() => _EcranListeState();
}

class _EcranListeState extends State<EcranListe> {
  bool _verifies = false;
  bool _aDistance = false;
  int? _rayonKm = 50;

  @override
  Widget build(BuildContext context) {
    final c = widget.c;
    return ListenableBuilder(
      listenable: c,
      builder: (context, _) {
        final t = c.t;
        final autour = c.mode == ModeLieu.autourDeMoi;
        final entrees = c.fiches(
          widget.types,
          filtre: FiltreFiches(niveauMin: _verifies ? 1 : 0, aDistance: _aDistance),
          rayonKm: autour ? _rayonKm?.toDouble() : null,
        );
        return Scaffold(
          appBar: barreHayaati(widget.titre, integre: c.config.integre),
          body: Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
                child: BandeauLieu(c: c),
              ),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Wrap(
                  spacing: 8,
                  children: [
                    FilterChip(
                      label: Text(t('verifie')),
                      selected: _verifies,
                      onSelected: (v) => setState(() => _verifies = v),
                    ),
                    FilterChip(
                      label: Text(t('a_distance')),
                      selected: _aDistance,
                      onSelected: (v) => setState(() => _aDistance = v),
                    ),
                    if (autour)
                      for (final k in const <int?>[10, 50, 200, null])
                        ChoiceChip(
                          label: Text(k == null ? t('tous_rayons') : '$k km'),
                          selected: _rayonKm == k,
                          onSelected: (_) => setState(() => _rayonKm = k),
                        ),
                  ],
                ),
              ),
              if (c.chargement) const LinearProgressIndicator(),
              Expanded(
                child: entrees.isEmpty
                    ? Center(child: Text(t('aucun')))
                    : ListView.builder(
                        itemCount: entrees.length,
                        itemBuilder: (context, i) => _CarteFiche(c: c, entree: entrees[i]),
                      ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _CarteFiche extends StatelessWidget {
  const _CarteFiche({required this.c, required this.entree});

  final ControleurAlAnsar c;
  final EntreeFiche entree;

  @override
  Widget build(BuildContext context) {
    final t = c.t;
    final fiche = entree.fiche;
    final d = entree.distanceM;
    final ligne = <String>[
      _lieu(c, fiche),
      if (d != null) formaterDistance(d),
      if (entree.aDistance) t('a_distance'),
    ].join(' · ');
    return CarteHayaati(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: ListTile(
        title: Text(fiche.nom),
        subtitle: Text(ligne),
        trailing: fiche.niveau >= 1
            ? Tooltip(
                message: t('verifie'),
                child: const Icon(Icons.verified, size: 20, color: PaletteHayaati.vertClair),
              )
            : null,
        onTap: () => _pousser(
          context,
          (_) => fiche.type == 'madrassa'
              ? EcranFicheMadrassa(c: c, fiche: fiche)
              : EcranFicheGenerique(c: c, fiche: fiche),
        ),
      ),
    );
  }
}

// ----------------------------------------------------------- Fiche madrassa

class EcranFicheMadrassa extends StatefulWidget {
  const EcranFicheMadrassa({super.key, required this.c, required this.fiche});

  final ControleurAlAnsar c;
  final Fiche fiche;

  @override
  State<EcranFicheMadrassa> createState() => _EcranFicheMadrassaState();
}

class _EcranFicheMadrassaState extends State<EcranFicheMadrassa> {
  GroupeCours _groupe = GroupeCours.parPublic;

  @override
  Widget build(BuildContext context) {
    final c = widget.c;
    final f = widget.fiche;
    return ListenableBuilder(
      listenable: c,
      builder: (context, _) {
        final t = c.t;
        final cours =
            (c.annuaire?.cours ?? const <Cours>[]).where((x) => x.ficheId == f.id).toList();
        final groupes = grouperCours(cours, _groupe);
        final theme = Theme.of(context);
        return Scaffold(
          appBar: barreHayaati(f.nom, integre: c.config.integre),
          body: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text(_lieu(c, f), style: theme.textTheme.bodyMedium),
              if (f.description.isNotEmpty) ...[
                const SizedBox(height: 8),
                Text(choisir(f.description, c.config.langue)),
              ],
              const SizedBox(height: 12),
              _Etiquettes(titre: t('public'), valeurs: f.madrassa.publics.map(t.call).toList()),
              const SizedBox(height: 6),
              _Etiquettes(titre: t('disciplines'), valeurs: f.madrassa.disciplines.map(t.call).toList()),
              const Divider(height: 32),
              Text(t('classes'), style: theme.textTheme.titleMedium),
              const SizedBox(height: 8),
              SegmentedButton<GroupeCours>(
                segments: <ButtonSegment<GroupeCours>>[
                  ButtonSegment<GroupeCours>(
                    value: GroupeCours.parPublic,
                    label: Text(t('par_public')),
                  ),
                  ButtonSegment<GroupeCours>(
                    value: GroupeCours.parJour,
                    label: Text(t('par_jour')),
                  ),
                ],
                selected: <GroupeCours>{_groupe},
                onSelectionChanged: (s) => setState(() => _groupe = s.first),
              ),
              for (final e in groupes.entries) ...[
                Padding(
                  padding: const EdgeInsets.only(top: 16, bottom: 4),
                  child: Text(t(e.key), style: theme.textTheme.titleSmall),
                ),
                for (final k in e.value) CarteCours(c: c, cours: k),
              ],
              if (f.whatsapp != null) ...[
                const SizedBox(height: 16),
                FilledButton.icon(
                  style: FilledButton.styleFrom(
                    backgroundColor: PaletteHayaati.terracotta,
                    foregroundColor: PaletteHayaati.blanc,
                  ),
                  icon: const Icon(Icons.chat),
                  label: Text(t('contacter')),
                  onPressed: () => ouvrirWhatsApp(
                    f.whatsapp!,
                    t('msg_contact').replaceAll('{nom}', f.nom),
                  ),
                ),
              ],
            ],
          ),
        );
      },
    );
  }
}

class _Etiquettes extends StatelessWidget {
  const _Etiquettes({required this.titre, required this.valeurs});

  final String titre;
  final List<String> valeurs;

  @override
  Widget build(BuildContext context) {
    if (valeurs.isEmpty) return const SizedBox.shrink();
    return Wrap(
      spacing: 6,
      runSpacing: 6,
      crossAxisAlignment: WrapCrossAlignment.center,
      children: [
        Text('$titre :'),
        for (final v in valeurs) Chip(label: Text(v), visualDensity: VisualDensity.compact),
      ],
    );
  }
}

class CarteCours extends StatelessWidget {
  const CarteCours({super.key, required this.c, required this.cours});

  final ControleurAlAnsar c;
  final Cours cours;

  String _tarif(Textes t) {
    if (cours.gratuit) return t('gratuit');
    final m = cours.montant;
    if (m == null) return '';
    final unite = t(cours.periodicite == 'mois'
        ? 'par_mois'
        : cours.periodicite == 'session'
            ? 'par_session'
            : 'par_cours');
    return '${formaterMontant(m)} ${cours.devise ?? ''} $unite'.trim();
  }

  @override
  Widget build(BuildContext context) {
    final t = c.t;
    final theme = Theme.of(context);
    final langue = c.config.langue;
    final pre = cours.preinscrits;
    final seuil = cours.seuilMin;
    return CarteHayaati(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(choisir(cours.sujet, langue), style: theme.textTheme.titleSmall),
            const SizedBox(height: 4),
            Text('${cours.jours.map(t.call).join(', ')} · ${cours.debut}–${cours.fin}'),
            if (cours.noteHoraire.isNotEmpty)
              Text(choisir(cours.noteHoraire, langue), style: theme.textTheme.bodySmall),
            Text(_tarif(t)),
            Text(t(cours.statut), style: theme.textTheme.bodySmall),
            if (cours.statut == 'ouvert_preinscriptions' && pre != null && seuil != null) ...[
              const SizedBox(height: 8),
              LinearProgressIndicator(
                value: (pre / seuil).clamp(0.0, 1.0).toDouble(),
                minHeight: 8,
                color: PaletteHayaati.ocre,
                backgroundColor: PaletteHayaati.ocreClair,
              ),
              const SizedBox(height: 4),
              Text('$pre / $seuil ${t('preinscrits')}'),
              if (cours.dateLimite != null) Text('${t('date_limite')} : ${cours.dateLimite}'),
            ],
          ],
        ),
      ),
    );
  }
}

// ------------------------------------------------------------ Fiche générique

class EcranFicheGenerique extends StatelessWidget {
  const EcranFicheGenerique({super.key, required this.c, required this.fiche});

  final ControleurAlAnsar c;
  final Fiche fiche;

  @override
  Widget build(BuildContext context) {
    final t = c.t;
    final langue = c.config.langue;
    final articles =
        (c.annuaire?.articles ?? const <Article>[]).where((a) => a.ficheId == fiche.id);
    final prestations =
        (c.annuaire?.prestations ?? const <Prestation>[]).where((p) => p.ficheId == fiche.id);
    return Scaffold(
      appBar: barreHayaati(fiche.nom, integre: c.config.integre),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(_lieu(c, fiche)),
          if (fiche.description.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(choisir(fiche.description, langue)),
          ],
          for (final a in articles)
            ListTile(
              contentPadding: EdgeInsets.zero,
              title: Text(choisir(a.nom, langue)),
              subtitle: Text(<String>[
                if (a.montant != null) '${formaterMontant(a.montant!)} ${a.devise ?? ''}'.trim(),
                t(a.disponibilite),
                if (a.avertissementSante) t('avert_sante'),
              ].join(' · ')),
            ),
          for (final p in prestations)
            ListTile(
              contentPadding: EdgeInsets.zero,
              title: Text(t(p.besoin)),
              subtitle: Text(_tarifPrestation(t, p)),
            ),
          if (fiche.whatsapp != null) ...[
            const SizedBox(height: 16),
            FilledButton.icon(
                  style: FilledButton.styleFrom(
                    backgroundColor: PaletteHayaati.terracotta,
                    foregroundColor: PaletteHayaati.blanc,
                  ),
              icon: const Icon(Icons.chat),
              label: Text(t('contacter')),
              onPressed: () => ouvrirWhatsApp(
                fiche.whatsapp!,
                t('msg_contact').replaceAll('{nom}', fiche.nom),
              ),
            ),
          ],
        ],
      ),
    );
  }

  String _tarifPrestation(Textes t, Prestation p) {
    final d = p.devise ?? '';
    switch (p.typeTarif) {
      case 'gratuit':
        return t('gratuit');
      case 'fixe':
        return '${formaterMontant(p.min ?? 0)} $d'.trim();
      case 'fourchette':
        return '${formaterMontant(p.min ?? 0)} à ${formaterMontant(p.max ?? 0)} $d'.trim();
      default:
        return t('sur_devis');
    }
  }
}

// ---------------------------------------------------------- Mosquées proches

class EcranMosquees extends StatefulWidget {
  const EcranMosquees({super.key, required this.c});

  final ControleurAlAnsar c;

  @override
  State<EcranMosquees> createState() => _EcranMosqueesState();
}

class _EcranMosqueesState extends State<EcranMosquees> {
  int _rayonKm = 5;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final c = widget.c;
      // Voyageur : sans choix manuel d'une ville, on part de la position GPS.
      if (c.mode != ModeLieu.autourDeMoi && !c.lieuManuel && c.config.fournisseurPosition != null) {
        c.choisirAutourDeMoi();
      }
      c.chargerMosquees();
    });
  }

  @override
  Widget build(BuildContext context) {
    final c = widget.c;
    return ListenableBuilder(
      listenable: c,
      builder: (context, _) {
        final t = c.t;
        final pos = c.positionEffective;
        final base = c.mosquees;
        final Widget corps;
        if (pos == null) {
          corps = Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    c.erreurPosition == null
                        ? t('position_absente')
                        : messageErreurPosition(t, c.erreurPosition!),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 12),
                  FilledButton.icon(
                    icon: const Icon(Icons.my_location),
                    label: Text(t('autour_de_moi')),
                    onPressed: c.choisirAutourDeMoi,
                  ),
                ],
              ),
            ),
          );
        } else if (base == null) {
          corps = c.chargement
              ? const Center(child: CircularProgressIndicator())
              : Center(child: Text(t('hors_ligne')));
        } else {
          final res = plusProches<Fiche>(
            base.fiches.where((f) => f.type == 'mosquee' && c.visible(f)),
            pos,
            (f) => f.gps,
            max: 30,
            rayonMaxM: _rayonKm * 1000.0,
          );
          corps = res.isEmpty
              ? Center(child: Text(t('aucun')))
              : ListView.builder(
                  itemCount: res.length + 1,
                  itemBuilder: (context, i) {
                    if (i == res.length) {
                      return Padding(
                        padding: const EdgeInsets.all(16),
                        child: Text(
                          base.attribution ?? '',
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      );
                    }
                    return _LigneMosquee(c: c, r: res[i]);
                  },
                );
        }
        return Scaffold(
          appBar: barreHayaati(
            t('mosquees'),
            integre: c.config.integre,
            actions: [
              IconButton(
                icon: const Icon(Icons.add_location_alt),
                tooltip: t('proposer_mosquee'),
                onPressed: () => _pousser(context, (_) => EcranProposition(c: c)),
              ),
            ],
          ),
          body: Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
                child: BandeauLieu(c: c),
              ),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                child: SegmentedButton<int>(
                  segments: <ButtonSegment<int>>[
                    for (final k in const <int>[1, 5, 20, 50])
                      ButtonSegment<int>(value: k, label: Text('$k km')),
                  ],
                  selected: <int>{_rayonKm},
                  onSelectionChanged: (s) => setState(() => _rayonKm = s.first),
                ),
              ),
              if (pos != null && c.positionEstVille)
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: Text(t('centre_ville'), style: Theme.of(context).textTheme.bodySmall),
                ),
              Expanded(child: corps),
            ],
          ),
        );
      },
    );
  }
}

class _LigneMosquee extends StatelessWidget {
  const _LigneMosquee({required this.c, required this.r});

  final ControleurAlAnsar c;
  final Resultat<Fiche> r;

  @override
  Widget build(BuildContext context) {
    final t = c.t;
    final f = r.item;
    final m = f.mosquee;
    final ligne1 = <String>[
      formaterDistance(r.distanceM),
      t('cap_${pointCardinal(r.capDeg)}'),
      if (!f.gpsVerifiee) t('position_a_verifier'),
    ].join(' · ');
    final ligne2 = <String>[
      if (m.jumuaHeure != null) '${t('jumua')} ${m.jumuaHeure}',
      if (m.femmes == 'oui') t('espace_femmes'),
      if (m.ablutions == 'oui') t('ablutions'),
    ].join(' · ');
    return CarteHayaati(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: ListTile(
        isThreeLine: ligne2.isNotEmpty,
        leading: const Icon(Icons.mosque, color: PaletteHayaati.vertProfond),
        title: Text(f.nom),
        subtitle: Text(ligne2.isEmpty ? ligne1 : '$ligne1\n$ligne2'),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            IconButton(
              icon: const Icon(Icons.directions),
              tooltip: t('itineraire'),
              onPressed: () {
                final p = f.gps;
                if (p != null) ouvrirItineraire(p.lat, p.lon, f.nom);
              },
            ),
            PopupMenuButton<String>(
              onSelected: (v) {
                if (v == 'corriger') {
                  _pousser(context, (_) => EcranProposition(c: c, mosquee: f));
                }
              },
              itemBuilder: (_) => <PopupMenuEntry<String>>[
                PopupMenuItem<String>(value: 'corriger', child: Text(t('corriger_position'))),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
