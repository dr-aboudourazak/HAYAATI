"""
core/qibla_engine.py — 10/09/2026

Calcul de la direction de la Qiblah (cap vers la Kaaba depuis la position
de l'utilisateur) et fusion des capteurs magnétomètre + accéléromètre en
un cap de boussole utilisable.

Séparé de gui/pages/page_qiblah.py volontairement : ce fichier ne dépend
d'aucun widget Flet, uniquement de math pur, donc testable en isolation
(comme core/prayertimes.py) sans avoir besoin de lancer l'app.

⚠️ Approximation connue, assumée : le cap est calculé par rapport au nord
GÉOGRAPHIQUE (vrai), mais ft.Magnetometer mesure le champ magnétique
terrestre, orienté vers le nord MAGNÉTIQUE. L'écart entre les deux
(déclinaison magnétique) varie selon le lieu — en Afrique de l'Ouest il
reste faible (de l'ordre de 1 à 3°), donc négligé ici plutôt que
d'embarquer un modèle mondial de déclinaison (WMM), trop lourd pour ce
projet. À revisiter si HAYAATI vise un jour des zones à forte déclinaison
(certaines régions d'Amérique du Nord ou d'Asie dépassent 15-20°).
"""
from __future__ import annotations
import math
from typing import Optional

# Coordonnées de la Kaaba (Masjid al-Haram, La Mecque).
KAABA_LATITUDE = 21.4225
KAABA_LONGITUDE = 39.8262

RAYON_TERRE_KM = 6371.0


def calculer_direction_qibla(latitude: float, longitude: float) -> float:
    """
    Calcule le cap initial (great-circle bearing) depuis (latitude,
    longitude) vers la Kaaba, en degrés depuis le nord vrai, dans le
    sens horaire (0° = nord, 90° = est, 180° = sud, 270° = ouest).

    Formule standard de navigation orthodromique (great-circle initial
    bearing), la même que celle utilisée par la quasi-totalité des apps
    de qiblah.
    """
    phi1 = math.radians(latitude)
    phi2 = math.radians(KAABA_LATITUDE)
    delta_lambda = math.radians(KAABA_LONGITUDE - longitude)

    x = math.sin(delta_lambda) * math.cos(phi2)
    y = (
        math.cos(phi1) * math.sin(phi2)
        - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    )
    cap = math.degrees(math.atan2(x, y))
    return (cap + 360.0) % 360.0


def calculer_distance_kaaba_km(latitude: float, longitude: float) -> float:
    """Distance orthodromique (à vol d'oiseau) jusqu'à la Kaaba, en km,
    via la formule de Haversine. Purement informatif pour l'écran Qiblah
    (« vous êtes à X km de la Kaaba »), n'affecte aucun calcul de prière."""
    phi1 = math.radians(latitude)
    phi2 = math.radians(KAABA_LATITUDE)
    delta_phi = math.radians(KAABA_LATITUDE - latitude)
    delta_lambda = math.radians(KAABA_LONGITUDE - longitude)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return RAYON_TERRE_KM * c


def calculer_cap_boussole(
    mx: float, my: float, mz: float,
    ax: float, ay: float, az: float,
) -> Optional[float]:
    """
    Fusionne une lecture magnétomètre (mx,my,mz, en µT) et une lecture
    accéléromètre (ax,ay,az, en m/s²) pour obtenir un cap de boussole
    compensé en inclinaison (tilt-compensated heading), en degrés depuis
    le nord magnétique, sens horaire.

    C'est l'algorithme standard utilisé par la plupart des boussoles
    logicielles (équivalent de SensorManager.getRotationMatrix +
    getOrientation() sur Android, reconstruit ici manuellement car Flet
    n'expose que les capteurs bruts, pas un cap déjà calculé) :
    1. Normaliser le vecteur gravité (accéléromètre).
    2. Est = Champ magnétique × Gravité (produit vectoriel), normalisé.
    3. Nord = Gravité × Est.
    4. Cap = atan2(Est_x, Nord_x).

    Retourne None si les vecteurs sont dégénérés (téléphone en chute
    libre, capteur défaillant, division par zéro) plutôt que de renvoyer
    une valeur aberrante.

    ⚠️ Convention d'axes supposée identique à celle d'Android
    (x = droite, y = haut de l'écran, z = hors de l'écran vers
    l'utilisateur), puisque ft.Magnetometer/Accelerometer enveloppent les
    capteurs natifs. Le signe final n'a pas pu être vérifié sur un
    appareil réel avant livraison : la calibration se fait maintenant
    via appliquer_calibration_cap() ci-dessous plutôt qu'ici — voir son
    docstring pour la marche à suivre sur un vrai téléphone.
    """
    norme_a = math.sqrt(ax * ax + ay * ay + az * az)
    if norme_a < 1e-6:
        return None
    ax, ay, az = ax / norme_a, ay / norme_a, az / norme_a

    # Est = M × G
    ex = my * az - mz * ay
    ey = mz * ax - mx * az
    ez = mx * ay - my * ax
    norme_e = math.sqrt(ex * ex + ey * ey + ez * ez)
    if norme_e < 1e-6:
        return None
    ex, ey, ez = ex / norme_e, ey / norme_e, ez / norme_e

    # Nord = G × Est
    nx = ay * ez - az * ey
    # ny, nz calculables si besoin (inclinaison/roulis), non utilisés ici.

    cap = math.degrees(math.atan2(ex, nx))
    return (cap + 360.0) % 360.0


# 🆕 17/09/2026 : calibration manuelle du cap boussole, à ajuster une
# fois sur un appareil réel plutôt que de deviner un modèle d'axes
# correct sans pouvoir le tester sur du matériel réel. Test confirmé sur
# téléphone le 17/09/2026 : le disque tourne (donc les capteurs et le
# lissage fonctionnent), mais le nord affiché n'est pas le bon — signe
# que c'est bien ici, et seulement ici, qu'il faut corriger.
#
# MARCHE À SUIVRE POUR CALIBRER :
#   1. Ouvrir une boussole fiable à côté (Google Maps en mode boussole,
#      ou une appli boussole dédiée) et se tourner soi-même, téléphone en
#      main, jusqu'à ce que cette boussole de référence indique 0°
#      (plein nord réel).
#   2. Sans bouger, regarder quelle lettre du cadran Hayaati (N, E, S ou
#      O) se trouve alors en haut du disque.
#   3. Reporter cette lettre dans le tableau ci-dessous pour fixer
#      DECALAGE_CALIBRATION_DEG :
#         "N" déjà en haut  → DECALAGE_CALIBRATION_DEG = 0      (rien à faire)
#         "E" en haut       → DECALAGE_CALIBRATION_DEG = -90
#         "S" en haut       → DECALAGE_CALIBRATION_DEG = 180
#         "O" en haut       → DECALAGE_CALIBRATION_DEG = 90
#   4. Vérifier ensuite le SENS : en pivotant sur soi-même vers la droite
#      (sens horaire), le disque doit tourner de façon à ce que la lettre
#      du haut change N → E → S → O → N. Si c'est l'inverse (N → O → S →
#      E → N), le sens lui-même est inversé : mettre
#      INVERSER_SENS_ROTATION = True, puis refaire l'étape 1-3 pour
#      réajuster DECALAGE_CALIBRATION_DEG avec ce nouveau sens.
INVERSER_SENS_ROTATION: bool = False
# 🆕 17/09/2026 : fixé à -90° suite au test réel sur table (téléphone
# immobile, à plat) — lettre "E" reproductible en haut du cadran à
# chaque relance de l'app quand le téléphone pointe réellement plein
# nord. Résultat stable et reproductible sur plusieurs relances, donc
# calibration fiable (contrairement aux tout premiers essais tenus en
# main, faussés par le bug de désynchronisation capteurs corrigé dans
# page_priere.py — voir _on_lecture_magnetometre).
DECALAGE_CALIBRATION_DEG: float = -90.0


# 🆕 18/09/2026 : signe du gyroscope, même principe que
# INVERSER_SENS_ROTATION mais pour l'axe Z du gyroscope spécifiquement —
# à calibrer séparément : pose le téléphone à plat et fais-le pivoter
# lentement à la main SANS le déplacer autrement (juste une rotation sur
# lui-même). Si le disque tourne dans le mauvais sens UNIQUEMENT depuis
# cet ajout (il tournait dans le bon sens avant, avec le seul
# magnétomètre), passe cette constante à -1.0.
# Le test fait révèle effectivement que le disque tourne dans le mauvais sens. 
# Donc constante passé à -1.0 ce 19/09/2026 à 10h34.
SIGNE_GYRO_Z: float = -1.0


def appliquer_calibration_cap(cap_brut: float) -> float:
    """Applique la calibration manuelle ci-dessus à un cap de boussole
    brut. Isolée dans sa propre fonction et appelée depuis un seul
    endroit (FiltreBoussole._cap_actuel) pour qu'un futur réglage du
    signe/décalage n'ait qu'un seul point à toucher."""
    cap = (360.0 - cap_brut) % 360.0 if INVERSER_SENS_ROTATION else cap_brut
    return (cap + DECALAGE_CALIBRATION_DEG) % 360.0


def angle_relatif_aiguille(cap_qibla: float, cap_boussole: Optional[float]) -> float:
    """
    Angle de rotation (en degrés) à appliquer à l'aiguille/Kaaba affichée
    à l'écran pour qu'elle pointe vers la qiblah réelle, sachant vers où
    le téléphone est actuellement orienté.

    Si cap_boussole est None (capteur indisponible, ex. sur PC où
    Magnetometer n'existe pas), retourne cap_qibla tel quel : l'aiguille
    reste fixe par rapport à l'écran (nord supposé en haut), ce qui reste
    correct dans le cas d'usage PC où on ne peut de toute façon pas
    physiquement tourner l'écran vers La Mecque.
    """
    if cap_boussole is None:
        return cap_qibla
    return (cap_qibla - cap_boussole + 360.0) % 360.0


class FiltreBoussole:
    """
    Lisse les lectures magnétomètre/accéléromètre pour stabiliser le cap
    de boussole, ET fusionne un gyroscope pour rester exploitable même
    quand le magnétomètre est ponctuellement peu fiable.

    🆕 17/09/2026 (3e round) — Fusion gyroscope ajoutée suite à un retour
    de test réel déterminant : en voiture, téléphone posé bien à plat sur
    une surface dure, route plane — le cap restait instable, alors que la
    boussole native du même téléphone, dans les mêmes conditions, restait
    stable. Le point commun de tous les essais précédents (posé sur table
    chez soi, en main) qui, eux, avaient fini par se stabiliser : pas de
    grosse masse métallique ni de moteur/alternateur à proximité immédiate
    comme dans une voiture. Une carrosserie et un moteur de voiture sont
    une source de perturbation magnétique largement documentée, à une
    échelle que le simple filtrage de tremblement de main ne peut pas
    absorber — ce n'est PLUS un problème de bruit à lisser, c'est le
    magnétomètre qui mesure ponctuellement autre chose que le champ
    terrestre. La boussole native s'en sort parce qu'elle utilise un
    capteur de rotation fusionné (magnétomètre + accéléromètre +
    GYROSCOPE) au niveau du système — notre filtre n'utilisait jusqu'ici
    que les deux premiers. D'où l'ajout ici :

    - Le gyroscope (vitesse de rotation, indifférent au champ magnétique
      ambiant) fait avancer en continu une estimation de cap "par
      inertie" (integrer_gyroscope), à chaque lecture — bien plus
      fréquentes que celles du magnétomètre.
    - Le magnétomètre ne sert plus qu'à recaler doucement cette
      estimation de temps en temps (calculer_cap), et seulement quand sa
      lecture semble physiquement plausible : si la NORME du champ
      magnétique mesuré s'écarte trop de sa valeur de référence récente
      (perturbation locale : carrosserie, moteur, structure métallique),
      le recalage est simplement suspendu le temps que ça passe — le cap
      continue d'avancer sur le seul gyroscope entre-temps, plutôt que de
      suivre une lecture magnétique aberrante.

    Ça n'élimine pas totalement la difficulté (aucune boussole ne peut
    physiquement extraire un cap fiable d'un champ magnétique noyé sous
    une perturbation plus forte que lui — même les boussoles natives
    affichent parfois un avertissement "peu fiable" en voiture), mais ça
    rapproche fortement du comportement natif : le gyroscope tient le
    cap à jour pendant que le magnétomètre est snobé, au lieu de refléter
    directement la lecture polluée.

    Approximation assumée : integrer_gyroscope suppose le téléphone
    globalement à plat, donc que la vitesse de rotation autour de l'axe Z
    de l'appareil (tel que rapporté par le gyroscope) représente
    correctement le taux de lacet réel. Raisonnable posé à plat ou tenu à
    peu près horizontal (le cas d'usage réel : consulter la qiblah) —
    moins précis téléphone fortement incliné.

    Historique des ajustements précédents (rounds 1 et 2, 17/09/2026) :
    1. Accéléromètre lissé en continu (moyenne mobile exponentielle,
       alpha_accel) avant la compensation d'inclinaison.
    2. Garde-fou de mouvement : accélération hors de la bande 6.0-13.5
       m/s² → téléphone secoué/en mouvement franc, lecture ignorée.
    3. Désynchronisation magnétomètre/accéléromètre : gérée côté appelant
       (SEUIL_DESYNCHRO_CAPTEURS_S dans page_priere.py), pas ici.

    ⚠️ RETIRÉ le 17/09/2026 (round 3) : la correction de biais
    magnétomètre par bornes min/max (_corriger_biais_magnetometre)
    introduite au round 1. Vérifiée par simulation avant de la retirer,
    pas seulement soupçonnée : dès qu'une vraie rotation du téléphone
    survient (usage tout à fait normal), ses bornes min/max élargissent
    à cause du changement de DIRECTION du champ terrestre — pas d'un
    biais de l'appareil — et la correction se met à soustraire quelque
    chose qui n'est pas un biais. Deux dégâts observés en simulation :
    le cap recalé partait dans le mauvais sens pendant la rotation, ET
    la référence de norme utilisée par la détection d'anomalie
    magnétique ci-dessous se retrouvait faussée à sa suite, laissant
    passer une perturbation véhicule qu'elle aurait dû rejeter. Sans
    cette correction, la même simulation (rotation de 90° puis
    perturbation véhicule) donne un cap qui suit la rotation à moins de
    0.5° près, ignore complètement la perturbation, et revient
    immédiatement au bon cap une fois celle-ci levée. Ça explique aussi,
    a posteriori, pourquoi le geste "en huit" semblait sans effet : ce
    geste EST une rotation, exactement la situation où cette correction
    faisait le plus de dégâts.

    Les coefficients par défaut (alpha_accel=0.12, alpha_cap=0.25 — ce
    dernier servant de gain de recalage gyroscope→magnétomètre plutôt
    que de lissage cos/sin) restent des points de départ raisonnables, à
    réajuster sur le terrain plutôt que sur ce seul raisonnement
    théorique.
    """
    SEUIL_ANOMALIE_MAGNETIQUE_RATIO = 1.35
    """Si la norme du champ magnétique mesuré s'écarte de plus de ce
    ratio par rapport à sa valeur de référence récente, la lecture est
    jugée peu fiable (perturbation locale plutôt que rotation du
    téléphone) et n'est pas utilisée pour recaler le cap — le gyroscope
    continue seul jusqu'à la prochaine lecture plausible."""

    def __init__(self, alpha_accel: float = 0.12, alpha_cap: float = 0.25):
        self.alpha_accel = alpha_accel
        self.alpha_cap = alpha_cap
        self._accel_lisse: Optional[tuple[float, float, float]] = None
        self._norme_mag_ref: Optional[float] = None
        self._cap_fusion: Optional[float] = None
        self._gyro_horodatage = None

    def _lisser_accel(self, ax: float, ay: float, az: float) -> tuple[float, float, float]:
        if self._accel_lisse is None:
            self._accel_lisse = (ax, ay, az)
        else:
            a = self.alpha_accel
            px, py, pz = self._accel_lisse
            self._accel_lisse = (
                a * ax + (1 - a) * px,
                a * ay + (1 - a) * py,
                a * az + (1 - a) * pz,
            )
        return self._accel_lisse

    def integrer_gyroscope(self, gz_rad_s: float, timestamp) -> Optional[float]:
        """À appeler à chaque lecture gyroscope (bien plus fréquentes que
        le magnétomètre) pour faire avancer le cap fusionné par inertie
        entre deux recalages magnétomètre. Sans effet tant qu'aucune
        première lecture magnétomètre n'a donné de cap de départ — le
        gyroscope seul ne connaît qu'une VITESSE de rotation, pas un cap
        absolu de départ."""
        if self._cap_fusion is not None and self._gyro_horodatage is not None:
            try:
                dt = (timestamp - self._gyro_horodatage).total_seconds()
            except Exception:
                dt = 0.0
            if 0.0 < dt < 0.5:
                self._cap_fusion = (self._cap_fusion + SIGNE_GYRO_Z * math.degrees(gz_rad_s) * dt) % 360.0
        self._gyro_horodatage = timestamp
        return self._cap_fusion

    def calculer_cap(self, mx: float, my: float, mz: float, ax: float, ay: float, az: float) -> Optional[float]:
        """Nouvelle lecture magnétomètre+accéléromètre → recale (ou pas,
        si jugée peu fiable) le cap fusionné avec le gyroscope. Retourne
        None uniquement avant la toute première lecture valide."""
        ax_l, ay_l, az_l = self._lisser_accel(ax, ay, az)

        norme_accel = math.sqrt(ax_l * ax_l + ay_l * ay_l + az_l * az_l)
        if norme_accel < 6.0 or norme_accel > 13.5:
            # Téléphone en mouvement franc (secousse) : on ne recale pas,
            # le gyroscope continue seul de tenir le cap à jour.
            return self._cap_fusion

        cap_brut = calculer_cap_boussole(mx, my, mz, ax_l, ay_l, az_l)
        if cap_brut is None:
            return self._cap_fusion
        cap_brut = appliquer_calibration_cap(cap_brut)

        # --- Détection d'anomalie magnétique (véhicule, structure
        # métallique...) : une rotation normale du téléphone ne change
        # PAS l'intensité du champ terrestre, seulement sa direction
        # apparente — si l'intensité mesurée s'écarte fortement de sa
        # valeur de référence récente, c'est qu'une source magnétique
        # locale s'ajoute au champ terrestre, pas que le téléphone a
        # tourné. ---
        norme_mag = math.sqrt(mx * mx + my * my + mz * mz)
        if self._norme_mag_ref is None:
            self._norme_mag_ref = norme_mag
        ratio = (norme_mag / self._norme_mag_ref) if self._norme_mag_ref > 1e-6 else 1.0
        fiable = (1.0 / self.SEUIL_ANOMALIE_MAGNETIQUE_RATIO) <= ratio <= self.SEUIL_ANOMALIE_MAGNETIQUE_RATIO

        if self._cap_fusion is None:
            # Tout premier recalage : rien à fusionner encore, on démarre
            # directement sur la lecture magnétomètre.
            self._cap_fusion = cap_brut
        elif fiable:
            ecart = ((cap_brut - self._cap_fusion + 540.0) % 360.0) - 180.0
            self._cap_fusion = (self._cap_fusion + self.alpha_cap * ecart) % 360.0
        # sinon (anomalie détectée) : _cap_fusion n'est PAS touché ici —
        # il continue d'avancer via integrer_gyroscope() jusqu'au prochain
        # recalage magnétomètre jugé plausible.

        if fiable:
            # Référence mise à jour lentement, et seulement sur des
            # lectures jugées fiables, pour suivre une dérive légitime
            # (latitude différente, etc.) sans se faire polluer par une
            # perturbation ponctuelle qu'on vient justement d'écarter.
            self._norme_mag_ref = 0.98 * self._norme_mag_ref + 0.02 * norme_mag

        return self._cap_fusion
