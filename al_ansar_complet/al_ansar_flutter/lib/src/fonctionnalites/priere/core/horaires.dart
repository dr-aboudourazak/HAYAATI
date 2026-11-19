import 'dart:math' as m;

import 'methodes_calcul.dart';
import 'precautions.dart';

/// Situation du soleil ce jour-là à cette latitude.
enum SituationSolaire {
  /// Le soleil se lève et se couche.
  normale,

  /// Le soleil ne se couche pas (jour polaire) : ni lever, ni coucher, ni aube, ni nuit.
  soleilDeMinuit,

  /// Le soleil ne se lève pas (nuit polaire) : ni lever, ni coucher.
  nuitPolaire,
}

/// Les six horaires d'une journée, au format « HH:MM » (heure locale).
///
/// Un horaire qui n'existe pas ce jour-là (soleil de minuit, nuit polaire) vaut [indisponible] : l'écran doit l'afficher comme
/// tel (et expliquer pourquoi, voir [situation]) plutôt que d'inventer une heure.
class HorairesJour {
  const HorairesJour({
    required this.date,
    required this.fajr,
    required this.lever,
    required this.dhuhr,
    required this.asr,
    required this.maghrib,
    required this.isha,
    required this.methode,
    this.situation = SituationSolaire.normale,
    this.hautesLatitudesAppliquees = false,
  });

  /// Valeur d'un horaire qui n'existe pas ce jour-là.
  static const String indisponible = '--:--';

  /// Jour demandé (année, mois, jour ; l'heure n'a pas de sens ici).
  final DateTime date;
  final String fajr;

  /// Lever du soleil (clé « sunrise » dans le moteur Python) : ce n'est pas une prière.
  final String lever;
  final String dhuhr;
  final String asr;
  final String maghrib;
  final String isha;
  final MethodeCalcul methode;
  final SituationSolaire situation;

  /// Vrai si le Fajr ou l'Isha vient de la règle des hautes latitudes et non du calcul par angle : à signaler à la personne.
  final bool hautesLatitudesAppliquees;

  /// Les clés du moteur Python : fajr, sunrise, dhuhr, asr, maghrib, isha.
  Map<String, String> toMap() => <String, String>{
        'fajr': fajr,
        'sunrise': lever,
        'dhuhr': dhuhr,
        'asr': asr,
        'maghrib': maghrib,
        'isha': isha,
      };

  static final RegExp _forme = RegExp(r'^\d{2}:\d{2}$');

  /// Vrai si cet horaire existe (ni [indisponible], ni valeur incohérente).
  static bool estDisponible(String hhmm) => _forme.hasMatch(hhmm);

  /// L'horaire « HH:MM » converti en date et heure locales du jour demandé ; null s'il n'est pas disponible.
  DateTime? instant(String hhmm) {
    if (!estDisponible(hhmm)) return null;
    final p = hhmm.split(':');
    return DateTime(date.year, date.month, date.day, int.parse(p[0]), int.parse(p[1]));
  }
}

/// Heures décimales -> « HH:MM ». Par défaut la minute est tronquée ; [versLeHaut] prend la minute supérieure (avec une
/// tolérance de 0,06 ms pour que 5,5 h donne bien 05:30 et non 05:31). [ajustementMinutes] s'ajoute ensuite ; le résultat est
/// ramené dans la journée (23:59 + 5 minutes = 00:04).
String formaterHeure(double heures, {bool versLeHaut = false, int ajustementMinutes = 0}) {
  final minutes = heures * 60.0;
  final entier = versLeHaut ? (minutes - 1e-6).ceil() : (minutes + 1e-6).floor();
  final total = (entier + ajustementMinutes) % 1440;
  final h = total ~/ 60;
  final mi = total % 60;
  return '${h.toString().padLeft(2, '0')}:${mi.toString().padLeft(2, '0')}';
}

/// Calcul des horaires de prière (astronomie « simple » : déclinaison et équation du temps). Même cœur que
/// core/prayertimes.py : mêmes formules, mêmes résultats quand on demande l'ancien comportement
/// (`PrecautionHoraires.aucune` et `RegleHautesLatitudes.aucune`), prouvé par le test de parité sur
/// test/fixtures/priere_reference.json. Aucune dépendance Flutter : ce fichier se teste en Dart pur.
///
/// Par défaut, le moteur est PLUS PRUDENT que l'ancien : minute de précaution, règle des hautes latitudes, heures « --:-- » quand
/// le soleil ne se lève ou ne se couche pas, et décalage horaire réel du jour (heure d'été comprise).
class CalculateurHoraires {
  CalculateurHoraires({required double latitude, required double longitude, this.fuseau})
      : _latDeg = latitude,
        _lat = _enRadians(latitude),
        _lng = longitude;

  final double _latDeg;
  final double _lat;
  final double _lng;

  /// Décalage UTC fixe en heures (ex. 0 pour le Togo toute l'année). Null : le moteur prend, pour chaque jour demandé, le décalage
  /// que l'appareil applique ce jour-là (heure d'été comprise) : voir [decalageLocalDu]. Un décalage fixe est le bon choix
  /// quand on calcule pour un lieu qui n'est pas celui de l'appareil.
  final double? fuseau;

  /// Décalage UTC (en heures) que l'appareil applique à midi du jour donné : tient compte de l'heure d'été.
  static double decalageLocalDu(DateTime jour) =>
      DateTime(jour.year, jour.month, jour.day, 12).timeZoneOffset.inMinutes / 60.0;

  /// Fuseau « théorique » d'une longitude (15° = 1 h), arrondi « au pair » comme round() de Python : 7,5° -> 0 h, 22,5° -> 2 h.
  /// Repli grossier, jamais utilisé automatiquement : un fuseau réel diffère souvent du fuseau théorique.
  static double fuseauDeduitDeLongitude(double longitude) => _arrondiPair(longitude / 15.0);

  static double _enRadians(double degres) => degres * (m.pi / 180.0);
  static double _enDegres(double radians) => radians * (180.0 / m.pi);

  /// Arrondi « au pair » (0,5 -> 0 ; 1,5 -> 2) comme round() de Python.
  static double _arrondiPair(double x) {
    final plancher = x.floorToDouble();
    final reste = x - plancher;
    if (reste < 0.5) return plancher;
    if (reste > 0.5) return plancher + 1;
    return plancher % 2 == 0 ? plancher : plancher + 1;
  }

  /// Numéro de jour julien (à midi) de la date grégorienne.
  static int _jourJulien(int annee, int mois, int jour) {
    final a = (14 - mois) ~/ 12;
    final y = annee + 4800 - a;
    final mo = mois + 12 * a - 3;
    return jour + (153 * mo + 2) ~/ 5 + 365 * y + y ~/ 4 - y ~/ 100 + y ~/ 400 - 32045;
  }

  /// (déclinaison en radians, équation du temps en minutes).
  static ({double decl, double eqt}) _declinaisonSolaire(double jd) {
    final d = jd - 2451545.0;
    final gDeg = (357.529 + 0.98560028 * d) % 360;
    final qDeg = (280.459 + 0.98564736 * d) % 360;
    final g = _enRadians(gDeg);
    final lDeg = (qDeg + 1.915 * m.sin(g) + 0.020 * m.sin(2 * g)) % 360;
    final l = _enRadians(lDeg);
    final eDeg = 23.439 - 0.00000036 * d;
    final e = _enRadians(eDeg);
    var ra = _enDegres(m.atan2(m.cos(e) * m.sin(l), m.cos(l)));
    ra = (ra + 360) % 360;
    final eqt = (qDeg - ra) * 4; // 1° d'écart = 4 minutes de temps
    final decl = m.asin(m.sin(e) * m.sin(l));
    return (decl: decl, eqt: eqt);
  }

  /// Valeurs sentinelles de l'angle horaire, héritées du moteur Python.
  static const double _toujoursAuDessus = 999; // le soleil reste toujours au-dessus de cette hauteur
  static const double _neAtteintJamais = 0; // le soleil n'atteint jamais cette hauteur

  /// Angle horaire (degrés) pour une hauteur du soleil donnée ; [_toujoursAuDessus] ou [_neAtteintJamais] si le soleil ne la
  /// franchit pas ce jour-là.
  double _angleHoraire(double decl, double angle) {
    final numerateur = m.sin(_enRadians(angle)) - m.sin(_lat) * m.sin(decl);
    final denominateur = m.cos(_lat) * m.cos(decl);
    final cosOmega = numerateur / denominateur;
    if (cosOmega < -1) return _toujoursAuDessus;
    if (cosOmega > 1) return _neAtteintJamais;
    return _enDegres(m.acos(cosOmega));
  }

  static bool _estSentinelle(double omega) => omega == _toujoursAuDessus || omega == _neAtteintJamais;

  /// Format de l'ancien moteur Python : heures décimales -> « HH:MM », minute tronquée (valeurs aberrantes comprises).
  static String _formaterHistorique(double heures) {
    var h0 = heures;
    if (h0 >= 24) h0 -= 24;
    if (h0 < 0) h0 += 24;
    final h = h0.truncate();
    final mi = ((h0 - h) * 60).truncate();
    return '${h.toString().padLeft(2, '0')}:${mi.toString().padLeft(2, '0')}';
  }

  /// Part de la nuit que Fajr et Isha peuvent occuper au plus, selon la règle (et l'angle de la méthode pour angleCrepuscule).
  double _partDeNuit(RegleHautesLatitudes regle, double angle) {
    final r = regle == RegleHautesLatitudes.automatique
        ? (_latDeg.abs() > 48 ? RegleHautesLatitudes.septiemeDeLaNuit : RegleHautesLatitudes.milieuDeLaNuit)
        : regle;
    switch (r) {
      case RegleHautesLatitudes.septiemeDeLaNuit:
        return 1.0 / 7.0;
      case RegleHautesLatitudes.angleCrepuscule:
        return angle / 60.0;
      case RegleHautesLatitudes.milieuDeLaNuit:
      case RegleHautesLatitudes.automatique:
      case RegleHautesLatitudes.aucune:
        return 0.5;
    }
  }

  /// Durée (heures, dans [0, 24[) qui sépare [a] de [b] en avançant dans le temps.
  static double _ecart(double a, double b) => (b - a + 24) % 24;

  /// Les horaires du jour donné. [asrHanafi] : ombre double (école hanafite) ; sinon ombre simple (chafiite, malikite,
  /// hanbalite). [decalageUtc] remplace [fuseau] et le décalage de l'appareil pour ce jour. [precaution] règle l'arrondi de la
  /// minute et les ajustements manuels ; [regleHautesLatitudes] traite les régions où l'aube et la nuit n'existent pas.
  HorairesJour calculer(
    DateTime date, {
    MethodeCalcul methode = MethodeCalcul.mwl,
    bool asrHanafi = false,
    double? decalageUtc,
    PrecautionHoraires precaution = PrecautionHoraires.prudente,
    RegleHautesLatitudes regleHautesLatitudes = RegleHautesLatitudes.automatique,
  }) {
    final tz = decalageUtc ?? fuseau ?? decalageLocalDu(date);
    final jd = _jourJulien(date.year, date.month, date.day).toDouble();
    final s = _declinaisonSolaire(jd);

    // Dhuhr = transit solaire
    final dhuhr = 12 + (tz - _lng / 15.0) - (s.eqt / 60.0);

    // Lever et coucher du soleil (hauteur -0,833° : réfraction + rayon du disque)
    final omegaSoleil = _angleHoraire(s.decl, -0.833);
    final lever = dhuhr - omegaSoleil / 15.0;
    final coucher = dhuhr + omegaSoleil / 15.0;
    final maghrib = coucher;

    final omegaFajr = _angleHoraire(s.decl, -methode.angleFajr);
    final fajr = dhuhr - omegaFajr / 15.0;

    // Asr : hauteur du soleil = arccot(t + tan|latitude - déclinaison|), t = 1 (standard) ou 2 (hanafite)
    final t = asrHanafi ? 2.0 : 1.0;
    final angleAsr = _enDegres(m.atan(1.0 / (t + m.tan((_lat - s.decl).abs()))));
    final omegaAsr = _angleHoraire(s.decl, angleAsr);
    final asr = dhuhr + omegaAsr / 15.0;

    final double? omegaIsha = methode.ishaApresMaghrib == null ? _angleHoraire(s.decl, -methode.angleIsha!) : null;
    final isha = methode.ishaApresMaghrib != null ? maghrib + methode.ishaApresMaghrib! / 60.0 : dhuhr + omegaIsha! / 15.0;

    // --- Ancien comportement exact : valeurs brutes, minute tronquée, rien d'indisponible.
    final historique = regleHautesLatitudes == RegleHautesLatitudes.aucune &&
        precaution.arrondi == ArrondiHoraires.tronque &&
        !precaution.aUnAjustement;
    if (historique) {
      return HorairesJour(
        date: DateTime(date.year, date.month, date.day),
        fajr: _formaterHistorique(fajr),
        lever: _formaterHistorique(lever),
        dhuhr: _formaterHistorique(dhuhr),
        asr: _formaterHistorique(asr),
        maghrib: _formaterHistorique(maghrib),
        isha: _formaterHistorique(isha),
        methode: methode,
      );
    }

    // --- Comportement prudent.
    var situation = SituationSolaire.normale;
    double? hFajr = fajr;
    double? hLever = lever;
    double? hAsr = asr;
    double? hMaghrib = maghrib;
    double? hIsha = isha;
    var hautesLatitudes = false;

    if (regleHautesLatitudes != RegleHautesLatitudes.aucune) {
      if (omegaSoleil == _toujoursAuDessus) {
        situation = SituationSolaire.soleilDeMinuit;
      } else if (omegaSoleil == _neAtteintJamais) {
        situation = SituationSolaire.nuitPolaire;
      }
      if (situation != SituationSolaire.normale) {
        // Pas de lever ni de coucher : l'aube et la nuit n'ont pas de sens non plus. Dhuhr (le transit) existe toujours.
        hLever = null;
        hMaghrib = null;
        hFajr = null;
        hIsha = null;
        if (_estSentinelle(omegaAsr)) hAsr = null;
      } else {
        final nuit = _ecart(maghrib, lever);
        final partFajr = _partDeNuit(regleHautesLatitudes, methode.angleFajr);
        if (_estSentinelle(omegaFajr) || _ecart(fajr, lever) > partFajr * nuit) {
          hFajr = lever - partFajr * nuit;
          hautesLatitudes = true;
        }
        if (omegaIsha != null) {
          final partIsha = _partDeNuit(regleHautesLatitudes, methode.angleIsha!);
          if (_estSentinelle(omegaIsha) || _ecart(maghrib, isha) > partIsha * nuit) {
            hIsha = maghrib + partIsha * nuit;
            hautesLatitudes = true;
          }
        }
      }
    }

    final prudent = precaution.arrondi == ArrondiHoraires.prudent;
    String f(double? h, String cle, {required bool versLeHaut}) => h == null
        ? HorairesJour.indisponible
        : formaterHeure(h, versLeHaut: prudent && versLeHaut, ajustementMinutes: precaution.ajustement(cle));

    return HorairesJour(
      date: DateTime(date.year, date.month, date.day),
      fajr: f(hFajr, 'fajr', versLeHaut: true),
      lever: f(hLever, 'sunrise', versLeHaut: false),
      dhuhr: f(dhuhr, 'dhuhr', versLeHaut: true),
      asr: f(hAsr, 'asr', versLeHaut: true),
      maghrib: f(hMaghrib, 'maghrib', versLeHaut: true),
      isha: f(hIsha, 'isha', versLeHaut: true),
      methode: methode,
      situation: situation,
      hautesLatitudesAppliquees: hautesLatitudes,
    );
  }

  /// La prochaine prière après [heureDecimale] (ex. 14,5 pour 14 h 30) : (nom, « HH:MM »). Quand toutes les prières du jour
  /// sont passées, c'est la première prière disponible du lendemain. Le lever du soleil n'est pas une prière et n'est jamais
  /// retourné. Les paramètres sont ceux de [calculer].
  ({String nom, String heure}) prochainePriere(
    DateTime date,
    double heureDecimale, {
    MethodeCalcul methode = MethodeCalcul.mwl,
    bool asrHanafi = false,
    double? decalageUtc,
    PrecautionHoraires precaution = PrecautionHoraires.prudente,
    RegleHautesLatitudes regleHautesLatitudes = RegleHautesLatitudes.automatique,
  }) {
    HorairesJour jour(DateTime d) => calculer(d,
        methode: methode,
        asrHanafi: asrHanafi,
        decalageUtc: decalageUtc,
        precaution: precaution,
        regleHautesLatitudes: regleHautesLatitudes);
    List<(String, String)> prieres(HorairesJour h) => <(String, String)>[
          ('fajr', h.fajr),
          ('dhuhr', h.dhuhr),
          ('asr', h.asr),
          ('maghrib', h.maghrib),
          ('isha', h.isha),
        ];
    final aujourdhui = jour(date);
    for (final (nom, valeur) in prieres(aujourdhui)) {
      if (!HorairesJour.estDisponible(valeur)) continue;
      final p = valeur.split(':');
      final decimal = int.parse(p[0]) + int.parse(p[1]) / 60.0;
      if (decimal > heureDecimale) return (nom: nom, heure: valeur);
    }
    final demain = jour(DateTime(date.year, date.month, date.day + 1));
    for (final (nom, valeur) in prieres(demain)) {
      if (HorairesJour.estDisponible(valeur)) return (nom: nom, heure: valeur);
    }
    return (nom: 'dhuhr', heure: demain.dhuhr);
  }
}
