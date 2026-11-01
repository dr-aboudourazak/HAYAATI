import 'package:flutter/material.dart';

/// Couleurs et proportions propres à la page de mushaf (mêmes valeurs que gui/pages/page_coran.py).
/// Les couleurs de la charte (vert, ocre, texte) viennent de PaletteHayaati, jamais d'ici.
const Color fondPage = Color(0xFFFFFDF8); // presque blanc
const Color surlignage = Color(0xFFFFE082); // verset sélectionné ou trouvé : jaune franc
const Color couleurNumero = Color(0xFF7B4F00); // brun doré foncé (contraste 7,0 sur le fond)
const Color couleurNumeroSignet = Color(0xFF9B1C1C); // numéro d'un verset qui porte un signet

const double rapportNumero = 0.6; // taille du numéro de verset / taille du texte
const double rapportSigne = 1.2; // taille de ۩ et ۞ / taille du texte
