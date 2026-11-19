import 'package:al_ansar/al_ansar.dart';
import 'package:al_ansar/src/commun/core/i18n_publications.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('identifiant YouTube', () {
    test('accepte un identifiant nu et les formes d\'adresse de YouTube', () {
      expect(idYoutubeValide('jNQXAC9IVRw'), 'jNQXAC9IVRw');
      expect(idYoutubeValide('https://youtu.be/jNQXAC9IVRw'), 'jNQXAC9IVRw');
      expect(idYoutubeValide('https://www.youtube.com/watch?v=jNQXAC9IVRw&t=3'), 'jNQXAC9IVRw');
      expect(idYoutubeValide('https://m.youtube.com/shorts/jNQXAC9IVRw'), 'jNQXAC9IVRw');
      expect(idYoutubeValide('https://www.youtube.com/embed/jNQXAC9IVRw'), 'jNQXAC9IVRw');
    });

    test('refuse tout le reste', () {
      for (final mauvais in <Object?>[
        null,
        42,
        '',
        'court',
        'jNQXAC9IVRw-trop-long',
        'http://youtu.be/jNQXAC9IVRw',
        'https://evil.example/watch?v=jNQXAC9IVRw',
        'https://youtube.com.evil.example/watch?v=jNQXAC9IVRw',
        'https://user:pw@youtu.be/jNQXAC9IVRw',
        'https://youtu.be:8443/jNQXAC9IVRw',
        'https://www.youtube.com/watch?v=<script>',
        'javascript:alert(1)',
        'jNQXAC9 IVR',
      ]) {
        expect(idYoutubeValide(mauvais), isNull, reason: '$mauvais');
      }
    });
  });

  group('adresse d\'image', () {
    test('https et ressources de l\'hôte seulement', () {
      expect(urlImageValide('https://exemple.org/a.jpg'), 'https://exemple.org/a.jpg');
      expect(urlImageValide('asset:assets/al_ansar/medias/x.png'), 'asset:assets/al_ansar/medias/x.png');
      for (final mauvais in <Object?>[
        null,
        '',
        'http://exemple.org/a.jpg',
        'file:///sdcard/a.jpg',
        'data:image/png;base64,AAAA',
        'javascript:alert(1)',
        '//exemple.org/a.jpg',
        'https://user:pw@exemple.org/a.jpg',
        'https://exemple.org/a b.jpg',
        'asset:../secret.png',
        'asset:assets/../../secret.png',
        'asset:assets/fichier.txt',
      ]) {
        expect(urlImageValide(mauvais), isNull, reason: '$mauvais');
      }
    });
  });

  group('liens de partage', () {
    test('lienPartage ne produit rien sans base sûre', () {
      expect(lienPartage('', 'tg-lome-mad-001'), '');
      expect(lienPartage('http://exemple.org/a/', 'tg-lome-mad-001'), '');
      expect(lienPartage('https://exemple.org/', 'tg-lome-mad-001'), '');
      expect(lienPartage('https://exemple.org/a/?x=1', 'tg-lome-mad-001'), '');
      expect(lienPartage('https://exemple.org/a/', '../x'), '');
      expect(lienPartage('https://exemple.org/a/', 'tg-lome-mad-001'), 'https://exemple.org/a/tg-lome-mad-001');
    });

    test('idFicheDepuisLien lit les deux formes et refuse le reste', () {
      expect(idFicheDepuisLien('https://exemple.org/a/tg-lome-mad-001'), 'tg-lome-mad-001');
      expect(idFicheDepuisLien('hayaati://a/tg-lome-mad-001'), 'tg-lome-mad-001');
      expect(idFicheDepuisLien('  https://exemple.org/a/tg-lome-mad-001/ '), 'tg-lome-mad-001');
      for (final mauvais in <String?>[
        null,
        '',
        'http://exemple.org/a/tg-lome-mad-001',
        'https://exemple.org/b/tg-lome-mad-001',
        'https://exemple.org/a/TG-LOME',
        'https://exemple.org/a/../etc',
        'hayaati://autre/tg-lome-mad-001',
        'hayaati://a/tg-lome-mad-001/extra',
        'https://u:p@exemple.org/a/tg-lome-mad-001',
        'tg-lome-mad-001',
        'javascript:alert(1)',
      ]) {
        expect(idFicheDepuisLien(mauvais), isNull, reason: '$mauvais');
      }
    });

    test('un lien produit par lienPartage est relu à l\'identique', () {
      const id = 'tg-dapaong-mad-001';
      expect(idFicheDepuisLien(lienPartage('https://exemple.org/a/', id)), id);
    });
  });

  group('bloc medias', () {
    test('absent ou sans média valide : null', () {
      expect(Medias.depuisJson(null), isNull);
      expect(Medias.depuisJson('texte'), isNull);
      expect(Medias.depuisJson(<String, dynamic>{}), isNull);
      expect(
        Medias.depuisJson(<String, dynamic>{
          'image': <String, dynamic>{'url': 'http://exemple.org/a.jpg'},
          'video': <String, dynamic>{'youtube': 'invalide'},
        }),
        isNull,
      );
    });

    test('un média invalide n\'empêche pas l\'autre', () {
      final m = Medias.depuisJson(<String, dynamic>{
        'image': <String, dynamic>{'url': 'http://exemple.org/a.jpg'},
        'video': <String, dynamic>{'youtube': 'https://youtu.be/jNQXAC9IVRw'},
      })!;
      expect(m.image, isNull);
      expect(m.video!.youtube, 'jNQXAC9IVRw');
      expect(m.video!.lien, 'https://www.youtube.com/watch?v=jNQXAC9IVRw');
    });

    test('image complète', () {
      final m = Medias.depuisJson(<String, dynamic>{
        'image': <String, dynamic>{
          'url': 'https://exemple.org/affiche.jpg',
          'largeur': 864,
          'hauteur': 1080,
          'genre': 'affiche',
          'credit': ' Atelier ',
          'legende': <String, dynamic>{'fr': 'Affiche', 'xx-': 'ignoré', 'en': ''},
        },
      })!;
      final i = m.image!;
      expect(i.estAffiche, isTrue);
      expect(i.ratio, closeTo(0.8, 1e-9));
      expect(i.credit, 'Atelier');
      expect(i.legende, <String, String>{'fr': 'Affiche'});
    });

    test('dimensions absurdes ignorées', () {
      final i = ImageFiche.depuisJson(<String, dynamic>{'url': 'https://exemple.org/a.jpg', 'largeur': -5, 'hauteur': 1e9})!;
      expect(i.largeur, isNull);
      expect(i.hauteur, isNull);
      expect(i.ratio, isNull);
    });
  });

  group('textes', () {
    test('les quatre langues ont les mêmes clés que le français', () {
      final fr = chainesPublications['fr']!.keys.toSet();
      for (final langue in <String>['en', 'ar', 'ha']) {
        expect(chainesPublications[langue]!.keys.toSet(), fr, reason: langue);
        for (final v in chainesPublications[langue]!.values) {
          expect(v.trim(), isNotEmpty);
        }
      }
    });

    test('Textes retrouve les textes du lot E dans chaque langue', () {
      for (final langue in <String>['fr', 'en', 'ar', 'ha']) {
        expect(Textes(langue)('pub_partager'), chainesPublications[langue]!['pub_partager']);
      }
    });
  });
}
