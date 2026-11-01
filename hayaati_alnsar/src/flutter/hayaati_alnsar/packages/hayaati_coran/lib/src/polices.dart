/// Polices du texte coranique. « hauteur » = interligne (multiple de la taille), mesuré sur le Coran entier ;
/// « rapport » = facteur de taille pour que le texte occupe la même largeur que sous Amiri Quran.
/// Mêmes valeurs que POLICES dans gui/pages/page_coran.py.
library;

class ConfigPolice {
  const ConfigPolice(this.cle, this.famille, this.hauteur, this.rapport, this.libelle);

  final String cle;
  final String famille;
  final double hauteur;
  final double rapport;
  final String libelle;
}

const Map<String, ConfigPolice> polices = <String, ConfigPolice>{
  'amiri': ConfigPolice('amiri', 'packages/hayaati_coran/AmiriQuran', 2.3, 1.0, 'Amiri Quran'),
  'naskh': ConfigPolice('naskh', 'packages/hayaati_coran/NotoNaskhArabic', 1.8, 0.94, 'Noto Naskh'),
};

/// Délai avant qu'une page soit comptée comme lue.
const Duration delaiPageLueDefaut = Duration(seconds: 8);
