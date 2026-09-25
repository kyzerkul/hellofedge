# Plan de développement Hellofedge

> Méthode : celle de la vidéo « Claude Code crash course » fournie par le trader, appliquée à ce projet.
> Statut : **proposition, en attente de validation**. Aucun code applicatif n'est écrit avant validation.

---

## 1. Les principes de la méthode, appliqués à Hellofedge

| Principe de la méthode | Application concrète ici |
|---|---|
| **Petites fonctionnalités**, une à la fois : construire, relire, valider, passer à la suivante | Chaque brique du moteur SMC (swings, liquidités, FVG, IPA…) est une fonctionnalité séparée, testée et validée avant la suivante |
| **Fichier de contexte court** (`CLAUDE.md` / `AGENTS.md`), moins de ~60 lignes, uniquement ce que l'agent doit savoir à chaque session | Stack, commandes, conventions d'heure (UTC en interne), règles non négociables (aucun ordre passé, jamais de secret dans le code). Le détail de la stratégie reste dans `docs/CAHIER_DES_CHARGES.md` |
| **Règles par dossier** (`.claude/rules/`) chargées seulement quand on touche les fichiers concernés | `rules/moteur-smc.md` (règles de détection) ne se charge que quand on travaille sur le moteur ; `rules/interface.md` seulement sur l'interface |
| **Permissions** : autoriser le routinier, demander pour le sensible, interdire le dangereux | Interdit : lire `.env`, `.env.*`, les clés. Demande : `git push`, déploiement, suppression de données. Autorisé : tests, lint, lecture du code |
| **Plan d'abord pour les décisions coûteuses**, action directe pour le reste | Plan obligatoire : modèle de données, architecture du moteur, flux temps réel, sécurité, déploiement. Pas de plan pour un ajustement d'interface ou un libellé |
| **Relire le plan avant de l'approuver** | Chaque plan t'est présenté en français, en clair : ce qui sera créé, les fichiers touchés, comment on vérifiera. Tu valides, corriges ou refuses |
| **Skills** : transformer un processus répété en procédure réutilisable, **seulement quand la répétition apparaît** | Pressentis : `valider-sur-exemples` (rejouer le moteur sur tes 19 trades et comparer), `construire-ui` (reprendre le design du prototype). Créés au moment où on en a besoin, pas avant |
| **Sous-agents** pour les enquêtes indépendantes, sans encombrer le contexte principal | Exemple : enquêter en parallèle sur l'API OANDA, les sources de calendrier économique et les sources de taux avant de concevoir la couche données |
| **Contexte propre** : repartir d'une session neuve quand on change de sujet | Chaque phase commence par une session neuve. Le fichier de contexte assure la continuité |
| **Relecture indépendante** de la sécurité : ne pas laisser le même modèle juger seul son propre code | Après chaque étape back-end importante : un scan externe (CodeRabbit, si tu l'installes sur le dépôt) en plus de la relecture interne. On trie chaque remarque : à corriger maintenant, à noter pour plus tard, ou non pertinente |
| **Tenir le contexte à jour** (le rôle du skill `sync`) | À la fin de chaque phase, on met à jour `CLAUDE.md` et le cahier des charges pour qu'ils décrivent le projet tel qu'il est réellement |

---

## 2. Les phases

### Phase 0 · Fondations de l'agent (pas de code applicatif)
- `CLAUDE.md` / `AGENTS.md` court.
- `.claude/settings.json` avec les permissions ci-dessus.
- `.claude/rules/moteur-smc.md`, résumé des règles de détection avec renvoi au cahier des charges.
- `.gitignore`, `.env.example` (noms des variables, sans valeurs).
- **Test des permissions** : créer un faux `.env`, demander à l'agent de le lire, vérifier que c'est refusé.

### Phase 1 · Le moteur SMC (le cœur, développé et testé hors ligne)
Ordre des fonctionnalités, chacune testée avant la suivante :
1. **Données** : lecture des bougies M1, reconstruction du M3, agrégation M5 → W. Stockage.
2. **Swings et structure** : Strong / No Strong, structure externe et interne, BOS vrai ou faux.
3. **Liquidités** : equal highs et lows, extrêmes de session, ASH/ASL, PDH/PDL. **Prise = clôture du corps.**
4. **FVG, IFVG, BPR**, puis **IPA/EPA en HTF** (touché dès qu'une mèche l'atteint, précédé d'un FVG).
5. **AMD et manipulation flagrante** (rapport entre l'accélération et le mouvement qui précède).
6. **Cycles et modèle d'entrée** : balayage puis reprise, SL, TP sur l'extrême opposé, BE sur le BOS interne.
7. **Validation sur tes 10 trades** : le moteur doit retrouver le balayage, la manipulation et l'entrée de chacun, et signaler les défauts des 4 pertes.

Plan obligatoire avant les étapes 1 et 6.

### Phase 2 · Données en temps réel et contexte
Flux OANDA, horloge des sessions (ancrée par ville, affichée à l'heure du Bénin), calendrier économique, jours gotobi et fixing de Tokyo.

### Phase 3 · Le cockpit
Interface web reprenant et dépassant le prototype : graphique annoté, boussole, radar de setup, fiche d'entrée, carte des liquidités. Relue par toi écran par écran.

### Phase 4 · Alertes, agents et compagnon de position
Alertes Telegram, brief du matin, plans de session, suivi de position (BE, annonces, nuit).

### Phase 5 · Journal et boucle d'apprentissage
Journal relié aux analyses, retours sur les détections, marqueur « hors plan / émotion », propositions d'ajustement à valider.

### Phase 6 · Étude des sessions et backtest
Plusieurs années de M1 : Asie, Londres, NY, gotobi, fixing, respect de l'IPA/EPA, tes fenêtres réelles.

### Phase 7 · Déploiement
Serveur, secrets dans l'environnement du serveur, sauvegardes, supervision. Scan de sécurité complet avant la mise en ligne.

---

## 3. La boucle de travail pour chaque fonctionnalité

1. **Je décris** la fonctionnalité et, si elle est coûteuse, **je te présente le plan**.
2. **Tu valides** (ou tu corriges).
3. **Je construis** une petite étape.
4. **Je vérifie** : tests automatiques et, pour le moteur, rejeu sur tes exemples.
5. **Je te résume** ce qui a changé et ce que tu dois regarder, en français simple.
6. **Commit et push** sur la branche de travail. Rien ne part sans ton accord sur les étapes sensibles.

---

## 4. Décisions à prendre avant de commencer

1. **Valider ce plan** et l'ordre des phases.
2. **Données pour la phase 1** : le moteur peut être développé **tout de suite, sans OANDA**, sur un historique M1 gratuit (Dukascopy), puis recalé sur OANDA pour la validation fine sur tes trades (tes graphiques sont en OANDA, les prix diffèrent de quelques dixièmes de pip). À valider.
3. **Skills de la méthode** (`scope`, `architect`, `develop`, `sync`… du dépôt open source de JS Mastery) : je propose de **les lire d'abord**, puis soit de les installer, soit d'en écrire des versions courtes en français adaptées au projet. On n'installe jamais un skill sans l'avoir lu.
4. **CodeRabbit** (relecture de sécurité indépendante) : facultatif. Il faut que tu installes toi-même son application GitHub sur le dépôt `hellofedge`.
