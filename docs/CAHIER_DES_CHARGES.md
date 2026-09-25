# HELLOFEDGE — Cahier des charges v0.3

> Compagnon de trading **USD/JPY uniquement**, basé sur la stratégie SMC RedPillFX, enrichi des leviers propres à USD/JPY.
> Statut : **brouillon de conception**. Aucune ligne de code tant que ce document n'est pas validé.
> Sources : `PDF FORMA YTB_compressed.pdf` (113 pages) + transcription complète de la formation (intégrée en v0.2).

---

## 0. Les principes (non négociables)

1. **Un seul instrument : USD/JPY.** D'autres données (taux, DXY, indices) ne servent qu'à *éclairer* USD/JPY, jamais à trader autre chose.
2. **Compagnon, pas robot.** L'outil analyse, prépare, surveille, alerte, suit et journalise. **Il ne passe aucun ordre.** C'est toi qui décides et qui cliques.
3. **Horizon : de quelques minutes à quelques heures.** Tout est pensé pour l'intraday. L'outil accompagne aussi une position ouverte jusqu'à sa clôture, y compris quand elle passe d'une session à l'autre ou la nuit.
4. **Le calcul est déterministe, l'IA synthétise.** Structure, liquidité, FVG, BB, CISD, sessions, niveaux : **du code, testé, reproductible**. Les agents IA lisent ces résultats et l'actualité, puis rédigent les plans, les briefs et les alertes. Une IA ne « devine » jamais où est un niveau.
5. **L'edge se mesure.** Chaque setup détecté (pris ou non) est enregistré avec tout son contexte et son résultat. Les statistiques décident de ce qui marche sur USD/JPY, pas l'intuition.
6. **Discipline intégrée.** La formation insiste sur la psychologie (chap. psycho, p.2 à 11). L'outil fait respecter le plan : fenêtres horaires, pièges de session, limites de risque, anti-revenge trading.
7. **Qualité pro.** Disponible 24 h/24 dans le cloud, monitoré, sauvegardé, sécurisé, utilisable sur PC et téléphone.

---

## 1. La stratégie formalisée (ce que le code doit savoir détecter)

Sources : le PDF (113 pages) et **la transcription complète de la formation**. Chaque concept est traduit en **règle calculable**. Les ⚠️ restants sont listés en section 11.

### 1.0 Le principe fondateur : la loi de cause à effet
- **Liquidité = cause. Mouvement = effet.** Le prix va de liquidité en liquidité : il prend une liquidité (cause), crée un mouvement (effet) dont le but est d'aller prendre la liquidité suivante, et ainsi de suite.
- **Un cycle** = cause, puis effet, puis prochaine cause. Quand la prochaine cause est prise, **le cycle est terminé**.
- Conséquence directe pour le moteur : chaque swing, chaque zone et chaque mouvement est rattaché au **cycle** qui l'a produit. C'est la base de tout le reste (zones valides ou pièges, interdiction du retest, cible du trade).
- « Tous les highs et les lows sont de la liquidité. » La difficulté est de savoir **laquelle est la plus importante** : plus l'UT est haute, plus elle compte. Pour la prochaine cible, c'est **la plus proche** du cycle en cours.

### 1.1 Rôle des unités de temps
| UT | Rôle |
|---|---|
| **W, D1, H4, H1, M15** | HTF : structure externe, **biais** (IPA/EPA + liquidité), POI |
| **M5 et M3** | UT principales : structure interne, lecture du cycle |
| **M5, M3, M1** | Positionnement : l'entrée peut se faire sur **M5, M3 ou M1** |
| **M15** | Repli pour le déclencheur si rien de propre en M5/M3/M1 |

- HTF en tendance → **setups de continuation**. HTF en consolidation → **setups de retournement** sur la structure interne, et seulement après la prise d'une grosse liquidité.
- L'analyse part **toujours du HTF vers le LTF** (« c'est le HTF qui dit ce qu'on fait en LTF »). Le prix est **fractal** : le même cycle se répète d'une UT à l'autre (structure en « poupées russes »).
- Précision : dans le PDF, « BPL » (p.20) est une **coquille pour Breaker Block**. La transcription le confirme : **le breaker block ne s'utilise que lorsque le prix vient de prendre une grosse liquidité externe**.
- **Pas d'UT en secondes** (15 s / 30 s) : hors périmètre.
- Note technique : l'API OANDA v20 propose S5 à S30, M1, M2, M4, M5, M10, M15, M30, H1 à H12, D, W et M, mais **pas M3** (vérifié dans la spécification officielle `oanda/v20-openapi`). Les plateformes de graphiques affichent du M3 en agrégeant du M1, et le moteur fera exactement pareil : chaque bougie M3 = open de la 1re minute, high et low maximum et minimum des 3 minutes, close de la 3e, alignée sur :00, :03, :06… Le résultat est identique, sans perte d'information.

### 1.2 Structure de marché « élite »
- **Structure externe** : entre le dernier high majeur et le dernier low majeur d'une UT haute. **Structure interne** : tout ce qui se passe entre les deux. On sort de la structure interne quand l'un des deux extrêmes est cassé.
- **Strong High / Strong Low** : un swing qui s'est formé **après avoir pris de la liquidité** (il a balayé un high ou un low précédent avant de se retourner). Ce sont **les seuls vrais points de structure et les seuls POI valides** (les « OB » de la formation).
- **No Strong High / Low** : un swing formé **sans prise de liquidité** → piège.
- **True BOS** : cassure provoquée par un mouvement parti d'un point Strong (le mouvement a « pris sa cause »). **Fake BOS** : cassure sans prise de liquidité préalable, ou cassure alors qu'une grosse liquidité voisine n'a pas encore été prise.
- **Follow the money** : les nouveaux Strong points réagissent dans les Strong points précédents.
- **Changement de tendance** : cassure du dernier Strong point opposé.
- Méthode : ① structure externe → ② structure interne → ③ vrais highs/lows → ④ liquidité.

### 1.3 Types de liquidité
- **Equal highs / equal lows**, y compris les **relative equals** (touches proches mais pas exactement au même prix, formant un « bloc »).
- **Trendline** (touches successives dans une direction).
- **Support / résistance à rebonds multiples**.
- **Breakouts** (ordres placés après la cassure d'une structure à gauche).
- **SMC Trap** (voir 1.10).
- Niveaux clés : **PDH/PDL**, plus haut et plus bas du mois, **ASH/ASL** (Asia High/Low), highs et lows de session, **IDC** (inducement : petite liquidité devant une zone).
- **Priorité** : UT la plus haute d'abord, puis la plus proche dans le cycle en cours.

### 1.4 AMD : Accumulation, Manipulation, Distribution (**le concept central**)
- « **Tout mouvement est précédé d'un AMD.** » Toute la stratégie repose sur ce concept.
- **A** : consolidation qui fabrique de la liquidité et de faux setups (fake BOS, faux BB, EQH/EQL, trendlines).
- **M** : **mouvement fort et agressif** qui liquide l'accumulation. Il se fait **toujours par un Buy to Sell ou un Sell to Buy**. Si le mouvement n'est pas agressif, **ce n'est pas une manipulation**.
- **D** : le vrai mouvement. **C'est lui qu'on cherche à prendre.**
- Le moteur étiquette la phase AMD en cours, par UT et par session. Un AMD peut exister à l'achat en LTF et à la vente en HTF en même temps (fractalité).

### 1.5 IPA / EPA (**70 % du biais**)
- **EPA (prix efficient)** : après chaque cassure (nouveau high ou nouveau low), **le prix revient toucher l'ancien point de structure cassé** avant de continuer. → Continuation probable.
- **IPA (prix inefficient)** : le prix casse puis continue **sans revenir** sur l'ancien point de structure. Il reste un « trou ». → Le prix a de fortes chances de **revenir combler l'IPA** (retournement possible), et **le retour sur l'IPA est une zone de rebond et de setup**.
- **Règle** : un IPA n'est intéressant que s'il est **précédé d'un FVG** (imbalance).
- **Uniquement en HTF : W, D1, H4, H1, M15.** Jamais en M5/M3/M1.
- Plus l'UT est haute, plus l'IPA compte. Un IPA peut exister en H1 alors qu'il est déjà comblé en M15 : il reste valide.
- Le prix va souvent **d'IPA en IPA** (« ping-pong »).
- Une zone située **juste avant un IPA non comblé** est un **piège** (le prix ira combler l'IPA avant de réagir).
- **Biais = 70 % IPA/EPA + 30 % liquidité**, lus en HTF. La question à se poser : le prix a-t-il pris sa cause (liquidité ou IPA atteint) ? Quelles liquidités et quels IPA restent à prendre, en haut et en bas ?

### 1.6 Buy to Sell / Sell to Buy
- **La seule preuve d'une vraie prise de liquidité** : une bougie (ou une série) d'**accélération nette**, clairement différente des bougies précédentes, qui balaie la liquidité, suivie du retournement.
- Règle du formateur : « **Si tu te demandes si c'en est un, c'est que ce n'en est pas un.** » C'est flagrant ou ça n'existe pas. → Le code utilisera un seuil strict (taille du corps comparée à l'ATR ou aux N bougies précédentes, à calibrer).
- **Pas de B/S ou de S/B = pas de manipulation = pas de trade.**
- **Règle du trader : la prise de liquidité se valide sur la clôture du corps d'une bougie au-delà du niveau** (M1, M3 ou M5), jamais sur une simple mèche.
- **« Flagrant » selon le trader** : après une petite accumulation, une accélération vers la liquidité anormalement grande par rapport au mouvement qui précède dans la zone.

### 1.7 CISD (définition propre à la formation)
- **La bougie qui prend la liquidité**, c'est-à-dire celle du B/S ou du S/B.
- Entrée **à la clôture, sur le corps** (pas sur la mèche) de cette bougie.
- Recherche en **M5, puis M3, puis M1** : on retient l'UT la plus haute où elle est nette. Si rien de net, on peut monter en M15. Le B/S peut s'étaler sur 2 ou 3 bougies ; une seule bougie est préférable.
- Stop « de base » : sur le corps de la bougie CISD (souvent élargi).

### 1.8 FVG, IFVG, BPR
- **FVG** : déséquilibre sur 3 bougies (les mèches des bougies 1 et 3 ne se touchent pas). « Les vrais supports et résistances. » Plus l'UT est haute, plus il compte.
- **IFVG** : un FVG **transpercé et non respecté**. Indice de retournement et **déclencheur d'entrée**.
- **BPR (« point de gravité »)** : un **IFVG et un nouveau FVG de sens opposé sur la même zone de prix**. Confluence très forte.
- Recherche en M5, puis M3, puis M1 (on retient l'UT la plus haute).

### 1.9 Breaker Block
- La seule « figure » utilisée par le formateur, parce que c'est **une figure de liquidité** : le prix prend une liquidité d'un côté puis de l'autre avant de partir. Le mitigation block n'est pas utilisé.
- Uniquement **après la prise d'une grosse liquidité externe**. Mieux encore **après la prise d'un IDC**.
- **Faux BB** : formé juste avant une grosse liquidité non prise (ex. sous un PDH ou dans une session piège) → piège.

### 1.10 SMC Trap : comment le reconnaître
Une zone (OB, BB, FVG, swing) est un **piège** si au moins un de ces critères s'applique :
1. elle s'est formée **sans prise de liquidité préalable** (No Strong) ;
2. **une grosse liquidité non prise se trouve juste derrière** (le prix ira la prendre avant) ;
3. **un IPA HTF non comblé se trouve juste derrière** ;
4. c'est la zone d'un **cycle déjà terminé** (voir 1.12 : pas de retest).

Chaque zone reçoit l'étiquette **VALIDE / TRAP** avec la raison.

### 1.11 SMT
Visible sur deux schémas mais **jamais expliquée dans la formation**. Hors de la stratégie de base. Option possible plus tard : divergence avec un DXY synthétique (voir 3.4).

### 1.12 Le modèle d'entrée (chapitre 4 de la formation)
1. **Biais HTF** (W → M15) : IPA/EPA + liquidité. Le prix a-t-il pris sa cause ? Où sont les prochaines causes ?
2. **Zone** : le prix revient dans une zone **VALIDE** et/ou prend une liquidité HTF ou revient sur un IPA HTF.
3. **Dans la zone, un nouveau cycle doit se former** en LTF : accumulation, puis **manipulation par B/S ou S/B**, de préférence **dans une fenêtre horaire** (section 2).
4. **Déclencheur**, recherché en M5 puis M3 puis M1. Au choix :
   - **IFVG / BPR** ;
   - **CISD** (clôture du corps de la bougie de manipulation) ;
   - **petit True BOS** (première cassure).
5. **⛔ Jamais sur le retest.** Entrée **pendant le cycle, avant que le prix prenne la prochaine liquidité du cycle**. Une fois cette liquidité prise, le cycle est terminé : l'ancienne zone devient elle-même une liquidité ou un piège, et il faut attendre un **nouveau cycle**.
6. **SL** : au-delà de la bougie CISD ou de l'extrême de la manipulation.
7. **Breakeven (règle du trader)** : avant la prise de liquidité, le prix forme de petits points de structure internes. Après l'entrée, **dès que le prix casse le dernier de ces points (BOS interne), le SL passe à l'entrée**. Le TP n'est jamais déplacé.
8. **TP** : **3R** si la prochaine liquidité du cycle est à 3R ou plus ; **2R** si elle est proche (moins de ~1,5R à 2R). Des cibles plus lointaines (IPA HTF, liquidité finale) sont possibles, mais le formateur coupe à 2 ou 3R.
9. **Discipline** : **1 trade par jour et arrêt après un TP** ; 2 trades maximum. Marché illisible → pas de trade (« ne pas trader, c'est trader »). Les meilleurs traders prop font 11 à 15 trades par mois.

### 1.13 Gestion du risque (chapitre prop firm)
- Modèle de la formation : compte de **50K**, perte max **2K** (drawdown EOD suiveur), **300 € de risque par trade**, soit **7 SL consécutifs** avant de perdre le compte.
- En financé : faire monter le compte à **54K avant le premier payout**, retirer 50 % du bénéfice et garder **2K de coussin** en permanence.
- Win rate annoncé par le formateur : ~70 %, avec des RR de 1:2 à 1:3.

---

## 2. Sessions et timings (heure de Paris)

### 2.1 Ce que dit la formation
| Session | Horaire | Comportement attendu | Action |
|---|---|---|---|
| Sydney | — | Exclue | — |
| **Asie** | 00h00 – 07h00 | Accumulation, fabrique la liquidité (ASH/ASL, trendlines, EQL) | Cartographier |
| **Francfort** | 08h00 – 09h00 | **70 à 80 % de pièges**, crée la « cause » de Londres | **Ne pas trader** |
| **London Open** | 09h00 – 12h00, **fenêtre 09h00 – 10h00** | Manipulation de l'accumulation Asie + Francfort, puis distribution | **Fenêtre 1** |
| **NY Trap** | **12h00 – 14h00** | Accumulation, faux setups | **Ne pas trader** |
| **NY** | **fenêtres 14h30 – 15h00 et 15h30 – 16h00** (~80 % des manipulations à 15h30) | Session la plus rapide et la plus agressive | **Fenêtre 2** |
| **London Close** | 17h00 – 20h00, **fenêtre 17h00 – 18h00** | ~70 % : retracement de la journée si Londres et NY vont dans le même sens ; sinon continuation après prise de liquidité | **Fenêtre 3** |

- Lecture AMD de la journée : **Asie + Francfort = A**, **London Open 9h-10h = M**, **reste de Londres = D**. Même schéma pour NY : **NY Trap = A**, **14h30 ou 15h30 = M**, **suite = D**.
- Chaque session **se nourrit de la liquidité des sessions précédentes** pour aller chercher des liquidités plus lointaines (PDH/PDL…).
- Le formateur **trade principalement la session de New York** (de 14h à 18h devant l'écran).
- Les incohérences du PDF sont tranchées par la transcription : les heures sont en **heure de Paris** (UTC+2 en été ; le formateur corrige lui-même un décalage UTC+1 / UTC+2).

### 2.2 L'amélioration « pro » : ancrer chaque session sur sa propre ville
La transcription le confirme : **15h30 à Paris = 9h30 à New York (ouverture de Wall Street)** et **14h30 à Paris = 8h30 à New York (statistiques US)**. **9h00 à Paris = 8h00 à Londres.**

Les passages à l'heure d'été ne se font **pas aux mêmes dates** aux États-Unis et en Europe (environ 3 semaines en mars, 1 semaine en octobre-novembre). → L'outil ancre chaque fenêtre sur le fuseau de sa place (Europe/London, America/New_York) et l'affiche dans **ton** fuseau. Les timings restent justes toute l'année.

### 2.3 Daily Cycle
- L'outil maintient en continu **l'état du cycle quotidien** : quelle session a pris quelle liquidité, dans quel sens, via B/S ou non, et ce qui reste à prendre.
- Variables de Londres : prise de l'ASH puis descente, ou prise de l'ASL puis montée.
- London Close : si Londres et NY vont dans le même sens → biais de retracement (~70 %).

---
## 3. Les leviers propres à USD/JPY (ce que la formation ne couvre pas)

La formation vient de l'or et des indices. USD/JPY a ses propres moteurs, qui deviennent ton avantage.

### 3.1 Moteurs fondamentaux
| Levier | Pourquoi c'est crucial | Usage dans l'outil |
|---|---|---|
| **Écart de taux US–Japon** (US 2 ans et 10 ans, JGB 10 ans) | Moteur n°1 de la paire | Biais fondamental quotidien ; alerte si les taux US décrochent pendant que tu es long |
| **Fed** (FOMC, dot plot, minutes, discours) | Côté USD | Calendrier, résumé des discours, ton hawkish ou dovish |
| **BoJ** (réunions, conférence du gouverneur, opérations obligataires, fuites de presse) | Côté JPY, souvent très violent | Mode « événement BoJ » ; les fuites de presse japonaises tombent souvent pendant la session asiatique |
| **Risque d'intervention du MoF** | Peut effacer 300 à 500 pips en quelques minutes | **Moniteur dédié** (voir 3.2) |
| **Sentiment de risque** (Nikkei, S&P, VIX) | Débouclage du carry trade → chute brutale | Indicateur risk-on / risk-off en direct |
| **Statistiques US à 14h30 Paris** | Elles tombent **pile dans ta fenêtre NY** | Filtre news : l'outil sait si la fenêtre de 14h30 est une fenêtre de news ou non |

### 3.2 Moniteur d'intervention MoF
- Niveaux psychologiques historiques d'intervention (zones où le MoF est déjà intervenu).
- **Vitesse du mouvement** (pips par jour ou par semaine) : le MoF réagit aux mouvements « excessifs et désordonnés ».
- **Escalade verbale** : le vocabulaire des officiels japonais suit une gradation connue (« on surveille » → « mouvements excessifs » → « toutes les options sur la table » → « action décisive »). Un agent suit ces déclarations et affiche un **niveau d'alerte de 0 à 5**.
- Rate checks rapportés par la presse.
- **Usage** : à l'approche d'une zone d'intervention avec un niveau d'alerte élevé, les longs sont signalés « à risque asymétrique ».

### 3.3 Flux et micro-structure propres au yen
- **Fixing de Tokyo** (09h55 heure de Tokyo, soit 02h55 à Paris l'été) et **jours gotobi** (5, 10, 15, 20, 25 et fin de mois) : demande de dollars des importateurs japonais. Une source de liquidité et de mouvement **pendant la session asiatique** que la formation traite comme pure accumulation.
- **Fins de mois, de trimestre et d'année fiscale japonaise (31 mars)** : flux de rapatriement.
- **Expirations d'options (NY cut, 10h00 New York = 16h00 Paris)** : les gros strikes proches du prix agissent comme des aimants. C'est pile la fin de ta fenêtre NY.
- **Pour USD/JPY, la session asiatique est la session domestique du yen.** La formation la traite comme une simple accumulation, mais elle peut porter de vrais mouvements (Tokyo, BoJ, fuites de presse). → **Les statistiques vérifieront si le schéma « Asie = accumulation » tient sur USD/JPY**, et à quelle fréquence.

### 3.3 bis Étude des sessions (premier livrable de recherche)
Tu envisages de passer à **Asie + Londres**. Avant de trancher, l'outil produira une **étude chiffrée sur l'historique USD/JPY** (plusieurs années de M1 OANDA) :
- amplitude, volatilité et « propreté » (respect de la structure, faux signaux) **par session et par fenêtre horaire** ;
- **effet gotobi** et **fixing de Tokyo** (09h55 JST) : direction et amplitude moyennes avant et après le fix, jours gotobi vs jours normaux, fins de mois ;
- taux de prise de l'ASH et de l'ASL par Londres, et comportement de l'Asie sur USD/JPY (accumulation ou vraie tendance ?) ;
- fréquence de la manipulation dans chaque fenêtre (9h–10h, 14h30, 15h30, 17h–18h) ;
- respect de l'IPA/EPA par UT et par session.

La littérature académique documente une demande de dollars des importateurs japonais avant le fixing de Tokyo, plus forte les jours gotobi. **Mais on ne s'appuiera que sur nos propres mesures sur USD/JPY récent**, pas sur des chiffres généraux.

### 3.4 Contexte technique complémentaire
- **ADR** (average daily range) : quelle part du range moyen a déjà été consommée ? Si l'ADR est déjà atteint à 15h, les objectifs lointains sont peu probables.
- **SMT avec le DXY synthétique** (voir 1.11).
- **Positionnement** : CFTC COT hebdomadaire (contexte de fond seulement) et sentiment retail si disponible.

### 3.5 Adapter la stratégie à USD/JPY : les points à surveiller
1. **La logique des sessions vient d'actifs dominés par le dollar.** Le formateur explique que l'Asie « ne fait rien » parce qu'il trade EUR/USD, GBP/USD et le Nasdaq, et que les institutions américaines sont fermées la nuit. **Sur USD/JPY, l'Asie est la session du yen** (Tokyo, BoJ, fixing, gotobi). Hypothèse de travail : la même logique d'AMD s'applique, mais **le moteur mesurera séparément le comportement de l'Asie sur USD/JPY**, et un mode « Tokyo » pourra être activé si les statistiques le justifient.
2. **Futures ou spot ?** Le formateur insiste pour lire la liquidité sur le **marché futures** (« le vrai marché ») et trade chez Topstep. Pour le yen, le contrat futures CME est le **6J (JPY/USD), l'inverse de USD/JPY** : un sweep des plus hauts sur USD/JPY est un sweep des plus bas sur 6J, et les mèches peuvent légèrement différer. → L'outil doit savoir **sur quel flux calculer** : spot OANDA, 6J, ou les deux avec contrôle de cohérence. Voir la question 1 de la section 11.
3. **Les stats US de 14h30 (heure de Paris)** tombent dans la fenêtre NY du formateur. Sur USD/JPY, ces annonces font souvent la manipulation elle-même (NFP, CPI). L'outil marque chaque fenêtre de 14h30 comme « fenêtre news » ou « fenêtre technique ».
4. **Le risque d'intervention du MoF** n'existe sur aucun des marchés de la formation. C'est un filtre supplémentaire propre à USD/JPY (3.2).

---

## 4. Architecture fonctionnelle : les modules

```
┌─────────────────────── DONNÉES ───────────────────────┐
│ Prix OANDA (stream + bougies) · Taux · Calendrier ·    │
│ News/déclarations · Indices/risk · Options expiries    │
└──────────────┬────────────────────────────┬───────────┘
               ▼                            ▼
   ┌─── MOTEUR SMC (code) ───┐   ┌── MOTEUR CONTEXTE (code) ──┐
   │ structure, liquidité,   │   │ sessions, timings, cycle,  │
   │ zones, AMD, IPA/EPA,    │   │ calendrier, ADR, fix/      │
   │ B/S, CISD, trap/valide  │   │ gotobi, risk, intervention │
   └───────────┬─────────────┘   └─────────────┬──────────────┘
               └──────────────┬────────────────┘
                              ▼
                ┌──── AGENTS (IA) ────┐
                │ briefs, plans,       │
                │ alertes, suivi,      │
                │ journal, coach, chat │
                └──────────┬───────────┘
                           ▼
        Dashboard web / mobile · Alertes Telegram · Journal
```

### 4.1 Module Données
- **OANDA v20** : stream de prix USD/JPY + bougies M1 à D1 (le M3 est reconstruit). Paires du DXY synthétique. Indices CFD (JP225, US500) et obligations CFD si ta juridiction OANDA les propose.
- **Taux** : US 2 ans et 10 ans, JGB 10 ans (intraday si possible, sinon quotidien via FRED ou le ministère des Finances japonais).
- **Calendrier économique** : annonces US et Japon avec consensus, précédent et réel.
- **News et déclarations** : Fed, BoJ, MoF, gouvernement japonais, collectées par les agents.
- **Stockage** : tout l'historique en base (pour les statistiques et le backtest).

### 4.2 Moteur SMC (déterministe, testé)
Pour chaque UT (W, D1, H4, H1, M15, M5, M3, M1), mis à jour à chaque clôture de bougie :
- swings, avec l'étiquette Strong ou No Strong ;
- structure externe et interne, tendance, True BOS / Fake BOS, changement de tendance ;
- pools de liquidité (EQH/EQL et relative equals, trendlines, PDH/PDL, PWH/PWL, plus haut et plus bas du mois, ASH/ASL, highs/lows de session, IDC) avec leur statut (intacte ou prise, par quelle session, via B/S ou non) ;
- zones FVG, IFVG, **BPR**, Strong points (OB) et BB, avec leur statut et l'étiquette **VALIDE / TRAP** et la raison (1.10) ;
- **IPA/EPA uniquement en HTF (W → M15)**, avec la vérification « précédé d'un FVG » ;
- **suivi des cycles cause-effet** : cycle en cours, liquidité prise (la cause), prochaine liquidité visée, cycle terminé ou non. C'est ce qui permet d'appliquer la règle « jamais de retest » ;
- phase AMD ;
- détection des événements B/S et S/B (seuil d'accélération strict) et **CISD** ;
- **biais HTF calculé** (70 % IPA/EPA + 30 % liquidité, 1.5), avec le détail des raisons.

**Calibration obligatoire** : pendant la phase 1, l'outil trace ses détections sur le graphique et **tu les valides ou les corriges**. On ajuste les paramètres jusqu'à ce que le moteur « voie » comme toi.

### 4.3 Moteur de contexte
- Horloge des sessions (ancrée sur chaque place, voir 2.2) avec statut : *pré-session, fenêtre active, piège, hors fenêtre*.
- État du cycle quotidien (voir 2.3).
- Fenêtres news : blocage de X minutes avant et après chaque annonce à fort impact.
- ADR consommé, jours gotobi et fixing, fins de mois, expirations d'options.
- Indicateur risk-on / risk-off, niveau d'alerte d'intervention.

### 4.4 Score de setup (la checklist de la formation)
Chaque setup candidat est vérifié selon le modèle d'entrée (1.12) :

**Conditions éliminatoires** (sans elles, pas d'alerte) :
- [ ] Biais HTF identifié (IPA/EPA + liquidité), setup dans son sens ou retournement autorisé
- [ ] **Manipulation par B/S ou S/B nette** (sinon il n'y a pas de manipulation)
- [ ] Entrée **dans le cycle en cours**, avant la prise de la prochaine liquidité (**pas de retest**)
- [ ] Au moins un déclencheur : **IFVG/BPR**, **CISD** ou **petit True BOS** (M5 → M3 → M1)

**Confluences** (elles font la note) :
- [ ] Zone VALIDE (Strong point) ou retour sur un IPA HTF précédé d'un FVG
- [ ] Liquidité HTF prise (PDH/PDL, ASH/ASL, EQH/EQL…)
- [ ] IDC balayé avant l'entrée
- [ ] Déclencheurs cumulés (CISD + IFVG + BPR…) et UT du déclencheur (M5 > M3 > M1)
- [ ] **Dans une fenêtre horaire** (09h–10h, 14h30–15h / 15h30–16h, 17h–18h) ; hors Francfort et NY Trap
- [ ] Accumulation claire (AMD complet)
- [ ] Prochaine liquidité du cycle à ≥ 2R
- [ ] Pas d'annonce majeure non intégrée, contexte fondamental non contraire (taux, intervention)

→ Note **A+ / A / B / non conforme**. Par défaut, seuls A+ et A déclenchent une alerte. La pondération sera ensuite **ajustée par les statistiques réelles**.

---

## 5. Les agents

| # | Agent | Déclenchement | Livrable |
|---|---|---|---|
| 1 | **Macro & Fondamental** | 06h30 chaque jour + événements | Biais fondamental du jour (taux, Fed, BoJ, risk) avec justification ; points de vigilance |
| 2 | **Calendrier & News** | Continu | Annonces du jour (consensus, précédent, impact typique sur USD/JPY), fenêtres bloquées, flash sur les titres importants, résumé post-annonce |
| 3 | **Veille Intervention** | Continu | Niveau d'alerte MoF de 0 à 5, déclarations, rate checks, zones sensibles |
| 4 | **Analyste Structure** | Avant chaque session + à la demande | Lecture HTF → LTF : structure, liquidité, POI valides et traps, IPA/EPA, AMD en cours |
| 5 | **Plan de session** | 07h30 (Londres), 13h45 (NY), 16h30 (London Close) | **2 ou 3 scénarios concrets** : conditions, zone, confirmation attendue, entrée, SL, TP, invalidation |
| 6 | **Sentinelle** | Continu (principalement du code) | Alerte quand un scénario s'active : prix dans le POI → liquidité prise → confirmation. Capture annotée et niveaux |
| 7 | **Compagnon de position** | Dès que tu déclares une position | Suivi jusqu'à la clôture (voir 5.1) |
| 8 | **Coach discipline** | Continu | Garde-fous psychologiques (voir 5.2) |
| 9 | **Journal & Stats** | Après chaque session + hebdo | Débrief, statistiques, ce qui marche et ce qui ne marche pas sur USD/JPY |
| 10 | **Chat analyste** | À la demande | Tu poses une question (« où est la liquidité H1 ? », « le biais a changé ? ») et il répond à partir des données en direct |

### 5.1 Compagnon de position (positions de quelques minutes à quelques heures)
Tu déclares ton trade (entrée, SL, TP, taille), ou il est importé si ton broker le permet. L'outil te suit ensuite :
- **Progression** : R en cours, distance au TP et au SL, prochaine liquidité sur le chemin.
- **Structure contre toi** : CHoCH ou BOS contraire sur M5/M15, IFVG dans le mauvais sens.
- **Liquidité intermédiaire atteinte** : rappel de la règle de la formation (passage à **breakeven** dès que la première liquidité est prise).
- **Cible** : TP à 2R ou 3R selon la distance de la prochaine liquidité du cycle (1.12) ; signal quand la cible du cycle est atteinte (« cycle terminé »).
- **Calendrier** : « NFP dans 20 min : ta position est à +1,2R ».
- **Changement de session** : entrée en NY Trap, approche de la London Close (risque de retracement de la journée), clôture de NY, ouverture de Tokyo.
- **Fondamental** : taux US qui décrochent contre ta position, escalade verbale du MoF, choc risk-off.
- **Position tenue la nuit** : swap, annonces japonaises pendant l'Asie, fixing de Tokyo, gotobi.

Tous les messages sont des **informations**, jamais des ordres.

### 5.2 Coach discipline (chapitre psycho de la formation)
- Alerte si tu veux entrer **hors fenêtre** ou **en session piège**.
- Après **N pertes** consécutives ou la **perte max journalière** : message de stop (« journée terminée »).
- Détection de **revenge trading** (nouvelle entrée juste après un SL) et de **surtrading**.
- Rappel du risque par trade.
- **Règle de la formation : 1 trade par jour, arrêt après un TP, 2 trades maximum.** Au-delà, l'outil affiche un avertissement.
- Rappel quand un setup est pris **sur un retest** (cycle terminé) : c'est la première erreur que la formation interdit.
- Si tu passes par une prop firm : suivi du drawdown EOD et de la distance à la perte max (le modèle de la formation : 50K, perte max 2K, 300 € par trade).
- Court débrief émotionnel optionnel dans le journal : « Quelle est votre première émotion quand vous gagnez ? Et quand vous perdez ? » (p.4).

---

## 6. Ta journée type avec l'outil (heure de Paris, été)

| Heure | L'outil fait |
|---|---|
| **Dimanche soir** | **Weekly outlook** : structure W/D, liquidité de la semaine, calendrier de la semaine, contexte BoJ/Fed/MoF |
| 00h00 – 07h00 | Suit l'Asie : ASH et ASL, EQH/EQL, trendlines, fixing de Tokyo, news japonaises. Pas d'alertes de setup (sauf si tu actives le mode Asie) |
| **06h30** | **Brief du matin** : fondamental, calendrier, niveau d'intervention, carte HTF |
| **07h30** | **Plan London** : scénarios pour 09h–10h |
| 08h00 – 09h00 | **Francfort, mode piège** : l'outil note les pièges (futures causes). Pas d'alerte d'entrée |
| **09h00 – 10h00** | **Fenêtre 1** : sentinelle active |
| 12h00 – 14h00 | **NY Trap** : observation, cartographie de l'accumulation |
| **13h45** | **Plan NY**, avec le point sur les stats US de 14h30 |
| **14h30 – 16h00** | **Fenêtre 2** : sentinelle active (fenêtres 14h30–15h00 et 15h30–16h00) |
| **16h30** | **Plan London Close** : la journée sera-t-elle retracée ? |
| **17h00 – 18h00** | **Fenêtre 3** : sentinelle active |
| **20h00** | **Débrief du jour** : ce qui s'est passé vs les scénarios, journal, stats |

---

## 7. Interface

- **Dashboard web** (PC + mobile, installable comme une application), réservé à toi et protégé par authentification.
  - **Graphique pro** (TradingView Lightweight Charts) avec **tracés automatiques** : structure, Strong/No Strong, liquidité, FVG/IFVG/BB (valide ou trap), sessions, fenêtres, niveaux clés. Chaque couche peut être affichée ou masquée.
  - Vue multi-UT (D1/H4/H1/M15 et M5/M3/M1).
  - Panneau **Biais du jour**, **Scénarios**, **Calendrier**, **Flux news USD/JPY**, **Jauge d'intervention**, **Horloge des sessions**.
  - **Position en cours** avec le suivi du compagnon.
  - **Journal** et **Statistiques**.
- **Alertes Telegram** (ou autre canal) : briefs, plans, alertes de setup avec capture annotée, alertes de suivi de position.
- **Tu pourras continuer à exécuter sur ta plateforme habituelle.** L'outil ne s'y substitue pas.

---

## 8. Journal, statistiques, backtest : l'edge mesuré

- **Chaque setup détecté** est enregistré (pris ou non) avec : UT, session, fenêtre, confluences, score, contexte macro, news, niveau d'intervention, jour de la semaine, gotobi, ADR consommé… et son **résultat théorique** (atteinte du TP ou du SL, MFE, MAE).
- **Tes trades réels** sont enregistrés avec tes notes et ton émotion.
- Exemples de statistiques visées :
  - taux de réussite et espérance **par fenêtre** (London 9h, NY 14h30, NY 15h30, London Close) ;
  - Francfort est-il vraiment un piège 70 à 80 % du temps **sur USD/JPY** ?
  - NY : manipulation à 15h30 dans ~80 % des cas selon le formateur. Et sur USD/JPY, où les stats de 14h30 pèsent plus lourd ?
  - London Close : retracement dans ~70 % des cas quand Londres et NY vont dans le même sens ?
  - Asie = accumulation : vrai sur USD/JPY ? Et les jours gotobi ?
  - performance des setups **avec vs sans** B/S, IDC balayé, zone valide ou trap ;
  - impact des jours de news, des régimes de taux et de la proximité d'une zone d'intervention ;
  - écart entre le plan et ton exécution réelle (discipline).
- **Priorité IPA/EPA** : ton observation est que **USD/JPY respecte très bien l'IPA/EPA**. Les premières statistiques porteront donc là-dessus : taux de comblement des IPA par UT (W → M15), délai avant comblement, taux de rebond au retour sur l'IPA, effet du FVG qui précède, fréquence du « ping-pong » d'IPA en IPA.
- **Backtest** : rejouer le moteur SMC sur des années d'historique M1 USD/JPY pour valider ou invalider chaque règle **avant** de risquer de l'argent.

---

## 8 bis. La boucle d'apprentissage : l'outil s'améliore avec tes retours

L'outil ne se contente pas de produire des analyses. **Il apprend de tes retours et de tes résultats.**

### 8b.1 Ce que tu renseignes (en quelques clics)
- **Sur chaque détection** tracée par le moteur (swing Strong, zone, IPA, B/S, CISD…) : ✅ juste / ❌ fausse / ✏️ corrigée (tu déplaces le niveau).
- **Sur chaque analyse et chaque plan** : utile / pas utile, biais juste ou faux a posteriori, commentaire libre.
- **Sur chaque setup alerté** : pris / pas pris, et pourquoi (pas convaincu, hors horaire, déjà en position, raté…).
- **Journal de trades** : chaque trade est **relié à l'analyse et au setup qui l'ont inspiré** (ou marqué « hors plan »). Entrée, SL, TP, taille, résultat en R et en €, capture, émotion avant et après, respect du plan (oui / non), leçon.
- **Prop firm** : solde, drawdown restant, règles du compte (voir 5.2).

### 8b.2 Ce que l'outil en fait
| Niveau | Mécanisme | Exemple |
|---|---|---|
| **Calibration du moteur** | Tes corrections ajustent les paramètres de détection | Tu corriges souvent des equal lows ratés → la tolérance en pips est élargie ; des B/S « pas assez flagrants » sont rejetés → le seuil d'accélération monte |
| **Pondération du score** | Les confluences sont repondérées selon les **résultats réels** (setups pris et non pris) | Sur USD/JPY, l'IFVG en M3 gagne plus que le CISD en M1 → il pèse plus dans la note |
| **Mémoire des agents** | Les leçons validées (journal, débriefs) sont réinjectées dans les briefs et les plans | « Les 3 derniers setups de London Close contre le biais H4 ont échoué » apparaît dans le plan du jour |
| **Revue hebdomadaire** | L'agent Journal & Stats propose des ajustements, **que tu valides ou refuses** | « Proposition : ne plus alerter en fenêtre 14h30 les jours de NFP » |

### 8b.3 Garde-fous
- **Rien ne change en silence** : chaque ajustement est proposé, expliqué, **validé par toi** et versionné, avec retour arrière possible.
- **Taille d'échantillon minimale** avant toute repondération (pas de conclusion sur 5 trades).
- **Validation hors échantillon** : un réglage n'est adopté que s'il tient sur des données qu'il n'a pas servi à fabriquer (anti-suroptimisation).
- La **règle de la formation reste la référence**. L'apprentissage ajuste des seuils et des poids, il ne réécrit pas ta stratégie.

---

## 9. Architecture technique (proposition)

| Brique | Choix proposé | Raison |
|---|---|---|
| Hébergement | Serveur cloud dédié (VPS) + Docker | 24 h/24, maîtrise, coût faible |
| Back-end | Python (FastAPI) + workers | Écosystème data et trading |
| Base de données | PostgreSQL + TimescaleDB | Séries temporelles (bougies, ticks), journal |
| Temps réel | Redis + WebSocket | Diffusion du prix et des alertes au dashboard |
| Planification | Scheduler fuseau-aware (sessions ancrées par ville) | Plans et briefs à l'heure exacte |
| Agents IA | API Claude (avec recherche web) | Recherche, synthèse, rédaction |
| Front-end | Next.js + Lightweight Charts, PWA | Pro, rapide, mobile |
| Alertes | Bot Telegram | Instantané, images, gratuit |
| Qualité | Tests unitaires du moteur SMC sur cas annotés, monitoring, logs, sauvegardes quotidiennes | Fiabilité pro |
| Sécurité | Authentification forte, clés API chiffrées, **clé OANDA en lecture seule** (données uniquement) | Aucun risque d'ordre involontaire |

Budget indicatif : **~20 à 60 €/mois** (serveur + IA), selon la fréquence des agents. À affiner.

---

## 10. Feuille de route

| Phase | Contenu | Résultat pour toi |
|---|---|---|
| **0. Règles** | ~~Transcription → règles exactes~~ (fait en v0.2). Reste : tes réponses à la section 11, puis la validation de ce document | Stratégie 100 % formalisée |
| **1. Fondations** | Données OANDA, base, moteur SMC, graphique avec tracés auto, **calibration avec toi** | Tu vois ta stratégie tracée automatiquement sur USD/JPY |
| **2. Sessions & Sentinelle** | Moteur de contexte, fenêtres, score de setup, alertes Telegram, plans de session | Tu reçois les setups au bon moment |
| **3. Intelligence macro** | Agents Macro, Calendrier/News, Veille Intervention, brief du matin, weekly outlook | Biais fondamental et risques du jour |
| **4. Compagnon & Coach** | Suivi de position, garde-fous discipline, chat analyste | Accompagnement de l'entrée à la sortie |
| **5. Edge mesuré** | Journal complet, statistiques, backtest | Tu sais chiffres à l'appui ce qui marche sur USD/JPY |

Chaque phase est livrée **utilisable**, pas seulement « en cours ».

---

## 11. Questions ouvertes

La transcription a réglé la plupart des questions de la v0.1 : BPL = breaker block, IPA/EPA, biais, modèle d'entrée, horaires, TP, BE, nombre de trades. Il reste :

**Décisions qui changent l'architecture** :
1. **Quelle prop firm, et sur quelle plateforme ?** Tu trades exclusivement en prop firm (un compte de 5K aujourd'hui, peut-être 10K plus tard). Un compte de 5K correspond plutôt à une prop **CFD/spot** (USD/JPY direct) qu'à une prop futures (6J). Il me faut le nom et les règles : perte max journalière, drawdown max, statique ou suiveur, objectif, jours minimum, restrictions sur les news.
2. Ton **pays** (accès OANDA : compte démo, juridiction) et ton **fuseau horaire**.
3. ~~Fenêtres tradées~~ : **Londres et New York aujourd'hui, Asie et Londres à terme.** → L'étude des sessions (3.3 bis) tranchera, chiffres à l'appui.

**Réglages de la stratégie** (on peut les calibrer ensemble en phase 1) :
4. **Cassure valide** : sur clôture de bougie ou sur mèche ? (La formation ne le précise pas.)
5. **Equal highs/lows** : tolérance en pips pour USD/JPY, par UT.
6. **Seuil du B/S** : que veut dire « flagrant » en chiffres (corps ≥ X fois la moyenne des N dernières bougies) ? À calibrer sur des exemples que tu valides.
7. **Tes propres règles** si elles s'écartent de la formation : risque par trade, perte max journalière, RR, 1 trade par jour ?
8. **MSU** (schéma p.81) et **SMT** : les utilises-tu ? Ils ne sont pas expliqués dans la formation.

**Pratique** :
9. **Canal d'alertes** : Telegram ?
10. As-tu un **historique de trades** (même sur l'or) à importer ?
11. Ton **indicateur de sessions et de swings** TradingView (celui que le formateur promet de partager) : si tu l'as, envoie-le, il servira de référence pour calibrer le moteur.
