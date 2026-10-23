import 'modeles.dart';

const List<String> ordreJours = <String>['lun', 'mar', 'mer', 'jeu', 'ven', 'sam', 'dim'];

enum GroupeCours { parPublic, parJour }

/// Une fiche dans une liste, avec sa distance à l'utilisateur quand elle est connue.
class EntreeFiche {
  const EntreeFiche(this.fiche, this.distanceM, {this.aDistance = false});

  final Fiche fiche;
  final double? distanceM;

  /// Service rendu à distance (hors du rayon choisi).
  final bool aDistance;
}

/// Filtres communs à toutes les fiches (Apprendre, Boutique, Accompagnement).
class FiltreFiches {
  const FiltreFiches({
    this.villeId,
    this.niveauMin = 0,
    this.aDistance = false,
    this.langue,
  });

  final String? villeId;
  final int niveauMin;
  final bool aDistance;
  final String? langue;

  FiltreFiches copyWith({int? niveauMin, bool? aDistance}) => FiltreFiches(
        villeId: villeId,
        niveauMin: niveauMin ?? this.niveauMin,
        aDistance: aDistance ?? this.aDistance,
        langue: langue,
      );

  bool accepte(Fiche f) {
    if (f.niveau < niveauMin) return false;
    if (langue != null && !f.langues.contains(langue)) return false;
    if (aDistance && !(f.zone.international || f.zone.paysEntier)) return false;
    final v = villeId;
    if (v != null) {
      final ici = f.villeId == v;
      final dessert = f.zone.paysEntier || f.zone.villes.contains(v);
      if (!ici && !dessert) return false;
    }
    return true;
  }
}

/// Créneau de la journée selon l'heure de début « HH:MM ».
String creneauDe(String heure) {
  final h = int.tryParse(heure.split(':').first) ?? 0;
  if (h < 12) return 'matin';
  if (h < 17) return 'apres_midi';
  return 'soir';
}

class FiltreCours {
  const FiltreCours({
    this.publics = const <String>{},
    this.jours = const <String>{},
    this.creneau,
    this.gratuitSeulement = false,
  });

  final Set<String> publics;
  final Set<String> jours;
  final String? creneau;
  final bool gratuitSeulement;

  bool accepte(Cours c) {
    if (publics.isNotEmpty && !c.publics.any(publics.contains)) return false;
    if (jours.isNotEmpty && !c.jours.any(jours.contains)) return false;
    if (creneau != null && creneauDe(c.debut) != creneau) return false;
    if (gratuitSeulement && !c.gratuit) return false;
    return true;
  }
}

/// Regroupe les classes par public ou par jour de la semaine.
/// Une classe donnée plusieurs jours apparaît sous chacun de ses jours.
Map<String, List<Cours>> grouperCours(List<Cours> cours, GroupeCours mode) {
  final res = <String, List<Cours>>{};
  void ajouter(String cle, Cours c) => (res[cle] ??= <Cours>[]).add(c);

  for (final c in cours) {
    if (mode == GroupeCours.parPublic) {
      final cles = c.publics.isEmpty ? <String>['tous'] : c.publics;
      for (final p in cles) {
        ajouter(p, c);
      }
    } else {
      for (final j in c.jours) {
        ajouter(j, c);
      }
    }
  }
  if (mode == GroupeCours.parJour) {
    return <String, List<Cours>>{
      for (final j in ordreJours)
        if (res.containsKey(j)) j: res[j]!,
    };
  }
  return res;
}
