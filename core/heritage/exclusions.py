"""
LOGIQUE ATOMIQUE - EXCLUSIONS ET MASQUAGES DES 21 CATÉGORIES (CORE/HERITAGE/EXCLUSIONS.PY)
Version 5.0 - Intégration exhaustive du Hajb pour les 21 candidats et arbitrage des écoles.
"""

def filtrer_heritiers_indignes(liste_brute_membres):
    """Filtre les membres exclus d'office pour cause d'indignité successorale ou quantité nulle."""
    valides = []
    exclus = []
    for membre in liste_brute_membres:
        if isinstance(membre, str):
            valides.append({"lien": membre, "quantite": 1, "est_indigne": False})
        elif isinstance(membre, dict):
            if membre.get("est_indigne", False) or membre.get("quantite", 0) <= 0:
                exclus.append(membre["lien"])
            else:
                valides.append(membre)
    return valides, exclus

def appliquer_blocages_reciproques(liste_membres_filtres, doctrine_active="Malikite"):
    """
    Applique les règles de masquage (Hajb) absolues ou partielles de la Sharia.
    Prend en compte les 21 catégories d'héritiers selon le Fiqh choisi.
    """
    dict_h = {}
    for m in liste_membres_filtres:
        dict_h[m["lien"]] = m["quantite"]
        
    finaux = dict_h.copy()
    doc = str(doctrine_active).strip().capitalize()

    # 🎯 0. SÉCURITÉ CONJOINTS (L'IHM bloque le double-cumul, mais le moteur valide l'étanchéité)
    if "epoux" in finaux and "epouse" in finaux:
        del finaux["epoux"]

    # 🎯 1. MASQUAGES UNIVERSELS PAR LE PÈRE (Bloque les aïeux et collatéraux)
    if dict_h.get("pere", 0) > 0:
        exclus_par_pere = [
            "grand_pere", "grand_mere", "frere_germain", "soeur_germaine", 
            "frere_paternel", "soeur_paternelle", "frere_uterin", "soeur_uterine",
            "fils_frere_germain", "fils_frere_paternel", "oncle_germain", 
            "oncle_paternel", "cousin_germain", "cousin_paternel"
        ]
        for h in exclus_par_pere:
            if h in finaux: del finaux[h]

    # 🎯 2. MASQUAGES UNIVERSELS PAR LE FILS (Lignée descendante directe mâle)
    if dict_h.get("fils", 0) > 0:
        exclus_par_fils = [
            "petit_fils", "petite_fille", "frere_germain", "soeur_germaine", 
            "frere_paternel", "soeur_paternelle", "frere_uterin", "soeur_uterine",
            "fils_frere_germain", "fils_frere_paternel", "oncle_germain", 
            "oncle_paternel", "cousin_germain", "cousin_paternel"
        ]
        for h in exclus_par_fils:
            if h in finaux: del finaux[h]

    # 🎯 3. MASQUAGES PAR LE PETIT-FILS (Si aucun fils direct n'est vivant)
    if dict_h.get("petit_fils", 0) > 0 and dict_h.get("fils", 0) == 0:
        exclus_par_p_fils = [
            "frere_germain", "soeur_germaine", "frere_paternel", "soeur_paternelle", 
            "frere_uterin", "soeur_uterine", "fils_frere_germain", "fils_frere_paternel", 
            "oncle_germain", "oncle_paternel", "cousin_germain", "cousin_paternel"
        ]
        for h in exclus_par_p_fils:
            if h in finaux: del finaux[h]

    # 🎯 4. MASQUAGES PAR LA MÈRE (Bloque toutes les grands-mères maternelles et paternelles)
    if dict_h.get("mere", 0) > 0:
        if "grand_mere" in finaux: 
            del finaux["grand_mere"]

    # 🎯 5. DIVERGENCE CRITIQUE DU FIQH : LE GRAND-PÈRE FACE À LA FRATRIE
    if dict_h.get("grand_pere", 0) > 0 and dict_h.get("pere", 0) == 0:
        # Règle absolue (Ijma') : Le grand-père exclut TOUJOURS la lignée utérine (côté mère)
        for h_uterin in ["frere_uterin", "soeur_uterine"]:
            if h_uterin in finaux: del finaux[h_uterin]
            
        if doc == "Hanafite":
            # ⚖️ ECOLE HANAFITE : Le grand-père est assimilé au père, il masque TOUTES les catégories de frères/sœurs
            for collat in ["frere_germain", "soeur_germaine", "frere_paternel", "soeur_paternelle"]:
                if collat in finaux: del finaux[collat]

    # 🎯 6. CASCADES DE BLOCAGES COLLATÉRAUX COMPLETS (Ordre de proximité Asabah)
    # A. Le Frère Germain ou la Sœur Germaine (si rendue Asabah) exclut les collatéraux paternels et éloignés
    if dict_h.get("frere_germain", 0) > 0 or (dict_h.get("soeur_germaine", 0) > 0 and dict_h.get("fille", 0) > 0):
        exclus_par_germain = [
            "frere_paternel", "soeur_paternelle", "fils_frere_germain", 
            "fils_frere_paternel", "oncle_germain", "oncle_paternel", 
            "cousin_germain", "cousin_paternel"
        ]
        for h in exclus_par_germain:
            if h in finaux: del finaux[h]

    # B. Le Frère Paternel exclut les neveux et oncles
    if dict_h.get("frere_paternel", 0) > 0:
        exclus_par_fr_pat = [
            "fils_frere_germain", "fils_frere_paternel", "oncle_germain", 
            "oncle_paternel", "cousin_germain", "cousin_paternel"
        ]
        for h in exclus_par_fr_pat:
            if h in finaux: del finaux[h]

    # C. Le Fils du Frère Germain (Neveu) exclut les neveux paternels et oncles
    if dict_h.get("fils_frere_germain", 0) > 0:
        exclus_par_nev_germ = [
            "fils_frere_paternel", "oncle_germain", "oncle_paternel", 
            "cousin_germain", "cousin_paternel"
        ]
        for h in exclus_par_nev_germ:
            if h in finaux: del finaux[h]

    # D. Le Fils du Frère Paternel exclut la lignée des oncles et cousins
    if dict_h.get("fils_frere_paternel", 0) > 0:
        exclus_par_nev_pat = ["oncle_germain", "oncle_paternel", "cousin_germain", "cousin_paternel"]
        for h in exclus_par_nev_pat:
            if h in finaux: del finaux[h]

    # E. L'Oncle Paternel Germain exclut l'oncle paternel simple et les cousins
    if dict_h.get("oncle_germain", 0) > 0:
        exclus_par_onc_germ = ["oncle_paternel", "cousin_germain", "cousin_paternel"]
        for h in exclus_par_onc_germ:
            if h in finaux: del finaux[h]

    # F. L'Oncle Paternel exclut tous les cousins
    if dict_h.get("oncle_paternel", 0) > 0:
        exclus_par_onc_pat = ["cousin_germain", "cousin_paternel"]
        for h in exclus_par_onc_pat:
            if h in finaux: del finaux[h]

    # G. Le Cousin Germain exclut le cousin par le père
    if dict_h.get("cousin_germain", 0) > 0:
        if "cousin_paternel" in finaux: del finaux["cousin_paternel"]

    return finaux

def _appliquer_moteur_exclusions_compat(liste_brute_membres, cas_indignite=None, doctrine_active="Malikite"):
    if isinstance(liste_brute_membres, dict):
        liste_brute_membres = [{"lien": k, "quantite": v, "est_indigne": False} for k, v in liste_brute_membres.items()]
        if isinstance(cas_indignite, list):
            for item in liste_brute_membres:
                if item["lien"] in cas_indignite: item["est_indigne"] = True

    valides, exclus_indignes = filtrer_heritiers_indignes(liste_brute_membres)
    finaux = appliquer_blocages_reciproques(valides, doctrine_active=doctrine_active)
    
    tous_les_exclus = exclus_indignes.copy()
    liste_liens_bruts = [m["lien"] if isinstance(m, dict) else m for m in liste_brute_membres]
    for original in liste_liens_bruts:
        if original not in finaux and original not in tous_les_exclus:
            tous_les_exclus.append(original)

    return {"heritiers_valides": finaux, "personnes_exclues": tous_les_exclus}

appliquer_moteur_exclusions = _appliquer_moteur_exclusions_compat
