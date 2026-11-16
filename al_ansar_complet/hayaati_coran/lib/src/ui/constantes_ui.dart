import 'package:flutter/material.dart';

/// Proportions propres à la page de mushaf (mêmes valeurs que gui/pages/page_coran.py). Les couleurs (fond de page,
/// surlignage, numéros de verset, couleurs du tajweed) viennent de la charte de l'apparence en cours : CharteHayaati.
const double rapportNumero = 0.6; // taille du numéro de verset / taille du texte
const double rapportSigne = 1.2; // taille de ۩ et ۞ / taille du texte

/// Le dernier verset d'une page finit exactement au bout de sa dernière ligne, comme dans un mushaf imprimé.
/// Désactiver (false) rend l'affichage justifié ordinaire, dont la dernière ligne s'arrête là où le texte finit.
const bool justifierDerniereLigne = true;
