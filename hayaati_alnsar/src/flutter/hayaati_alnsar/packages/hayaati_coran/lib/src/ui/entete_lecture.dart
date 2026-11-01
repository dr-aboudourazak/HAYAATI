import 'package:flutter/material.dart';
import 'package:hayaati_ui/hayaati_ui.dart';

import '../controleur.dart';
import '../polices.dart';
import '../texte.dart';

/// Bande fine toujours visible : retour, signet de page, titre compact (un appui déplie ou replie l'en-tête complet)
/// et chevron. Elle laisse l'essentiel accessible quand l'en-tête complet est replié.
class PoigneeLecture extends StatelessWidget {
  const PoigneeLecture({super.key, required this.controleur});

  final ControleurCoran controleur;

  @override
  Widget build(BuildContext context) {
    final c = controleur;
    final t = c.textes;
    final replie = c.etat.enteteReplie;
    final titre = '${c.moteur.nomSourate(c.sourateActive)}  ·  ${t('mot_page', 'Page')} ${chiffresArabes(c.pageActive)}';
    return Container(
      decoration: const BoxDecoration(
        color: PaletteHayaati.blanc,
        border: Border(bottom: BorderSide(color: PaletteHayaati.grisClair)),
      ),
      child: Row(
        children: [
          IconButton(
            tooltip: t('retour', 'Retour'),
            icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 16),
            color: PaletteHayaati.vertProfond,
            onPressed: () => Navigator.of(context).maybePop(),
          ),
          IconButton(
            tooltip: t('signet_bascule', 'Signet'),
            icon: Icon(c.pageEstSignet ? Icons.bookmark : Icons.bookmark_border_rounded, size: 20),
            color: PaletteHayaati.ocre,
            onPressed: c.basculerSignetPage,
          ),
          Expanded(
            child: InkWell(
              onTap: c.basculerEntete,
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 10),
                child: Text(
                  titre,
                  textAlign: TextAlign.center,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontFamily: familleArabe,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: PaletteHayaati.vertProfond,
                  ),
                ),
              ),
            ),
          ),
          IconButton(
            tooltip: replie ? t('entete_afficher', "Afficher l'en-tête") : t('entete_replier', "Replier l'en-tête"),
            icon: Icon(replie ? Icons.keyboard_arrow_down_rounded : Icons.keyboard_arrow_up_rounded, size: 22),
            color: PaletteHayaati.vertProfond,
            onPressed: c.basculerEntete,
          ),
        ],
      ),
    );
  }
}

/// En-tête complet, repliable : recherche d'un verset par numéro, sourate précédente et suivante, tajweed, taille,
/// police, choix du mode (page ou liste).
class EnteteLecture extends StatefulWidget {
  const EnteteLecture({super.key, required this.controleur});

  final ControleurCoran controleur;

  @override
  State<EnteteLecture> createState() => _EnteteLectureState();
}

class _EnteteLectureState extends State<EnteteLecture> {
  final TextEditingController _champ = TextEditingController();

  @override
  void dispose() {
    _champ.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final c = widget.controleur;
    final t = c.textes;
    final sourate = c.sourateActive;
    // Le champ se vide quand le contrôleur le vide (changement de sourate), sans modifier un contrôleur de texte pendant la construction.
    if (c.filtreVerset.isEmpty && _champ.text.isNotEmpty) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) _champ.clear();
      });
    }
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          color: PaletteHayaati.blanc,
          padding: const EdgeInsets.fromLTRB(4, 4, 4, 6),
          // Sens de lecture arabe : « suivante » (avancer dans le livre) à GAUCHE du titre, « précédente » à DROITE.
          child: Directionality(
            textDirection: TextDirection.ltr,
            child: Row(
              children: [
                SizedBox(
                  width: 88,
                  height: 38,
                  child: TextField(
                    controller: _champ,
                    keyboardType: TextInputType.number,
                    textAlign: TextAlign.center,
                    style: const TextStyle(fontSize: 12),
                    onChanged: c.saisirVerset,
                    decoration: InputDecoration(
                      hintText: t('verset_court', 'Verset'),
                      isDense: true,
                      contentPadding: const EdgeInsets.symmetric(horizontal: 4, vertical: 8),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                        borderSide: const BorderSide(color: PaletteHayaati.ocre),
                      ),
                    ),
                  ),
                ),
                IconButton(
                  tooltip: t('sourate_suivante', 'Sourate suivante'),
                  icon: const Icon(Icons.chevron_left_rounded, size: 24),
                  color: PaletteHayaati.vertProfond,
                  onPressed: sourate >= 114 ? null : () => c.ouvrirSourate(sourate + 1),
                ),
                Expanded(
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Container(
                        width: 26,
                        height: 26,
                        alignment: Alignment.center,
                        decoration: const BoxDecoration(color: PaletteHayaati.ocreClair, shape: BoxShape.circle),
                        child: Text(
                          '$sourate',
                          style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: PaletteHayaati.vertProfond),
                        ),
                      ),
                      const SizedBox(width: 6),
                      Flexible(
                        child: Text(
                          c.moteur.nomSourate(sourate),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            fontFamily: familleArabe,
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: PaletteHayaati.vertProfond,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  tooltip: t('sourate_precedente', 'Sourate précédente'),
                  icon: const Icon(Icons.chevron_right_rounded, size: 24),
                  color: PaletteHayaati.vertProfond,
                  onPressed: sourate <= 1 ? null : () => c.ouvrirSourate(sourate - 1),
                ),
              ],
            ),
          ),
        ),
        Container(
          decoration: const BoxDecoration(border: Border(bottom: BorderSide(color: PaletteHayaati.grisClair))),
          padding: const EdgeInsets.only(left: 8, right: 4, bottom: 2),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Switch(
                    value: c.etat.tajweed,
                    activeTrackColor: PaletteHayaati.vertProfond,
                    onChanged: (_) => c.basculerTajweed(),
                  ),
                  Text(t('tajweed', 'Tajweed'), style: const TextStyle(fontSize: 13)),
                ],
              ),
              Row(
                children: [
                  IconButton(
                    tooltip: t('texte_plus_petit', 'Texte plus petit'),
                    icon: const Icon(Icons.text_decrease_rounded, size: 20),
                    color: PaletteHayaati.vertProfond,
                    onPressed: c.peutReduire ? () => c.changerTaille(-1) : null,
                  ),
                  IconButton(
                    tooltip: t('texte_plus_grand', 'Texte plus grand'),
                    icon: const Icon(Icons.text_increase_rounded, size: 20),
                    color: PaletteHayaati.vertProfond,
                    onPressed: c.peutAgrandir ? () => c.changerTaille(1) : null,
                  ),
                  PopupMenuButton<String>(
                    tooltip: t('police_titre', 'Police du texte'),
                    icon: const Icon(Icons.tune_rounded, size: 20, color: PaletteHayaati.vertProfond),
                    onSelected: c.changerPolice,
                    itemBuilder: (_) => [
                      for (final p in polices.values)
                        CheckedPopupMenuItem<String>(value: p.cle, checked: c.etat.police == p.cle, child: Text(p.libelle)),
                    ],
                  ),
                  _bouton(c, Icons.auto_stories_rounded, 'page', t('mode_page', 'Mode page')),
                  _bouton(c, Icons.view_agenda_outlined, 'liste', t('mode_liste', 'Mode liste')),
                ],
              ),
            ],
          ),
        ),
        if (c.messageRecherche != null)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 3),
            child: Text(
              c.messageRecherche!,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 11, fontStyle: FontStyle.italic, color: PaletteHayaati.grisTexte),
            ),
          ),
      ],
    );
  }

  Widget _bouton(ControleurCoran c, IconData icone, String mode, String info) {
    final actif = c.etat.mode == mode;
    return IconButton(
      tooltip: info,
      icon: Icon(icone, size: 20),
      color: actif ? PaletteHayaati.blanc : PaletteHayaati.vertProfond,
      style: IconButton.styleFrom(backgroundColor: actif ? PaletteHayaati.vertProfond : null),
      onPressed: () => c.changerMode(mode),
    );
  }
}
