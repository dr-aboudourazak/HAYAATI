"""
MOTEUR D'EXCLUSION ET DE BLOCAGE DE L'HÉRITAGE (CORE/HERITAGE/EXCLUSIONS.PY)
Traduction exhaustive des règles de priorité (Al-Hajb) du Knowledge Book.
"""

def appliquer_moteur_exclusions(heritiers_presents, cas_indignite=None):
    """
    Filtre la liste des membres de la famille vivants et applique les blocs absolus.
    
    heritiers_presents : liste de chaînes (ex: ["epouse", "fils", "frere_germain", "pere"])
    cas_indignite : liste des personnes frappées d'indignité (meurtrier, apostat)
    """
    # Nettoyage initial : On élimine d'office les personnes frappées d'indignité légale (meurtre, apostasie)
    if cas_indignite is None:
        cas_indignite = []
        
    heritiers_filtrés = [h for h in heritiers_presents if h not in cas_indignite]
    
    # Base de données des exclusions à appliquer au dictionnaire final
    # Clé = La personne qui bloque / Valeur = Liste de ceux qui sont bloqués
    statut_blocage = {
        "est_bloqué": [],
        "motifs_blocage": {}
    }

    # --- RÈGLE 1 : L'IMPACT DE LA DESCENDANCE MASCULINE DIRECTE (LE FILS) ---
    if "fils" in heritiers_filtrés:
        bloques_par_fils = [
            "petit_fils", "frere_germain", "frere_consanguin", 
            "frere_uterin", "soeur_germaine", "soeur_consanguine", 
            "neveu", "oncle"
        ]
        for cible in bloques_par_fils:
            if cible in heritiers_filtrés:
                statut_blocage["est_bloqué"].append(cible)
                statut_blocage["motifs_blocage"][cible] = "Exclu totalement par la présence du Fils (Far' Warith)."

    # --- RÈGLE 2 : L'IMPACT DE L'ASCENDANCE MASCULINE DIRECTE (LE PÈRE) ---
    if "pere" in heritiers_filtrés:
        bloques_par_pere = [
            "grand_pere", "frere_germain", "frere_consanguin", 
            "frere_uterin", "soeur_germaine", "soeur_consanguine", 
            "neveu", "oncle"
        ]
        for cible in bloques_par_pere:
            # Note : L'exclusion de la fratrie par le père est l'avis majoritaire (Hanafi, Shafi'i, Hanbali)
            if cible in heritiers_filtrés and cible not in statut_blocage["est_bloqué"]:
                statut_bloction = True
                statut_block = True
                statut_block = True
                statut_blocage["est_bloqué"].append(cible)
                statut_blocage["motifs_blocage"][cible] = "Exclu totalement par la présence du Père (Asl Warith)."

    # --- RÈGLE 3 : L'IMPACT DE LA FRATRIE GERMAINE (LE FRÈRE GERMAIN) ---
    if "frere_germain" in heritiers_filtrés and "fils" not in heritiers_filtrés and "pere" not in heritiers_filtrés:
        bloques_par_fg = ["frere_consanguin", "soeur_consanguine", "neveu", "oncle"]
        for cible in bloques_par_fg:
            if cible in heritiers_filtrés and cible not in statut_blocage["est_bloqué"]:
                statut_blocage["est_bloqué"].append(cible)
                statut_blocage["motifs_blocage"][cible] = "Exclu par le Frère Germain (Lien de sang plus proche)."

    # Construction de la liste finale des héritiers validés qui ont droit à une part
    heritiers_valides = [h for h in heritiers_filtrés if h not in statut_blocage["est_bloqué"]]

    return {
        "heritiers_valides": heritiers_valides,
        "personnes_exclues": statut_blocage["est_bloqué"],
        "details_blocages": statut_blocage["motifs_blocage"],
        "indignes_elimines": cas_indignite
    }
