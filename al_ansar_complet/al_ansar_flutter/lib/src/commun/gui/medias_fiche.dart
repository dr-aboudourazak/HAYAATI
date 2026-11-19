import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../fonctionnalites/annuaire/core/controleur.dart';
import '../core/i18n.dart';
import '../core/liens_publication.dart';
import '../../fonctionnalites/annuaire/core/modeles.dart';

/// Image d'une publication, depuis internet (https) ou depuis les ressources de l'application hôte (« asset: »).
/// La décode à taille réduite (cacheWidth) pour ménager la mémoire des téléphones modestes.
Widget _imageDe(ControleurAlAnsar c, ImageFiche img, {BoxFit fit = BoxFit.cover, int largeurMax = 900}) {
  Widget secours(BuildContext contexte, Object erreur, StackTrace? pile) =>
      _Indisponible(texte: c.t('pub_image_indisponible'));
  final legende = choisir(img.legende, c.config.langue);
  final etiquette = legende.isEmpty ? null : legende;
  if (img.estAsset) {
    return Image.asset(img.cheminAsset, fit: fit, cacheWidth: largeurMax, semanticLabel: etiquette, errorBuilder: secours);
  }
  return Image.network(
    img.url,
    fit: fit,
    cacheWidth: largeurMax,
    semanticLabel: etiquette,
    errorBuilder: secours,
    loadingBuilder: (contexte, enfant, progres) =>
        progres == null ? enfant : const Center(child: CircularProgressIndicator(strokeWidth: 2)),
  );
}

class _Indisponible extends StatelessWidget {
  const _Indisponible({required this.texte});

  final String texte;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return ColoredBox(
      color: theme.colorScheme.surfaceContainerHighest,
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.broken_image_outlined),
            const SizedBox(height: 4),
            Text(texte, style: theme.textTheme.bodySmall, textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }
}

Widget _fondVideo() => const ColoredBox(
      color: Colors.black87,
      child: Center(child: Icon(Icons.play_circle_outline, color: Colors.white70)),
    );

/// Vignette de la carte dans la liste : l'image, sinon la miniature de la vidéo, sinon rien (null).
Widget? miniatureFiche(ControleurAlAnsar c, Medias? m) {
  if (m == null || m.vide) return null;
  final Widget contenu;
  if (m.image != null) {
    contenu = _imageDe(c, m.image!, largeurMax: 160);
  } else if (m.video != null && c.config.miniaturesYoutube) {
    contenu = Image.network(
      m.video!.miniature,
      fit: BoxFit.cover,
      cacheWidth: 160,
      errorBuilder: (contexte, erreur, pile) => _fondVideo(),
    );
  } else {
    contenu = _fondVideo();
  }
  return SizedBox(
    width: 56,
    height: 56,
    child: ClipRRect(borderRadius: BorderRadius.circular(8), child: contenu),
  );
}

void _agrandir(BuildContext context, ControleurAlAnsar c, ImageFiche img) {
  final legende = choisir(img.legende, c.config.langue);
  final credit = img.credit == null ? '' : '${c.t('pub_credit')}${img.credit}';
  final pied = <String>[if (legende.isNotEmpty) legende, if (credit.isNotEmpty) credit].join('\n');
  showDialog<void>(
    context: context,
    builder: (ctx) => Dialog.fullscreen(
      backgroundColor: Colors.black,
      child: Stack(
        children: [
          Positioned.fill(
            child: InteractiveViewer(
              minScale: 1,
              maxScale: 5,
              child: Center(child: _imageDe(c, img, fit: BoxFit.contain, largeurMax: 2000)),
            ),
          ),
          PositionedDirectional(
            top: 8,
            end: 8,
            child: SafeArea(
              child: IconButton(
                tooltip: c.t('pub_fermer'),
                icon: const Icon(Icons.close, color: Colors.white),
                onPressed: () => Navigator.of(ctx).pop(),
              ),
            ),
          ),
          if (pied.isNotEmpty)
            PositionedDirectional(
              start: 16,
              end: 16,
              bottom: 16,
              child: SafeArea(child: Text(pied, style: const TextStyle(color: Colors.white, fontSize: 13))),
            ),
        ],
      ),
    ),
  );
}

/// Médias d'une fiche : image agrandissable et vidéo avec miniature. Rien n'est affiché si la fiche n'a pas de média valide.
class BlocMediasFiche extends StatelessWidget {
  const BlocMediasFiche({super.key, required this.c, required this.fiche});

  final ControleurAlAnsar c;
  final Fiche fiche;

  @override
  Widget build(BuildContext context) => BlocMedias(c: c, medias: fiche.medias);
}

/// Médias d'une publication quelconque (fiche, forfait Hadj et Omra...).
class BlocMedias extends StatelessWidget {
  const BlocMedias({super.key, required this.c, required this.medias});

  final ControleurAlAnsar c;
  final Medias? medias;

  @override
  Widget build(BuildContext context) {
    final m = medias;
    if (m == null || m.vide) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (m.image != null) _CarteImage(c: c, image: m.image!),
          if (m.image != null && m.video != null) const SizedBox(height: 12),
          if (m.video != null) _CarteVideo(c: c, video: m.video!),
        ],
      ),
    );
  }
}

class _CarteImage extends StatelessWidget {
  const _CarteImage({required this.c, required this.image});

  final ControleurAlAnsar c;
  final ImageFiche image;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final ratio = (image.ratio ?? 4 / 3).clamp(0.6, 2.0).toDouble();
    final legende = choisir(image.legende, c.config.langue);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Semantics(
          button: true,
          label: c.t('pub_agrandir'),
          child: Material(
            color: theme.colorScheme.surfaceContainerHighest,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            clipBehavior: Clip.antiAlias,
            child: InkWell(
              onTap: () => _agrandir(context, c, image),
              child: AspectRatio(
                aspectRatio: ratio,
                child: _imageDe(c, image, fit: image.estAffiche ? BoxFit.contain : BoxFit.cover),
              ),
            ),
          ),
        ),
        if (legende.isNotEmpty || image.credit != null)
          Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Text(
              <String>[if (legende.isNotEmpty) legende, if (image.credit != null) '${c.t('pub_credit')}${image.credit}'].join(' · '),
              style: theme.textTheme.bodySmall,
            ),
          ),
      ],
    );
  }
}

class _CarteVideo extends StatefulWidget {
  const _CarteVideo({required this.c, required this.video});

  final ControleurAlAnsar c;
  final VideoFiche video;

  @override
  State<_CarteVideo> createState() => _CarteVideoEtat();
}

class _CarteVideoEtat extends State<_CarteVideo> {
  bool _lecture = false;

  Future<void> _ouvrirExterne() async {
    var ok = false;
    try {
      ok = await launchUrl(Uri.parse(widget.video.lien), mode: LaunchMode.externalApplication);
    } catch (_) {
      ok = false;
    }
    if (!ok && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(widget.c.t('pub_ouverture_impossible'))));
    }
  }

  /// Lecture dans l'application quand l'hôte fournit un lecteur (lecteurVideo) ; sinon YouTube s'ouvre à l'extérieur.
  /// Le lecteur n'est construit qu'au toucher : tant qu'on ne lit pas, aucune connexion à YouTube autre que la miniature.
  void _lire() {
    if (widget.c.config.lecteurVideo != null) {
      setState(() => _lecture = true);
    } else {
      _ouvrirExterne();
    }
  }

  @override
  Widget build(BuildContext context) {
    final c = widget.c;
    final video = widget.video;
    final theme = Theme.of(context);
    final titre = choisir(video.titre, c.config.langue);
    final etiquette = titre.isEmpty ? c.t('pub_lire_video') : titre;
    final lecteur = c.config.lecteurVideo;
    if (_lecture && lecteur != null) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: AspectRatio(aspectRatio: 16 / 9, child: lecteur(context, video.youtube)),
          ),
          Row(
            children: [
              Expanded(child: Text('${c.t('pub_video')} · $etiquette', style: theme.textTheme.bodySmall)),
              TextButton.icon(
                icon: const Icon(Icons.close, size: 18),
                label: Text(c.t('pub_fermer_video')),
                onPressed: () => setState(() => _lecture = false),
              ),
            ],
          ),
        ],
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Semantics(
          button: true,
          label: etiquette,
          child: Material(
            color: Colors.black87,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            clipBehavior: Clip.antiAlias,
            child: InkWell(
              onTap: _lire,
              child: AspectRatio(
                aspectRatio: 16 / 9,
                child: Stack(
                  fit: StackFit.expand,
                  children: [
                    if (c.config.miniaturesYoutube)
                      Image.network(
                        video.miniature,
                        fit: BoxFit.cover,
                        cacheWidth: 900,
                        errorBuilder: (contexte, erreur, pile) => const ColoredBox(color: Colors.black87),
                      ),
                    const Center(child: Icon(Icons.play_circle_fill, size: 56, color: Colors.white)),
                  ],
                ),
              ),
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.only(top: 4),
          child: Text('${c.t('pub_video')} · $etiquette', style: theme.textTheme.bodySmall),
        ),
      ],
    );
  }
}
