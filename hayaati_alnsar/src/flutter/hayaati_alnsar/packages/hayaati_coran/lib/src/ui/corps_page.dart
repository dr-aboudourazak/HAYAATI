import 'package:flutter/material.dart';
import 'package:hayaati_ui/hayaati_ui.dart';

import '../controleur.dart';
import '../texte.dart';
import 'page_mushaf.dart';

/// Mode page : les 604 pages se feuillettent latéralement comme un livre arabe. La page 1 est à DROITE, on avance
/// en glissant le doigt de gauche à droite. Le sens est fixé ici (Directionality) et ne dépend donc pas de la langue
/// de l'interface. Les flèches « page suivante » à GAUCHE et « page précédente » à DROITE complètent le geste.
class CorpsPage extends StatefulWidget {
  const CorpsPage({super.key, required this.controleur, required this.barre});

  final ControleurCoran controleur;

  /// Barre d'actions du verset sélectionné, placée entre la page et les flèches.
  final Widget barre;

  @override
  State<CorpsPage> createState() => _CorpsPageState();
}

class _CorpsPageState extends State<CorpsPage> {
  late final PageController _pages = PageController(initialPage: widget.controleur.pageActive - 1);

  @override
  void initState() {
    super.initState();
    widget.controleur.saut.addListener(_surSaut);
  }

  @override
  void dispose() {
    widget.controleur.saut.removeListener(_surSaut);
    _pages.dispose();
    super.dispose();
  }

  /// Recherche de verset ou changement de sourate : on rejoint la page demandée et l'on peut continuer à feuilleter.
  void _surSaut() {
    final d = widget.controleur.saut.value;
    if (d != null && _pages.hasClients) _pages.jumpToPage(d.page - 1);
  }

  void _aller(int delta) {
    final cible = widget.controleur.pageActive - 1 + delta;
    if (cible < 0 || cible >= nbPages) return;
    _pages.animateToPage(cible, duration: const Duration(milliseconds: 250), curve: Curves.easeOut);
  }

  @override
  Widget build(BuildContext context) {
    final c = widget.controleur;
    final t = c.textes;
    return Column(
      children: [
        Expanded(
          child: Directionality(
            textDirection: TextDirection.rtl,
            child: PageView.builder(
              controller: _pages,
              itemCount: nbPages,
              onPageChanged: (i) {
                // Un saut demandé par le contrôleur a déjà fixé la page active : seul un vrai feuilletage la change.
                if (i + 1 != c.pageActive) c.pageFeuilletee(i + 1);
              },
              itemBuilder: (_, i) => PageMushaf(key: ValueKey<int>(i + 1), controleur: c, page: i + 1),
            ),
          ),
        ),
        widget.barre,
        // Dessinée de gauche à droite (les flèches ne s'inversent pas) ; seule la place des boutons suit la lecture arabe.
        Directionality(
          textDirection: TextDirection.ltr,
          child: Row(
            children: [
              IconButton(
                tooltip: t('page_suivante', 'Page suivante'),
                icon: const Icon(Icons.chevron_left_rounded, size: 26),
                color: PaletteHayaati.vertProfond,
                onPressed: () => _aller(1),
              ),
              Expanded(
                child: Text(
                  '${chiffresArabes(c.pageActive)} / ${chiffresArabes(nbPages)}  ·  Tanzil.net',
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 11, color: PaletteHayaati.grisTexte),
                ),
              ),
              IconButton(
                tooltip: t('page_precedente', 'Page précédente'),
                icon: const Icon(Icons.chevron_right_rounded, size: 26),
                color: PaletteHayaati.vertProfond,
                onPressed: () => _aller(-1),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
