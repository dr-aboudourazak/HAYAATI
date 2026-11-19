import 'dart:async';

import 'package:flutter/foundation.dart';

import 'etat_lecture.dart';
import 'moteur_coran.dart';
import 'polices.dart';
import 'texte.dart';
import 'textes.dart';

/// Demande à l'écran de lecture d'afficher une page précise (recherche de verset, changement de sourate).
/// [numero] distingue deux demandes successives vers la même page.
class DemandeSaut {
  const DemandeSaut(this.page, this.numero);

  final int page;
  final int numero;
}

/// Message bref à montrer à l'utilisateur (« Signet ajouté... »).
class MessageUi {
  const MessageUi(this.texte, this.numero);

  final String texte;
  final int numero;
}

/// État vivant du module Coran : réglages, page affichée, sélection d'un verset, recherche, signets, progression.
/// Chaque changement d'état de lecture est enregistré (avec un court délai pour regrouper les rafales) dans le
/// [DepotEtatLecture].
class ControleurCoran extends ChangeNotifier {
  ControleurCoran({
    required this.moteur,
    required this.depot,
    this.textes = const TextesCoran(),
    this.delaiPageLue = delaiPageLueDefaut,
    this.delaiSauvegarde = const Duration(milliseconds: 400),
    this.delaiRecherche = const Duration(milliseconds: 350),
  });

  final MoteurCoran moteur;
  final DepotEtatLecture depot;
  final Duration delaiPageLue;
  final Duration delaiSauvegarde;
  final Duration delaiRecherche;

  TextesCoran textes;
  EtatLecture etat = EtatLecture.defauts();

  /// Page de mushaf affichée (1-604) et sourate à laquelle elle se rattache.
  int pageActive = 1;
  int sourateActive = 1;

  /// Verset sélectionné (toucher) ou trouvé par la recherche ; null s'il n'y en a pas.
  VersetRef? selection;

  /// Contenu du champ « n° de verset », et message qui l'accompagne (« Verset 255 - page 42 du mushaf »).
  String filtreVerset = '';
  String? messageRecherche;

  /// Liste des signets de l'écran des sourates : dépliée ou non.
  bool signetsOuverts = false;

  /// Les écrans s'abonnent à ces deux canaux ; chaque nouvelle valeur est un événement.
  final ValueNotifier<DemandeSaut?> saut = ValueNotifier<DemandeSaut?>(null);
  final ValueNotifier<MessageUi?> messages = ValueNotifier<MessageUi?>(null);

  Timer? _minuterieSauvegarde;
  Timer? _minuteriePageLue;
  Timer? _minuterieRecherche;
  int _compteur = 0;
  bool _libere = false;

  ConfigPolice get police => polices[etat.police] ?? polices['amiri']!;

  /// Lit l'état enregistré (ou les valeurs par défaut si rien n'est lisible).
  Future<void> init() async {
    Object? brut;
    try {
      brut = await depot.charger();
    } catch (_) {
      brut = null;
    }
    etat = EtatLecture.depuisJson(brut);
    pageActive = etat.dernierePage ?? 1;
    sourateActive = moteur.sourateDePage(pageActive) ?? 1;
    _notifier();
  }

  void definirTextes(TextesCoran t) {
    textes = t;
    _notifier();
  }

  // ------------------------------------------------------------ ouverture et navigation

  /// Prépare l'ouverture de la lecture à [page] ; [surligne] : verset à montrer sélectionné (signet de verset).
  /// À appeler juste avant d'empiler l'écran de lecture.
  void ouvrirLecture(int sourate, int page, {VersetRef? surligne}) {
    _minuterieRecherche?.cancel();
    sourateActive = sourate;
    pageActive = page;
    selection = surligne;
    filtreVerset = '';
    messageRecherche = null;
    if (etat.definirDernierePage(page)) _planifierSauvegarde();
  }

  /// L'écran de lecture se ferme : une page quittée trop vite n'est pas comptée comme lue.
  void quitterLecture() {
    _minuteriePageLue?.cancel();
    _minuterieRecherche?.cancel();
    selection = null;
    filtreVerset = '';
    messageRecherche = null;
    // Après la fermeture de l'écran (pas pendant) : l'écran des sourates se met à jour (reprise, progression).
    Future<void>.microtask(_notifier);
  }

  /// À appeler quand une page devient la page affichée (ouverture, saut, reprise).
  void pageAffichee(int page) {
    if (page < 1 || page > nbPages) return;
    pageActive = page;
    _minuteriePageLue?.cancel();
    if (etat.definirDernierePage(page)) _planifierSauvegarde();
    _minuteriePageLue = Timer(delaiPageLue, () {
      // Une page n'est comptée comme lue qu'après un temps d'affichage : le simple défilement ne compte pas.
      if (!_libere && pageActive == page && etat.marquerPageLue(page)) {
        _planifierSauvegarde();
        _notifier();
      }
    });
    _notifier();
  }

  /// L'utilisateur a feuilleté ou défilé jusqu'à [page] : la sourate affichée suit (comme l'en-tête d'un mushaf).
  void pageFeuilletee(int page) {
    final s = moteur.sourateDePage(page);
    if (s != null) sourateActive = s;
    pageAffichee(page);
  }

  /// Ouvre la sourate [numero] à sa première page (flèches « sourate précédente / suivante »).
  Future<void> ouvrirSourate(int numero) async {
    if (numero < 1 || numero > 114) return;
    final page = await moteur.premierePageSourate(numero);
    if (page == null || _libere) return;
    _minuterieRecherche?.cancel();
    sourateActive = numero;
    selection = null;
    filtreVerset = '';
    messageRecherche = null;
    pageAffichee(page); // d'abord la page : l'écran, en la rejoignant, constate qu'elle est déjà la page active
    _demanderSaut(page);
  }

  void _demanderSaut(int page) => saut.value = DemandeSaut(page, ++_compteur);

  void _message(String texte) => messages.value = MessageUi(texte, ++_compteur);

  // ------------------------------------------------------------ sélection d'un verset

  /// Toucher un verset le sélectionne ; le retoucher le désélectionne.
  void toucherVerset(int sourate, int verset) {
    final cle = VersetRef(sourate, verset);
    selection = selection == cle ? null : cle;
    _notifier();
  }

  void effacerSelection() {
    if (selection == null) return;
    selection = null;
    _notifier();
  }

  bool get selectionEstSignet {
    final s = selection;
    return s != null && etat.estSignetVerset(s.sourate, s.verset);
  }

  /// Pose ou retire le signet du verset sélectionné.
  Future<void> basculerSignetVerset() async {
    final sel = selection;
    if (sel == null) return;
    final page = await moteur.pageDeVerset(sel.sourate, sel.verset);
    if (page == null || _libere) return;
    final ajoute = etat.basculerSignetVerset(sel.sourate, sel.verset, page);
    _modifie();
    final modele = ajoute
        ? textes('signet_verset_ajoute', 'Signet ajouté : {nom} {verset}')
        : textes('signet_verset_retire', 'Signet retiré : {nom} {verset}');
    _message(modele.replaceAll('{nom}', moteur.nomSourate(sel.sourate)).replaceAll('{verset}', '${sel.verset}'));
  }

  /// Texte à copier pour le verset sélectionné : le verset entre parenthèses ornées, puis sa référence.
  Future<String?> contenuACopier() async {
    final sel = selection;
    if (sel == null) return null;
    final texte = await moteur.texteVerset(sel.sourate, sel.verset);
    if (texte == null || texte.isEmpty) return null;
    return '$marqueurPremier$texte$marqueurDernier\n[سورة ${moteur.nomSourate(sel.sourate)} : ${sel.verset}]';
  }

  void confirmerCopie() => _message(textes('verset_copie', 'Verset copié'));

  // ------------------------------------------------------------ recherche d'un verset

  /// Saisie dans le champ « n° de verset » : la recherche s'applique après une courte pause (la saisie garde le focus).
  void saisirVerset(String valeur) {
    filtreVerset = valeur;
    _minuterieRecherche?.cancel();
    _minuterieRecherche = Timer(delaiRecherche, () => unawaited(appliquerRechercheVerset()));
  }

  /// Chiffres arabes-indiens (٠-٩) et persans (۰-۹) ramenés à 0-9, comme int() en Python.
  static String _chiffresLatins(String s) {
    final sortie = StringBuffer();
    for (final u in s.codeUnits) {
      if (u >= 0x0660 && u <= 0x0669) {
        sortie.writeCharCode(0x30 + (u - 0x0660));
      } else if (u >= 0x06F0 && u <= 0x06F9) {
        sortie.writeCharCode(0x30 + (u - 0x06F0));
      } else {
        sortie.writeCharCode(u);
      }
    }
    return sortie.toString();
  }

  /// Cherche le verset saisi dans la sourate affichée : le sélectionne et rejoint sa page, où l'on peut continuer
  /// à feuilleter.
  Future<void> appliquerRechercheVerset() async {
    final requete = _chiffresLatins(filtreVerset.trim());
    if (requete.isEmpty) {
      messageRecherche = null;
      selection = null;
      _notifier();
      return;
    }
    int? numero;
    int? page;
    if (requete.length <= 4 && RegExp(r'^[0-9]+$').hasMatch(requete)) {
      numero = int.parse(requete);
      page = await moteur.pageDeVerset(sourateActive, numero);
    }
    if (_libere) return;
    if (page == null || numero == null) {
      messageRecherche = textes('aucun_verset', 'Aucun verset ne correspond à ce numéro.');
      selection = null;
      _notifier();
      return;
    }
    selection = VersetRef(sourateActive, numero);
    messageRecherche = textes.modele(
      'verset_trouve_page',
      <String, Object>{'verset': numero, 'page': page},
      'Verset {verset} - page {page} du mushaf',
    );
    if (page == pageActive) {
      _notifier(); // déjà à l'écran : le surlignage suffit
    } else {
      pageAffichee(page);
      _demanderSaut(page);
    }
  }

  // ------------------------------------------------------------ réglages

  void changerTaille(int delta) {
    final i = taillesValides.indexOf(etat.taille);
    final j = (i + delta).clamp(0, taillesValides.length - 1);
    if (etat.definirTaille(taillesValides[j])) _modifie();
  }

  bool get peutAgrandir => etat.taille < taillesValides.last;
  bool get peutReduire => etat.taille > taillesValides.first;

  void changerPolice(String cle) {
    if (etat.definirPolice(cle)) _modifie();
  }

  void basculerTajweed() {
    etat.definirTajweed(!etat.tajweed);
    _modifie();
  }

  /// « page » (feuilletage) ou « liste » (défilement continu).
  void changerMode(String mode) {
    if (etat.definirMode(mode)) _modifie();
  }

  /// Replie l'en-tête complet vers le haut (toute la hauteur revient à la page) ou le redéploie.
  void basculerEntete() {
    etat.definirEnteteReplie(!etat.enteteReplie);
    _modifie();
  }

  // ------------------------------------------------------------ signets et progression

  bool get pageEstSignet => etat.estSignet(pageActive);

  void basculerSignetPage() {
    final ajoute = etat.basculerSignet(pageActive);
    _modifie();
    final modele = ajoute
        ? textes('signet_ajoute', 'Signet ajouté : page {page}')
        : textes('signet_retire', 'Signet retiré : page {page}');
    _message(modele.replaceAll('{page}', '$pageActive'));
  }

  void retirerSignet(Signet s) {
    if (s.estVerset) {
      etat.basculerSignetVerset(s.sourate!, s.verset!, s.page);
    } else {
      etat.basculerSignet(s.page);
    }
    _modifie();
  }

  void basculerSignetsOuverts() {
    signetsOuverts = !signetsOuverts;
    _notifier();
  }

  void reinitialiserProgression() {
    etat.reinitialiserProgression();
    _modifie();
  }

  // ------------------------------------------------------------ enregistrement

  void _modifie() {
    _planifierSauvegarde();
    _notifier();
  }

  void _planifierSauvegarde() {
    _minuterieSauvegarde?.cancel();
    _minuterieSauvegarde = Timer(delaiSauvegarde, _sauvegarderMaintenant);
  }

  Future<void> _sauvegarderMaintenant() async {
    _minuterieSauvegarde?.cancel();
    _minuterieSauvegarde = null;
    try {
      await depot.sauver(etat.toJson());
    } catch (_) {
      // Un enregistrement raté ne doit jamais empêcher de lire.
    }
  }

  void _notifier() {
    if (!_libere) notifyListeners();
  }

  @override
  void dispose() {
    _libere = true;
    _minuteriePageLue?.cancel();
    _minuterieRecherche?.cancel();
    if (_minuterieSauvegarde != null) {
      _minuterieSauvegarde!.cancel();
      unawaited(_sauvegarderMaintenant());
    }
    saut.dispose();
    messages.dispose();
    super.dispose();
  }
}
