/// Accès sûr au contenu pédagogique de HAYAATI (sections « madrassa », « interface_savoir »,
/// « encyclopedie », « langue_arabe » et « sciences_islamiques » du fichier de langue actif).
/// Le contenu est transmis par l'application hôte : le module n'en garde aucune copie.
library;

Map<String, dynamic> mapDe(Object? v) => v is Map ? Map<String, dynamic>.from(v) : <String, dynamic>{};

List<dynamic> listeDe(Object? v) => v is List ? v : <dynamic>[];

String texteDe(Object? v, [String defaut = '']) => v == null ? defaut : v.toString();

/// Remplace les « {} » d'un gabarit, dans l'ordre, comme le fait Python avec str.format.
String formaterGabarit(String gabarit, List<Object> valeurs) {
  var s = gabarit;
  for (final v in valeurs) {
    final i = s.indexOf('{}');
    if (i < 0) break;
    s = s.replaceRange(i, i + 2, v.toString());
  }
  return s;
}

/// Contenu et progression transmis par l'hôte.
class MadrassaHote {
  const MadrassaHote({
    required this.contenu,
    this.progres = const <String, dynamic>{},
    this.visiteur = false,
    this.surSauver,
  });

  /// Sections du fichier de langue actif.
  final Map<String, dynamic> contenu;

  /// Progression par module : { JEU_EDUCATIF_PROGRES: {...}, LANGUE_ARABE_PROGRES: {...}, SCIENCES_ISLAMIQUES_PROGRES: {...} }.
  final Map<String, dynamic> progres;

  /// Vrai si aucun utilisateur n'est connecté : la progression n'est pas conservée.
  final bool visiteur;

  /// Appelé à chaque changement de progression d'un module.
  final void Function(String module, Map<String, dynamic> donnees)? surSauver;
}

class ContenuMadrassa {
  ContenuMadrassa({
    required this.madrassa,
    required this.savoir,
    required this.encyclopedie,
    required this.langueArabe,
    required this.sciences,
  });

  factory ContenuMadrassa.depuisJson(Map<String, dynamic> j) => ContenuMadrassa(
        madrassa: mapDe(j['madrassa']),
        savoir: mapDe(j['interface_savoir']),
        encyclopedie: mapDe(j['encyclopedie']),
        langueArabe: mapDe(j['langue_arabe']),
        sciences: mapDe(j['sciences_islamiques']),
      );

  final Map<String, dynamic> madrassa;
  final Map<String, dynamic> savoir;
  final Map<String, dynamic> encyclopedie;
  final Map<String, dynamic> langueArabe;
  final Map<String, dynamic> sciences;

  /// Textes du hub (section « madrassa »).
  String m(String cle, [String defaut = '']) => texteDe(madrassa[cle], defaut);

  /// Textes communs aux écrans d'apprentissage (section « interface_savoir »).
  String s(String cle, [String defaut = '']) => texteDe(savoir[cle], defaut);

  /// Textes de l'encyclopédie.
  String e(String cle, [String defaut = '']) => texteDe(encyclopedie[cle], defaut);

  bool get disponible => encyclopedie.isNotEmpty || langueArabe.isNotEmpty || sciences.isNotEmpty;

  List<Map<String, dynamic>> get categories =>
      listeDe(encyclopedie['categories']).map(mapDe).toList();

  List<Map<String, dynamic>> get etapesLangue => listeDe(langueArabe['etapes']).map(mapDe).toList();

  List<Map<String, dynamic>> get etapesSciences => listeDe(sciences['etapes']).map(mapDe).toList();

  Map<String, dynamic> etapeLangue(String cle) {
    for (final e in etapesLangue) {
      if (e['cle'] == cle) return e;
    }
    return <String, dynamic>{};
  }
}
