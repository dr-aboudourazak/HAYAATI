/// Comment une heure calculée devient une minute affichée.
enum ArrondiHoraires {
  /// Minute tronquée, sans aucune précaution : le comportement historique du moteur Python (core/prayertimes.py).
  /// Un Maghrib peut alors tomber jusqu'à 59 secondes avant le coucher réel.
  tronque,

  /// Minute de précaution : chaque heure est arrondie dans le sens qui ne risque ni d'invalider la prière ni de rompre le jeûne
  /// trop tôt. Fajr, Dhuhr, Asr, Maghrib et Isha : minute SUPÉRIEURE (on ne prie ni ne rompt le jeûne avant l'instant calculé).
  /// Lever du soleil : minute INFÉRIEURE (on termine la prière de l'aube avant le lever). L'écart avec « tronque » est de 0 ou
  /// 1 minute, jamais plus.
  prudent,
}

/// Réglage de précaution : l'arrondi de la minute, puis un ajustement manuel (en minutes) par horaire, comme le proposent
/// beaucoup de communautés (« Fajr +2, Isha -3 »...). Les clés sont celles du moteur : fajr, sunrise, dhuhr, asr, maghrib, isha.
class PrecautionHoraires {
  const PrecautionHoraires({this.arrondi = ArrondiHoraires.prudent, this.ajustementsMinutes = const <String, int>{}});

  final ArrondiHoraires arrondi;
  final Map<String, int> ajustementsMinutes;

  /// Borne des ajustements manuels (en minutes, dans les deux sens) : au-delà, on se trompe de réglage plus qu'on ne se protège.
  static const int ajustementMax = 30;

  /// Valeur par défaut recommandée : minute de précaution, aucun ajustement manuel.
  static const PrecautionHoraires prudente = PrecautionHoraires();

  /// Aucune précaution : minute tronquée, comme l'ancien moteur Python (sert aux tests de parité).
  static const PrecautionHoraires aucune = PrecautionHoraires(arrondi: ArrondiHoraires.tronque);

  /// L'ajustement de cet horaire, borné à ±[ajustementMax] minutes.
  int ajustement(String cle) => (ajustementsMinutes[cle] ?? 0).clamp(-ajustementMax, ajustementMax);

  bool get aUnAjustement => ajustementsMinutes.values.any((v) => v != 0);

  /// Copie avec un ajustement de plus (ou remplacé) pour [cle].
  PrecautionHoraires avecAjustement(String cle, int minutes) => PrecautionHoraires(
        arrondi: arrondi,
        ajustementsMinutes: <String, int>{...ajustementsMinutes, cle: minutes},
      );

  PrecautionHoraires avecArrondi(ArrondiHoraires nouveau) =>
      PrecautionHoraires(arrondi: nouveau, ajustementsMinutes: ajustementsMinutes);
}

/// Règle appliquée aux hautes latitudes, quand le soleil ne descend pas assez bas sous l'horizon pour que l'aube et la nuit
/// (Fajr et Isha définis par un angle) existent, ou quand ils tombent trop loin du lever et du coucher du soleil.
/// Cela n'arrive pas au Togo ; cela arrive en Europe du Nord en été (au-delà d'environ 48° de latitude).
enum RegleHautesLatitudes {
  /// Aucune règle : valeurs brutes du moteur Python (résultats incohérents possibles en été aux hautes latitudes).
  /// À réserver aux comparaisons avec l'ancien moteur.
  aucune,

  /// Recommandée : milieu de la nuit jusqu'à 48° de latitude, septième de la nuit au-delà.
  automatique,

  /// Fajr et Isha ne s'écartent jamais de plus de la moitié de la nuit du lever, ou du coucher, du soleil.
  milieuDeLaNuit,

  /// Fajr et Isha ne s'écartent jamais de plus d'un septième de la nuit du lever, ou du coucher, du soleil.
  septiemeDeLaNuit,

  /// Fajr et Isha ne s'écartent jamais de plus de (angle / 60) de la nuit : l'angle de la méthode (18°, 17°...) en fixe la part.
  angleCrepuscule,
}
