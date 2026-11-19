/// Réglages de lecture, signets et progression. Port de core/coran_lecture_store.py, MÊME format JSON :
/// le fichier existant de l'utilisateur (coran_lecture.json) est relu tel quel, rien n'est perdu à la migration.
///
/// Ce fichier ne dépend pas de Flutter. Le stockage réel est confié à un [DepotEtatLecture] : l'hôte Flet
/// aujourd'hui (Python écrit le fichier), un fichier local de l'application Flutter le jour où Python disparaît.
library;

import 'texte.dart';

const List<int> taillesValides = <int>[16, 18, 20, 22, 24, 28, 32];
const List<String> modesValides = <String>['page', 'liste'];
const List<String> policesValides = <String>['amiri', 'naskh'];

bool _pageValide(Object? v) => v is int && v >= 1 && v <= nbPages;

/// Équivalent de bool() en Python, pour les valeurs lues d'un fichier JSON quelconque.
bool _vrai(Object? v) {
  if (v == null) return false;
  if (v is bool) return v;
  if (v is num) return v != 0;
  if (v is String) return v.isNotEmpty;
  if (v is List) return v.isNotEmpty;
  if (v is Map) return v.isNotEmpty;
  return true;
}

/// Référence d'un verset (sourate, numéro) : le verset sélectionné ou trouvé par la recherche.
class VersetRef {
  const VersetRef(this.sourate, this.verset);

  final int sourate;
  final int verset;

  @override
  bool operator ==(Object autre) => autre is VersetRef && autre.sourate == sourate && autre.verset == verset;

  @override
  int get hashCode => Object.hash(sourate, verset);

  @override
  String toString() => 'VersetRef($sourate:$verset)';
}

/// Un signet : une page entière (sourate et verset nuls) ou un VERSET précis.
class Signet {
  const Signet(this.page, [this.sourate, this.verset]);

  final int page;
  final int? sourate;
  final int? verset;

  bool get estVerset => sourate != null && verset != null;

  Map<String, dynamic> toJson() => <String, dynamic>{
        'p': page,
        if (sourate != null) 's': sourate,
        if (verset != null) 'v': verset,
      };

  bool correspond(int p, [int? s, int? v]) => page == p && sourate == s && verset == v;
}

class EtatLecture {
  EtatLecture._();

  static const int version = 1;

  /// « page » (feuilletage latéral, un écran = une page de mushaf) ou « liste » (défilement continu).
  String mode = 'page';
  int taille = 20;

  /// « amiri » (Amiri Quran) ou « naskh » (Noto Naskh Arabic).
  String police = 'amiri';
  bool enteteReplie = false;
  bool tajweed = false;
  int? dernierePage;
  List<Signet> signets = <Signet>[];
  List<int> pagesLues = <int>[];

  factory EtatLecture.defauts() => EtatLecture._();

  /// Ramène le contenu d'un fichier (édité, ancien ou illisible) à des valeurs sûres.
  factory EtatLecture.depuisJson(Object? brut) {
    final etat = EtatLecture._();
    if (brut is! Map) return etat;
    final m = brut;
    final mode = m['mode'];
    if (mode is String && modesValides.contains(mode)) etat.mode = mode;
    final taille = m['taille'];
    if (taille is int && taillesValides.contains(taille)) etat.taille = taille;
    final police = m['police'];
    if (police is String && policesValides.contains(police)) etat.police = police;
    etat.enteteReplie = _vrai(m['entete_replie']);
    etat.tajweed = _vrai(m['tajweed']);
    if (_pageValide(m['derniere_page'])) etat.dernierePage = m['derniere_page'] as int;
    if (m['signets'] is List) etat.signets = _nettoyerSignets(m['signets'] as List);
    if (m['pages_lues'] is List) {
      etat.pagesLues = <int>{for (final p in (m['pages_lues'] as List)) if (_pageValide(p)) p as int}.toList()..sort();
    }
    return etat;
  }

  /// Accepte l'ancien format (liste de numéros de page) et le nouveau (dictionnaires).
  static List<Signet> _nettoyerSignets(List liste) {
    final propres = <Signet>[];
    final vus = <String>{};
    for (final brut in liste) {
      Signet entree;
      if (_pageValide(brut)) {
        entree = Signet(brut as int);
      } else if (brut is Map && _pageValide(brut['p'])) {
        final p = brut['p'] as int;
        final s = brut['s'];
        final v = brut['v'];
        if (s is int && v is int && s >= 1 && s <= 114 && v >= 1 && v <= 286) {
          entree = Signet(p, s, v);
        } else {
          entree = Signet(p);
        }
      } else {
        continue;
      }
      if (vus.add('${entree.page}|${entree.sourate}|${entree.verset}')) propres.add(entree);
    }
    _trier(propres);
    return propres;
  }

  /// Tri par (page, verset), STABLE comme celui de Python (List.sort de Dart ne garantit pas la stabilité).
  static void _trier(List<Signet> liste) {
    final decores = <(int, Signet)>[for (var i = 0; i < liste.length; i++) (i, liste[i])];
    decores.sort((a, b) {
      final c = a.$2.page != b.$2.page ? a.$2.page.compareTo(b.$2.page) : (a.$2.verset ?? 0).compareTo(b.$2.verset ?? 0);
      return c != 0 ? c : a.$1.compareTo(b.$1);
    });
    liste
      ..clear()
      ..addAll(<Signet>[for (final d in decores) d.$2]);
  }

  Map<String, dynamic> toJson() => <String, dynamic>{
        'version': version,
        'mode': mode,
        'taille': taille,
        'police': police,
        'entete_replie': enteteReplie,
        'tajweed': tajweed,
        'derniere_page': dernierePage,
        'signets': <Map<String, dynamic>>[for (final s in signets) s.toJson()],
        'pages_lues': List<int>.of(pagesLues),
      };

  // ------------------------------------------------------------ réglages (validés comme en Python)

  bool definirMode(String v) {
    if (!modesValides.contains(v) || mode == v) return false;
    mode = v;
    return true;
  }

  bool definirTaille(int v) {
    if (!taillesValides.contains(v) || taille == v) return false;
    taille = v;
    return true;
  }

  bool definirPolice(String v) {
    if (!policesValides.contains(v) || police == v) return false;
    police = v;
    return true;
  }

  bool definirEnteteReplie(bool v) {
    if (enteteReplie == v) return false;
    enteteReplie = v;
    return true;
  }

  bool definirTajweed(bool v) {
    if (tajweed == v) return false;
    tajweed = v;
    return true;
  }

  bool definirDernierePage(int? v) {
    if (v != null && !_pageValide(v)) return false;
    if (dernierePage == v) return false;
    dernierePage = v;
    return true;
  }

  // ------------------------------------------------------------ signets

  Signet? _trouver(int page, [int? sourate, int? verset]) {
    for (final e in signets) {
      if (e.correspond(page, sourate, verset)) return e;
    }
    return null;
  }

  /// Signet de PAGE (marqueur de page entière).
  bool estSignet(int page) => _trouver(page) != null;

  bool estSignetVerset(int sourate, int verset) => signets.any((e) => e.sourate == sourate && e.verset == verset);

  /// Ajoute ou retire le signet de PAGE. Retourne vrai si le signet existe après l'appel.
  bool basculerSignet(int page) {
    if (!_pageValide(page)) return false;
    return _basculer(page, null, null);
  }

  /// Ajoute ou retire le signet d'un VERSET précis. Retourne vrai s'il existe après l'appel.
  bool basculerSignetVerset(int sourate, int verset, int page) {
    if (!_pageValide(page)) return false;
    return _basculer(page, sourate, verset);
  }

  bool _basculer(int page, int? sourate, int? verset) {
    final existant = _trouver(page, sourate, verset);
    if (existant != null) {
      signets.remove(existant);
      return false;
    }
    signets.add(Signet(page, sourate, verset));
    _trier(signets);
    return true;
  }

  // ------------------------------------------------------------ progression

  /// Compte une page comme lue. Retourne vrai si elle ne l'était pas encore.
  bool marquerPageLue(int page) {
    if (!_pageValide(page) || pagesLues.contains(page)) return false;
    pagesLues = <int>[...pagesLues, page]..sort();
    return true;
  }

  /// (nombre de pages lues, total).
  (int, int) progression() => (pagesLues.length, nbPages);

  /// Remet la progression à zéro (nouvelle lecture complète). Signets et réglages sont conservés.
  void reinitialiserProgression() {
    pagesLues = <int>[];
    dernierePage = null;
  }
}

/// Où l'état de lecture est conservé. Toute erreur doit être absorbée par l'implémentation : un fichier illisible
/// ne doit jamais empêcher de lire le Coran.
abstract class DepotEtatLecture {
  /// Contenu brut enregistré (peut être invalide ; [EtatLecture.depuisJson] le nettoie), ou null s'il n'y en a pas.
  Future<Object?> charger();

  Future<void> sauver(Map<String, dynamic> etat);
}

/// Dépôt en mémoire (tests, mode sans hôte).
class DepotMemoire implements DepotEtatLecture {
  DepotMemoire([this.contenu]);

  Object? contenu;
  int nbSauvegardes = 0;

  @override
  Future<Object?> charger() async => contenu;

  @override
  Future<void> sauver(Map<String, dynamic> etat) async {
    contenu = etat;
    nbSauvegardes++;
  }
}

/// Dépôt confié à l'hôte : l'état initial est fourni par l'hôte, chaque changement lui est signalé.
class DepotHote implements DepotEtatLecture {
  DepotHote({this.initial, required this.surSauver});

  final Object? initial;
  final void Function(Map<String, dynamic> etat) surSauver;

  @override
  Future<Object?> charger() async => initial;

  @override
  Future<void> sauver(Map<String, dynamic> etat) async => surSauver(etat);
}
