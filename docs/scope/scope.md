# Scope : Hellofedge

Compagnon de trading USD/JPY en ligne 24 h/24 pour un trader SMC (méthode RedPillFX) qui trade en prop firm. Il analyse le graphique, repère les setups, alerte et journalise. Il ne passe jamais d'ordre.

**Build approach:** Tracer Bullet (on fait d'abord passer un fil réel et fin à travers toutes les couches, données, moteur, alerte, écran, puis on épaissit un segment à la fois).
**Workflow:** Beta (après `/develop` : `/check verify`, puis `/test`). C'est le niveau de rigueur par défaut. Les briques du moteur SMC portent `· GA` parce qu'une erreur de détection se paie en argent réel. `/architect` reste le premier arrêt pour toute fonction qui porte une vraie décision.

_Ce sont des recommandations pour garder la construction en ordre, pas des obligations. Si tu sais déjà comment construire une fonction, passe directement à `/develop`. C'est toi qui décides quand une fonction est `done`._

**Cadre du MVP (décidé avec le trader) :**
- Le MVP, c'est le moteur SMC plus les alertes, sur des prix en temps réel.
- Un seul utilisateur, avec une connexion protégée.
- Budget de fonctionnement : moins de 30 € par mois (serveur, IA et données).
- Alertes par Telegram.
- Dès le départ : une alerte si l'outil tombe, et un cockpit utilisable sur téléphone.
- **Succès** : le moteur retrouve au moins 8 des 10 trades de référence de `exemples/README.md` (mêmes niveaux, même entrée à quelques bougies près), puis les alertes en direct paraissent justes au trader pendant 2 semaines.
- **Source de prix** : OANDA est indisponible (création du compte impossible). La priorité est d'avoir des prix fidèles au graphique TradingView du trader, même si c'est payant, dans le budget.

## At a glance

| # | Feature | Phase | Status |
|---|---------|-------|--------|
| 1 | Stack et architecture | Foundation | in-progress |
| 2 | Source de prix (historique et temps réel) | Foundation | planned |
| 3 | Normes de code et outillage | Foundation | planned |
| 4 | Modèle de données | Foundation | planned |
| 5 | Design system et base de l'interface | Foundation | planned |
| 6 | Connexion (compte unique) | Slice 1 | planned |
| 7 | Fil minimal : bougie, prise de liquidité, alerte, cockpit | Slice 1 | planned |
| 8 | Structure : swings, Strong/No Strong, True/Fake BOS | Slice 2 | planned |
| 9 | FVG, IFVG, BPR et zones IPA/EPA | Slice 3 | planned |
| 10 | AMD, manipulation flagrante et CISD | Slice 4 | planned |
| 11 | Modèle d'entrée complet et alerte de setup | Slice 5 | planned |
| 12 | Rejeu et validation sur les 10 trades | Slice 6 | planned |
| 13 | Surveillance de panne | Slice 7 | planned |
| 14 | Cockpit sur téléphone | Slice 8 | planned |

## Foundations

### 1. Stack et architecture · in-progress
Choisir les outils (langage, base de données, hébergement 24 h/24, planification des tâches, envoi Telegram), puis poser un squelette qui démarre. Tout le reste s'appuie dessus.
**Done when:** la stack est écrite dans une spec validée par le trader, le coût mensuel estimé tient sous 30 €, et le squelette vide démarre et passe le build.
- [x] Décider la stack (spec): `/architect stack et architecture`
- [ ] Poser le squelette selon la décision: `/develop stack et architecture`
- [ ] Vérifier qu'il démarre: `/test`
Spec [0001](../specs/0001-stack-architecture/index.md)

### 2. Source de prix (historique et temps réel) · needs a decision
Remplacer OANDA par une source de bougies USD/JPY la plus proche possible du flux TradingView du trader, en historique (pour le rejeu) comme en direct (pour les alertes).
**Done when:** la source est choisie et son écart avec le graphique du trader est mesuré sur quelques journées des exemples. Les bougies M1 arrivent en direct et le M3 et le M5 sont reconstruits à partir du M1 (M3 calé sur :00, :03, :06).
- [ ] Décider la source (spec): `/architect source de prix`

### 3. Normes de code et outillage
Fixer les conventions à partir du vrai squelette, puis installer le lint, le formatage, les hooks et la CI.
**Done when:** le `AGENTS.md` racine décrit la vraie stack, et le lint, le formatage et les hooks passent sans erreur.
- [ ] Capturer conventions et outillage: `/audit`

### 4. Modèle de données · needs a decision
Les entités de base : bougies par unité de temps, niveaux détectés (liquidité, swings, FVG, IPA/EPA), setups, alertes. Tout est horodaté en UTC.
**Done when:** le modèle porte les tranches 1 à 8 et les futures fonctions différées (journal, retours, étude des sessions) sans migration cassante.
- [ ] Décider le modèle (spec): `/architect modèle de données`

### 5. Design system et base de l'interface · needs a decision
Reprendre le langage visuel du prototype (`docs/prototype/hellofedge-cockpit.html`) et le rendre plus fort : couleurs (rouge liquidité, bleu IPA, blanc extrêmes, jaune objectif), typographies et composants de base.
**Done when:** `design.md` couvre couleurs, typographies, espacements et composants, et les composants de base marchent au clavier comme au doigt.
- [ ] Décider le design (spec): `/architect design system`

## Slice 1 : le fil complet, en fin

### 6. Connexion (compte unique) · needs a decision
Une seule personne peut entrer dans le cockpit, avec une vraie connexion, parce que l'outil est en ligne en permanence.
**Done when:** sans connexion, aucune page ni donnée n'est accessible, et le trader se connecte depuis son ordinateur comme depuis son téléphone.
- [ ] Décider la connexion (spec): `/architect connexion`

### 7. Fil minimal : bougie, prise de liquidité, alerte, cockpit · needs a decision
Le squelette qui marche : les bougies en direct entrent, le moteur repère une seule chose (une prise de liquidité par clôture du corps au delà d'un swing M5), une alerte part sur Telegram et le niveau s'affiche sur le graphique du cockpit. Tout tourne sur le serveur 24 h/24.
**Done when:** une prise de liquidité réelle déclenche en moins d'une minute une alerte Telegram (heure du Bénin) et apparaît en rouge sur le graphique du cockpit. Une mèche seule ne déclenche rien.
- [ ] Décider le fil (spec): `/architect fil minimal`

## Slice 2 : structure

### 8. Structure : swings, Strong/No Strong, True/Fake BOS · GA
Épaissir le moteur : repérer les swings et dire s'ils sont Strong (formés après une prise de liquidité) ou No Strong, et distinguer un vrai BOS d'un faux.
**Done when:** sur les journées des exemples, les swings Strong et No Strong et les BOS correspondent à la lecture du trader, et le cockpit les affiche.
- [ ] Construire: `/develop structure`

## Slice 3 : zones

### 9. FVG, IFVG, BPR et zones IPA/EPA · GA · needs a decision
Repérer les FVG, IFVG et BPR, puis les zones IPA/EPA sur W, D1, H4, H1 et M15 (IPA précédé d'un FVG, touché dès qu'une mèche l'atteint), et en tirer le biais (70 % IPA/EPA, 30 % liquidité).
**Done when:** la matrice IPA/EPA du cockpit montre les zones actives et touchées pour chaque unité de temps, et le biais affiché correspond à celui du trader sur les exemples.
- [ ] Décider les règles de zones (spec): `/architect zones IPA EPA`

## Slice 4 : manipulation

### 10. AMD, manipulation flagrante et CISD · GA · needs a decision
Reconnaître l'accumulation, la manipulation et la distribution. Mesurer si l'accélération vers la liquidité est « flagrante » (anormalement grande par rapport au mouvement qui précède), et repérer le CISD.
**Done when:** le seuil « flagrant » est calibré sur les exemples et chaque cycle détecté est affiché avec sa cause (liquidité) et son effet.
- [ ] Décider le calibrage (spec): `/architect manipulation flagrante`

## Slice 5 : le setup

### 11. Modèle d'entrée complet et alerte de setup · GA · needs a decision
Assembler le modèle d'entrée (section 1.12 du cahier des charges) : cycle, déclencheur (IFVG/BPR, CISD, petit True BOS) cherché en M5 puis M3 puis M1, jamais sur retest, SL, TP à 2R ou 3R, et règle du breakeven. L'alerte devient une vraie fiche de setup.
**Done when:** une alerte Telegram donne le sens, l'entrée, le SL, le TP et le point de BE avec une capture du graphique, et au maximum une idée de trade par jour est poussée comme principale.
- [ ] Décider le modèle (spec): `/architect modèle d'entrée`

## Slice 6 : la preuve

### 12. Rejeu et validation sur les 10 trades · GA
Rejouer l'historique des journées des exemples comme si c'était en direct, et comparer ce que le moteur aurait signalé avec ce que le trader a réellement tracé et pris.
**Done when:** un rapport montre, trade par trade, niveaux, entrée et résultat, et le moteur en retrouve au moins 8 sur 10.
- [ ] Construire: `/develop rejeu et validation`

## Slice 7 : fiabilité

### 13. Surveillance de panne
Prévenir le trader quand le flux de prix ou le moteur s'arrête, pour qu'il ne prenne jamais un silence pour une absence de setup.
**Done when:** une coupure du flux ou du moteur de plus de 2 minutes envoie un message Telegram, et le retour à la normale aussi.
- [ ] Construire: `/develop surveillance de panne`

## Slice 8 : mobilité

### 14. Cockpit sur téléphone
Le cockpit s'adapte à l'écran du téléphone et s'installe comme une appli.
**Done when:** sur téléphone, le graphique, la matrice IPA/EPA et la dernière alerte se lisent sans zoom, et l'appli s'installe sur l'écran d'accueil.
- [ ] Construire: `/develop cockpit téléphone`

## Deferred
Hors du MVP, gardé ici pour que le plan reste honnête. Ces fonctions viennent du cahier des charges et seront planifiées au prochain `/scope`.
- **Agenda et leviers USD/JPY** : annonces, jours gotobi, fixing de Tokyo, risque d'intervention du MoF, différentiel de taux · needs a decision
- **Plan du jour par agents IA** : recherche macro du matin et fiche de trade du jour · needs a decision
- **Compagnon de position** : suivi d'une position ouverte, BE et sortie, même la nuit · needs a decision
- **Journal lié aux analyses** : chaque trade relié à l'analyse du moment · needs a decision
- **Boucle d'apprentissage** : l'outil s'améliore avec les retours du trader · needs a decision
- **Étude des sessions et backtest** : Londres et New York contre Asie et Londres · needs a decision
- **Coach de discipline** : repère les trades hors plan · needs a decision
- **Suivi des coûts IA** : dépense mensuelle et plafond · needs a decision
- **Sauvegardes quotidiennes** : journal, retours et historique · needs a decision

## Legend

**La case de décision.** Chaque fonction en porte une seule, celle dont le libellé finit par `(spec)`. Les autres cases sont des cases d'exécution.

- **Étape suivante** = la première case non cochée (toujours une commande ou une étape suivie).
- **needs a decision** = lancer `/architect` d'abord, sinon directement `/develop` (ou `/audit` pour les normes et l'outillage). Le tag disparaît quand la spec est écrite.
- Les tâches de construction détaillées vivent dans le `## Build plan` de la spec, pas ici. Le scope ne garde que 2 à 5 grandes étapes par fonction.
- **Status** : `planned` → `in-progress` → `done`, plus `existing` (déjà là avant le workflow) et `dropped` (retiré, gardé pour l'historique).
- **Tag de rigueur** (par exemple `· GA`) : plus de rigueur que le niveau par défaut pour cette fonction. GA = `/check verify`, `/test`, revue par un modèle neuf (`/check review`), puis `/document`.
- **Workflow** (ligne d'en tête) : le niveau par défaut, Beta = `/check verify` puis `/test` après `/develop`.
- **Ligne de pointeurs** (`spec <n> · code dans <chemin>`) : le lien de spec ajouté par `/architect`, le chemin du code par `/develop`.
