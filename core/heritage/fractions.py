"""
MOTEUR DE CALCUL DES PARTS SUCCESSORALES EXHAUSTIF (CORE/HERITAGE/FRACTIONS.PY)
Prend en charge le décompte des personnes, les grands-parents, oncles, et le Kalâlah.
"""

def distribuer_parts_completes(heritiers_retenus, configuration_nombres):
    """
    Calcule les fractions exactes selon la présence et le nombre de chaque héritier.
    configuration_nombres : dictionnaire (ex: {"epouse": 2, "fils": 1, "fille": 3, "frere_uterin": 2})
    """
    parts = {}
    
    # Extraction des présences réelles (uniquement s'ils ont survécu au filtre des exclusions)
    nb_epouse = configuration_nombres.get("epouse", 0) if "epouse" in heritiers_retenus else 0
    nb_epoux = configuration_nombres.get("epoux", 0) if "epoux" in heritiers_retenus else 0
    nb_fils = configuration_nombres.get("fils", 0) if "fils" in heritiers_retenus else 0
    nb_fille = configuration_nombres.get("fille", 0) if "fille" in heritiers_retenus else 0
    
    pere = 1 if "pere" in heritiers_retenus else 0
    mere = 1 if "mere" in heritiers_retenus else 0
    grand_pere = 1 if "grand_pere" in heritiers_retenus else 0
    
    nb_frere_g = configuration_nombres.get("frere_germain", 0) if "frere_germain" in heritiers_retenus else 0
    nb_soeur_g = configuration_nombres.get("soeur_germaine", 0) if "soeur_germaine" in heritiers_retenus else 0
    nb_frere_ut = configuration_nombres.get("frere_uterin", 0) if "frere_uterin" in heritiers_retenus else 0
    nb_oncles = configuration_nombres.get("oncle", 0) if "oncle" in heritiers_retenus else 0

    has_descendance = (nb_fils > 0 or nb_fille > 0)
    has_ascendance = (pere > 0 or grand_pere > 0)

    # 🚨 DÉTECTION DU CAS KALÂLAH (Ni descendance direct, ni ascendance masculine)
    is_kalalah = (not has_descendance and not has_ascendance)

    # 1. LES CONJOINTS
    if nb_epouse > 0:
        parts["epouse"] = 0.125 if has_descendance else 0.25
    if nb_epoux > 0:
        parts["epoux"] = 0.25 if has_descendance else 0.5

    # 2. LES ASCENDANTS
    if pere > 0:
        parts["pere"] = 1/6  # Part fixe minimale s'il y a des enfants
    elif grand_pere > 0 and pere == 0:
        parts["grand_pere"] = 1/6

    if mere > 0:
        if has_descendance or (nb_frere_g + nb_soeur_g + nb_frere_ut > 1):
            parts["mere"] = 1/6
        else:
            parts["mere"] = 1/3

    # 3. LES FILLES EN L'ABSENCE DE FILS (Parts fixes coraniques)
    if nb_fille > 0 and nb_fils == 0:
        parts["fille"] = 0.5 if nb_fille == 1 else (2/3)

    # 4. APPLICATION DU KALÂLAH MATERNEL (Frères/Sœurs utérins)
    if is_kalalah and nb_frere_ut > 0:
        parts["frere_uterin"] = 1/6 if nb_frere_ut == 1 else 1/3

    # 5. GESTION DU RELIQUAT (ASABAH / HÉRITIERS RÉSIDUELS)
    somme_parts_fixes = sum(parts.values())
    reliquat = max(0.0, 1.0 - somme_parts_fixes)

    if reliquat > 0:
        # Priorité 1 des résiduels : Les enfants (Fils et Filles ensemble)
        if nb_fils > 0:
            # Règle du double ratio pour l'homme : Fils = 2 parts, Fille = 1 part
            poids_total = (nb_fils * 2) + (nb_fille * 1)
            valeur_part_unitaire = reliquat / poids_total
            parts["fils"] = valeur_part_unitaire * 2 * nb_fils
            if nb_fille > 0:
                parts["fille"] = valeur_part_unitaire * 1 * nb_fille
        
        # Priorité 2 : Le Père récupère le reliquat s'il n'y a pas de fils
        elif pere > 0:
            parts["pere"] = parts.get("pere", 0) + reliquat
            
        # Priorité 3 : Le Grand-père (si le père est absent)
        elif grand_pere > 0:
            parts["grand_pere"] = parts.get("grand_pere", 0) + reliquat

        # Priorité 4 : LA FRATRIE GERMAINE EN CAS DE KALÂLAH
        elif is_kalalah and (nb_frere_g > 0 or nb_soeur_g > 0):
            poids_fratrie = (nb_frere_g * 2) + (nb_soeur_g * 1)
            if poids_fratrie > 0:
                valeur_u = reliquat / poids_fratrie
                if nb_frere_g > 0: parts["frere_germain"] = valeur_u * 2 * nb_frere_g
                if nb_soeur_g > 0: parts["soeur_germaine"] = valeur_u * 1 * nb_soeur_g

        # Priorité 5 : LES ONCLES PATERNELS
        elif nb_oncles > 0 and not pere and not grand_pere and nb_fils == 0 and nb_frere_g == 0:
            parts["oncle"] = reliquat

    return {
        "ventilation_fractions": parts,
        "is_kalalah_detected": is_kalalah
    }
