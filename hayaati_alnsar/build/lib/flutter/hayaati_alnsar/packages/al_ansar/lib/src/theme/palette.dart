import 'package:flutter/material.dart';

/// Palette officielle de HAYAATI, reprise à l'identique de gui/palette_hayaati.py
/// (identité « vive et chaleureuse » : terracotta, ocre, vert, sable).
/// Toute couleur du module passe par ici, jamais de code hexadécimal en dur ailleurs.
class PaletteHayaati {
  PaletteHayaati._();

  // Couleur historique : barre d'outils, accents « validé ».
  static const Color vertProfond = Color(0xFF064E3B);
  static const Color vertClair = Color(0xFF0F766E);

  // Identité chaude, inspirée des motifs sahéliens.
  static const Color terracotta = Color(0xFFC1502E);
  static const Color terracottaClair = Color(0xFFF4E4DC);
  static const Color terracottaFonce = Color(0xFF6B2712);
  static const Color ocre = Color(0xFFD9A441);
  static const Color ocreClair = Color(0xFFFBF0DA);
  static const Color ocreFonce = Color(0xFF7A5510);

  // Texte de corps : contraste maximal, jamais coloré par la marque.
  static const Color texteFonce = Color(0xFF2B1607);

  // Neutres et fonds.
  static const Color sable = Color(0xFFFBF6EE);
  static const Color blanc = Color(0xFFFFFFFF);
  static const Color grisTexte = Color(0xFF374151);
  static const Color grisClair = Color(0xFFF3F4F6);

  // Signalétique sémantique.
  static const Color vertSucces = Color(0xFF27500A);
  static const Color rougeErreur = Color(0xFF791F1F);
  static const Color ambreAttente = Color(0xFFD97706);
}
