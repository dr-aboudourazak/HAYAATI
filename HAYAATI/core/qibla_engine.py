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
    appareil réel : à calibrer en pointant le téléphone vers un point
    connu (le soleil à midi pointe plein sud dans l'hémisphère nord, par
    exemple) et en ajustant AJUSTEMENT_SIGNE ci-dessous si le cap affiché
    est inversé ou décalé de 90°/180°.
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
    de boussole. Sans lissage, chaque lecture brute (bruitée par le
    tremblement de la main ou un téléphone jamais parfaitement à plat)
    produit un cap légèrement différent d'une lecture à l'autre — d'où
    une aiguille qui tremble au lieu de se stabiliser sur une direction,
    confirmé après test réel sur téléphone.

    Deux lissages distincts, plus un garde-fou :
    1. L'accéléromètre est lissé en continu (moyenne mobile exponentielle)
       avant de servir à la compensation d'inclinaison — sans ça, le
       tremblement de la main contamine directement le calcul de tilt.
    2. Le cap final est lissé via ses composantes (cos, sin) plutôt que
       par une moyenne linéaire de l'angle — une moyenne linéaire naïve
       casse au passage 0°/360° (ex. moyenne de 359° et 1° donnerait 180°,
       alors que la vraie moyenne directionnelle est 0°).
    3. Garde-fou : si la norme de l'accélération lissée s'écarte trop de
       9.8 m/s², le téléphone est en train d'être bougé/secoué plutôt que
       simplement tenu — la lecture est ignorée plutôt que d'introduire du
       bruit de mouvement dans le calcul d'inclinaison.

    Les coefficients alpha (0.0-1.0) sont un compromis stabilité/réactivité
    : plus petit = plus stable mais plus lent à suivre un vrai mouvement de
    rotation, plus grand = plus réactif mais plus sensible au bruit. Les
    valeurs par défaut sont un point de départ raisonnable pour des lectures
    toutes les 200ms (voir page_priere.py) ; à ajuster sur le terrain selon
    la sensation réelle plutôt que sur un calcul théorique seul.
    """

    def __init__(self, alpha_accel: float = 0.15, alpha_cap: float = 0.15):
        self.alpha_accel = alpha_accel
        self.alpha_cap = alpha_cap
        self._accel_lisse: Optional[tuple[float, float, float]] = None
        self._cap_vecteur: Optional[tuple[float, float]] = None

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

    def _cap_actuel(self) -> Optional[float]:
        if self._cap_vecteur is None:
            return None
        vx, vy = self._cap_vecteur
        return (math.degrees(math.atan2(vy, vx)) + 360.0) % 360.0

    def calculer_cap(self, mx: float, my: float, mz: float, ax: float, ay: float, az: float) -> Optional[float]:
        """Nouvelle lecture brute → cap lissé. Retourne None uniquement
        avant la toute première lecture valide (aucun historique encore)."""
        ax_l, ay_l, az_l = self._lisser_accel(ax, ay, az)

        norme = math.sqrt(ax_l * ax_l + ay_l * ay_l + az_l * az_l)
        if norme < 7.0 or norme > 12.5:
            # Téléphone en mouvement (secousse, tremblement fort) plutôt
            # que simplement tenu : on garde le dernier cap stable au lieu
            # d'intégrer une lecture d'inclinaison peu fiable.
            return self._cap_actuel()

        cap_brut = calculer_cap_boussole(mx, my, mz, ax_l, ay_l, az_l)
        if cap_brut is None:
            return self._cap_actuel()

        rad = math.radians(cap_brut)
        vx, vy = math.cos(rad), math.sin(rad)
        if self._cap_vecteur is None:
            self._cap_vecteur = (vx, vy)
        else:
            a = self.alpha_cap
            pvx, pvy = self._cap_vecteur
            self._cap_vecteur = (a * vx + (1 - a) * pvx, a * vy + (1 - a) * pvy)

        return self._cap_actuel()
