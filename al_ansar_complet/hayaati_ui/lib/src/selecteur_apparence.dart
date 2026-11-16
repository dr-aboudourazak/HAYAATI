import 'package:flutter/material.dart';

import 'apparence.dart';
import 'charte_hayaati.dart';

/// Écran de choix de l'apparence : un arrière-plan (clair, papier, sombre) et une couleur principale (vert, terracotta,
/// ocre), avec un aperçu réel de chaque choix. Il ne sait rien de l'endroit où l'apparence est enregistrée : il
/// signale le nouveau choix par [surChangement] ; l'hôte l'enregistre et reconstruit le thème.
///
/// [libelle] fournit les textes traduits (clés : apparence_titre, apparence_fond, apparence_clair, apparence_papier,
/// apparence_sombre, apparence_couleur, apparence_vert, apparence_terracotta, apparence_ocre) ; à défaut, le français.
class SelecteurApparence extends StatelessWidget {
  const SelecteurApparence({super.key, required this.apparence, required this.surChangement, this.libelle});

  final ApparenceHayaati apparence;
  final ValueChanged<ApparenceHayaati> surChangement;
  final String Function(String cle, String defaut)? libelle;

  static const Map<String, String> _francais = <String, String>{
    'apparence_titre': 'Apparence',
    'apparence_fond': 'Arrière-plan',
    'apparence_clair': 'Clair',
    'apparence_papier': 'Papier',
    'apparence_sombre': 'Sombre',
    'apparence_couleur': 'Couleur principale',
    'apparence_vert': 'Vert',
    'apparence_terracotta': 'Terracotta',
    'apparence_ocre': 'Ocre',
  };

  String _t(String cle) => libelle?.call(cle, _francais[cle]!) ?? _francais[cle]!;

  @override
  Widget build(BuildContext context) {
    final ch = CharteHayaati.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(_t('apparence_fond'), style: TextStyle(fontWeight: FontWeight.bold, color: ch.vertProfond)),
        const SizedBox(height: 8),
        Row(
          children: [
            for (final f in fondsApparence)
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 4),
                  child: _VignetteFond(
                    fond: f,
                    couleur: apparence.couleur,
                    libelle: _t('apparence_$f'),
                    choisi: apparence.fond == f,
                    surToucher: () => surChangement(apparence.avec(fond: f)),
                  ),
                ),
              ),
          ],
        ),
        const SizedBox(height: 20),
        Text(_t('apparence_couleur'), style: TextStyle(fontWeight: FontWeight.bold, color: ch.vertProfond)),
        const SizedBox(height: 8),
        Row(
          children: [
            for (final c in couleursApparence)
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 4),
                  child: _PastilleCouleur(
                    fond: apparence.fond,
                    couleur: c,
                    libelle: _t('apparence_$c'),
                    choisie: apparence.couleur == c,
                    surToucher: () => surChangement(apparence.avec(couleur: c)),
                  ),
                ),
              ),
          ],
        ),
      ],
    );
  }
}

/// Aperçu d'un arrière-plan : une miniature de page avec un bandeau, un titre, un texte et une carte, dans les vraies
/// couleurs de cet arrière-plan (avec la couleur principale actuelle).
class _VignetteFond extends StatelessWidget {
  const _VignetteFond({
    required this.fond,
    required this.couleur,
    required this.libelle,
    required this.choisi,
    required this.surToucher,
  });

  final String fond;
  final String couleur;
  final String libelle;
  final bool choisi;
  final VoidCallback surToucher;

  @override
  Widget build(BuildContext context) {
    final v = ValeursCharte.pour(ApparenceHayaati(fond: fond, couleur: couleur));
    final ch = CharteHayaati.of(context);
    return Semantics(
      button: true,
      selected: choisi,
      label: libelle,
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: surToucher,
        child: Container(
          padding: const EdgeInsets.all(6),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: choisi ? ch.vertProfond : ch.bordure, width: choisi ? 2.5 : 1),
          ),
          child: Column(
            children: [
              Container(
                height: 70,
                decoration: BoxDecoration(color: Color(v.sable), borderRadius: BorderRadius.circular(8)),
                clipBehavior: Clip.antiAlias,
                child: Column(
                  children: [
                    Container(height: 14, color: Color(v.primaire)),
                    Padding(
                      padding: const EdgeInsets.fromLTRB(6, 6, 6, 0),
                      child: Row(
                        children: [
                          Container(width: 22, height: 5, decoration: BoxDecoration(color: Color(v.vertProfond), borderRadius: BorderRadius.circular(3))),
                          const SizedBox(width: 4),
                          Container(width: 10, height: 5, decoration: BoxDecoration(color: Color(v.ocre), borderRadius: BorderRadius.circular(3))),
                        ],
                      ),
                    ),
                    Padding(
                      padding: const EdgeInsets.fromLTRB(6, 5, 6, 0),
                      child: Container(
                        height: 18,
                        decoration: BoxDecoration(
                          color: Color(v.blanc),
                          borderRadius: BorderRadius.circular(5),
                          border: Border.all(color: Color(v.bordure)),
                        ),
                        alignment: Alignment.center,
                        child: Text('﷽', style: TextStyle(fontSize: 10, color: Color(v.texteFonce))),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 6),
              Text(
                libelle,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(fontSize: 12, fontWeight: choisi ? FontWeight.bold : FontWeight.normal, color: ch.texteFonce),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Pastille de la couleur principale, dans l'arrière-plan en cours.
class _PastilleCouleur extends StatelessWidget {
  const _PastilleCouleur({
    required this.fond,
    required this.couleur,
    required this.libelle,
    required this.choisie,
    required this.surToucher,
  });

  final String fond;
  final String couleur;
  final String libelle;
  final bool choisie;
  final VoidCallback surToucher;

  @override
  Widget build(BuildContext context) {
    final v = ValeursCharte.pour(ApparenceHayaati(fond: fond, couleur: couleur));
    final ch = CharteHayaati.of(context);
    return Semantics(
      button: true,
      selected: choisie,
      label: libelle,
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: surToucher,
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 6),
          child: Column(
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: Color(v.primaire),
                  shape: BoxShape.circle,
                  border: Border.all(color: choisie ? ch.vertProfond : ch.bordure, width: choisie ? 3 : 1),
                ),
                child: choisie ? Icon(Icons.check, color: Color(v.surPrimaire), size: 22) : null,
              ),
              const SizedBox(height: 4),
              Text(libelle, style: TextStyle(fontSize: 12, color: ch.texteFonce)),
            ],
          ),
        ),
      ),
    );
  }
}
