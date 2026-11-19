import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show SystemUiOverlayStyle;

import 'apparence.dart';
import 'charte_hayaati.dart';
import 'palette.dart';

/// Police arabe de HAYAATI. Désignée par son nom de paquet : elle est embarquée par hayaati_ui, donc disponible
/// aussi bien dans HAYAATI (Flet) que dans une application Flutter pure.
const String policeArabe = 'packages/hayaati_ui/NotoSansArabic';

/// Thème de HAYAATI. Par défaut, la charte officielle : bandeau vert profond comme la barre d'outils de l'application,
/// fond sable, cartes blanches, accents terracotta et ocre. [apparence] choisit un autre arrière-plan (papier, sombre)
/// ou une autre couleur principale (terracotta, ocre) ; toutes les couleurs viennent alors de [CharteHayaati].
ThemeData themeHayaati({bool arabe = false, ApparenceHayaati apparence = ApparenceHayaati.defaut}) {
  final ch = CharteHayaati.depuis(apparence);
  final sombre = ch.sombre;
  const encreSurOcre = Color(0xFF2B1607); // texte sur un aplat ocre ou terracotta clair
  var schema = ColorScheme.fromSeed(
    seedColor: ch.primaire,
    brightness: sombre ? Brightness.dark : Brightness.light,
  ).copyWith(
    primary: ch.primaire,
    onPrimary: ch.surPrimaire,
    secondary: ch.terracotta,
    onSecondary: sombre ? encreSurOcre : PaletteHayaati.blanc,
    tertiary: ch.ocre,
    onTertiary: encreSurOcre,
    secondaryContainer: ch.ocreClair,
    onSecondaryContainer: ch.texteFonce,
    surface: ch.blanc,
    onSurface: ch.texteFonce,
    error: ch.rougeErreur,
    onError: sombre ? encreSurOcre : PaletteHayaati.blanc,
  );
  if (apparence.fond != 'clair') {
    // Papier et sombre : les surfaces teintées par Material suivent la charte au lieu du vert d'origine.
    schema = schema.copyWith(
      surfaceTint: Colors.transparent,
      surfaceContainerLowest: ch.blanc,
      surfaceContainerLow: ch.blanc,
      surfaceContainer: ch.grisClair,
      surfaceContainerHigh: ch.grisClair,
      surfaceContainerHighest: ch.grisClair,
      outline: ch.grisTexte,
      outlineVariant: ch.bordure,
    );
  }
  final barreSombre = luminance(ch.valeurs.primaire) < 0.4; // texte clair sur un bandeau foncé, et inversement
  return ThemeData(
    useMaterial3: true,
    colorScheme: schema,
    scaffoldBackgroundColor: ch.sable,
    fontFamily: arabe ? policeArabe : null,
    extensions: <ThemeExtension<dynamic>>[ch],
    appBarTheme: AppBarTheme(
      backgroundColor: ch.primaire,
      foregroundColor: ch.surPrimaire,
      elevation: 0,
      scrolledUnderElevation: 0,
      toolbarHeight: 60,
      systemOverlayStyle: barreSombre ? SystemUiOverlayStyle.light : SystemUiOverlayStyle.dark,
    ),
    chipTheme: ChipThemeData(
      backgroundColor: ch.ocreClair,
      selectedColor: sombre ? const Color(0xFF6B5016) : ch.ocre,
      checkmarkColor: ch.texteFonce,
      labelStyle: TextStyle(color: ch.texteFonce),
      side: BorderSide.none,
    ),
    dividerTheme: apparence.fond == 'clair' ? null : DividerThemeData(color: ch.bordure),
  );
}

/// Carte à coins arrondis et fin liseré, sans ombre.
class CarteHayaati extends StatelessWidget {
  const CarteHayaati({super.key, required this.child, this.margin});

  final Widget child;
  final EdgeInsetsGeometry? margin;

  @override
  Widget build(BuildContext context) {
    final ch = CharteHayaati.of(context);
    return Card(
      color: ch.blanc,
      elevation: 0,
      margin: margin,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: ch.bordure),
      ),
      child: child,
    );
  }
}

/// Bandeau vert de HAYAATI. Sur l'écran d'accueil, l'icône de la marque
/// (même fichier que la barre d'outils de l'application) précède le titre.
///
/// [illustration] : pictogramme ou icône affiché à côté du titre quand la page d'une rubrique est ouverte
/// (jamais dans la liste des rubriques, où chaque tuile a déjà son icône).
PreferredSizeWidget barreHayaati(
  String titre, {
  List<Widget> actions = const <Widget>[],
  bool avecIcone = false,
  bool integre = false,
  Widget? illustration,
}) =>
    BarreHayaati(titre, actions: actions, avecIcone: avecIcone, integre: integre, illustration: illustration);

/// Bandeau de HAYAATI (voir [barreHayaati]). Les couleurs de la barre intégrée viennent de la charte en cours.
class BarreHayaati extends StatelessWidget implements PreferredSizeWidget {
  const BarreHayaati(
    this.titre, {
    super.key,
    this.actions = const <Widget>[],
    this.avecIcone = false,
    this.integre = false,
    this.illustration,
  });

  final String titre;
  final List<Widget> actions;
  final bool avecIcone;
  final bool integre;
  final Widget? illustration;

  @override
  Size get preferredSize => Size.fromHeight(integre ? 48 : 60);

  @override
  Widget build(BuildContext context) {
    final simple = Text(titre, overflow: TextOverflow.ellipsis);
    final texte = illustration == null
        ? simple
        : Row(
            mainAxisSize: MainAxisSize.min,
            children: [illustration!, const SizedBox(width: 8), Flexible(child: simple)],
          );
    if (integre) {
      // Dans HAYAATI, le bandeau vert appartient à l'application : ici, simple titre et flèche de retour.
      final ch = CharteHayaati.of(context);
      return AppBar(
        backgroundColor: ch.sable,
        foregroundColor: ch.vertProfond,
        toolbarHeight: 48,
        elevation: 0,
        scrolledUnderElevation: 0,
        title: texte,
        actions: actions,
      );
    }
    return AppBar(
      title: avecIcone
          ? Row(
              children: [
                ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: Image.asset(
                    'assets/images/Icone-Hayaati.png',
                    package: 'hayaati_ui',
                    width: 38,
                    height: 38,
                    cacheWidth: 114,
                    fit: BoxFit.contain,
                    errorBuilder: (context, erreur, trace) => const SizedBox(width: 38, height: 38),
                  ),
                ),
                const SizedBox(width: 10),
                Flexible(child: texte),
              ],
            )
          : texte,
      actions: actions,
    );
  }
}
