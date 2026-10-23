import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show SystemUiOverlayStyle;

import 'palette.dart';

/// Police arabe de HAYAATI (déjà déclarée par l'application hôte Flet).
const String policeArabe = 'NotoSansArabic';

/// Thème clair de HAYAATI : bandeau vert profond comme la barre d'outils de
/// l'application, fond sable, cartes blanches, accents terracotta et ocre.
ThemeData themeHayaati({bool arabe = false}) {
  final schema = ColorScheme.fromSeed(
    seedColor: PaletteHayaati.vertProfond,
    brightness: Brightness.light,
  ).copyWith(
    primary: PaletteHayaati.vertProfond,
    onPrimary: PaletteHayaati.blanc,
    secondary: PaletteHayaati.terracotta,
    onSecondary: PaletteHayaati.blanc,
    tertiary: PaletteHayaati.ocre,
    onTertiary: PaletteHayaati.texteFonce,
    secondaryContainer: PaletteHayaati.ocreClair,
    onSecondaryContainer: PaletteHayaati.texteFonce,
    surface: PaletteHayaati.blanc,
    onSurface: PaletteHayaati.texteFonce,
    error: PaletteHayaati.rougeErreur,
    onError: PaletteHayaati.blanc,
  );
  return ThemeData(
    useMaterial3: true,
    colorScheme: schema,
    scaffoldBackgroundColor: PaletteHayaati.sable,
    fontFamily: arabe ? policeArabe : null,
    appBarTheme: const AppBarTheme(
      backgroundColor: PaletteHayaati.vertProfond,
      foregroundColor: PaletteHayaati.blanc,
      elevation: 0,
      scrolledUnderElevation: 0,
      toolbarHeight: 60,
      systemOverlayStyle: SystemUiOverlayStyle.light,
    ),
    chipTheme: const ChipThemeData(
      backgroundColor: PaletteHayaati.ocreClair,
      selectedColor: PaletteHayaati.ocre,
      checkmarkColor: PaletteHayaati.texteFonce,
      labelStyle: TextStyle(color: PaletteHayaati.texteFonce),
      side: BorderSide.none,
    ),
  );
}

/// Carte blanche à coins arrondis et fin liseré, sans ombre.
class CarteHayaati extends StatelessWidget {
  const CarteHayaati({super.key, required this.child, this.margin});

  final Widget child;
  final EdgeInsetsGeometry? margin;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: PaletteHayaati.blanc,
      elevation: 0,
      margin: margin,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: const BorderSide(color: Color(0xFFE5E7EB)),
      ),
      child: child,
    );
  }
}

/// Bandeau vert de HAYAATI. Sur l'écran d'accueil, l'icône de la marque
/// (même fichier que la barre d'outils de l'application) précède le titre.
AppBar barreHayaati(
  String titre, {
  List<Widget> actions = const <Widget>[],
  bool avecIcone = false,
  bool integre = false,
}) {
  final texte = Text(titre, overflow: TextOverflow.ellipsis);
  if (integre) {
    // Dans HAYAATI, le bandeau vert appartient à l'application : ici, simple titre et flèche de retour.
    return AppBar(
      backgroundColor: PaletteHayaati.sable,
      foregroundColor: PaletteHayaati.vertProfond,
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
                  package: 'al_ansar',
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
