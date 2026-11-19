/// Paramètres d'une méthode de calcul des horaires de prière. Mêmes six méthodes, mêmes angles et mêmes clés que
/// core/prayertimes.py (CalculationMethod) : la clé est ce qu'on enregistre dans les réglages.
class MethodeCalcul {
  const MethodeCalcul({
    required this.cle,
    required this.nom,
    required this.angleFajr,
    this.angleIsha,
    this.ishaApresMaghrib,
  });

  final String cle;
  final String nom;

  /// Dépression du soleil sous l'horizon à l'aube (degrés).
  final double angleFajr;

  /// Dépression du soleil à la nuit tombée (degrés). Null quand l'Isha est fixée en minutes après le Maghrib.
  final double? angleIsha;

  /// Isha = Maghrib + ce nombre de minutes (Umm Al-Qura, Golfe). Null quand l'Isha se calcule par un angle.
  final int? ishaApresMaghrib;

  static const MethodeCalcul mwl =
      MethodeCalcul(cle: 'MWL', nom: 'Muslim World League', angleFajr: 18.0, angleIsha: 17.0);
  static const MethodeCalcul isna = MethodeCalcul(cle: 'ISNA', nom: 'ISNA', angleFajr: 15.0, angleIsha: 15.0);
  static const MethodeCalcul egypte =
      MethodeCalcul(cle: 'EGYPT', nom: 'Egyptian General Authority', angleFajr: 19.5, angleIsha: 17.5);
  static const MethodeCalcul karachi = MethodeCalcul(
      cle: 'KARACHI', nom: 'University of Islamic Sciences, Karachi', angleFajr: 18.0, angleIsha: 18.0);
  static const MethodeCalcul oummAlQoura =
      MethodeCalcul(cle: 'UMM_AL_QURA', nom: 'Umm Al-Qura', angleFajr: 18.5, ishaApresMaghrib: 90);
  static const MethodeCalcul golfe = MethodeCalcul(cle: 'GULF', nom: 'Gulf Region', angleFajr: 19.5, ishaApresMaghrib: 90);

  static const List<MethodeCalcul> toutes = <MethodeCalcul>[mwl, isna, egypte, karachi, oummAlQoura, golfe];

  /// La méthode enregistrée sous cette clé, ou null si la clé est inconnue.
  static MethodeCalcul? depuisCle(String? cle) {
    for (final m in toutes) {
      if (m.cle == cle) return m;
    }
    return null;
  }

  @override
  String toString() => 'MethodeCalcul($cle)';
}
