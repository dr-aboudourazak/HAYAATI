/// Moteur de lecture coranique. Port de core/quran_engine.py : index des 114 sourates, texte de chaque sourate
/// chargé à la demande, pages du mushaf de Médine (1-604).
///
/// Ce fichier ne dépend pas de Flutter. Les fichiers sont lus par un [LecteurFichier] fourni par l'appelant
/// (rootBundle dans l'application, le disque dans les tests).
library;

import 'dart:convert';

import 'texte.dart';

/// Lit un fichier du dossier assets/coran/ par son nom (« index.json », « surah_001.json »...).
typedef LecteurFichier = Future<String> Function(String nom);

/// Reçoit les messages d'erreur du moteur (journal de diagnostic). Facultatif.
typedef Journal = void Function(String message);

class EntreeSourate {
  const EntreeSourate({
    required this.numero,
    required this.nomArabe,
    required this.translitteration,
    required this.nomAnglais,
    required this.nbVersets,
    required this.revelation,
  });

  final int numero;
  final String nomArabe;
  final String translitteration;
  final String nomAnglais;
  final int nbVersets;

  /// « meccane » ou « medinoise ».
  final String revelation;

  factory EntreeSourate.depuisJson(Map<String, dynamic> j) => EntreeSourate(
        numero: (j['numero'] as num).toInt(),
        nomArabe: (j['nom_arabe'] ?? '').toString(),
        translitteration: (j['translitteration'] ?? '').toString(),
        nomAnglais: (j['nom_anglais'] ?? '').toString(),
        nbVersets: (j['nb_versets'] as num?)?.toInt() ?? 0,
        revelation: (j['revelation'] ?? '').toString(),
      );
}

class VersetCoran {
  const VersetCoran({
    required this.numero,
    required this.texte,
    required this.page,
    required this.tajweed,
    required this.sajda,
  });

  final int numero;

  /// Texte VERBATIM de Tanzil (signes de pause, ۩ et ۞ intégrés).
  final String texte;

  /// Page du mushaf (1-604) qui contient le verset.
  final int page;
  final List<List<int>> tajweed;

  /// Vrai si le signe ۩ figure dans le texte (verset de prosternation).
  final bool sajda;

  factory VersetCoran.depuisJson(Map<String, dynamic> j) {
    final texte = (j['texte'] ?? '').toString();
    return VersetCoran(
      numero: (j['numero'] as num).toInt(),
      texte: texte,
      page: (j['page'] as num?)?.toInt() ?? 0,
      tajweed: annotationsDepuisJson(j['tajweed']),
      sajda: texte.contains(signeSajda),
    );
  }
}

class SourateCoran {
  const SourateCoran({
    required this.numero,
    required this.nomArabe,
    required this.basmalah,
    required this.basmalahTajweed,
    required this.versets,
  });

  final int numero;
  final String nomArabe;

  /// La basmala (que Tanzil place au début du verset 1 de chaque sourate sauf 1 et 9) est mise à part ici.
  final String? basmalah;
  final List<List<int>>? basmalahTajweed;
  final List<VersetCoran> versets;

  factory SourateCoran.depuisJson(Map<String, dynamic> j) => SourateCoran(
        numero: (j['numero'] as num).toInt(),
        nomArabe: (j['nom_arabe'] ?? '').toString(),
        basmalah: j['basmalah'] as String?,
        basmalahTajweed: j['basmalah_tajweed'] == null ? null : annotationsDepuisJson(j['basmalah_tajweed']),
        versets: <VersetCoran>[
          for (final v in (j['versets'] as List? ?? const <dynamic>[])) VersetCoran.depuisJson(Map<String, dynamic>.from(v as Map)),
        ],
      );
}

/// [sourate, premier verset, dernier verset] d'un morceau de page.
class SegmentPage {
  const SegmentPage(this.sourate, this.premier, this.dernier);

  final int sourate;
  final int premier;
  final int dernier;
}

/// Contenu d'une page du mushaf, un élément par sourate présente.
class BlocPage {
  const BlocPage({
    required this.sourate,
    required this.nomArabe,
    required this.debut,
    required this.basmalah,
    required this.basmalahTajweed,
    required this.versets,
  });

  final int sourate;
  final String nomArabe;

  /// Vrai si la sourate commence sur cette page.
  final bool debut;
  final String? basmalah;
  final List<List<int>>? basmalahTajweed;
  final List<VersetCoran> versets;
}

class MoteurCoran {
  MoteurCoran._(this._lire, this._journal, this.index, this._juzParPage, this._segments);

  final LecteurFichier _lire;
  final Journal? _journal;

  /// Les 114 entrées, dans l'ordre. Vide si l'index n'a pas pu être lu.
  final List<EntreeSourate> index;
  final List<int?> _juzParPage;
  final List<List<SegmentPage>> _segments;
  final Map<int, SourateCoran> _cache = <int, SourateCoran>{};

  /// Charge l'index et la table des pages (petits fichiers). Une erreur de lecture est journalisée et laisse un
  /// moteur vide : l'écran affiche alors « texte indisponible » au lieu de planter.
  static Future<MoteurCoran> ouvrir(LecteurFichier lire, {Journal? journal}) async {
    var index = <EntreeSourate>[];
    try {
      final brut = jsonDecode(await lire('index.json')) as List;
      index = <EntreeSourate>[for (final e in brut) EntreeSourate.depuisJson(Map<String, dynamic>.from(e as Map))];
    } catch (e) {
      journal?.call("[CORAN] Échec de chargement de l'index : $e");
    }
    var juz = <int?>[];
    var segments = <List<SegmentPage>>[];
    try {
      final brut = Map<String, dynamic>.from(jsonDecode(await lire('pages.json')) as Map);
      juz = <int?>[for (final j in (brut['juz_par_page'] as List)) (j as num?)?.toInt()];
      segments = <List<SegmentPage>>[
        for (final s in (brut['segments'] as List))
          if (s == null)
            const <SegmentPage>[]
          else
            <SegmentPage>[
              for (final t in (s as List)) SegmentPage((t[0] as num).toInt(), (t[1] as num).toInt(), (t[2] as num).toInt()),
            ],
      ];
    } catch (e) {
      journal?.call('[CORAN] Échec de chargement de pages.json : $e');
    }
    return MoteurCoran._(lire, journal, index, juz, segments);
  }

  /// Numéro du juz (1-30) qui contient la page de mushaf donnée (1-604).
  int? juzDePage(int page) => (page > 0 && page < _juzParPage.length) ? _juzParPage[page] : null;

  /// [[sourate, premier verset, dernier verset], ...] de la page de mushaf (1-604).
  List<SegmentPage> segmentsDePage(int page) => (page > 0 && page < _segments.length) ? _segments[page] : const <SegmentPage>[];

  /// Sourate du premier verset de la page (celle que le mushaf imprime en en-tête).
  int? sourateDePage(int page) {
    final s = segmentsDePage(page);
    return s.isEmpty ? null : s.first.sourate;
  }

  String nomSourate(int numero) {
    for (final e in index) {
      if (e.numero == numero) return e.nomArabe;
    }
    return '';
  }

  /// Texte complet d'une sourate (1 à 114), mis en cache après le premier chargement ; null si illisible.
  Future<SourateCoran?> sourate(int numero) async {
    final deja = _cache[numero];
    if (deja != null) return deja;
    final nom = 'surah_${numero.toString().padLeft(3, '0')}.json';
    try {
      final j = Map<String, dynamic>.from(jsonDecode(await _lire(nom)) as Map);
      return _cache[numero] = SourateCoran.depuisJson(j);
    } catch (e) {
      _journal?.call('[CORAN] Échec de chargement de la sourate $numero ($nom) : $e');
      return null;
    }
  }

  /// Contenu d'une page de mushaf, dans l'ordre de lecture. Liste vide si la page est inconnue ou illisible.
  Future<List<BlocPage>> versetsDePage(int page) async {
    final blocs = <BlocPage>[];
    for (final seg in segmentsDePage(page)) {
      final s = await sourate(seg.sourate);
      if (s == null) continue;
      final debut = seg.premier == 1;
      blocs.add(BlocPage(
        sourate: seg.sourate,
        nomArabe: nomSourate(seg.sourate),
        debut: debut,
        basmalah: debut ? s.basmalah : null,
        basmalahTajweed: debut ? s.basmalahTajweed : null,
        versets: <VersetCoran>[for (final v in s.versets) if (v.numero >= seg.premier && v.numero <= seg.dernier) v],
      ));
    }
    return blocs;
  }

  /// Page de mushaf (1-604) qui contient le verset donné, ou null s'il n'existe pas.
  Future<int?> pageDeVerset(int sourate, int verset) async {
    final s = await this.sourate(sourate);
    if (s == null) return null;
    for (final v in s.versets) {
      if (v.numero == verset) return v.page;
    }
    return null;
  }

  /// Page de mushaf où commence la sourate.
  Future<int?> premierePageSourate(int sourate) => pageDeVerset(sourate, 1);

  /// Pages de mushaf (distinctes, dans l'ordre) que couvre la sourate.
  Future<List<int>> pagesDeSourate(int sourate) async {
    final s = await this.sourate(sourate);
    if (s == null) return const <int>[];
    final pages = <int>[];
    for (final v in s.versets) {
      if (pages.isEmpty || pages.last != v.page) pages.add(v.page);
    }
    return pages;
  }

  /// Texte arabe d'un verset, tel que stocké (verbatim).
  Future<String?> texteVerset(int sourate, int verset) async {
    final s = await this.sourate(sourate);
    if (s == null) return null;
    for (final v in s.versets) {
      if (v.numero == verset) return v.texte;
    }
    return null;
  }
}
