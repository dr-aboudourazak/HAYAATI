**Guide Technique Universel & Doctrine de Référence : Successions (*Farâ'id*) et Liquidation Fiscale (*Zakât*)**

**Édition Spéciale de Prestige — Application HAYAATI v1.2.0**
**Conforme aux Quatre Écoles Sunnites (*Chafi'ite, Hanbalite, Malékite, Hanafite*)**

Dans un monde où la transformation digitale redéfinit l'accès aux services essentiels, la gestion du patrimoine musulman faisait face à un défi paradoxal. D'un côté, la complexité mathématique et doctrinale des sciences rituelles de la *Zakât* et des successions, les *Farâ'id*. De l'autre, le besoin fondamental de clarté, de transparence et d'accessibilité pour les fidèles et les praticiens du droit.

Face à ce défi, la réponse traditionnelle consistait souvent à simplifier les règles au détriment de la précision, ou à figer les calculs dans des outils rudimentaires incapables de s'adapter aux divergences des quatre grandes écoles juridiques sunnites.

**HAYAATI change radicalement ce paradigme.** Développée en Python avec le framework réactif Flet, HAYAATI n'est pas une simple calculatrice. C'est un **moteur d'audits patrimoniaux et de vigilance doctrinale** de niveau industriel, entièrement autonome et *Sharia-Compliant*.

Sur le plan de la *Zakât*, l'application intègre une modélisation inédite. Elle purges de plein droit le passif cultuel — comme les dettes spirituelles des *Kaffârât* ou du pèlerinage obligatoire en retard — avant toute confrontation au seuil de richesse, le *Nisâb*. De plus, elle réadapte dynamiquement ses barèmes agro-pastoraux, appliquant par exemple le correctif d'irrigation à deux paliers fixant l'impôt agricole à 10% ou 5% selon l'effort mécanique de l'exploitant.

Sur le plan successoral, le cœur algorithmique de la plateforme résout les équations les plus redoutées du droit musulman avec une exactitude chirurgicale au centime près. Qu'il s'agisse des cas de saturation par l'*Aoul*, de redistribution par le *Radd*, ou de configurations d'exceptions historiques majeures comme la *Himariyyah*, l'*Akdariyyah*, le traitement récursif complexe de l'hermaphrodite ambigu (*Khountha Moshkil*) ou la parenté utérine périphérique (*Zawil Arham*).

Hayaati dispose de deux innovations majeures apportées par cette ultime version :

1. **La réhabilitation universelle des femmes de la fratrie** en mode résiduel (*’Asabah bi-Ghayrihi*), qui corrige les angles morts des systèmes classiques.
2. **Le stabilisateur de transparence comptable**. Désormais, un héritier éligible dont les droits s'effacent par pur épuisement de la masse — comme l'Oncle paternel dans un cas de blocage par les parts fixes — n'est plus invisibilisé. Il s'affiche explicitement à l'écran et sur le certificat PDF ReportLab avec un quota de 0.0000, offrant une visibilité et une traçabilité totales.

Enfin, pour offrir un écosystème d'apprentissage complet, l'architecture a été refondue pour intégrer le **Hub central Madrassa**. Ce panneau d'aiguillage réactif centralise de manière étanche l'Encyclopédie patrimoniale, les sciences islamiques et les outils de grammaire arabe sans aucun I/O bloquant sur le stockage Android, le tout internationalisé en 12 langues dont l'arabe littéraire canonique.

**Partie 1 : Architecture Fondamentale des Assiettes et Distinctions Comptables**

L'écosystème **HAYAATI v1.3.2** repose sur une séparation hermétique entre deux masses patrimoniales distinctes : l'**Assiette de la Zakât** (fiscalité du vivant) et la **Masse Successorale Nette / *Tarika*** (liquidation après décès). Un contresens fréquent consiste à confondre ces deux volumes. Le moteur d'HAYAATI applique des règles d'évaluation radicalement différentes selon le contexte d'audit sélectionné.

**1.1 L'Assiette de la Zakât Monétaire et Agro-Pastorale (Évaluation du Vivant)**

La Zakât est un prélèvement sur une richesse disponible, détenue en pleine propriété, ayant franchi un seuil de prospérité (*Nisâb*) et — pour les avoirs monétaires et le bétail — conservée durant une année lunaire complète (*Al-Hawl*).

[ FORTUNE BRUTE VIVANTE ]

(Liquidités + Marchandises + Métaux précieux soumis + Créances)

│

▼

– [ Passif Humain (Dettes) ]

– [ Passif Spirituel (Kaffârât, Reliquat Zakât) ]

│

▼

[ ASSIETTE FINANCIÈRE NETTE ] ◄──── Évaluation face au Nisâb arbitré (Or/Argent)

│

▼

Si ≥ Nisâb ──► Prélèvement strict de 2,5%

**Différence majeure d'évaluation (L'impôt sur le flux vs l'évaluation patrimoniale)**

* **Les Biens Immobiliers et Automobiles :** Dans le module Zakât d'HAYAATI, la valeur brute des biens immobiliers personnels, de la résidence principale ou des véhicules n'est **jamais** soumise à l'impôt (Exonération des outils de travail et biens de jouissance personnelle). Seuls les revenus ou loyers générés et thésaurisés entrent dans l'assiette.
* **Le Bétail (*An'âm*) et l'Agriculture :** Ils possèdent leurs propres barèmes canoniques et unités de prélèvement (en têtes de bétail ou en kilogrammes de grains). Ils ne sont **pas** convertis en argent pour le calcul de l'impôt monétaire, mais font l'objet d'une valorisation à blanc à l'écran pour la visibilité comptable de l'utilisateur.

**1.2 La Masse Successorale Nette / *Tarika* (Liquidation Post-Mortem)**

À la mort du fidèle, son patrimoine change instantanément de nature juridique. L'immunité fiscale des biens immobiliers ou des voitures s'éteint. **Tout ce que possédait le défunt, sans aucune exception, doit être converti en valeur monétaire** pour constituer la masse brute successorale.

[ PATRIMOINE TOTAL IMMOBILISÉ & FINANCIER ]

(Immeubles + Terrains + Voitures + Cash + Or + Troupeaux + Récoltes)

│

▼

+ [ Créances Actives ] (Argent dû au défunt)

│

▼

– [ Passif Humain ] (Dettes rigoureuses envers les tiers)

│

▼

– [ Passif Spirituel (Selon Rite) ] (Kaffârât, Coût Hajj en retard)

│

▼

[ MASSE SÉCURISÉE DE LA TARIKA ]

│

▼

– [ Legs Testamentaires / Wasiyya ] (Plafonné à 1/3 du reste)

│

▼

[ MASSE SUCCESSORALE NETTE DISTRIBUABLE ] (Ventilée aux héritiers)

**Partie 2 : Algorithmes Spécifiques du Moteur de la Zakât**

**2.1 Arbitrage du *Nisâb* (Or, Argent, Prudent)**

Le moteur d'HAYAATI permet d'arbitrer le seuil de référence selon trois modes :

1. **Arbitrage OR :** Fixé invariablement à **85 grammes d'or pur**.
2. **Arbitrage ARGENT :** Fixé invariablement à **595 grammes d'argent pur**.
3. **Arbitrage PLUS\_BAS (Prudent / Par défaut) :** Le moteur calcule en temps réel \(85 \times \text{cours\\_or}\) et \(595 \times \text{cours\\_argent}\), puis retient le minimum des deux. *Justification du Fiqh :* C’est l’avis contemporain majoritaire destiné à déclencher la Zakât le plus tôt possible afin de protéger au maximum les bénéficiaires indigents (*Masâkîn*).

**2.2 Traitement Doctrinal des Bijoux de Parure (*Al-Houly*)**

* **Régime Hanafite :** Tout or et argent possède une valeur intrinsèque soumise à la Zakât, qu'il s'agisse de lingots de refuge ou de bijoux portés. L'IHM Live inclut de force le poids de la parure personnelle (or\_parure\_poids) dans l'assiette imposable.
* **Régime des Trois Écoles (Malikite, Chafi'ite, Hanbalite) :** Les bijoux destinés à l'usage féminin licite et raisonnable sont assimilés à des vêtements ou des objets de jouissance. Le moteur d'HAYAATI les extrait et les exempte du calcul imposable.

**2.3 Le Correctif Agricole d'Irrigation et Barème Pastoral**

* **Le Nisâb Agricole :** Fixé à 5 *Wasaqs*, ce qui équivaut rigoureusement à **653 kg** d'après le consensus des savants. La Zakât est exigible le jour même de la récolte (Sourate 6, v. 141).
* **Correctif d'Irrigation Dynamique :**
  + *Irrigation Naturelle (Pluie, Crues) :* Le taux appliqué est de **10%** (*Ushr*).
  + *Irrigation Artificielle (Pompes mécaniques, Puits forés, Achat d'eau) :* L'exploitant fournissant un effort financier et humain, le taux est réduit de moitié par le moteur et passe à **5%** (*Nisf al-Ushr*).
  + *Hadith de référence :* Le Prophète ﷺ a dit : *« Pour ce qui est irrigué par la pluie et les sources, le dixième (10%). Et pour ce qui est irrigué par traction ou irrigation artificielle, le demi-dizième (5%) »* (Ibn Mâjah).
* **Barème des Cheptels (*An'âm*) :** Le moteur intègre le pacte écrit d'Abou Bakr As-Siddiq (Al-Boukhari) :
  + *Ovins/Caprins :* Nisâb à 40 têtes. De 40 à 120 \(\rightarrow \) 1 brebis ; de 121 à 200 \(\rightarrow \) 2 brebis ; de 201 à 300 \(\rightarrow \) 3 brebis.
  + *Bovins :* Nisâb à 30 têtes. De 30 à 39 \(\rightarrow \) 1 *Tabî'* (veau d'un an) ; de 40 à 59 \(\rightarrow \) 1 *Musinnah* (génisse de deux ans).

**2.4 L'Impact Étanche des Dettes Spirituelles (*Diyoun Allah*)**

Avant d'évaluer l'assiette face au *Nisâb*, le moteur d'HAYAATI applique l'arbitrage rituel :

* **Rite Hanafite & Malékite :** Les dettes envers Dieu ne réduisent pas l'assiette de la Zakât monétaire du vivant, car les créanciers humains ont la priorité d'exigibilité immédiate par la contrainte.
* **Rite Hanbalite & Chafi'ite :** Les dettes cultuelles (*Kaffârât*, Hajj obligatoire en retard) sont soustraites au même titre que les dettes humaines. *Hadith de référence :* *« La dette envers Allah a plus de droit d'être acquittée »* (Al-Boukhari).

**Partie 3 : Algorithmes Spécifiques du Moteur de l'Héritage**

**3.1 La Purge Rigoureuse du Passif Successoral (*Tarika*)**

Lors de l'appel à executer\_audit\_successoral\_complet, HAYAATI applique la chronologie des quatre devoirs successoraux :

1. **Frais d'obsèques :** Prélevés de manière décente sans gaspillage.
2. **Règlement des Dettes (Humaines et Spirituelles) :**
   * *Chafi'ite :* Les dettes spirituelles (Hajj, Expiations) sont payées en **priorité absolue** avant les dettes humaines.
   * *Hanbalite :* Égalité stricte. Si l'actif est insuffisant, répartition proportionnelle entre Dieu et les hommes.
   * *Hanafite & Malékite :* Les dettes spirituelles s'éteignent avec la mort. Elles ne sont payées **que** si le défunt a laissé un testament écrit, et s'imputent alors sur le tiers disponible.
3. **Exécution des Legs testamentaires (*Wasiyya*) :** Limité à \(1/3\) maximum de la masse restante, uniquement en faveur de non-héritiers.
4. **Distribution aux héritiers :** Application des quotas coraniques.

**3.2 Les Mécanismes d'Ajustement Proportionnel**

**A. Al-Aoul (La Saturation / Dilatation)**

Si la somme des fractions coraniques dépasse l'unité (\(\sum \text{parts} > 1.0\)), le moteur d'HAYAATI augmente dynamiquement le dénominateur commun de la base (qui passe de 6 à 7, 8, 9 ou 10 ; de 12 à 13, 15, 17 ; de 24 à 27). Cela réduit proportionnellement la valeur financière de chaque part sans léser aucun ayant droit.

* **Précédent historique :** Jurisprudence du Calife Omar ibn al-Khattâb face à la succession combinant un Époux (\(1/2\)) et deux Sœurs (\(2/3\)). Le Compagnon Zayd ibn Thâbit proposa d'élargir le dénominateur de 6 à 7.

**B. Al-Radd (La Restitution du Surplus)**

Si \(\sum \text{parts} < 1.0\) et qu'aucun héritier résiduel (*’Asabah*) n'est présent, le surplus est restitué aux héritiers à part fixe au prorata de leur droit d'origine.

* **Règle d'or hanafite/chafi'ite moderne :** L'époux ou l'épouse sont **exclus** du *Radd*. Leurs dénominateurs sont isolés de manière étanche par le moteur pour que seul le sang récupère le reliquat.
* **Exception Malékite :** L'école Malékite classique refuse le *Radd*. Le surplus non distribué est fléché vers le Trésor Public, matérialisé par la clé souveraine "###" dans HAYAATI.

**3.3 Traitement des Cas Complexes : *Khountha* et *Zawil Arham***

**A. Le Khountha Moshkil (L'Hermaphrodite Ambigu)**

Désigné par la tuile 🧬 sur l'IHM d'HAYAATI, ce cas déclenche une double simulation récursive synchrone sous-jacente :

1. **Hypothèse Mâle :** Le Khountha est traité comme un fils/frère.
2. **Hypothèse Femelle :** Le Khountha est traité comme une fille/sœur.

*Calcul final du moteur :*

* **Hanafite (Principe de prudence minimale) :** L'application lui attribue d'office la plus petite des deux parts des simulations pour sécuriser les autres héritiers.
* **Trois Écoles (Moyenne arithmétique) :** Le moteur fusionne les deux matrices et attribue au Khountha la moyenne exacte des deux statuts : \(\text{Part} = (\text{Part}\_{\text{Mâle}} + \text{Part}\_{\text{Femelle}}) / 2\).

**B. Les Zawil Arham (La Parenté Utérine Périphérique)**

Activé par la tuile 🌿, ce mode intervient lorsque le défunt ne laisse aucun héritier à part fixe ni aucun *’Asabah*.

* **Hanafite / Hanbalite (Doctrine du *Tanzil*) :** Le moteur applique une assimilation par racine. Le neveu utérin remplace le frère, la tante remplace le père. Ils absorbent la totalité de la masse et le moteur applique la règle du double pour l'homme sur leur sous-groupe.
* **Malékite / Chafi'ite :** Rejet de la parenté utérine. Le bouclier "###" s'active et attribue 100% des fonds au Trésor.

**Partie 4 : Catalogue Raisonné des Cas Pratiques (Du Simple au Complexe)**

Chaque cas est simulé sur une valeur de référence nette ou une récolte d'une valeur de **12 000 000 XOF**.

**4.1 Registre des Cas Pratiques de la Zakât**

**Cas Z1 : Moisson Agricole sous Irrigation Mixte (Le Correctif d'Eau)**

* **Intrants :** Récolte de 5 000 kg de riz (Supérieur au Nisâb de 653 kg). Valeur marchande : 12 000 000 XOF.
* **Simulation A (Pluviale / Naturelle) :** Taux plein de 10%.
  \(\text{Zakât}=12\ 000\ 000\times 0.10=\mathbf{1\ 200\ 000\ XOF}\quad (\text{ou\ }500\text{\ kg\ de\ riz})\)
* **Simulation B (Bouton Irrigation Artificielle activé) :** Taux réduit de 5% en raison des frais de carburant et de motopompe.
  \(\text{Zakât}=12\ 000\ 000\times 0.05=\mathbf{600\ 000\ XOF}\quad (\text{ou\ }250\text{\ kg\ de\ riz})\)

**Cas Z2 : Épuration par le Passif Cultuel (Diyoun Allah)**

* **Intrants (Rite Chafi'ite) :** Liquidités en banque : 12 000 000 XOF. Dettes créanciers : 4 000 000 XOF. Dettes spirituelles (Kaffâra cumulée + Frais de Hajj obligatoire non effectué) : 5 000 000 XOF. Valeur du Nisâb Or : 3 825 000 XOF.
* **Calcul du Moteur :**
  \(\text{Assiette\ Financière\ Nette}=12\ 000\ 000-4\ 000\ 000\text{\ (Dettes\ H.)}-5\ 000\ 000\text{\ (Dettes\ S.)}=3\ 000\ 000\ XOF\)
* **Verdict :** L'assiette nette (3 000 000 XOF) étant tombée **en dessous** du Nisâb (3 825 000 XOF), le rectangle d'accueil d'HAYAATI passe instantanément au vert et affiche **🟢 EXEMPTÉ**. Le montant de la Zakât due est de **0 XOF**.
* *Note :* En mode Hanafite, les 5 000 000 XOF de dettes de Dieu auraient été rejetés du vivant. L'assiette serait restée à 8 000 000 XOF (Supérieur au Nisâb), rendant le fidèle imposable à hauteur de 200 000 XOF.

**4.2 Registre des Cas Pratiques de l'Héritage**

**Cas H1 : Modèle Canonique Ordinaire avec Réhabilitation de la Sœur**

* **Composition :** Mère, Frère Utérin, Sœur Utérine, Frère Paternel, Sœur Paternelle. Masse successorale nette : 12 000 000 XOF.
* **Règle du Fiqh :** La Mère prend 1/6 (Fratrie multiple). Les deux utérins prennent 1/3 à égalité (1/6 chacun). Le reste (1/2) va aux collatéraux paternels par *Ta'sib* selon la règle du double pour l'homme (2 parts pour le frère, 1 part pour la sœur).
* **Rendu Visuel Unifié (HAYAATI v1.3.1) :**
  + Mère : \(1/6 = 0.1667 \rightarrow\) **2 000 000 XOF**
  + Frère Utérin : \(1/6 = 0.1667 \rightarrow\) **2 000 000 XOF**
  + Sœur Utérine : \(1/6 = 0.1667 \rightarrow\) **2 000 000 XOF**
  + Frère Paternel : \(2/3 \text{ du reliquat} = 1/3 = 0.3333 \rightarrow\) **4 000 000 XOF**
  + Sœur Paternelle : \(1/3 \text{ du reliquat} = 1/6 = 0.1667 \rightarrow\) **2 000 000 XOF**
* **Total :** \(1.0000 \rightarrow \mathbf{12\ 000\ 000\ XOF}\) (Fermeture comptable parfaite).

**Cas H2 : Saturation de Masse Réglée par *Al-Aoul***

* **Composition :** Époux, Mère, 2 Sœurs Germaines. Masse successorale nette : 12 000 000 XOF.
* **Règle du Fiqh :** L'Époux a droit à 1/2 (3/6), la Mère à 1/6, les deux Sœurs Germaines à 2/3 (4/6). Somme brute des numérateurs : \(3 + 1 + 4 = 8/6\). La masse est saturée. Le dénominateur commun passe automatiquement à **8**.
* **Ventilation Écran & PDF :**
  + Époux : \(3/8 = 0.3750 \rightarrow\) **4 500 000 XOF** (au lieu de 6M)
  + Mère : \(1/8 = 0.1250 \rightarrow\) **1 500 000 XOF** (au lieu de 2M)
  + Chaque Sœur Germaine : \(2/8 = 0.2500 \rightarrow\) **3 000 000 XOF** (soit 6M pour le binôme)
* **Total :** \(1.0000 \rightarrow \mathbf{12\ 000\ 000\ XOF}\)

**Cas H3 : L'Infiltration Historique de la *Himariyyah* / *Moushtarakah***

* **Composition :** Époux, Mère, 2 Frères Utérins, 1 Frère Germain. Masse : 12 000 000 XOF.
* **Règle du Fiqh :** L'Époux prend 1/2, la Mère 1/6, les frères utérins 1/3. La somme fait \(6/6 = 1.0\). Le reliquat pour le Frère Germain (*Asabah*) tombe à 0.
* **Divergence et Arbitrage du Moteur :**
  + *Mode Malikite / Chafi'ite :* Application du jugement du Calife Omar. Le frère germain est assimilé aux utérins dans leur tiers coranique. Le tiers (4 000 000 XOF) est divisé par 3 têtes à parts égales.
    - Frère Utérin 1 : **1 333 333,33 XOF** | Frère Utérin 2 : **1 333 333,33 XOF** | Frère Germain : **1 333 333,33 XOF**
  + *Mode Hanafite / Hanbalite :* Règle littérale stricte. Le résidu étant nul, le Frère Germain prend **0.00 XOF**. Grâce au stabilisateur de transparence, il s'affiche en haut dans le tableau principal : **Frère Germain : 0.0000 (0.00 XOF)**.

**Cas H4 : L'Affrontement Épique de l'*Akdariyyah* (Jurisprudence de l'Aïeul)**

* **Composition :** Époux, Mère, Sœur Germaine, Grand-Père Paternel. Masse : 12 000 000 XOF.
* **Règle du Fiqh (Hors Hanafite) :** C'est le seul cas où le grand-père n'exclut pas la sœur mais subit un *Aoul* suivi d'un co-partage forcé au ratio 2:1. La base de calcul finale s'établit sur **27**.
* **Ventilation de Prestige (Chafi'ite/Malékite/Hanbalite) :**
  + Époux : \(9/27 = 0.3333 \rightarrow\) **4 000 000 XOF**
  + Mère : \(6/27 = 0.2222 \rightarrow\) **2 666 666,67 XOF**
  + Grand-Père Paternel : \(8/27 = 0.2963 \rightarrow\) **3 555 555,56 XOF**
  + Sœur Germaine : \(4/27 = 0.1481 \rightarrow\) **1 777 777,78 XOF**
* **Mode Hanafite :** Le Grand-père équivaut strictement au Père et exclut la sœur. Époux : 1/2 (**6M**) | Mère : 1/3 (**4M**) | Grand-Père : 1/6 (**2M**) | Sœur : **0 XOF** (Envoyée dans la section des exclus *Hajb*).

**Cas H5 : Transparence de l'Asabah Évincé par Épuisement de la Masse**

* **Composition :** Mère, Petite-Fille (Fille du Fils), Frère Utérin, Sœur Utérine, Oncle Paternel Germain. Masse Successorale Nette : 12 000 000 XOF.
* **Règle du Fiqh :** La Petite-fille prend sa moitié coranique de 1/2 (6M) car elle est seule et remplace la fille. La Mère prend 1/6 (2M). Les deux utérins prennent 1/3 (4M, soit 2M chacun). La somme des parts fixes fait : \(3/6 + 1/6 + 2/6 = 6/6 = 1.0\). La masse est épuisée. L'Oncle Paternel Germain (*Asabah*) se retrouve avec un résidu nul.
* **Rendu Visuel Révolutionnaire HAYAATI v1.3.2 :**
  + Petite-Fille : 0.5000 \(\rightarrow \) **6 000 000 XOF**
  + Mère : 0.1667 \(\rightarrow \) **2 000 000 XOF**
  + Frère Utérin : 0.1667 \(\rightarrow \) **2 000 000 XOF**
  + Sœur Utérine : 0.1667 \(\rightarrow \) **2 000 000 XOF**
  + **Oncle Paternel Germain :** 0.0000 \(\rightarrow \) **0.00 XOF** (Affiché fièrement tout en haut du tableau pour une clarté absolue, sans polluer la section des exclus de sang).

**Partie 5 : Faits Historiques Enregistrés dans la *Sîrah* et Grandes Figures**

Pour fortifier la soutenance, le moteur d'HAYAATI s'appuie sur les précédents historiques majeurs qui ont fixé les lignes de code de la Sharia.

**5.1 L'Origine du Plafond du Tiers : Sa'd ibn Abî Waqqâs**

Lors du Pèlerinage d'Adieu (10 AH), le grand Compagnon Sa'd ibn Abî Waqqâs tomba gravement malade à La Mecque. Étant fort fortuné et n'ayant alors qu'une seule fille pour héritière, il dit au Prophète ﷺ : *« Puis-je faire don des deux tiers (2/3) de mes biens en aumône ? »* Le Prophète ﷺ répondit : *« Non »*. Sa'd dit : *« Et de la moitié (1/2) ? »* Le Prophète ﷺ répondit : *« Non »*. Sa'd dit : *« Et du tiers (1/3) ? »* Le Prophète ﷺ dit : **« Le tiers, oui, et le tiers c'est déjà beaucoup. Il vaut mieux que tu laisses tes héritiers riches plutôt que de les laisser pauvres et dépendants, tendant la main aux gens »** (Al-Boukhari & Muslim).

* *Application Informatique :* C’est la ligne de code exacte qui borne la variable wasiyya\_retenue = min(legs\_demande, safe\_mass / 3.0).

**5.2 L'Origine de la *Moushtarakah* / *Himariyyah* : Le Décret d'Omar**

Sous le califat d'Omar ibn al-Khattâb, une première affaire fut jugée selon la règle littérale : le frère germain fut écarté car les utérins avaient épuisé le tiers coranique. L'année suivante, le même cas se représenta. Le frère germain s'exclama alors devant Omar : *« Ô Émir des croyants ! Suppose que notre père ait été un âne (Himar) ou une pierre jetée à la mer, ne partageons-nous pas la même mère ? »* Omar ibn al-Khattâb reconnut la justesse de l'interpellation et modifia sa jurisprudence en ordonnant le co-partage égalitaire dans le tiers.

* *Application Informatique :* C’est le commutateur algorithmique activé lorsque doctrine in ["Malikite", "Chafiite"] rencontre une absence de descendants masculins directs.

**5.3 Le Maître des Fractions : Zayd ibn Thâbit**

Qualifié par le Prophète ﷺ de *« plus savant de la communauté en matière de successions »*, Zayd ibn Thâbit est la figure centrale qui a modélisé l'arbre des exclusions collatérales et fixé les règles de l'Aïeul (*Al-Jadd*). C'est lui qui a résolu l'équation complexe de l'*Akdariyyah* (nommée ainsi car elle a "assombri" les règles habituelles en forçant une exception de co-partage). Ses formules mathématiques constituent l'ossature algorithmique globale du fichier fractions.py d'HAYAATI.

**📊 Tableau Mémo des Cas de Rupture et Équations Spécifiques**

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
| **Type d'Audit** | **Cas Clinique / Rupture** | **Intrants Saisis à l'Écran** | **Comportement de l'Algorithme d'HAYAATI** | **Fondement Canonique & Référence** |
| **ZAKÂT** | **L'irrigation artificielle** | Récolte : 5 000 kg Option : *Irrigation Artificielle Activée* | Le moteur applique le correctif de **5%** (*Nisf al-Ushr*) au lieu de 10%. La Zakât tombe à 250 kg. | Hadith Ibn Omar (Al-Boukhari) : « 5% pour ce qui est irrigué par traction mécanique. » |
| **ZAKÂT** | **Purge spirituelle (Diyoun Allah)** | Cash : 12M XOF Dettes Dieu : 5M XOF Nisâb : 3.82M XOF | **Chafi'ite/Hanbalite :** Déduit le passif de Dieu. L'assiette tombe à 3M (inférieure au Nisâb). L'IHM affiche **🟢 EXEMPTÉ**. | Hadith Ibn Abbas (Al-Boukhari) : « La dette envers Allah a plus de droit d'être acquittée. » |
| **HERITAGE** | **Saturation par l'Aoul** | Époux, Mère, 2 Sœurs Germaines | La somme des parts fait 8/6. Le moteur élargit dynamiquement le **dénominateur à 8**. L'Époux passe de 1/2 à 3/8. | Jurisprudence du Calife Omar ibn al-Khattâb et Zayd ibn Thâbit. |
| **HERITAGE** | **Destitution de l'Asabah par épuisement** | Mère, Petite-Fille, Frère Utérin, Sœur Utérine, Oncle | La somme des parts fixes fait 1.0 pile. Le reliquat est nul. L'Oncle s'affiche au tableau avec **0.0000 (0.00 XOF)** par transparence. | Versets coraniques des parts fixes (Sourate An-Nisâ', v. 11-12) et statut résiduel de l'Oncle. |
| **HERITAGE** | **L'infiltration de la Himariyyah** | Époux, Mère, 2 Frères Utérins, 1 Frère Germain | **Malékite/Chafi'ite :** Fusionne le frère germain dans le 1/3 des utérins. **Hanafite/Hanbalite :** Frère germain = 0.00 XOF. | Jugement historique d'Omar : « Considérez que notre père était un âne... » |
| **HERITAGE** | **L'exception de l'Akdariyyah** | Époux, Mère, Sœur Germaine, Grand-Père Paternel | **Hors Hanafite :** Fusionne les parts du grand-père et de la sœur puis applique le ratio 2:1 sur une **base de 27**. | Jurisprudence de Zayd ibn Thâbit (Seul cas où la sœur co-hérite avec le grand-père). |
| **HERITAGE** | **Le Khountha Moshkil (Hermaphrodite)** | 1 Fils, 1 Fille, + Activer Tuile 🧬 (Khountha) | **Chafi'ite/Malékite :** Calcule la **moyenne arithmétique** exacte des deux arbres virtuels mâles et femelles. | Consensus des juristes contemporains sur la fusion géométrique des risques. |
| **HERITAGE** | **Les Zawil Arham (Parenté périphérique)** | Aucun héritier standard + Activer Tuile 🌿 | **Hanafite/Hanbalite :** Applique la doctrine du ***Tanzil*** (assimilation par la racine de la Mère) à 100%. | Jurisprudence des compagnons Ibn Mas'oud et Ali ibn Abi Talib. |