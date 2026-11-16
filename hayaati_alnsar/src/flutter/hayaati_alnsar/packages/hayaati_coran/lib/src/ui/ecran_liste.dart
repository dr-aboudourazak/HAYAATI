import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:hayaati_ui/hayaati_ui.dart';

import '../controleur.dart';
import '../etat_lecture.dart';
import '../moteur_coran.dart';
import '../textes.dart';
import 'ecran_lecture.dart';

/// Ouvre la lecture de [sourate] à [page] ; [surligne] : verset à montrer sélectionné (signet de verset).
void ouvrirLecture(BuildContext context, ControleurCoran c, int sourate, int page, {VersetRef? surligne}) {
  c.ouvrirLecture(sourate, page, surligne: surligne);
  Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => EcranLecture(controleur: c, pageInitiale: page)));
}

/// Les 114 sourates. L'en-tête (reprise, progression, signets, recherche) reste fixe : seule la liste défile.
class EcranListeSourates extends StatefulWidget {
  const EcranListeSourates({super.key, required this.controleur});

  final ControleurCoran controleur;

  @override
  State<EcranListeSourates> createState() => _EcranListeSouratesState();
}

class _EcranListeSouratesState extends State<EcranListeSourates> {
  CharteHayaati get ch => CharteHayaati.of(context);

  String _filtre = '';
  bool _confirmerReinit = false;
  Timer? _antiRebond;

  @override
  void dispose() {
    _antiRebond?.cancel();
    super.dispose();
  }

  /// Numéro exact, ou fragment du nom (translittération, anglais, arabe).
  List<EntreeSourate> _filtrer(List<EntreeSourate> index) {
    final requete = _filtre.trim().toLowerCase();
    if (requete.isEmpty) return index;
    return <EntreeSourate>[
      for (final e in index)
        if (requete == e.numero.toString() ||
            e.translitteration.toLowerCase().contains(requete) ||
            e.nomAnglais.toLowerCase().contains(requete) ||
            e.nomArabe.toLowerCase().contains(requete))
          e,
    ];
  }

  void _saisie(String valeur) {
    _antiRebond?.cancel();
    _antiRebond = Timer(const Duration(milliseconds: 350), () {
      if (mounted) setState(() => _filtre = valeur);
    });
  }

  @override
  Widget build(BuildContext context) {
    final c = widget.controleur;
    return ListenableBuilder(
      listenable: c,
      builder: (context, _) {
        final t = c.textes;
        final liste = _filtrer(c.moteur.index);
        return Scaffold(
          appBar: barreHayaati(t('titre', 'Le Coran'), integre: true),
          body: SafeArea(
            child: Column(
              children: [
                Padding(
                  padding: const EdgeInsets.fromLTRB(12, 10, 12, 4),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        t('consigne', 'Sélectionnez une sourate pour la lire.'),
                        style: TextStyle(fontSize: 11, fontStyle: FontStyle.italic, color: ch.grisTexte),
                      ),
                      const SizedBox(height: 6),
                      ..._reprise(c),
                      _progression(c),
                      ..._signets(c),
                      const SizedBox(height: 6),
                      SizedBox(
                        height: 42,
                        child: TextField(
                          onChanged: _saisie,
                          style: const TextStyle(fontSize: 13),
                          decoration: InputDecoration(
                            hintText: t('filtre_placeholder', 'Rechercher une sourate (nom ou numéro)'),
                            isDense: true,
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(8),
                              borderSide: BorderSide(color: ch.ocre),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: liste.isEmpty
                      ? Center(child: Text(t('aucun_resultat', 'Aucune sourate ne correspond à cette recherche.'), textAlign: TextAlign.center))
                      : ListView.builder(
                          padding: const EdgeInsets.fromLTRB(12, 4, 12, 12),
                          itemCount: liste.length + 1,
                          itemBuilder: (context, i) => i < liste.length ? _ligneSourate(c, liste[i]) : _pied(t),
                        ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _pied(TextesCoran t) {
    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: Column(
        children: [
          Text(t('source_attribution', 'Source : Tanzil.net'), style: TextStyle(fontSize: 11, color: ch.grisTexte)),
          Text(
            t('source_tajweed', 'Tajweed : annotations cpfair/quran-tajweed (CC BY 4.0)'),
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 10, color: ch.grisTexte),
          ),
        ],
      ),
    );
  }

  List<Widget> _reprise(ControleurCoran c) {
    final page = c.etat.dernierePage;
    if (page == null) return const <Widget>[];
    final sourate = c.moteur.sourateDePage(page);
    if (sourate == null) return const <Widget>[];
    final t = c.textes;
    return <Widget>[
      Material(
        color: ch.ocreClair,
        borderRadius: BorderRadius.circular(10),
        child: InkWell(
          borderRadius: BorderRadius.circular(10),
          onTap: () => ouvrirLecture(context, c, sourate, page),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            child: Row(
              children: [
                Icon(Icons.auto_stories_rounded, color: ch.vertProfond, size: 22),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        t('reprendre_lecture', 'Reprendre la lecture'),
                        style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: ch.vertProfond),
                      ),
                      Text(
                        '${c.moteur.nomSourate(sourate)} · ${t('mot_page', 'Page')} $page',
                        style: TextStyle(fontSize: 12, fontFamily: familleArabe, color: ch.texteFonce),
                      ),
                    ],
                  ),
                ),
                Icon(Icons.arrow_forward_ios_rounded, size: 12, color: ch.grisTexte),
              ],
            ),
          ),
        ),
      ),
      const SizedBox(height: 6),
    ];
  }

  Widget _progression(ControleurCoran c) {
    final (lues, total) = c.etat.progression();
    final t = c.textes;
    return Column(
      children: [
        LinearProgressIndicator(
          value: total == 0 ? 0 : lues / total,
          minHeight: 5,
          color: ch.vertProfond,
          backgroundColor: ch.grisClair,
        ),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              t.modele('progression_pages', <String, Object>{'n': lues, 'total': total}, '{n} / {total} pages lues'),
              style: TextStyle(fontSize: 11, color: ch.grisTexte),
            ),
            if (lues > 0)
              TextButton(
                onPressed: () {
                  if (_confirmerReinit) {
                    c.reinitialiserProgression();
                    setState(() => _confirmerReinit = false);
                  } else {
                    setState(() => _confirmerReinit = true);
                  }
                },
                child: Text(
                  _confirmerReinit
                      ? t('confirmer_reinitialiser', 'Confirmer la remise à zéro')
                      : t('reinitialiser_progression', 'Remettre à zéro'),
                  style: TextStyle(fontSize: 11, color: _confirmerReinit ? ch.rougeErreur : ch.grisTexte),
                ),
              ),
          ],
        ),
      ],
    );
  }

  /// Une ligne « Signets (N) » qui déplie ou replie la liste ; dépliée, la liste a sa propre hauteur maximale et son
  /// propre défilement pour ne pas écraser l'en-tête fixe.
  List<Widget> _signets(ControleurCoran c) {
    final signets = c.etat.signets;
    if (signets.isEmpty) return const <Widget>[];
    final t = c.textes;
    final ouvert = c.signetsOuverts;
    return <Widget>[
      InkWell(
        onTap: c.basculerSignetsOuverts,
        child: Padding(
          padding: const EdgeInsets.all(4),
          child: Row(
            children: [
              Icon(Icons.bookmark, color: ch.ocre, size: 16),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  '${t('signets_titre', 'Signets')} (${signets.length})',
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: ch.vertProfond),
                ),
              ),
              Icon(
                ouvert ? Icons.keyboard_arrow_up_rounded : Icons.keyboard_arrow_down_rounded,
                color: ch.grisTexte,
                size: 20,
              ),
            ],
          ),
        ),
      ),
      if (ouvert)
        ConstrainedBox(
          constraints: BoxConstraints(maxHeight: math.min(signets.length * 44.0, 176.0)),
          child: ListView(
            shrinkWrap: true,
            padding: EdgeInsets.zero,
            children: [for (final s in signets) _ligneSignet(c, s)],
          ),
        ),
    ];
  }

  Widget _ligneSignet(ControleurCoran c, Signet s) {
    final t = c.textes;
    final motPage = t('mot_page', 'Page');
    final String libelle;
    final int sourate;
    if (s.estVerset) {
      sourate = s.sourate!;
      libelle = '${c.moteur.nomSourate(sourate)} · ${t('mot_verset', 'verset')} ${s.verset} · $motPage ${s.page}';
    } else {
      sourate = c.moteur.sourateDePage(s.page) ?? 0;
      libelle = '$motPage ${s.page} · ${c.moteur.nomSourate(sourate)}';
    }
    return Padding(
      padding: const EdgeInsets.only(bottom: 3),
      child: Material(
        color: ch.sable,
        borderRadius: BorderRadius.circular(8),
        child: InkWell(
          borderRadius: BorderRadius.circular(8),
          onTap: () => ouvrirLecture(
            context,
            c,
            sourate,
            s.page,
            surligne: s.estVerset ? VersetRef(sourate, s.verset!) : null,
          ),
          child: Padding(
            padding: const EdgeInsets.only(left: 10, right: 2),
            child: Row(
              children: [
                Icon(s.estVerset ? Icons.bookmark_added : Icons.bookmark, color: ch.ocre, size: 18),
                const SizedBox(width: 8),
                Expanded(child: Text(libelle, style: TextStyle(fontSize: 12, fontFamily: familleArabe, color: ch.texteFonce))),
                IconButton(
                  tooltip: t('fermer', 'Fermer'),
                  icon: const Icon(Icons.delete_outline_rounded, size: 18),
                  color: ch.grisTexte,
                  onPressed: () => c.retirerSignet(s),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _ligneSourate(ControleurCoran c, EntreeSourate e) {
    final t = c.textes;
    final revelation = e.revelation == 'meccane' ? t('revelation_meccane', 'Meccane') : t('revelation_medinoise', 'Médinoise');
    final sousTitre = '${e.translitteration} · $revelation · ${e.nbVersets} ${t('mot_versets', 'versets')}';
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Material(
        color: ch.sable,
        borderRadius: BorderRadius.circular(8),
        child: InkWell(
          borderRadius: BorderRadius.circular(8),
          onTap: () async {
            final page = await c.moteur.premierePageSourate(e.numero);
            if (page != null && mounted) ouvrirLecture(context, c, e.numero, page);
          },
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
            child: Row(
              children: [
                Container(
                  width: 32,
                  height: 32,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(color: ch.ocreClair, shape: BoxShape.circle),
                  child: Text('${e.numero}', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: ch.vertProfond)),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(e.nomArabe, style: TextStyle(fontFamily: familleArabe, fontSize: 16, color: ch.texteFonce)),
                      Align(
                        alignment: AlignmentDirectional.centerStart,
                        child: Text(sousTitre, style: TextStyle(fontSize: 10, color: ch.grisTexte)),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                Icon(Icons.arrow_forward_ios_rounded, size: 12, color: ch.grisTexte),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
