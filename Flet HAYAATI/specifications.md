# 🏛️ DOCUMENTATION TECHNIQUE PLAN-MAÎTRE : PLATEFORME SHARIA-COMPLIANT
> **Version :** 1.0.0 (Édition Complète Exhaustive)  
> **Auteur :** Abdourazak & AI Collaborator  
> **Statut :** Prêt pour implémentation  

---

# 📖 PARTIE 1 : KNOWLEDGE BOOK (KB) EXHAUSTIF

## 🏦 MODULE I : MOTEUR COMPTABLE DE LA ZAKAT (FINTECH)
L'application doit calculer la Zakat sur la base du patrimoine net à la date anniversaire (*Al-Hawl*). Si la valeur totale dépasse le *Nissab* (valeur de 85g d'or pur ou 595g d'argent pur), la Zakat de 2,5% est déclenchée sur les actifs éligibles.

### 1. Actifs Financiers et Métaux Précieux
* **Liquidités & Comptes courants** : Soumis à **2,5%** à l'unanimité.
* **Or & Argent d'investissement** : Soumis à **2,5%** (lingots, pièces, jetons).
* **Bijoux personnels (Or/Argent)** :
  * *Moteur Hanafi :* Soumis à **2,5%** (l'intention de parure ne modifie pas la valeur intrinsèque du métal).
  * *Moteurs Maliki / Shafi'i / Hanbali :* **Exonérés** si l'usage est licite et destiné à la parure personnelle.

### 2. Investissements Modernes, Commerce & Immobilier
* **Fonds de commerce (Stocks marchands)** : Évalués à leur valeur marchande actuelle (prix de gros au jour du calcul) → Soumis à **2,5%**. Les actifs immobilisés (murs, serveurs, mobilier) sont exonérés.
* **Actions & Actifs Crypto** :
  * *Trading/Spéculation (Court terme) :* Soumis à **2,5%** sur la valeur totale du portefeuille au jour du calcul.
  * *Investissement long terme (Rendement) :* Soumis à **2,5%** uniquement sur la part liquide de l'entreprise émettrice (fonds de roulement + marchandises stockées).
* **Immobilier et Propriétés** :
  * *Résidence principale/secondaire :* Exonérée.
  * *Biens destinés à la revente (Promotion) :* Soumis à **2,5%** de la valeur marchande estimée chaque année.
  * *Biens locatifs :* Structure exonérée. Les loyers perçus accumulés sont soumis à **2,5%** s'ils sont conservés jusqu'au terme de l'année.

### 3. Actifs Agricoles & Élevage
* **Agriculture (Céréales et fruits stockables)** : Prélèvement direct au moment de la récolte (pas de condition de durée d'un an). Seuil (*Nissab*) = 5 Awsuq (~653 kg).
  * *Irrigation naturelle (Pluie/Rivières) :* **10%** de la récolte.
  * *Irrigation artificielle (Pompes, coûts humains) :* **5%** de la récolte.
* **Élevage (Ovins, Bovins, Camelins)** : Application stricte du barème par paliers (ex: 40-120 moutons = 1 mouton ; 30-39 bovins = 1 veau d'un an).

---

## 📜 MODULE II : MOTEUR LOGIQUE DE L'HÉRITAGE (LEGALTECH)
Le moteur d'héritage applique des calculs fractionnaires basés sur les règles de priorité, d'exclusion constitutionnelle et de réduction proportionnelle.

### 1. Les Héritiers à Parts Fixes (*Ashab al-Furud*)
Le système doit attribuer en priorité les quotes-parts coraniques absolues selon la présence d'une descendance (*Far' Warith*) :
* **Époux :** **1/2** (si aucun enfant) ou **1/4** (s'il y a des enfants).
* **Épouse(s) :** **1/4** (si aucun enfant) ou **1/8** (s'il y a des enfants). Partagée équitablement en cas de polygamie.
* **Fille unique :** **1/2** (si elle n'a pas de frère).
* **Plusieurs filles (≥ 2) :** **2/3** partagés équitablement entre elles (si aucun fils).
* **Père :** **1/6** s'il y a une descendance masculine (Fils/Petit-fils).
* **Mère :** **1/6** (si enfants ou présence de plusieurs frères/sœurs) ou **1/3** (en l'absence d'enfants et de fratrie).

### 2. Le Moteur d'Exclusion Absolue et Relative (*Al-Hajb*)
Le code doit exécuter un filtre d'exclusion systématique avant toute distribution :
* **Le Fils** exclut totalement : Les petits-enfants, les frères (germains, consanguins, utérins), les sœurs, les oncles, et les neveux.
* **Le Père** exclut : Les grands-pères, ainsi que l'ensemble des frères et sœurs (selon la majorité jurisprudentielle).
* **Exclusions pour cause d'indignité :** Le meurtrier de l'auteur de la succession ou l'apostat voient leur part fixée à **0** de manière irrévocable.

### 3. Les Héritiers Résiduels (*Al-Asabah*)
Après distribution des parts fixes, le reliquat de l'actif revient aux parents masculins les plus proches.
* **Règle du double ratio :** En présence d'un fils et d'une fille, la fille perd sa part fixe (1/2). Ils deviennent résiduels ensemble. Le reliquat est divisé selon la formule : **2 parts pour un homme, 1 part pour une femme**.

### 4. Correcteurs Algorithmiques Mathématiques
* **Al-Aoul (Surcharge budgétaire) :** Si la somme des fractions attribuées est supérieure à 1 (ex: 1/2 + 2/3 + 1/6 = 8/6). Le programme doit automatiquement ajuster le dénominateur commun (le passer de 6 à 8) pour réduire proportionnellement toutes les parts.
* **Al-Radd (Restitution du surplus) :** Si la somme des fractions est inférieure à 1 et qu'il n'y a aucun héritier résiduel pour récupérer le reste. Le surplus est redistribué proportionnellement aux héritiers fixes (à l'exclusion des conjoints selon la jurisprudence standard).

---

# 📋 PARTIE 2 : PRODUCT REQUIREMENT DOCUMENT (PRD)

## 🎯 1. VISION ET CADRAGE DU PRODUIT
Développer une suite applicative capable de centraliser les obligations légales islamiques financières et successorales d'un utilisateur, en garantissant la conformité textuelle via un sélecteur d'école jurisprudentielle (*Madhhab*).

## 🛠️ 2. SPÉCIFICATIONS FONCTIONNELLES
* **F-CORE-01 (Gestion du Madhhab) :** L'utilisateur doit pouvoir configurer son école (Hanafi, Maliki, Shafi'i, Hanbali) dès l'initialisation de l'application.
* **F-ZAK-01 (Saisie Multi-Actifs) :** Formulaire complet segmenté : Cash, Or (investissement), Bijoux (personnels), Actions, Immobilier commercial.
* **F-ZAK-02 (Vérification Algorithmique) :** Récupération automatique ou manuelle du cours de l'or. Calcul automatique du seuil du *Nissab*. Application de la condition temporelle (*Al-Hawl*).
* **F-HER-01 (Configuration Familiale) :** Interface graphique permettant de cocher dynamiquement les membres de la famille encore en vie et d'indiquer d'éventuels cas d'exclusion (ex: meurtrier).
* **F-HER-02 (Rapport Fractionnaire) :** Affichage du tableau de ventilation final indiquant la fraction brute, le pourcentage réel et la conversion en monnaie locale basée sur l'actif net saisi.

## 🚨 3. SÉCURITÉ ET CRITÈRES D'ACCEPTATION
* **Zéro plantage informatique :** Toute entrée de caractères alphabétiques dans un champ numérique doit déclencher une alerte visuelle explicite sans interrompre le processus.
* **Précision mathématique :** Les calculs de fractions d'héritage doivent conserver une précision absolue (pas d'arrondis prématurés sur les flottants avant la conversion monétaire finale).

---

# 🏗️ PARTIE 3 : DOCUMENT D'ARCHITECTURE (ARC)

## 📂 1. ARBORESCENCE TECHNIQUE DU PROJET
Le projet est structuré suivant une architecture modulaire propre afin de séparer la logique métier de l'interface visuelle.

```text
MaPlateforme/
│
├── core/
│   ├── __init__.py
│   ├── zakat/
│   │   ├── __init__.py
│   │   ├── finance.py       # Traitement Cash, Métaux, Cryptomonnaies
│   │   ├── commerce.py      # Évaluation Stocks et Actifs Immobiliers
│   │   └── agriculture.py   # Calculs Récoltes et Élevage
│   │
│   └── heritage/
│       ├── __init__.py
│       ├── exclusions.py    # Logique de filtrage et de blocage (Hajb)
│       ├── fractions.py     # Attribution des quotes-parts de base
│       └── math_adjust.py   # Algorithmes correcteurs Al-Aoul et Al-Radd
│
├── gui/
│   ├── __init__.py
│   ├── app_visuelle.py      # Fenêtre principale et navigation inter-modules
│   ├── interface_zakat.py   # Formulaires et grilles d'actifs
│   └── interface_heritage.py# Interface d'arbre généalogique dynamique
│
└── app.py                   # Script d'allumage principal de la plateforme
```

## 🧮 2. MODÉLISATION DE LA LOGIQUE MÉTIER (PSEUDO-CODE PYTHON)

### module: `core/zakat/finance.py`
```python
def determiner_eligibilite_zakat(cash, or_invest, bijoux, cours_or, madhhab="maliki"):
    """
    Calcule la valeur totale des actifs financiers et applique les filtres du KB.
    """
    nissab = 85 * cours_or
    total_actifs = cash + or_invest
    
    # Règle de l'école Hanafi sur la parure personnelle
    if madhhab == "hanafi":
        total_actifs += bijoux
        
    if total_actifs >= nissab:
        montant_du = total_actifs * 0.025
        return {"eligible": True, "montant": montant_du, "nissab": nissab}
    
    return {"eligible": False, "montant": 0, "nissab": nissab}
```

### module: `core/heritage/exclusions.py`
```python
def appliquer_moteur_exclusions(liste_heritiers):
    """
    Analyse les liens de parenté et applique les règles de blocage (Hajb).
    """
    heritiers_actifs = liste_heritiers.copy()
    
    # Règle de blocage : Le fils bloque la fratrie
    if "fils" in heritiers_actifs:
        for fraternel in ["frere_germain", "frere_consanguin", "soeur", "neveu"]:
            if fraternel in heritiers_actifs:
                heritiers_actifs.remove(fraternel)
                
    # Règle de blocage : Le père bloque les grands-parents
    if "pere" in heritiers_actifs:
        if "grand_pere" in heritiers_actifs:
            heritiers_actifs.remove("grand_pere")
            
    return heritiers_actifs
```
