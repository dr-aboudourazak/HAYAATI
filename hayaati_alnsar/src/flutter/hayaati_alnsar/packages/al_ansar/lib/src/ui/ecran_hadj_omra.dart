import 'package:flutter/material.dart';

import '../controleur.dart';
import '../i18n.dart';
import '../modeles.dart';
import '../theme/palette.dart';
import '../theme/theme_hayaati.dart';
import 'ecrans.dart' show BandeauLieu;
import 'outils.dart';

String _ouiNon(Textes t, bool? v) =>
    v == null ? t('non_renseigne') : (v ? t('inclus') : t('non_inclus'));

String _hotel(Textes t, Hotel? h, String cleDu) {
  if (h == null) return t('non_renseigne');
  final etoiles = h.etoiles == null ? '' : ' ${h.etoiles}★';
  final distance = h.distanceM == null ? '' : ' · ${h.distanceM} m ${t(cleDu)}';
  return '${h.nom ?? t('non_renseigne')}$etoiles$distance';
}

String _repas(Textes t, String? r) => r == null ? t('non_renseigne') : t('repas_$r');

String _frais(Textes t, Forfait f, String langue) {
  final l = f.fraisNonInclus;
  if (l == null) return t('non_renseigne');
  if (l.isEmpty) return t('aucun_frais');
  return l.map((m) => choisir(m, langue)).join(', ');
}

String _guide(Textes t, Forfait f) {
  if (f.guidePresent == null) return t('non_renseigne');
  if (f.guidePresent == false) return t('non_inclus');
  final langues = f.guideLangues.isEmpty ? '' : ' (${f.guideLangues.join(', ')})';
  return '${t('inclus')}$langues';
}

String _groupe(Textes t, Forfait f) {
  if (f.groupeMax == null) return t('non_renseigne');
  return f.groupeMin == null ? 'max ${f.groupeMax}' : '${f.groupeMin} à ${f.groupeMax}';
}

String _prix(Forfait f) => '${formaterMontant(f.montant)} ${f.devise}';

Color _couleurScore(int s) => s >= 80
    ? PaletteHayaati.vertClair
    : (s >= 50 ? PaletteHayaati.ocre : PaletteHayaati.terracotta);

Fiche? _agence(ControleurAlAnsar c, String id) {
  for (final f in c.annuaire?.fiches ?? const <Fiche>[]) {
    if (f.id == id) return f;
  }
  return null;
}

/// Liste des forfaits Hadj ou Omra, avec comparateur côte à côte.
class EcranHadjOmra extends StatefulWidget {
  const EcranHadjOmra({super.key, required this.c});

  final ControleurAlAnsar c;

  @override
  State<EcranHadjOmra> createState() => _EcranHadjOmraState();
}

class _EcranHadjOmraState extends State<EcranHadjOmra> {
  String _type = 'omra';
  final Set<String> _selection = <String>{};

  @override
  Widget build(BuildContext context) {
    final c = widget.c;
    return ListenableBuilder(
      listenable: c,
      builder: (context, _) {
        final t = c.t;
        final ordreAgences = c.fiches(const {'agence'}).map((e) => e.fiche.id).toList();
        final forfaits = (c.annuaire?.forfaits ?? const <Forfait>[])
            .where((f) => f.type == _type && ordreAgences.contains(f.ficheId) && f.statut != 'annule')
            .toList()
          ..sort((a, b) => a.dateDepart.compareTo(b.dateDepart));
        final choisis = forfaits.where((f) => _selection.contains(f.id)).toList();
        return Scaffold(
          appBar: barreHayaati(t('hadj_omra'), integre: c.config.integre),
          floatingActionButton: choisis.length >= 2
              ? FloatingActionButton.extended(
                  onPressed: () => Navigator.of(context).push(
                    MaterialPageRoute<void>(builder: (_) => EcranComparateur(c: c, forfaits: choisis)),
                  ),
                  icon: const Icon(Icons.compare_arrows),
                  label: Text('${t('comparer')} (${choisis.length})'),
                )
              : null,
          body: Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
                child: BandeauLieu(c: c),
              ),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: SegmentedButton<String>(
                  segments: <ButtonSegment<String>>[
                    ButtonSegment<String>(value: 'omra', label: Text(t('omra'))),
                    ButtonSegment<String>(value: 'hadj', label: Text(t('hadj'))),
                  ],
                  selected: <String>{_type},
                  onSelectionChanged: (s) => setState(() {
                    _type = s.first;
                    _selection.clear();
                  }),
                ),
              ),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Text(t('avert_hadj'), style: Theme.of(context).textTheme.bodySmall),
              ),
              Expanded(
                child: forfaits.isEmpty
                    ? Center(child: Text(t('aucun_forfait')))
                    : ListView.builder(
                        padding: const EdgeInsets.only(bottom: 80),
                        itemCount: forfaits.length,
                        itemBuilder: (context, i) {
                          final f = forfaits[i];
                          return _CarteForfait(
                            c: c,
                            forfait: f,
                            choisi: _selection.contains(f.id),
                            onChoisir: (v) => setState(() {
                              if (v == true && _selection.length < 3) {
                                _selection.add(f.id);
                              } else {
                                _selection.remove(f.id);
                              }
                            }),
                          );
                        },
                      ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _CarteForfait extends StatelessWidget {
  const _CarteForfait({
    required this.c,
    required this.forfait,
    required this.choisi,
    required this.onChoisir,
  });

  final ControleurAlAnsar c;
  final Forfait forfait;
  final bool choisi;
  final ValueChanged<bool?> onChoisir;

  @override
  Widget build(BuildContext context) {
    final t = c.t;
    final langue = c.config.langue;
    final f = forfait;
    final agence = _agence(c, f.ficheId);
    final theme = Theme.of(context);
    final agrement = agence?.agence.agrement;
    return CarteHayaati(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => Navigator.of(context).push(
          MaterialPageRoute<void>(builder: (_) => EcranForfait(c: c, forfait: f)),
        ),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(choisir(f.intitule, langue), style: theme.textTheme.titleMedium),
                  ),
                  Checkbox(value: choisi, onChanged: onChoisir),
                ],
              ),
              if (agence != null)
                Row(
                  children: [
                    Flexible(child: Text(agence.nom)),
                    if (agence.niveau >= 2)
                      const Padding(
                        padding: EdgeInsets.only(left: 4),
                        child: Icon(Icons.verified, size: 18, color: PaletteHayaati.vertClair),
                      ),
                  ],
                ),
              if (agrement?.valideJusqua != null)
                Text(
                  '${t('agree_jusqua')} ${agrement!.valideJusqua}',
                  style: theme.textTheme.bodySmall,
                ),
              const SizedBox(height: 8),
              Text('${t('depart')} ${f.dateDepart} · ${f.dureeJours} ${t('jours')}'),
              const SizedBox(height: 4),
              Text(_prix(f), style: theme.textTheme.titleSmall),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 4,
                children: [
                  Chip(
                    label: Text('${t('transparence')} ${f.scoreTransparence} %'),
                    backgroundColor: _couleurScore(f.scoreTransparence),
                    labelStyle: const TextStyle(color: PaletteHayaati.blanc),
                    visualDensity: VisualDensity.compact,
                  ),
                  Chip(label: Text(t(f.statut)), visualDensity: VisualDensity.compact),
                  if (f.placesRestantes != null)
                    Chip(
                      label: Text('${f.placesRestantes} ${t('places_restantes')}'),
                      visualDensity: VisualDensity.compact,
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Ligne extends StatelessWidget {
  const _Ligne(this.libelle, this.valeur);

  final String libelle;
  final String valeur;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(flex: 4, child: Text(libelle, style: Theme.of(context).textTheme.bodySmall)),
          Expanded(flex: 6, child: Text(valeur)),
        ],
      ),
    );
  }
}

/// Fiche de coûts complète d'un forfait.
class EcranForfait extends StatelessWidget {
  const EcranForfait({super.key, required this.c, required this.forfait});

  final ControleurAlAnsar c;
  final Forfait forfait;

  @override
  Widget build(BuildContext context) {
    final t = c.t;
    final langue = c.config.langue;
    final f = forfait;
    final agence = _agence(c, f.ficheId);
    final agrement = agence?.agence.agrement;
    final theme = Theme.of(context);
    return Scaffold(
      appBar: barreHayaati(choisir(f.intitule, langue), integre: c.config.integre),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (agence != null) Text(agence.nom, style: theme.textTheme.titleMedium),
          if (agrement != null)
            Text(
              '${t('agrement')} ${agrement.numero}'
              '${agrement.autorite == null ? '' : ' · ${agrement.autorite}'}'
              '${agrement.valideJusqua == null ? '' : ' · ${t('agree_jusqua')} ${agrement.valideJusqua}'}',
              style: theme.textTheme.bodySmall,
            ),
          const SizedBox(height: 8),
          Chip(
            label: Text('${t('transparence')} ${f.scoreTransparence} %'),
            backgroundColor: _couleurScore(f.scoreTransparence),
            labelStyle: const TextStyle(color: PaletteHayaati.blanc),
          ),
          const Divider(),
          _Ligne(t('prix'), _prix(f)),
          if (f.acompte != null) _Ligne(t('acompte'), '${formaterMontant(f.acompte!)} ${f.devise}'),
          _Ligne(t('depart'), f.dateDepart),
          _Ligne(t('retour'), f.dateRetour),
          _Ligne(t('duree'), '${f.dureeJours} ${t('jours')}'),
          _Ligne(t('vol'), '${_ouiNon(t, f.volInclus)}${f.volDetail == null ? '' : ' · ${f.volDetail}'}'),
          _Ligne(t('hotel_makkah'), _hotel(t, f.hotelMakkah, 'du_haram')),
          _Ligne(t('hotel_madina'), _hotel(t, f.hotelMadina, 'du_masjid')),
          _Ligne(t('repas'), _repas(t, f.repas)),
          _Ligne(t('visa'), _ouiNon(t, f.visaInclus)),
          _Ligne(t('transport'), _ouiNon(t, f.transportInclus)),
          _Ligne(t('guide'), _guide(t, f)),
          _Ligne(t('groupe'), _groupe(t, f)),
          _Ligne(t('assurance'), _ouiNon(t, f.assuranceIncluse)),
          _Ligne(
            t('annulation'),
            f.annulation.isEmpty ? t('non_renseigne') : choisir(f.annulation, langue),
          ),
          _Ligne(t('frais_non_inclus'), _frais(t, f, langue)),
          if (f.placesRestantes != null)
            _Ligne(t('places_restantes'), '${f.placesRestantes}'),
          if (f.dateLimite != null) _Ligne(t('date_limite'), f.dateLimite!),
          const SizedBox(height: 16),
          CarteHayaati(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Text(t('avert_hadj')),
            ),
          ),
          if (agence?.whatsapp != null) ...[
            const SizedBox(height: 16),
            FilledButton.icon(
              style: FilledButton.styleFrom(
                backgroundColor: PaletteHayaati.terracotta,
                foregroundColor: PaletteHayaati.blanc,
              ),
              icon: const Icon(Icons.chat),
              label: Text(t('contacter')),
              onPressed: () => ouvrirWhatsApp(
                agence!.whatsapp!,
                t('msg_contact').replaceAll('{nom}', choisir(f.intitule, langue)),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

/// Comparateur : les forfaits choisis (2 ou 3) côte à côte.
class EcranComparateur extends StatelessWidget {
  const EcranComparateur({super.key, required this.c, required this.forfaits});

  final ControleurAlAnsar c;
  final List<Forfait> forfaits;

  @override
  Widget build(BuildContext context) {
    final t = c.t;
    final langue = c.config.langue;
    Widget cellule(String texte) => ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 170),
          child: Text(texte),
        );
    DataRow ligne(String libelle, String Function(Forfait) valeur) => DataRow(
          cells: <DataCell>[
            DataCell(cellule(libelle)),
            for (final f in forfaits) DataCell(cellule(valeur(f))),
          ],
        );
    return Scaffold(
      appBar: barreHayaati(t('comparateur'), integre: c.config.integre),
      body: SingleChildScrollView(
        child: SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: DataTable(
            columnSpacing: 16,
            dataRowMinHeight: 40,
            dataRowMaxHeight: 120,
            columns: <DataColumn>[
              const DataColumn(label: Text('')),
              for (final f in forfaits)
                DataColumn(label: cellule(_agence(c, f.ficheId)?.nom ?? choisir(f.intitule, langue))),
            ],
            rows: <DataRow>[
              ligne(t('prix'), _prix),
              ligne(t('depart'), (f) => f.dateDepart),
              ligne(t('duree'), (f) => '${f.dureeJours} ${t('jours')}'),
              ligne(t('vol'), (f) => _ouiNon(t, f.volInclus)),
              ligne(t('hotel_makkah'), (f) => _hotel(t, f.hotelMakkah, 'du_haram')),
              ligne(t('hotel_madina'), (f) => _hotel(t, f.hotelMadina, 'du_masjid')),
              ligne(t('repas'), (f) => _repas(t, f.repas)),
              ligne(t('visa'), (f) => _ouiNon(t, f.visaInclus)),
              ligne(t('transport'), (f) => _ouiNon(t, f.transportInclus)),
              ligne(t('guide'), (f) => _guide(t, f)),
              ligne(t('groupe'), (f) => _groupe(t, f)),
              ligne(t('assurance'), (f) => _ouiNon(t, f.assuranceIncluse)),
              ligne(t('annulation'), (f) => f.annulation.isEmpty ? t('non_renseigne') : choisir(f.annulation, langue)),
              ligne(t('frais_non_inclus'), (f) => _frais(t, f, langue)),
              ligne(t('transparence'), (f) => '${f.scoreTransparence} %'),
            ],
          ),
        ),
      ),
    );
  }
}
