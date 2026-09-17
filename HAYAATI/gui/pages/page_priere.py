"""
ÉCRAN PRIÈRE — CADRAN HYBRIDE (GUI/PAGES/PAGE_PRIERE.PY)
Version 3.0 - 10/09/2026

── Journal des corrections (10/09/2026) ──────────────────────────────
v3.0 — Refonte visuelle à partir des maquettes SVG fournies
(v1-qiblah-hayaati.svg, v2-qiblah-hayaati.svg) :
  • Les 6 "cônes" des branches sont maintenant de vraies formes SVG
    (pointe au centre, chapeau arrondi vers l'extérieur, dégradé de
    transparence), plus fidèles à la maquette qu'une pointe en losange
    Container. Rendues via ft.Image(src=<svg>), qui supporte nativement
    le SVG en source (confirmé via la doc Flet officielle), aucune
    dépendance supplémentaire nécessaire.
  • L'aiguille redevient un simple trait fin à sens unique (plus de
    queue arrière symétrique comme en v2.0), avec bout arrondi — copie
    directe du <path d="M 0,0 L 0,-420" stroke-linecap="round"> de la
    maquette v2.
  • L'ensemble boussole + croix + rose des vents + lettres cardinales +
    aiguille + Kaaba forme UN SEUL bloc rotatif (comme dans la maquette
    v2, groupe compass-qiblah-group), placé en DERNIER dans le Stack —
    donc au-dessus de tout le reste, pour survoler visuellement les
    branches en tournant. C'était l'inverse en v2.0 (branches dessinées
    par-dessus), corrigé ici.
  • Ornements floraux entre les branches remplacés par de vraies courbes
    de Bézier (symbole ornament-floral de la maquette v2) plutôt que le
    glyphe Unicode "✾" de la v2.0.
  • 🆕 Horloge au centre : l'heure actuelle s'affiche au milieu de la
    boussole, mise à jour chaque seconde. Élément à part, PAS inclus
    dans le bloc rotatif (un texte qui tournerait avec la boussole
    deviendrait illisible à mi-course) — posée par-dessus tout, y
    compris par-dessus le moyeu de l'aiguille.
─────────────────────────────────────────────────────────────────────

⚠️ Sur PC/desktop, ft.Magnetometer et ft.Accelerometer ne sont pas
supportés (Android/iOS uniquement, confirmé par la doc Flet officielle).
Le bloc rotatif reste alors statique, nord en haut.

⚠️ Le sens de rotation exact dépend de la convention d'axes du capteur
natif, non vérifiée sur un appareil réel avant livraison — voir la note
dans core/qibla_engine.py. À calibrer au premier test.
"""
from __future__ import annotations
import asyncio
import math
from datetime import datetime
import flet as ft

from gui.langues import DICTIONNAIRE_LANGUES
from gui.palette_hayaati import (
    VERT_PROFOND, TERRACOTTA, TERRACOTTA_FONCE, OCRE, OCRE_FONCE,
    SABLE, BLANC, GRIS_TEXTE, GRIS_CLAIR,
)
from core.agenda_engine import AgendaEngine
from core.qibla_engine import calculer_direction_qibla, calculer_distance_kaaba_km, FiltreBoussole
from core.time_engine import gregorien_vers_hegiri, obtenir_evenement_hegiri
# Réutilise la même résolution de texte d'événement que le calendrier de
# l'onboarding (jours_blancs, dhu_hijjah_N formaté, etc.) plutôt que de
# dupliquer cette logique une seconde fois dans ce fichier.
from gui.pages.page_onboarding_calendrier import _texte_evenement_court
from datetime import date, timedelta

# --- Dimensions générales du cadran ---
DIAMETRE_CADRAN = 340
TAILLE_BRANCHE = 68
RAYON_BRANCHES = 118            # rayon où sont centrées les 6 branches
LONGUEUR_CONE = 96              # longueur du cône, de l'apex (centre) au chapeau arrondi
LARGEUR_CONE = 20               # demi-largeur du chapeau arrondi, à l'extrémité du cône

# --- Boussole centrale : son propre petit cercle, pas tout le cadran ---
DIAMETRE_COMPAS = 150

# --- Kaaba et aiguille : voyagent sur un cercle invisible, au-delà des branches ---
RAYON_ORBITE_KAABA = 152
# Marge intérieure de l'image SVG de l'aiguille (voir _svg_needle) —
# nommée ici car aussi nécessaire pour calculer le bon point de pivot de
# rotation : l'aiguille doit tourner autour de sa base (le centre du
# cadran), pas autour du centre géométrique de son image.
MARGE_AIGUILLE = 6
# ⚠️ Point de pivot vertical (convention Alignment : -1=haut, 0=centre,
# +1=bas) correspondant à la base de l'aiguille dans son image, calculé
# à partir des mêmes dimensions que _svg_needle. Sans ce calcul,
# alignment=Alignment.CENTER ferait pivoter l'aiguille autour du milieu
# de sa propre longueur au lieu de sa base — elle dériverait au lieu de
# pivoter, et se désynchroniserait de la Kaaba (positionnée, elle, par
# vraie trigonométrie autour du centre réel du cadran).
_ALIGNEMENT_PIVOT_AIGUILLE = RAYON_ORBITE_KAABA / (RAYON_ORBITE_KAABA + 2 * MARGE_AIGUILLE)

ORDRE_BRANCHES = [
    ("fajr", 0, "🌅"),
    ("sunrise", 60, "☀️"),
    ("dhuhr", 120, "🕛"),
    ("asr", 180, "🕒"),
    ("maghrib", 240, "🌇"),
    ("isha", 300, "🌙"),
]

NOMS_SECOURS = {
    "fajr": "Fajr", "sunrise": "Lever", "dhuhr": "Dhuhr",
    "asr": "Asr", "maghrib": "Maghrib", "isha": "Isha",
}


def _position_polaire(angle_deg: float, rayon: float, cx: float, cy: float) -> tuple[float, float]:
    """Convertit un angle (0°=haut, sens horaire) et un rayon en
    coordonnées (x, y) dans le repère d'un Stack, centré sur (cx, cy)."""
    rad = math.radians(angle_deg)
    x = cx + rayon * math.sin(rad)
    y = cy - rayon * math.cos(rad)
    return x, y


# ----------------------------------------------------------------------
# Générateurs de formes SVG (rendues nativement par ft.Image — source
# SVG directe, confirmée par la documentation Flet officielle, aucune
# dépendance supplémentaire nécessaire).
# ----------------------------------------------------------------------

def _svg_cone(couleur: str, r: float = LONGUEUR_CONE, w: float = LARGEUR_CONE) -> str:
    """Cône d'une branche : pointe à l'apex (centre du cadran), chapeau
    arrondi à l'extrémité extérieure, dégradé du transparent (au centre)
    vers la couleur pleine (à l'extrémité) — même principe que la
    maquette de référence (path + linearGradient)."""
    marge = w * 1.15
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{-marge} {-r * 1.06} {2 * marge} {r * 1.06}" '
        f'width="{2 * marge}" height="{r * 1.06}">'
        f'<defs><linearGradient id="g" x1="0%" y1="100%" x2="0%" y2="0%">'
        f'<stop offset="0%" stop-color="{couleur}" stop-opacity="0.05"/>'
        f'<stop offset="100%" stop-color="{couleur}" stop-opacity="0.95"/>'
        f'</linearGradient></defs>'
        f'<path d="M 0,0 L {-w},{-r} A {r},{r} 0 0,1 {w},{-r} Z" fill="url(#g)"/>'
        f'</svg>'
    )


def _svg_needle(couleur: str, longueur: float = RAYON_ORBITE_KAABA, rayon_interieur: float = 0) -> str:
    """Aiguille fine à sens unique (pas de queue arrière), bout arrondi
    — copie directe du <path> minimaliste de la maquette v2.

    ⚠️ 12/09/2026 : rayon_interieur permet de commencer le trait après le
    bord du disque central (au lieu du centre exact), pour que l'aiguille
    ne traverse plus visiblement le disque où se trouve l'horloge. Le
    viewBox et les dimensions de l'image restent calculés sur toute la
    longueur (centre → pointe) sans changement, pour ne pas modifier le
    calcul du point de pivot de rotation (_ALIGNEMENT_PIVOT_AIGUILLE) —
    seul le tracé visible commence plus loin, l'espace avant reste vide."""
    marge = MARGE_AIGUILLE
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{-marge} {-longueur - marge} {2 * marge} {longueur + 2 * marge}" '
        f'width="{2 * marge}" height="{longueur + 2 * marge}">'
        f'<path d="M 0,{-rayon_interieur} L 0,{-longueur}" stroke="{couleur}" stroke-width="3.2" stroke-linecap="round"/>'
        f'</svg>'
    )


def _svg_rose(diametre: float = DIAMETRE_COMPAS) -> str:
    """Petit cercle de boussole : fond uni, croix N-S/E-O, rose des vents
    à 8 branches (deux carrés octogonaux superposés à 45°, motif
    classique de l'art géométrique islamique), anneau interne — tout ce
    bloc tourne comme un seul élément avec l'aiguille."""
    r = diametre / 2
    r_croix = r * 0.94
    r_rose = r * 0.82
    r_anneau = r * 0.44
    r_lettres = r * 0.86
    pts_rose = f"0,{-r_rose} {r_rose*0.18},{-r_rose*0.18} {r_rose},0 {r_rose*0.18},{r_rose*0.18} 0,{r_rose} {-r_rose*0.18},{r_rose*0.18} {-r_rose},0 {-r_rose*0.18},{-r_rose*0.18}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-r} {-r} {2*r} {2*r}" width="{2*r}" height="{2*r}">'
        f'<circle cx="0" cy="0" r="{r - 3}" fill="{SABLE}" stroke="{OCRE}" stroke-width="3"/>'
        f'<path d="M 0,{-r_croix} L 0,{r_croix} M {-r_croix},0 L {r_croix},0" '
        f'stroke="{OCRE_FONCE}" stroke-width="1.5" stroke-opacity="0.5"/>'
        f'<polygon points="{pts_rose}" fill="none" stroke="{OCRE_FONCE}" stroke-width="1.5" opacity="0.55"/>'
        f'<circle cx="0" cy="0" r="{r_anneau}" fill="none" stroke="{OCRE_FONCE}" stroke-width="1.5" opacity="0.6"/>'
        f'<text x="0" y="{-r_lettres + 5}" text-anchor="middle" font-size="15" font-weight="bold" fill="{VERT_PROFOND}">N</text>'
        f'<text x="{r_lettres - 4}" y="5" text-anchor="middle" font-size="15" font-weight="bold" fill="{VERT_PROFOND}">E</text>'
        f'<text x="0" y="{r_lettres + 2}" text-anchor="middle" font-size="15" font-weight="bold" fill="{VERT_PROFOND}">S</text>'
        f'<text x="{-r_lettres + 4}" y="5" text-anchor="middle" font-size="15" font-weight="bold" fill="{VERT_PROFOND}">O</text>'
        f'</svg>'
    )



# ⚠️ 11/09/2026 : _svg_fleur() retirée. Sa construction en 4 pétales
# disposés en croix (paire horizontale + paire verticale se rejoignant
# au centre) pouvait rappeler une croix chrétienne ou le symbole de la
# Rose-Croix — pas du tout l'intention, mais mieux vaut retirer tout
# élément prêtant à une lecture religieuse étrangère plutôt que de
# risquer une mauvaise interprétation. Rien ne remplace cet ornement :
# l'espace entre les branches reste simplement vide.


def _obtenir_evenements_mois_hegiri_courant(ajustement_lune: int = 0) -> list[dict]:
    """Liste les événements du mois hégirien en cours (celui d'aujourd'hui),
    chacun avec sa date grégorienne correspondante.

    Parcourt le calendrier grégorien jour par jour, car il n'existe pas de
    conversion hégirien → grégorien directe dans ce projet
    (core/time_engine.py ne fait que l'inverse) — coût négligeable, au
    plus une soixantaine de conversions pour couvrir tout un mois lunaire."""
    aujourdhui = date.today()
    h_auj = gregorien_vers_hegiri(aujourdhui.year, aujourdhui.month, aujourdhui.day, ajustement_lune)
    mois_cible, annee_cible = h_auj["mois_num"], h_auj["annee"]

    # Recule jusqu'au 1er jour du mois hégirien en cours.
    d = aujourdhui
    while True:
        h = gregorien_vers_hegiri(d.year, d.month, d.day, ajustement_lune)
        if h["mois_num"] != mois_cible or h["annee"] != annee_cible:
            d = d + timedelta(days=1)
            break
        d = d - timedelta(days=1)

    evenements = []
    for _ in range(32):  # garde-fou : un mois hégirien ne dépasse jamais 30 jours
        h = gregorien_vers_hegiri(d.year, d.month, d.day, ajustement_lune)
        if h["mois_num"] != mois_cible or h["annee"] != annee_cible:
            break
        evt_cle = obtenir_evenement_hegiri(h["mois_num"], h["jour"])
        if evt_cle:
            evenements.append({
                "evt_cle": evt_cle,
                "date_gregorienne": d,
                "jour_hijri": h["jour"],
                "mois_nom_hijri": h["mois_nom"],
                "mois_num_hijri": h["mois_num"],
                "annee_hijri": h["annee"],
            })
        d = d + timedelta(days=1)
    return evenements


class PagePriere(ft.Container):
    def __init__(self, app_reference):
        self.app = app_reference
        self.page_flet = app_reference.page

        self._cap_qibla = 0.0
        self._distance_km = 0.0
        self._cap_boussole: float | None = None
        self._dernier_accel = (0.0, 0.0, 9.8)  # secours : téléphone à plat
        # 🆕 12/09/2026 : filtre à mémoire pour stabiliser le cap — sans
        # lui, chaque lecture brute (bruitée par le tremblement de la
        # main ou un téléphone jamais parfaitement à plat) faisait
        # trembler l'aiguille au lieu de la laisser se stabiliser.
        self._filtre_boussole = FiltreBoussole()
        self._capteurs_actifs = False
        self._horloge_active = True
        # 🔧 17/09/2026 : raccordé à la préférence fiqh personnelle de
        # l'utilisateur (le +/-2 jours de page_reglages.py) — valeur de
        # secours ici le temps du tout premier rendu, réellement lue et
        # tenue à jour dans actualiser_donnees_affichage() ci-dessous,
        # comme le fait déjà page_onboarding.py pour son propre calendrier.
        self._ajustement_lune = 0

        self.lbl_titre = ft.Text(size=16, weight=ft.FontWeight.BOLD, color=VERT_PROFOND)
        self.lbl_info_distance = ft.Text(size=12, color=GRIS_TEXTE, text_align=ft.TextAlign.CENTER)
        self.lbl_note_capteur = ft.Text(size=10, italic=True, color=GRIS_TEXTE, text_align=ft.TextAlign.CENTER)
        self.lbl_horloge = ft.Text("--:--", size=20, weight=ft.FontWeight.BOLD, color=VERT_PROFOND)

        self.btn_retour = ft.IconButton(
            icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
            icon_color=VERT_PROFOND, icon_size=16,
            on_click=lambda _: self._revenir_en_arriere(),
        )

        self.branches_widgets: dict[str, ft.Container] = {}
        self.branches_labels: dict[str, dict[str, ft.Text]] = {}
        self.cones_images: dict[str, ft.Image] = {}

        cx = cy = DIAMETRE_CADRAN / 2

        controles_branches = self._construire_branches(cx, cy)

        # --- Bloc rotatif : boussole + croix + rose + lettres + aiguille + Kaaba ---
        # Un seul bloc, comme dans la maquette v2 (compass-qiblah-group) :
        # tout tourne ensemble. Placé en DERNIER dans cadran_stack, donc
        # rendu par-dessus les branches — c'est ça qui fait que l'aiguille
        # et la Kaaba survolent visuellement toute l'infrastructure en
        # tournant.
        self.image_rose = ft.Image(src=_svg_rose(), width=DIAMETRE_COMPAS, height=DIAMETRE_COMPAS)
        self.image_aiguille = ft.Image(
            # ⚠️ 12/09/2026 : le tracé commence juste après le bord du
            # disque (rayon_interieur), pas au centre — pour que l'aiguille
            # ne traverse plus visiblement la zone où s'affiche l'horloge.
            src=_svg_needle(TERRACOTTA, rayon_interieur=DIAMETRE_COMPAS / 2 + 4),
            width=12, height=RAYON_ORBITE_KAABA + 12,
        )
        # 🆕 12/09/2026 : Kaaba redevenue l'émoji 🕋 (même icône que le
        # bandeau/menu) plutôt que la boîte SVG dessinée à la main — plus
        # réaliste, comme demandé.
        self.image_kaaba = ft.Text("🕋", size=20)

        bloc_interieur = ft.Stack(width=DIAMETRE_CADRAN, height=DIAMETRE_CADRAN, controls=[
            ft.Container(content=self.image_rose, left=cx - DIAMETRE_COMPAS / 2, top=cy - DIAMETRE_COMPAS / 2),
            ft.Container(
                content=self.image_aiguille, left=cx - 6, top=cy - RAYON_ORBITE_KAABA - 6,
            ),
        ])
        self.conteneur_aiguille = bloc_interieur.controls[1]

        self.kaaba_container = ft.Container(content=self.image_kaaba, left=0, top=0)
        bloc_interieur.controls.append(self.kaaba_container)

        self.conteneur_rotatif = ft.Container(
            content=bloc_interieur,
            width=DIAMETRE_CADRAN, height=DIAMETRE_CADRAN,
            rotate=ft.Rotate(angle=0, alignment=ft.Alignment.CENTER),
            animate_rotation=ft.Animation(duration=150, curve=ft.AnimationCurve.LINEAR),
        )

        # --- Horloge centrale : PAS dans le bloc rotatif (resterait lisible
        # à tout instant, plutôt que de tourner et devenir illisible à
        # mi-course). Posée par-dessus tout, y compris le moyeu de l'aiguille.
        # 🆕 12/09/2026 : un petit fond uni juste derrière le chiffre de
        # l'heure (pas tout le disque) — masque la croix/rose SEULEMENT à
        # cet endroit précis, sans les faire disparaître du reste du
        # disque comme le ferait un remplacement complet.
        self.fond_horloge = ft.Container(
            content=self.lbl_horloge,
            width=60, height=26,
            bgcolor=SABLE, border_radius=13,
            alignment=ft.Alignment.CENTER,
        )
        self.conteneur_horloge = ft.Container(
            content=self.fond_horloge,
            width=DIAMETRE_CADRAN, height=DIAMETRE_CADRAN,
            alignment=ft.Alignment.CENTER,
        )

        self.cadran_stack = ft.Stack(
            width=DIAMETRE_CADRAN, height=DIAMETRE_CADRAN,
            controls=[
                *controles_branches,
                # ⚠️ 11/09/2026 : sans TransparentPointer, ces deux couches
                # (posées AU-DESSUS des branches pour que l'aiguille et la
                # Kaaba survolent visuellement le cadran) absorbaient aussi
                # les clics destinés aux branches en dessous — plus aucune
                # branche ne réagissait au tap. TransparentPointer fait
                # remonter le geste au widget suivant dans le Stack au lieu
                # de l'arrêter ici, exactement le problème qu'il est fait
                # pour résoudre (doc officielle Flet : "comment faire
                # passer les gestes entre deux widgets superposés").
                ft.TransparentPointer(content=self.conteneur_rotatif),
                ft.TransparentPointer(content=self.conteneur_horloge),
            ],
        )

        # 🆕 12/09/2026 : liste des événements du mois hégirien en cours,
        # sous le cadran — construite/remplie dans actualiser_donnees_affichage().
        self.lbl_titre_evenements = ft.Text(size=12, weight=ft.FontWeight.BOLD, color=VERT_PROFOND)
        self.colonne_evenements = ft.Column(spacing=4)
        self.cadre_evenements = ft.Container(
            content=ft.Column([self.lbl_titre_evenements, self.colonne_evenements], spacing=6),
            bgcolor=SABLE, padding=12, border_radius=8, border=ft.Border.all(1, OCRE),
        )

        self.layout_priere = ft.Column(
            [
                ft.Row([self.btn_retour, self.lbl_titre], spacing=8),
                ft.Container(content=self.cadran_stack, alignment=ft.Alignment.CENTER, padding=ft.Padding(0, 10, 0, 10)),
                self.lbl_info_distance,
                self.lbl_note_capteur,
                ft.Container(height=6),
                self.cadre_evenements,
            ],
            spacing=8, scroll=ft.ScrollMode.AUTO, expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        super().__init__(content=self.layout_priere, expand=True, bgcolor=BLANC, padding=ft.Padding(15, 15, 15, 15))

        self._enregistrer_capteurs()

        if hasattr(DICTIONNAIRE_LANGUES, "moteur_i18n"):
            DICTIONNAIRE_LANGUES.moteur_i18n.abonner_au_changement_langue(self.action_langue)

        self.actualiser_donnees_affichage()

        if self.page_flet:
            self.page_flet.run_task(self._boucle_horloge)

    # ------------------------------------------------------------------
    # Horloge centrale
    # ------------------------------------------------------------------
    async def _boucle_horloge(self):
        """Met à jour l'heure affichée au centre du cadran chaque
        seconde. S'arrête d'elle-même si l'utilisateur a quitté l'écran
        Prière — ce routeur n'a pas de crochet de démontage explicite, donc
        c'est cette boucle qui doit se surveiller plutôt que d'attendre
        d'être arrêtée de l'extérieur."""
        while self._horloge_active:
            if getattr(self.app, "ecran_courant", None) != "PRIERE":
                break
            try:
                self.lbl_horloge.value = datetime.now().strftime("%H:%M")
                self.lbl_horloge.update()
            except Exception:
                break
            await asyncio.sleep(1)

    # ------------------------------------------------------------------
    # Branches de prières (cône SVG + badge rond + toggle)
    # ------------------------------------------------------------------
    def _construire_branches(self, cx: float, cy: float) -> list[ft.Container]:
        controles = []
        for cle, angle, emoji in ORDRE_BRANCHES:
            image_cone = ft.Image(src=_svg_cone(GRIS_CLAIR), width=2 * LARGEUR_CONE * 1.15, height=LONGUEUR_CONE * 1.06)
            self.cones_images[cle] = image_cone
            x_cone, y_cone = _position_polaire(angle, LONGUEUR_CONE / 2, cx, cy)
            conteneur_cone = ft.Container(
                content=image_cone,
                left=x_cone - LARGEUR_CONE * 1.15, top=y_cone - LONGUEUR_CONE * 0.53,
                rotate=ft.Rotate(angle=math.radians(angle), alignment=ft.Alignment.CENTER),
            )
            controles.append(conteneur_cone)

            x, y = _position_polaire(angle, RAYON_BRANCHES, cx, cy)
            lbl_nom = ft.Text(NOMS_SECOURS[cle], size=9, weight=ft.FontWeight.BOLD)
            lbl_heure = ft.Text("--:--", size=10)
            icone_son = ft.Icon(ft.Icons.VOLUME_UP, size=12)
            self.branches_labels[cle] = {"nom": lbl_nom, "heure": lbl_heure, "son": icone_son}

            branche = ft.Container(
                width=TAILLE_BRANCHE, height=TAILLE_BRANCHE,
                border_radius=TAILLE_BRANCHE / 2,
                content=ft.Column(
                    [ft.Text(emoji, size=14), lbl_nom, lbl_heure, icone_son],
                    spacing=0, alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                on_click=lambda e, c=cle: self._basculer_alarme(c),
            )
            self.branches_widgets[cle] = branche
            controles.append(ft.Container(content=branche, left=x - TAILLE_BRANCHE / 2, top=y - TAILLE_BRANCHE / 2))
        return controles

    def _appliquer_style_branche(self, cle: str, activee: bool):
        branche = self.branches_widgets[cle]
        labels = self.branches_labels[cle]
        couleur = TERRACOTTA if activee else GRIS_CLAIR
        if activee:
            branche.bgcolor = TERRACOTTA
            branche.border = ft.Border.all(2, TERRACOTTA_FONCE)
            labels["nom"].color = BLANC
            labels["heure"].color = BLANC
            labels["son"].name = ft.Icons.VOLUME_UP
            labels["son"].color = BLANC
        else:
            branche.bgcolor = GRIS_CLAIR
            branche.border = ft.Border.all(2, OCRE)
            labels["nom"].color = GRIS_TEXTE
            labels["heure"].color = GRIS_TEXTE
            labels["son"].name = ft.Icons.VOLUME_OFF
            labels["son"].color = GRIS_TEXTE
        self.cones_images[cle].src = _svg_cone(couleur)

    def _basculer_alarme(self, cle: str):
        scheduler = getattr(self.app, "notification_scheduler", None)
        if not scheduler:
            return
        nouvel_etat = not scheduler.is_prayer_enabled(cle)
        try:
            scheduler.set_prayer_preference(cle, enabled=nouvel_etat)
        except Exception as exc:
            print(f"[PRIERE] Erreur set_prayer_preference({cle}) : {exc}")
            return
        self._appliquer_style_branche(cle, nouvel_etat)
        try:
            self.branches_widgets[cle].update()
            self.cones_images[cle].update()
        except Exception:
            pass

        if self.page_flet:
            async def _reschedule():
                try:
                    await scheduler.reschedule_all(30)
                except Exception as exc:
                    print(f"[PRIERE] Erreur reschedule_all après toggle : {exc}")
            self.page_flet.run_task(_reschedule)

    # ------------------------------------------------------------------
    # Capteurs (magnétomètre + accéléromètre)
    # ------------------------------------------------------------------
    def _enregistrer_capteurs(self):
        if not self.page_flet:
            return

        # ⚠️ 11/09/2026 : vérification de plateforme AVANT de créer les
        # capteurs, pas seulement un try/except après coup. Le try/except
        # seul attrapait bien l'échec au moment de l'enregistrement (log
        # "Capteurs indisponibles" affiché), mais l'objet Magnetometer
        # restait ensuite accroché dans page.services malgré l'échec.
        # Au redimensionnement de la fenêtre (PC ↔ Phone), Flet retraverse
        # tous les services pour comparer l'état (on_media_change), retombe
        # sur cet objet non supporté, et l'exception ressort cette fois
        # dans le gestionnaire d'événement interne de Flet — hors de
        # portée de mon try/except, d'où le crash observé. Vérifier la
        # plateforme en amont évite de créer le problème à la source.
        # ⚠️ CORRECTION 12/09/2026 : comparaison stricte cassée. Dans cette
        # version de Flet, page.platform est une énumération dont la
        # représentation textuelle est "PagePlatform.ANDROID", pas "ANDROID"
        # tout court — confirmé par le logcat réel sur téléphone : les
        # capteurs n'étaient JAMAIS tentés, même sur Android, à cause de
        # cette comparaison exacte qui ne pouvait jamais correspondre.
        # Recherche de sous-chaîne à la place, insensible à la forme exacte
        # (chaîne brute "android" ou énumération "PagePlatform.ANDROID").
        plateforme = str(getattr(self.page_flet, "platform", "") or "").upper()
        if not ("ANDROID" in plateforme or "IOS" in plateforme):
            print(f"[PRIERE] Capteurs non tentés (plateforme {plateforme or 'inconnue'} — Android/iOS uniquement).")
            self._capteurs_actifs = False
            return

        try:
            self.magnetometre = ft.Magnetometer(
                on_reading=self._on_lecture_magnetometre,
                on_error=self._on_erreur_capteur,
                interval=ft.Duration(milliseconds=200),
            )
            self.accelerometre = ft.Accelerometer(
                on_reading=self._on_lecture_accelerometre,
                on_error=self._on_erreur_capteur,
                interval=ft.Duration(milliseconds=200),
            )
            self.page_flet.services.append(self.magnetometre)
            self.page_flet.services.append(self.accelerometre)
            self._capteurs_actifs = True
        except Exception as exc:
            print(f"[PRIERE] Capteurs indisponibles malgré plateforme {plateforme} : {exc}")
            # Filet de sécurité : si l'un des deux a quand même fini dans
            # page.services avant l'échec, on le retire pour ne pas le
            # laisser traîner et faire planter un futur cycle de mise à
            # jour, exactement comme dans le crash observé.
            self._retirer_service_orphelin(getattr(self, "magnetometre", None))
            self._retirer_service_orphelin(getattr(self, "accelerometre", None))
            self._capteurs_actifs = False

    def _retirer_service_orphelin(self, service):
        if service is None or not self.page_flet:
            return
        try:
            if service in self.page_flet.services:
                self.page_flet.services.remove(service)
        except Exception:
            pass

    def _on_lecture_accelerometre(self, e):
        self._dernier_accel = (e.x, e.y, e.z)

    def _on_lecture_magnetometre(self, e):
        ax, ay, az = self._dernier_accel
        cap = self._filtre_boussole.calculer_cap(e.x, e.y, e.z, ax, ay, az)
        # ⚠️ DIAGNOSTIC 11/09/2026 : trace non filtrée, pour savoir si le
        # capteur envoie bien des lectures et ce que le calcul en tire.
        # Log volontairement discret (une ligne sur ~10) pour ne pas noyer
        # logcat à raison d'une lecture toutes les 200ms.
        if not hasattr(self, "_compteur_diag"):
            self._compteur_diag = 0
        self._compteur_diag += 1
        if self._compteur_diag % 10 == 0:
            print(f"[PRIERE][DIAG] mag=({e.x:.1f},{e.y:.1f},{e.z:.1f}) accel=({ax:.1f},{ay:.1f},{az:.1f}) cap_lisse={cap}")
        if cap is None:
            return
        self._cap_boussole = cap
        self._appliquer_rotation_disque()

    def _on_erreur_capteur(self, e):
        print(f"[PRIERE] Erreur capteur (normal sur PC) : {getattr(e, 'message', e)}")
        self._capteurs_actifs = False
        try:
            self.lbl_note_capteur.value = self._texte_note_capteur_indisponible()
            self.lbl_note_capteur.update()
        except Exception:
            pass

    def _angle_rotation_disque(self) -> float:
        if self._cap_boussole is None:
            return 0.0
        return (-self._cap_boussole) % 360.0

    def _appliquer_rotation_disque(self):
        angle = self._angle_rotation_disque()
        self.conteneur_rotatif.rotate.angle = math.radians(angle)
        # ⚠️ CORRECTION 12/09/2026, v2 : la vérification "if ... .page is
        # None: return" placée AVANT le try bloquait tout l'affichage de la
        # page — signe que lire .page sur un contrôle pas encore monté lève
        # elle-même une exception (probablement la même "Control must be
        # added to the page first"), pas seulement update(). Un if séparé
        # avant le try ne peut pas intercepter ça. Tout rentre maintenant
        # dans le même bloc try/except, y compris la lecture de .page.
        # Le cas "pas encore monté" est normal et attendu au premier appel
        # (déclenché depuis __init__), donc plus de print pour ce cas précis
        # — seulement pour une vraie erreur inattendue une fois monté.
        try:
            if self.cadran_stack.page is None:
                return
            self.cadran_stack.update()
        except AssertionError:
            pass
        except Exception as exc:
            if "must be added to the page" not in str(exc):
                print(f"[PRIERE][DIAG] Échec update rotation inattendu : {exc}")

    # ------------------------------------------------------------------
    # i18n et rafraîchissement des données
    # ------------------------------------------------------------------
    def action_langue(self, dic: dict):
        # ⚠️ 12/09/2026 : _notifier_les_interfaces() (gui/langues.py) avale
        # silencieusement toute exception levée ici — sans ce try/except
        # avec print, un bug dans traduire_page() serait invisible dans
        # les logs, comme si la page ignorait juste le changement de langue.
        try:
            self.traduire_page(dic)
        except Exception as exc:
            import traceback
            print(f"[PRIERE][DIAG] action_langue a échoué : {exc}")
            traceback.print_exc()

    def changer_langue(self, n_lang: str):
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)

    def _texte_note_capteur_indisponible(self) -> str:
        q = DICTIONNAIRE_LANGUES.actif.get("qiblah", {}) if hasattr(DICTIONNAIRE_LANGUES, "actif") else {}
        return q.get(
            "note_pc",
            "Boussole en direct indisponible sur cet appareil — le disque reste orienté nord en haut.",
        )

    def traduire_page(self, dic: dict):
        if not dic:
            return
        q = dic.get("qiblah", {})
        self.lbl_titre.value = str(q.get("titre", "🕋 Prière"))
        for cle, _, _ in ORDRE_BRANCHES:
            nom_traduit = q.get(f"priere_{cle}", NOMS_SECOURS[cle])
            self.branches_labels[cle]["nom"].value = str(nom_traduit)
        if not self._capteurs_actifs:
            self.lbl_note_capteur.value = self._texte_note_capteur_indisponible()
        # 🔧 17/09/2026 : sans cet appel, la liste des événements lunaires
        # restait dans l'ancienne langue jusqu'au prochain retour sur la
        # page — traduire_page() ne touchait que le titre, les noms de
        # prières et la note capteur.
        try:
            self._rafraichir_liste_evenements()
        except Exception:
            pass
        if self.page_flet:
            try:
                self.update()
            except Exception:
                pass

    def actualiser_donnees_affichage(self):
        # 🔧 17/09/2026 : lu à chaque rafraîchissement (pas seulement à la
        # construction) pour que le curseur +/-2 jours de page_reglages.py
        # s'applique immédiatement au retour sur cette page, comme il
        # s'applique déjà au calendrier et aux alertes de l'onboarding.
        try:
            u_id = getattr(self.app, "user_id_connecte", "INVITE")
            if hasattr(self.app, "sync_engine") and self.app.sync_engine:
                c_pref = self.app.sync_engine.charger_donnees_module(u_id, "PREFERENCES") or {}
                self._ajustement_lune = int(c_pref.get("ajustement_hegiri", 0))
        except Exception as exc:
            print(f"[PRIERE] Lecture ajustement_hegiri échouée, valeur conservée : {exc}")

        try:
            moteur_position = AgendaEngine()
            lat, lon = moteur_position.latitude, moteur_position.longitude
        except Exception as exc:
            print(f"[PRIERE] Position indisponible, valeurs par défaut : {exc}")
            lat, lon = 10.86, 0.20

        self._cap_qibla = calculer_direction_qibla(lat, lon)
        self._distance_km = calculer_distance_kaaba_km(lat, lon)
        self._repositionner_kaaba()
        self._appliquer_rotation_disque()

        q = DICTIONNAIRE_LANGUES.actif.get("qiblah", {}) if hasattr(DICTIONNAIRE_LANGUES, "actif") else {}
        # ⚠️ CORRECTION 12/09/2026 : en arabe, un nombre avec séparateur
        # ("4 783") inséré dans une phrase RTL peut se faire réordonner par
        # l'algorithme bidirectionnel Unicode — les espaces entre chiffres
        # sont des caractères "neutres" que le bidi peut redistribuer selon
        # le sens du texte environnant. LRI (U+2066) / PDI (U+2069) isolent
        # le nombre comme un bloc de gauche-à-droite autonome, quel que
        # soit le sens du texte autour — invisible et sans effet dans les
        # langues déjà LTR (français, anglais, haoussa).
        LRI, PDI = "\u2066", "\u2069"
        cap_isole = f"{LRI}{round(self._cap_qibla)}{PDI}"
        distance_isolee = f"{LRI}{self._distance_km:,.0f}{PDI}".replace(",", " ")
        self.lbl_info_distance.value = q.get(
            "info_distance", "Cap {cap}° — à {distance} km de la Kaaba"
        ).format(cap=cap_isole, distance=distance_isolee)

        horaires = getattr(self.app, "horaires_prieres_aujourdhui", {}) or {}
        scheduler = getattr(self.app, "notification_scheduler", None)
        for cle, _, _ in ORDRE_BRANCHES:
            heure_str = horaires.get(cle.capitalize(), "--:--")
            self.branches_labels[cle]["heure"].value = heure_str
            activee = scheduler.is_prayer_enabled(cle) if scheduler else True
            self._appliquer_style_branche(cle, activee)

        self._rafraichir_liste_evenements()
        self.traduire_page(DICTIONNAIRE_LANGUES.actif)

    def _rafraichir_liste_evenements(self):
        """Reconstruit la liste des événements du mois hégirien en cours,
        chacun avec ses deux dates (hégirienne et grégorienne)."""
        txt_onb = DICTIONNAIRE_LANGUES.actif.get("onboarding", {}) if hasattr(DICTIONNAIRE_LANGUES, "actif") else {}
        q = DICTIONNAIRE_LANGUES.actif.get("qiblah", {}) if hasattr(DICTIONNAIRE_LANGUES, "actif") else {}
        noms_mois_greg = txt_onb.get("calendrier", {}).get("mois_gregoriens", [
            "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
            "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
        ])

        self.lbl_titre_evenements.value = q.get("titre_evenements", "🌙 Événements du mois")

        try:
            evenements = _obtenir_evenements_mois_hegiri_courant(self._ajustement_lune)
        except Exception as exc:
            print(f"[PRIERE] Échec calcul des événements lunaires : {exc}")
            evenements = []

        self.colonne_evenements.controls.clear()
        if not evenements:
            self.colonne_evenements.controls.append(
                ft.Text(q.get("aucun_evenement_mois", "Aucun événement particulier ce mois-ci."),
                        size=11, italic=True, color=GRIS_TEXTE)
            )
        else:
            for evt in evenements:
                nom_mois_hijri = txt_onb.get(f"mois_nom_{evt['mois_num_hijri']}", evt["mois_nom_hijri"])
                texte_evt = _texte_evenement_court(evt["evt_cle"], evt["jour_hijri"], txt_onb)
                d = evt["date_gregorienne"]
                nom_mois_greg = noms_mois_greg[d.month - 1] if 1 <= d.month <= 12 else str(d.month)
                self.colonne_evenements.controls.append(
                    ft.Row([
                        ft.Text("📅", size=12),
                        ft.Column([
                            ft.Text(f"{evt['jour_hijri']} {nom_mois_hijri} {evt['annee_hijri']} AH", size=11, weight=ft.FontWeight.BOLD, color=VERT_PROFOND),
                            ft.Text(f"{d.day} {nom_mois_greg} {d.year} — {texte_evt}", size=10, color=GRIS_TEXTE),
                        ], spacing=0, tight=True),
                    ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.START)
                )
        try:
            self.cadre_evenements.update()
        except Exception:
            pass

    def _repositionner_kaaba(self):
        """Réoriente l'aiguille et repositionne la Kaaba à son nouveau
        cap, après un recalcul de position (déménagement de
        l'utilisateur). Ne fait pas tourner le bloc entier : c'est
        conteneur_rotatif.rotate qui gère la rotation d'ensemble."""
        cx = cy = DIAMETRE_CADRAN / 2
        self.conteneur_aiguille.rotate = ft.Rotate(
            angle=math.radians(self._cap_qibla),
            alignment=ft.Alignment(0, _ALIGNEMENT_PIVOT_AIGUILLE),
        )
        x_k, y_k = _position_polaire(self._cap_qibla, RAYON_ORBITE_KAABA, cx, cy)
        self.kaaba_container.left = x_k - 12
        self.kaaba_container.top = y_k - 14

    def actualiser_contexte(self):
        """Alias pour le routeur central (OrganisateurLayout)."""
        self.actualiser_donnees_affichage()

    def _revenir_en_arriere(self):
        self._horloge_active = False
        layout = getattr(self.app, "layout_central", None)
        if layout and hasattr(layout, "revenir_ecran_precedent"):
            if layout.revenir_ecran_precedent():
                return
        if layout:
            layout.basculer_vers_ecran("ONBOARDING")
