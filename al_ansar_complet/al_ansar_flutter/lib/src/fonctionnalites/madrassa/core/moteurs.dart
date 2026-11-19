// Port Dart des moteurs Python de HAYAATI : core/jeu_educatif_engine.py,
// core/langue_arabe_engine.py et core/caravane_savoir_engine.py.
//
// Le comportement est identique à celui de Python : test/madrassa_moteurs_test.dart rejoue des
// cas générés par les moteurs Python eux-mêmes (test/fixtures/madrassa_vecteurs.json).
// Toute évolution d'un moteur Python doit être répercutée ici, puis les vecteurs régénérés.

// ---------------------------------------------------------------- utilitaires

List<String> _chaines(Object? v) => v is List ? v.map((e) => e.toString()).toList() : <String>[];

List<String> _triesUniques(Iterable<String> l) => (l.toSet().toList()..sort());

/// Élément d'une liste avec l'indexation de Python : les indices négatifs comptent depuis la fin.
T? _elementPython<T>(List<T> l, int i) {
  final k = i < 0 ? i + l.length : i;
  return (k >= 0 && k < l.length) ? l[k] : null;
}

Map<String, dynamic> _mp(Object? v) => v is Map ? Map<String, dynamic>.from(v) : <String, dynamic>{};

List<dynamic> _ls(Object? v) => v is List ? v : <dynamic>[];

String _s(Object? v, [String defaut = '']) => v == null ? defaut : v.toString();

// ------------------------------------------------------------ jeu éducatif

const String cleModuleJeu = 'JEU_EDUCATIF_PROGRES';

class Palier {
  const Palier(this.seuil, this.cle, this.libelle);

  final int seuil;
  final String cle;
  final String libelle;
}

const List<Palier> paliersBadges = <Palier>[
  Palier(0, 'apprenti', '🌱 Apprenti du Savoir'),
  Palier(5, 'eclaire', '🕯️ Éclairé du Savoir'),
  Palier(13, 'savant', '📖 Savant HAYAATI'),
  Palier(21, 'gardien', '🏅 Gardien du Sentier'),
];

class ProgresJeu {
  const ProgresJeu({this.lus = const <int>[], this.quizReussis = const <String, List<int>>{}});

  final List<int> lus;
  final Map<String, List<int>> quizReussis;

  Map<String, dynamic> versJson() => <String, dynamic>{
        'lus': lus,
        'quiz_reussis': quizReussis,
      };
}

ProgresJeu normaliserProgresJeu(Object? donnees) {
  final d = _mp(donnees);
  final lus = <int>{};
  for (final e in _ls(d['lus'])) {
    final texte = e.toString();
    if (RegExp(r'^-*\d+$').hasMatch(texte)) {
      final n = int.tryParse(texte);
      if (n != null) lus.add(n);
    }
  }
  final quiz = <String, List<int>>{};
  final brut = d['quiz_reussis'];
  if (brut is Map) {
    brut.forEach((cle, valeur) {
      final c = int.tryParse(cle.toString());
      if (c == null || valeur is! List) return;
      final ints = <int>{};
      for (final v in valeur) {
        final n = int.tryParse(v.toString());
        if (n == null) return;
        ints.add(n);
      }
      quiz[c.toString()] = ints.toList()..sort();
    });
  }
  return ProgresJeu(lus: lus.toList()..sort(), quizReussis: quiz);
}

int compterPerles(ProgresJeu p) => p.quizReussis.values.fold(0, (a, v) => a + v.length);

Palier badgeActuel(int nbPerles) {
  var r = paliersBadges.first;
  for (final p in paliersBadges) {
    if (nbPerles >= p.seuil) r = p;
  }
  return r;
}

/// (perles manquantes, badge suivant), ou null si le dernier palier est atteint.
({int manque, Palier palier})? prochainPalier(int nbPerles) {
  for (final p in paliersBadges) {
    if (nbPerles < p.seuil) return (manque: p.seuil - nbPerles, palier: p);
  }
  return null;
}

ProgresJeu enregistrerReponse(ProgresJeu progres, int indexCategorie, int indexQuestion, bool estCorrecte) {
  final p = normaliserProgresJeu(progres.versJson());
  if (!estCorrecte) return p;
  final cle = indexCategorie.toString();
  final deja = <int>{...(p.quizReussis[cle] ?? <int>[]), indexQuestion};
  final quiz = Map<String, List<int>>.from(p.quizReussis);
  quiz[cle] = deja.toList()..sort();
  return ProgresJeu(lus: p.lus, quizReussis: quiz);
}

Set<int> questionsMaitriseesCategorie(ProgresJeu p, int indexCategorie) =>
    (p.quizReussis[indexCategorie.toString()] ?? <int>[]).toSet();

ProgresJeu basculerLu(ProgresJeu progres, int index, bool valeur) {
  final lus = progres.lus.toSet();
  if (valeur) {
    lus.add(index);
  } else {
    lus.remove(index);
  }
  return ProgresJeu(lus: lus.toList()..sort(), quizReussis: progres.quizReussis);
}

// ------------------------------------------------------------- langue arabe

const String cleModuleLangueArabe = 'LANGUE_ARABE_PROGRES';
const String cleModuleSciencesIslamiques = 'SCIENCES_ISLAMIQUES_PROGRES';

typedef ProgresLangue = Map<String, Map<String, List<String>>>;

Map<String, List<String>> _normaliserEtape(Object? donnees) {
  final d = _mp(donnees);
  return <String, List<String>>{
    'connues': _triesUniques(_chaines(d['connues'])),
    'a_revoir': _triesUniques(_chaines(d['a_revoir'])),
  };
}

ProgresLangue normaliserProgresLangue(Object? donnees) {
  var d = _mp(donnees);
  if (d.containsKey('lettres_connues') || d.containsKey('lettres_a_revoir')) {
    d = <String, dynamic>{
      'alphabet': <String, dynamic>{
        'connues': d['lettres_connues'] ?? <dynamic>[],
        'a_revoir': d['lettres_a_revoir'] ?? <dynamic>[],
      },
    };
  }
  final res = <String, Map<String, List<String>>>{};
  d.forEach((cle, valeur) {
    if (valeur is Map) res[cle] = _normaliserEtape(valeur);
  });
  return res;
}

ProgresLangue marquerItem(ProgresLangue progres, String cleEtape, Object identifiant, bool connu) {
  final p = normaliserProgresLangue(progres);
  final etape = p[cleEtape] ?? <String, List<String>>{'connues': <String>[], 'a_revoir': <String>[]};
  final connues = etape['connues']!.toSet();
  final aRevoir = etape['a_revoir']!.toSet();
  final id = identifiant.toString();
  if (connu) {
    connues.add(id);
    aRevoir.remove(id);
  } else {
    aRevoir.add(id);
    connues.remove(id);
  }
  p[cleEtape] = <String, List<String>>{
    'connues': connues.toList()..sort(),
    'a_revoir': aRevoir.toList()..sort(),
  };
  return p;
}

/// « connu », « a_revoir » ou « non_vu ».
String etatItem(ProgresLangue progres, String cleEtape, Object identifiant) {
  final etape = normaliserProgresLangue(progres)[cleEtape];
  final id = identifiant.toString();
  if (etape != null && etape['connues']!.contains(id)) return 'connu';
  if (etape != null && etape['a_revoir']!.contains(id)) return 'a_revoir';
  return 'non_vu';
}

class ResumeEtape {
  const ResumeEtape(this.connues, this.aRevoir, this.nonVues, this.total);

  final int connues;
  final int aRevoir;
  final int nonVues;
  final int total;

  Map<String, int> toMap() => <String, int>{
        'connues': connues,
        'a_revoir': aRevoir,
        'non_vues': nonVues,
        'total': total,
      };
}

ResumeEtape resumeEtape(ProgresLangue progres, String cleEtape, int totalItems) {
  final etape = normaliserProgresLangue(progres)[cleEtape];
  final c = etape == null ? 0 : etape['connues']!.length;
  final r = etape == null ? 0 : etape['a_revoir']!.length;
  final non = totalItems - c - r;
  return ResumeEtape(c, r, non < 0 ? 0 : non, totalItems);
}

// ------------------------------------------------------- caravane du savoir

class ItemCaravane {
  const ItemCaravane({
    required this.arabe,
    required this.translitteration,
    required this.sens,
    required this.module,
    this.cleEtape = '',
    this.identifiant = '',
    this.complement = false,
  });

  final String arabe;
  final String translitteration;
  final String sens;
  final String module;
  final String cleEtape;
  final String identifiant;

  /// Vrai quand le point est déjà « connu » et ne sert qu'à compléter la séance.
  final bool complement;

  ItemCaravane avecOrigine(String cleEtape, String identifiant, bool complement) => ItemCaravane(
        arabe: arabe,
        translitteration: translitteration,
        sens: sens,
        module: module,
        cleEtape: cleEtape,
        identifiant: identifiant,
        complement: complement,
      );

  Map<String, dynamic> toMap() => <String, dynamic>{
        'arabe': arabe,
        'translitteration': translitteration,
        'sens': sens,
        'module': module,
        'cle_etape': cleEtape,
        'identifiant': identifiant,
        'complement': complement,
      };
}

ItemCaravane? _resoudreAlphabet(Map<String, dynamic> etape, String identifiant) {
  final i = int.tryParse(identifiant.trim());
  if (i == null) return null;
  final l = _elementPython(_ls(etape['lettres']), i);
  if (l == null) return null;
  final m = _mp(l);
  return ItemCaravane(
    arabe: _s(m['lettre']),
    translitteration: _s(m['translitteration']),
    sens: _s(m['nom']),
    module: 'Alphabet',
  );
}

ItemCaravane? _resoudreVocabulaire(Map<String, dynamic> etape, String identifiant) {
  final parties = identifiant.split('_mot');
  if (parties.length != 2) return null;
  final iListe = int.tryParse(parties[0].replaceAll('liste', '').trim());
  final iMot = int.tryParse(parties[1].trim());
  if (iListe == null || iMot == null) return null;
  final liste = _elementPython(_ls(etape['listes']), iListe);
  if (liste is! Map || liste['mots'] is! List) return null;
  final mot = _elementPython(_ls(liste['mots']), iMot);
  if (mot == null) return null;
  final m = _mp(mot);
  return ItemCaravane(
    arabe: _s(m['arabe']),
    translitteration: _s(m['translitteration']),
    sens: _s(m['sens']),
    module: 'Vocabulaire',
  );
}

ItemCaravane? _resoudreConjugaison(Map<String, dynamic> etape, String cleEtape, String identifiant) {
  final tempsCle = cleEtape.substring('conjugaison_'.length);
  for (final t in _ls(etape['temps'])) {
    final temps = _mp(t);
    if (temps['cle'] != tempsCle) continue;
    final prefixe = '${cleEtape}_';
    if (!identifiant.startsWith(prefixe)) return null;
    final i = int.tryParse(identifiant.substring(prefixe.length).trim());
    if (i == null) return null;
    final c = _elementPython(_ls(temps['conjugaisons']), i);
    if (c == null) return null;
    final m = _mp(c);
    return ItemCaravane(
      arabe: _s(m['forme']),
      translitteration: _s(m['translitteration']),
      sens: _s(m['sens']),
      module: 'Conjugaison — ${_s(temps['titre'])}',
    );
  }
  return null;
}

Map<String, dynamic> _premierExemple(Map<String, dynamic> lecon) {
  final ex = _ls(lecon['exemples']);
  return ex.isEmpty ? <String, dynamic>{'arabe': '', 'translitteration': ''} : _mp(ex.first);
}

ItemCaravane? _depuisLecon(Map<String, dynamic> lecon, String module) {
  final ex = _premierExemple(lecon);
  final arabe = _s(ex['arabe']);
  return ItemCaravane(
    arabe: arabe.isNotEmpty ? arabe : _s(lecon['titre']),
    translitteration: _s(ex['translitteration']),
    sens: _s(lecon['titre']),
    module: module,
  );
}

ItemCaravane? _resoudreGrammaire(Map<String, dynamic> etape, String cleEtape, String identifiant) {
  final reste = cleEtape.substring('grammaire_'.length);
  final i = int.tryParse(identifiant.trim());
  if (i == null) return null;
  for (final b in _ls(etape['babs'])) {
    final bab = _mp(b);
    final cleBab = _s(bab['cle']);
    if (reste == cleBab) {
      final lecons = _ls(bab['lecons']);
      if (i >= 0 && i < lecons.length) {
        return _depuisLecon(_mp(lecons[i]), 'Grammaire — ${_s(bab['titre'])}');
      }
    }
    for (final s in _ls(bab['sous_rubriques'])) {
      final sr = _mp(s);
      if (reste == '${cleBab}_${_s(sr['cle'])}') {
        final lecons = _ls(sr['lecons']);
        if (i >= 0 && i < lecons.length) {
          return _depuisLecon(_mp(lecons[i]), 'Grammaire — ${_s(bab['titre'])} / ${_s(sr['titre'])}');
        }
      }
    }
  }
  return null;
}

ItemCaravane? _resoudreLecture(Map<String, dynamic> etape, String identifiant) {
  final i = int.tryParse(identifiant.trim());
  if (i == null) return null;
  final t = _elementPython(_ls(etape['textes']), i);
  if (t == null) return null;
  final m = _mp(t);
  return ItemCaravane(arabe: _s(m['titre']), translitteration: '', sens: _s(m['niveau']), module: 'Lecture');
}

ItemCaravane? _resoudreSciences(Map<String, dynamic>? contenu, String cleEtape, String identifiant) {
  if (contenu == null || contenu.isEmpty) return null;
  final domaine = cleEtape.substring('sciences_'.length);
  final i = int.tryParse(identifiant.trim());
  if (i == null) return null;
  for (final e in _ls(contenu['etapes'])) {
    final etape = _mp(e);
    if (etape['cle'] != domaine) continue;
    final lecons = _ls(etape['lecons']);
    if (i >= 0 && i < lecons.length) {
      return _depuisLecon(_mp(lecons[i]), 'Sciences islamiques — ${_s(etape['titre'])}');
    }
  }
  return null;
}

/// Retrouve (arabe, translittération, sens, module) pour un identifiant de progression.
/// Renvoie null si le contenu a changé ou disparu : l'appelant ignore ces cas.
ItemCaravane? resoudreItem(
  Map<String, dynamic> contenuLangue,
  String cleEtape,
  String identifiant, {
  Map<String, dynamic>? contenuSciences,
}) {
  try {
    final index = <Object?, Map<String, dynamic>>{
      for (final e in _ls(contenuLangue['etapes'])) _mp(e)['cle']: _mp(e),
    };
    Map<String, dynamic> etape(String cle) => index[cle] ?? <String, dynamic>{};
    if (cleEtape == 'alphabet') return _resoudreAlphabet(etape('alphabet'), identifiant);
    if (cleEtape == 'vocabulaire') return _resoudreVocabulaire(etape('vocabulaire'), identifiant);
    if (cleEtape.startsWith('conjugaison_')) return _resoudreConjugaison(etape('conjugaison'), cleEtape, identifiant);
    if (cleEtape.startsWith('grammaire_')) return _resoudreGrammaire(etape('grammaire'), cleEtape, identifiant);
    if (cleEtape == 'lecture') return _resoudreLecture(etape('lecture'), identifiant);
    if (cleEtape.startsWith('sciences_')) return _resoudreSciences(contenuSciences, cleEtape, identifiant);
  } catch (_) {
    return null;
  }
  return null;
}

/// Priorité aux points « à revoir » de tous les modules ; si la séance est trop courte,
/// elle est complétée par des points déjà « connus » pour ne jamais présenter un écran vide.
List<ItemCaravane> construireSessionRevision(
  ProgresLangue progres,
  Map<String, dynamic> contenuLangue, {
  int tailleMax = 10,
  Map<String, dynamic>? contenuSciences,
}) {
  final candidats = <ItemCaravane>[];
  for (final e in progres.entries) {
    if (e.key == 'caravane') continue;
    for (final id in e.value['a_revoir'] ?? <String>[]) {
      final item = resoudreItem(contenuLangue, e.key, id, contenuSciences: contenuSciences);
      if (item != null) candidats.add(item.avecOrigine(e.key, id, false));
    }
  }
  if (candidats.length < tailleMax) {
    for (final e in progres.entries) {
      if (e.key == 'caravane' || candidats.length >= tailleMax) continue;
      for (final id in e.value['connues'] ?? <String>[]) {
        if (candidats.length >= tailleMax) break;
        final item = resoudreItem(contenuLangue, e.key, id, contenuSciences: contenuSciences);
        if (item != null) candidats.add(item.avecOrigine(e.key, id, true));
      }
    }
  }
  return candidats.length > tailleMax ? candidats.sublist(0, tailleMax) : candidats;
}

int compterPointsARevoir(ProgresLangue progres) => progres.entries
    .where((e) => e.key != 'caravane')
    .fold(0, (a, e) => a + (e.value['a_revoir']?.length ?? 0));
