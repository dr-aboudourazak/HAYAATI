// Médias et liens d'une publication d'Al Ansâr (lot E).
//
// Ce fichier n'a aucune dépendance : tout ce qui vient d'un fichier de données ou d'un lien reçu est contrôlé ici,
// avant d'atteindre l'écran. Règle générale : une valeur douteuse est ignorée, jamais « réparée ».

final RegExp _reIdYoutube = RegExp(r'^[A-Za-z0-9_-]{11}$');
final RegExp _reIdFiche = RegExp(r'^[a-z]{2}-[a-z0-9]+(-[a-z0-9]+)*$');
final RegExp _reLangue = RegExp(r'^[a-z]{2}$');
final RegExp _reAsset = RegExp(r'^assets/[A-Za-z0-9_./-]+\.(png|jpg|jpeg|webp)$');
final RegExp _reEspace = RegExp(r'\s');

const Set<String> _hotesYoutube = <String>{'youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be'};
const String prefixeAsset = 'asset:';

/// Un identifiant de publication est sûr s'il respecte la forme du schéma (« tg-lome-mad-001 »), 60 caractères au plus.
bool idFicheSur(String? id) => id != null && id.length <= 60 && _reIdFiche.hasMatch(id);

/// Identifiant YouTube (11 caractères) tiré d'un identifiant nu ou d'une adresse https de YouTube ; null sinon.
/// Seuls youtube.com, www.youtube.com, m.youtube.com et youtu.be sont acceptés.
String? idYoutubeValide(Object? entree) {
  if (entree is! String) return null;
  final s = entree.trim();
  if (_reIdYoutube.hasMatch(s)) return s;
  if (s.isEmpty || s.length > 300 || _reEspace.hasMatch(s)) return null;
  final u = Uri.tryParse(s);
  if (u == null || u.scheme != 'https' || u.userInfo.isNotEmpty || (u.hasPort && u.port != 443)) return null;
  final hote = u.host.toLowerCase();
  if (!_hotesYoutube.contains(hote)) return null;
  final seg = u.pathSegments.where((e) => e.isNotEmpty).toList();
  String? candidat;
  if (hote == 'youtu.be') {
    candidat = seg.isNotEmpty ? seg.first : null;
  } else if (seg.length == 1 && seg.first == 'watch') {
    candidat = u.queryParameters['v'];
  } else if (seg.length == 2 && (seg.first == 'shorts' || seg.first == 'embed' || seg.first == 'live')) {
    candidat = seg[1];
  }
  return candidat != null && _reIdYoutube.hasMatch(candidat) ? candidat : null;
}

/// Adresse d'image acceptée : https sans identifiants, ou « asset:assets/... » (image fournie avec l'application hôte,
/// utile à la démonstration). Tout le reste (http, file, data, javascript...) est refusé.
String? urlImageValide(Object? v) {
  if (v is! String) return null;
  final s = v.trim();
  if (s.isEmpty || s.length > 2000 || _reEspace.hasMatch(s)) return null;
  if (s.startsWith(prefixeAsset)) {
    final chemin = s.substring(prefixeAsset.length);
    return _reAsset.hasMatch(chemin) && !chemin.contains('..') ? s : null;
  }
  final u = Uri.tryParse(s);
  if (u == null || u.scheme != 'https' || u.host.isEmpty || u.userInfo.isNotEmpty) return null;
  return s;
}

/// Lien de partage « <baseLien><id> ». Vide si la base n'est pas une adresse sûre terminée par « /a/ », ou si l'identifiant
/// n'est pas sûr : dans ce cas le bouton Partager n'est pas proposé.
String lienPartage(String baseLien, String id) {
  final base = baseLien.trim();
  if (!idFicheSur(id) || !base.endsWith('/a/')) return '';
  final u = Uri.tryParse(base);
  if (u == null || u.host.isEmpty || u.userInfo.isNotEmpty || u.hasQuery || u.hasFragment) return '';
  if (u.scheme != 'https' && u.scheme != 'hayaati') return '';
  return '$base$id';
}

/// Identifiant de publication contenu dans un lien « https://domaine/a/<id> » ou « hayaati://a/<id> » ; null si le lien
/// n'a pas cette forme. Le domaine n'a aucune importance : on ne retient que l'identifiant, qui ne peut désigner qu'une
/// publication déjà présente dans l'annuaire chargé.
String? idFicheDepuisLien(String? lien) {
  if (lien == null) return null;
  final s = lien.trim();
  if (s.isEmpty || s.length > 300 || _reEspace.hasMatch(s)) return null;
  final u = Uri.tryParse(s);
  if (u == null || u.userInfo.isNotEmpty || u.hasQuery && u.query.length > 200) return null;
  final seg = u.pathSegments.where((e) => e.isNotEmpty).toList();
  String? id;
  if (u.scheme == 'https' && u.host.isNotEmpty) {
    if (seg.length == 2 && seg.first == 'a') id = seg[1];
  } else if (u.scheme == 'hayaati' && u.host == 'a') {
    if (seg.length == 1) id = seg.first;
  }
  return idFicheSur(id) ? id : null;
}

Map<String, String> _textesLangue(Object? v) {
  final r = <String, String>{};
  if (v is Map) {
    v.forEach((k, x) {
      if (k is String && _reLangue.hasMatch(k) && x is String && x.trim().isNotEmpty) {
        final t = x.trim();
        r[k] = t.length > 1000 ? t.substring(0, 1000) : t;
      }
    });
  }
  return r;
}

int? _dimension(Object? v) => v is num && v == v.roundToDouble() && v >= 1 && v <= 10000 ? v.toInt() : null;

/// Image d'une publication : affiche marketing ou photo du lieu. HAYAATI ne l'héberge pas.
class ImageFiche {
  const ImageFiche({
    required this.url,
    this.largeur,
    this.hauteur,
    this.genre = 'photo',
    this.credit,
    this.legende = const <String, String>{},
  });

  final String url;
  final int? largeur;
  final int? hauteur;

  /// « affiche » (jamais rognée à l'affichage) ou « photo ».
  final String genre;
  final String? credit;
  final Map<String, String> legende;

  bool get estAsset => url.startsWith(prefixeAsset);
  String get cheminAsset => url.substring(prefixeAsset.length);
  bool get estAffiche => genre == 'affiche';

  /// Rapport largeur/hauteur annoncé, ou null s'il est inconnu.
  double? get ratio => largeur != null && hauteur != null ? largeur! / hauteur! : null;

  static ImageFiche? depuisJson(Object? v) {
    if (v is! Map) return null;
    final url = urlImageValide(v['url']);
    if (url == null) return null;
    final credit = v['credit'] is String ? (v['credit'] as String).trim() : '';
    final genre = v['genre'] == 'affiche' ? 'affiche' : 'photo';
    return ImageFiche(
      url: url,
      largeur: _dimension(v['largeur']),
      hauteur: _dimension(v['hauteur']),
      genre: genre,
      credit: credit.isEmpty ? null : (credit.length > 120 ? credit.substring(0, 120) : credit),
      legende: _textesLangue(v['legende']),
    );
  }
}

/// Vidéo YouTube d'une publication. Elle se lit chez YouTube ; HAYAATI n'en stocke aucune.
class VideoFiche {
  const VideoFiche({required this.youtube, this.titre = const <String, String>{}});

  /// Identifiant YouTube déjà validé (11 caractères).
  final String youtube;
  final Map<String, String> titre;

  String get lien => 'https://www.youtube.com/watch?v=$youtube';
  String get miniature => 'https://i.ytimg.com/vi/$youtube/hqdefault.jpg';

  static VideoFiche? depuisJson(Object? v) {
    if (v is! Map) return null;
    final id = idYoutubeValide(v['youtube']);
    return id == null ? null : VideoFiche(youtube: id, titre: _textesLangue(v['titre']));
  }
}

/// Bloc « medias » d'une publication : une image et/ou une vidéo.
class Medias {
  const Medias({this.image, this.video});

  final ImageFiche? image;
  final VideoFiche? video;

  bool get vide => image == null && video == null;

  /// Null quand le bloc est absent ou qu'aucun média n'est valide : la publication s'affiche alors sans média.
  static Medias? depuisJson(Object? v) {
    if (v is! Map) return null;
    final m = Medias(image: ImageFiche.depuisJson(v['image']), video: VideoFiche.depuisJson(v['video']));
    return m.vide ? null : m;
  }
}
