import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:youtube_player_iframe/youtube_player_iframe.dart';

/// Le lecteur intégré existe sur Android, iOS, macOS et le web. Sous Windows et Linux, l'application ne le fournit pas :
/// le module Al Ansâr ouvre alors la vidéo dans le navigateur.
bool get lecteurYoutubeDisponible =>
    kIsWeb ||
    defaultTargetPlatform == TargetPlatform.android ||
    defaultTargetPlatform == TargetPlatform.iOS ||
    defaultTargetPlatform == TargetPlatform.macOS;

/// Lecteur YouTube intégré (lecteur officiel « iframe » dans la WebView du système : rien n'est téléchargé en plus dans
/// l'application). Il est construit seulement quand la personne touche la miniature, sur le domaine youtube-nocookie.com
/// (mode « confidentialité renforcée » du paquet), sans vidéos suggérées d'autres chaînes. La lecture s'arrête quand
/// l'application passe en arrière-plan et quand on quitte la fiche.
class LecteurYoutube extends StatefulWidget {
  const LecteurYoutube({super.key, required this.idYoutube, this.langue = 'fr'});

  /// Identifiant déjà validé par le module (11 caractères).
  final String idYoutube;
  final String langue;

  @override
  State<LecteurYoutube> createState() => _LecteurYoutubeEtat();
}

class _LecteurYoutubeEtat extends State<LecteurYoutube> with WidgetsBindingObserver {
  late final YoutubePlayerController _controleur;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _controleur = YoutubePlayerController.fromVideoId(
      videoId: widget.idYoutube,
      autoPlay: true,
      params: YoutubePlayerParams(
        showFullscreenButton: true,
        strictRelatedVideos: true,
        interfaceLanguage: widget.langue,
        captionLanguage: widget.langue,
      ),
    );
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state != AppLifecycleState.resumed) _controleur.pauseVideo();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _controleur.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => YoutubePlayer(controller: _controleur, aspectRatio: 16 / 9);
}
