/// Calendrier hégirien « arithmétique » (cycle de 30 ans), avec ajustement manuel de -2 à +2 jours pour suivre l'observation
/// réelle du croissant. Port de core/time_engine.py (conversion, âge, événements). Dart pur, sans Flutter.
///
/// Ce calendrier est une approximation : la date réelle d'un mois dépend de l'observation du croissant et peut différer d'un ou de
/// deux jours selon le pays et l'autorité religieuse. C'est le rôle de `ajustementFiqh`, que la personne règle elle-même.
library;

const List<String> moisHegiriens = <String>[
  'Muharram',
  'Safar',
  "Rabi' al-Awwal",
  "Rabi' al-Thani",
  'Jumada al-Awwal',
  'Jumada al-Thani',
  'Rajab',
  "Sha'ban",
  'Ramadan',
  'Shawwal',
  "Dhu al-Qa'dah",
  'Dhu al-Hijjah',
];

/// Une date hégirienne.
class DateHegirienne {
  const DateHegirienne({required this.annee, required this.moisNum, required this.jour});

  final int annee;

  /// 1 (Muharram) à 12 (Dhu al-Hijjah).
  final int moisNum;
  final int jour;

  String get moisNom => moisHegiriens[moisNum - 1];

  @override
  bool operator ==(Object other) =>
      other is DateHegirienne && other.annee == annee && other.moisNum == moisNum && other.jour == jour;

  @override
  int get hashCode => Object.hash(annee, moisNum, jour);

  @override
  String toString() => '$jour $moisNom $annee';
}

/// Convertit une date grégorienne en date hégirienne. [ajustementFiqh] (borné à -2..+2 jours) décale la date avant conversion.
DateHegirienne gregorienVersHegirien(int annee, int mois, int jour, {int ajustementFiqh = 0}) {
  final delta = ajustementFiqh.clamp(-2, 2);
  final civile = DateTime(annee, mois, jour + delta);
  var gAnnee = civile.year;
  var gMois = civile.month;
  final gJour = civile.day;
  if (gMois <= 2) {
    gAnnee -= 1;
    gMois += 12;
  }
  final a = (gAnnee / 100).truncate();
  final b = 2 - a + (a / 4).truncate();

  // Jour julien (à minuit)
  final jd = (365.25 * (gAnnee + 4716)).truncate() + (30.6001 * (gMois + 1)).truncate() + gJour + b - 1524.5;

  const jdEpoque = 1948439.5; // 1er Muharram de l'an 1 (époque civile)
  final joursEcoules = jd - jdEpoque;

  var anneeH = ((joursEcoules * 30) / 10631.0).truncate() + 1;
  var cycleJours = joursEcoules - ((anneeH - 1) * 10631 / 30).truncate();
  if (cycleJours < 0) {
    anneeH -= 1;
    cycleJours = joursEcoules - ((anneeH - 1) * 10631 / 30).truncate();
  }

  var moisH = 1;
  for (var m = 1; m <= 12; m++) {
    var joursMois = m % 2 != 0 ? 30 : 29;
    if (m == 12 && ((11 * anneeH + 14) % 30 < 11)) joursMois = 30; // année bissextile islamique
    if (cycleJours < joursMois) {
      moisH = m;
      break;
    }
    cycleJours -= joursMois;
  }
  return DateHegirienne(annee: anneeH, moisNum: moisH, jour: cycleJours.truncate() + 1);
}

/// La même conversion à partir d'une [DateTime] (seule la date compte).
DateHegirienne hegirienDe(DateTime date, {int ajustementFiqh = 0}) =>
    gregorienVersHegirien(date.year, date.month, date.day, ajustementFiqh: ajustementFiqh);

/// Âge en années lunaires. [aujourdhui] est injectable pour les tests ; l'ajustement ne s'applique qu'à aujourd'hui, pas à la naissance.
int calculerAgeIslamique(DateTime naissance, {DateTime? aujourdhui, int ajustementFiqh = 0}) {
  final auj = aujourdhui ?? DateTime.now();
  final hNaissance = gregorienVersHegirien(naissance.year, naissance.month, naissance.day);
  final hActuel = gregorienVersHegirien(auj.year, auj.month, auj.day, ajustementFiqh: ajustementFiqh);
  var age = hActuel.annee - hNaissance.annee;
  if (hActuel.moisNum < hNaissance.moisNum || (hActuel.moisNum == hNaissance.moisNum && hActuel.jour < hNaissance.jour)) {
    age -= 1;
  }
  return age < 0 ? 0 : age;
}

/// Comme [calculerAgeIslamique] pour une date « AAAA-MM-JJ » ; 0 si le texte n'a pas cette forme.
int calculerAgeIslamiqueDepuisTexte(String naissance, {DateTime? aujourdhui, int ajustementFiqh = 0}) {
  final m = RegExp(r'^(\d{4})-(\d{2})-(\d{2})$').firstMatch(naissance.trim());
  if (m == null) return 0;
  final a = int.parse(m.group(1)!);
  final mo = int.parse(m.group(2)!);
  final j = int.parse(m.group(3)!);
  final d = DateTime(a, mo, j);
  if (d.year != a || d.month != mo || d.day != j) return 0;
  return calculerAgeIslamique(d, aujourdhui: aujourdhui, ajustementFiqh: ajustementFiqh);
}

/// La clé de traduction de la grande date du calendrier sunnite correspondant à ce jour, ou null.
/// Mêmes événements que le moteur Python : jours blancs (13, 14, 15 de chaque mois sauf Ramadan et le 13 Dhu al-Hijjah), fin de
/// Ramadan (à partir du 25), les neuf premiers jours de Dhu al-Hijjah (evt_dhu_hijjah_N), Arafa (9), Aïd al-Adha (10 Dhu al-Hijjah),
/// Achoura (10 Muharram). L'Aïd al-Fitr (1er Shawwal) n'y figure PAS : voir LISEZMOI_lot_F2.md.
String? evenementHegirien(int moisH, int jourH) {
  if (const <int>[13, 14, 15].contains(jourH) && moisH != 9) {
    if (!(moisH == 12 && jourH == 13)) return 'evt_jours_blancs';
  }
  if (moisH == 9 && jourH >= 25) return 'evt_fin_ramadan';
  if (moisH == 12 && jourH >= 1 && jourH <= 9) {
    if (jourH == 9) return 'evt_arafa';
    return 'evt_dhu_hijjah_$jourH';
  }
  if (moisH == 12 && jourH == 10) return 'evt_aid_adha';
  if (moisH == 1 && jourH == 10) return 'evt_achoura';
  return null;
}

/// Un événement du mois hégirien en cours, avec la date grégorienne correspondante.
class EvenementHegirien {
  const EvenementHegirien({required this.cle, required this.dateGregorienne, required this.dateHegirienne});

  final String cle;
  final DateTime dateGregorienne;
  final DateHegirienne dateHegirienne;
}

/// Les événements du mois hégirien qui contient [aujourdhui], dans l'ordre. Il n'existe pas de conversion hégirien -> grégorien
/// directe : on parcourt les jours (au plus une soixantaine de conversions).
List<EvenementHegirien> evenementsDuMois(DateTime aujourdhui, {int ajustementFiqh = 0}) {
  final hAuj = hegirienDe(aujourdhui, ajustementFiqh: ajustementFiqh);
  var d = DateTime(aujourdhui.year, aujourdhui.month, aujourdhui.day);
  // Recule jusqu'au premier jour du mois hégirien en cours (garde-fou : 40 jours).
  for (var i = 0; i < 40; i++) {
    final h = hegirienDe(d, ajustementFiqh: ajustementFiqh);
    if (h.moisNum != hAuj.moisNum || h.annee != hAuj.annee) {
      d = DateTime(d.year, d.month, d.day + 1);
      break;
    }
    d = DateTime(d.year, d.month, d.day - 1);
  }
  final evenements = <EvenementHegirien>[];
  for (var i = 0; i < 32; i++) {
    final h = hegirienDe(d, ajustementFiqh: ajustementFiqh);
    if (h.moisNum != hAuj.moisNum || h.annee != hAuj.annee) break;
    final cle = evenementHegirien(h.moisNum, h.jour);
    if (cle != null) evenements.add(EvenementHegirien(cle: cle, dateGregorienne: d, dateHegirienne: h));
    d = DateTime(d.year, d.month, d.day + 1);
  }
  return evenements;
}
