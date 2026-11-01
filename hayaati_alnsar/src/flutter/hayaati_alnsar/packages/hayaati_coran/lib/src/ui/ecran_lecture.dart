import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:hayaati_ui/hayaati_ui.dart';

import '../controleur.dart';
import 'barre_verset.dart';
import 'corps_liste.dart';
import 'corps_page.dart';
import 'entete_lecture.dart';

/// Lecture d'une sourate : une poignée toujours visible, un en-tête repliable, puis la page de mushaf (feuilletage)
/// ou la liste (défilement continu), et la barre d'actions du verset sélectionné.
class EcranLecture extends StatefulWidget {
  const EcranLecture({super.key, required this.controleur, required this.pageInitiale});

  final ControleurCoran controleur;
  final int pageInitiale;

  @override
  State<EcranLecture> createState() => _EcranLectureState();
}

class _EcranLectureState extends State<EcranLecture> {
  @override
  void initState() {
    super.initState();
    widget.controleur.messages.addListener(_surMessage);
    // Après le premier affichage : notifier pendant la construction est interdit.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) widget.controleur.pageAffichee(widget.pageInitiale);
    });
  }

  @override
  void dispose() {
    widget.controleur.messages.removeListener(_surMessage);
    widget.controleur.quitterLecture();
    super.dispose();
  }

  void _surMessage() {
    final m = widget.controleur.messages.value;
    if (m == null || !mounted) return;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(
        content: Text(m.texte, style: const TextStyle(fontSize: 13)),
        backgroundColor: PaletteHayaati.vertProfond,
        duration: const Duration(milliseconds: 2500),
        behavior: SnackBarBehavior.floating,
      ));
  }

  Future<void> _copier() async {
    final c = widget.controleur;
    final texte = await c.contenuACopier();
    if (texte == null) return;
    try {
      await Clipboard.setData(ClipboardData(text: texte));
      c.confirmerCopie();
    } catch (_) {
      // Copie impossible sur cet appareil : rien à signaler de plus.
    }
  }

  @override
  Widget build(BuildContext context) {
    final c = widget.controleur;
    return ListenableBuilder(
      listenable: c,
      builder: (context, _) {
        final barre = BarreVerset(controleur: c, surCopier: _copier);
        return Scaffold(
          backgroundColor: PaletteHayaati.blanc,
          body: SafeArea(
            child: Column(
              children: [
                PoigneeLecture(controleur: c),
                if (!c.etat.enteteReplie) EnteteLecture(controleur: c),
                Expanded(
                  // Clé : quand l'en-tête apparaît ou disparaît, la position des enfants change ; sans elle, la page
                  // serait recréée et reviendrait à son point de départ.
                  key: const ValueKey<String>('corps-lecture'),
                  child: c.etat.mode == 'liste'
                      ? CorpsListe(controleur: c, barre: barre)
                      : CorpsPage(controleur: c, barre: barre),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
