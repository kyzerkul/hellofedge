# 0002. Source de prix : choisir par la mesure, bougies M1 bid du fournisseur

**Date**: 2026-09-26
**Status**: In Progress

## Summary

OANDA étant impossible, on ne choisit pas la source de prix sur une promesse : on mesure. Un petit script compare FXCM, Finnhub (qui relaie le flux OANDA) et Dukascopy aux vrais prix OANDA lus sur tes captures TradingView. On garde la source la plus proche qui offre aussi un direct fiable (FXCM part favori). Ensuite, le moteur reçoit chaque bougie M1 **bid** (le prix de vente, celui de ton graphique) quelques secondes après sa clôture, garde 2 ans d'historique, signale les coupures et rattrape les trous tout seul.

## Requirements

**User stories**:
- En tant que trader, je veux que le moteur voie les mêmes bougies que mon graphique OANDA, pour qu'un balayage de 0,2 pip vu par l'outil existe aussi sur mon écran.
- En tant que trader, je veux savoir de combien la source choisie s'écarte d'OANDA, chiffres à l'appui, pour savoir quelle confiance accorder aux alertes.
- En tant que trader, je veux que l'outil me prévienne quand le flux s'arrête et comble le trou tout seul, pour ne jamais prendre un silence pour une absence de setup.

**Acceptance criteria**:
- **AC-1**: Le fichier `exemples/reference_oanda.csv` contient au moins un point de référence par capture des exemples (19 captures), dont au moins 5 points `ut=3` et 5 points `ut=5`. Chaque point est lu sur la capture et validé par le trader (voir *Points de référence*).
- **AC-2**: Un rapport `exemples/mesure_sources.md` donne pour chaque source candidate, sur les jours des exemples : le pourcentage de points à 0,3 pip ou moins (0,003), l'écart moyen **absolu**, l'écart maximum, le prix fourni (bid ou mid), et le résultat du test du direct (30 minutes, marché ouvert). Classement : d'abord le pourcentage, puis l'écart moyen absolu, puis l'écart maximum. La source retenue est la première du classement parmi celles dont l'historique et le direct fonctionnent. Si aucune n'atteint 90 % des points à 0,3 pip, on garde quand même la première, et le rapport ainsi que la spec l'indiquent avec l'écart mesuré.
- **AC-3**: 2 ans de bougies M1 bid de la source active sont en base, horodatées en UTC sur la minute pleine. Relancer le chargement ne crée aucun doublon (unicité `source` + `ts_open`).
- **AC-4**: Pendant les heures de marché, chaque bougie M1 clôturée est en base moins de 10 secondes après la fin de sa minute, pour 95 % des minutes. La mesure porte sur une journée complète, du mardi au jeudi, avec le résultat par session (Tokyo, Londres, New York).
- **AC-5**: Si aucune nouvelle bougie n'arrive pendant 2 minutes (heures de marché, hors fenêtre du rollover), une coupure `feed_outage` est ouverte avec sa cause. Elle est fermée au retour des bougies. Le week-end, les jours fériés configurés et la fenêtre du rollover n'ouvrent jamais de coupure.
- **AC-6**: Après une coupure ou un redémarrage, les bougies manquantes sont rechargées chez le fournisseur, stockées avec `backfilled = true`, et comptées dans `bars_backfilled`. Il n'y a ni doublon ni trou quand le fournisseur a bien la bougie.
- **AC-7**: Les bougies M3 et M5 reconstruites depuis le M1 stocké (calées sur :00, :03, :06… et :00, :05…) respectent le seuil de l'AC-2 sur les points de référence pris sur les captures M3 et M5.
- **AC-8**: Changer `PRICE_SOURCE` fait lire au moteur une autre source sans toucher au code du moteur. Les bougies des autres sources restent en base.
- **AC-9**: Aucun adaptateur ne contient d'appel capable de passer, modifier ou annuler un ordre. Un test pytest lancé en CI parcourt le code de `data/` et échoue s'il trouve un mot interdit dans un nom de fonction, une URL ou un chemin d'API (`order`, `trade`, `position`, `close_trade`, `OpenTrade`, `entry`).
- **AC-10**: Une bougie déjà stockée n'est jamais réécrite. Si le fournisseur renvoie plus tard une valeur différente pour la même minute, la différence est enregistrée dans `candle_revision`, et la bougie stockée reste celle que le moteur a vue.
- **AC-12**: Chaque adaptateur convertit les heures du fournisseur en UTC et date chaque bougie à l'**ouverture** de sa minute. Un test le vérifie sur une date d'hiver et une date d'été (changement d'heure de New York), et la mesure compare aussi chaque point aux bougies voisines (une minute avant et après) pour révéler un décalage d'une minute.
- **AC-11**: Le cockpit peut afficher l'état du flux : source active, heure de la dernière bougie, coupure en cours s'il y en a une.

## Decision

**Chosen option**: Option 1 : mesure comparative, puis un seul fournisseur pour l'historique et le direct, lu en bougies M1 clôturées.

On compare FXCM, Finnhub (flux OANDA) et Dukascopy aux points OANDA lus sur les captures. On retient la source la plus proche dont l'historique et le direct fonctionnent (FXCM est le favori par défaut, parce qu'il est gratuit et qu'un seul compte démo couvre l'historique et le direct). Le direct lit la bougie M1 **clôturée** du fournisseur, pas des ticks. Le rejeu et le direct voient ainsi exactement les mêmes bougies.

Décisions prises par l'architecte (tu peux les contester) :
- **Lecture du direct** : on interroge le fournisseur à la seconde 3 de chaque minute, puis toutes les 2 secondes jusqu'à ce que la bougie soit disponible, pendant 60 secondes au plus. C'est plus simple et plus robuste qu'un flux permanent, et ça suffit pour une règle « clôture du corps ». Le runner up : un flux temps réel (WebSocket), qui se justifiera seulement pour le prix vivant du cockpit.
- **Révisions** : la première valeur stockée fait foi (AC-10). Le runner up, réécrire la bougie, changerait après coup ce que le moteur a vu.
- **Fenêtre du rollover** : de 16h58 à 17h10, heure de New York. À cette heure, beaucoup de fournisseurs n'ont pas de prix pendant quelques minutes. Sans cette fenêtre, une fausse panne tomberait chaque soir.
- **Minutes sans prix** : on ne fabrique pas de bougie artificielle. TradingView n'en affiche pas non plus. Une bougie M3 ou M5 dont une minute manque est construite avec les minutes présentes, comme TradingView.
- **Jours fériés** : `MARKET_HOLIDAYS` ne contient que des dates fixes (25/12 et 01/01 suffisent pour USD/JPY). C'est une limite assumée : un jour de faible activité (Vendredi saint, Thanksgiving) peut au pire déclencher une fausse coupure.
- **Prix** : les décimales sont stockées en `NUMERIC(10,3)`, jamais en nombre à virgule flottante, pour que 0,2 pip reste exactement 0,002.

## Rationale

Le raisonnement, les options et les résultats de la vérification web sont dans [rationale.md](rationale.md).

## Feature design

**Data model sketch** (validé par le trader) :

`candle_m1` : les bougies M1, la seule vérité en base.
| Champ | Type | Règle |
|---|---|---|
| `source` | `text` | clé primaire (1/2). Valeurs : `fxcm`, `finnhub_oanda`, `dukascopy`, et plus tard `fundednext` |
| `ts_open` | `timestamptz` | clé primaire (2/2). Minute pleine en UTC (secondes = 0) |
| `open`, `high`, `low`, `close` | `numeric(10,3)` | obligatoires, prix **bid**. Contrainte : `low <= least(open, close)` et `high >= greatest(open, close)` |
| `ask_close` | `numeric(10,3)` | facultatif, sert à connaître le spread |
| `tick_volume` | `integer` | facultatif |
| `backfilled` | `boolean` | obligatoire, `false` par défaut. `true` si la bougie a été récupérée par un rattrapage |
| `received_at` | `timestamptz` | obligatoire, heure de réception |

`feed_outage` : les coupures de la source.
| Champ | Type | Règle |
|---|---|---|
| `id` | `bigint` identité | clé primaire |
| `source` | `text` | obligatoire |
| `started_at` | `timestamptz` | obligatoire |
| `ended_at` | `timestamptz` | vide tant que la coupure dure. Au plus une coupure ouverte par source (index unique partiel sur `source` où `ended_at is null`) |
| `cause` | `text` | obligatoire : `timeout`, `erreur_api`, `reseau`, `auth`, `limite_api`, `donnees_absentes` |
| `closed_reason` | `text` | vide tant que la coupure dure, puis `retour_flux` ou `fermeture_marche` |
| `bars_backfilled` | `integer` | obligatoire, `0` par défaut |

`candle_revision` : les valeurs différentes renvoyées plus tard par le fournisseur (AC-10).
| Champ | Type | Règle |
|---|---|---|
| `id` | `bigint` identité | clé primaire |
| `source`, `ts_open` | comme `candle_m1` | clé étrangère vers `candle_m1` |
| `champ` | `text` | `open`, `high`, `low`, `close` |
| `valeur_stockee`, `valeur_recue` | `numeric(10,3)` | obligatoires |
| `detected_at` | `timestamptz` | obligatoire |

Relations : une source a 1:N bougies et 1:N coupures. Une bougie a 0:N révisions. `source` n'a pas de table à elle : la liste des sources vit dans la configuration. Les UT M3, M5, M15, H1, H4, D1 et W ne sont **jamais stockées**, elles sont recalculées depuis `candle_m1`.

Hors base, dans le dépôt : `exemples/reference_oanda.csv` et `exemples/mesure_sources.md`.

**Points de référence** (`exemples/reference_oanda.csv`) :

Colonnes : `capture`, `ut` (1, 3 ou 5), `type`, `ts_open_utc`, `prix`, `champ` (`open`, `high`, `low`, `close`), `note`.

Deux types de points, parce qu'une capture montre la dernière bougie **en cours de formation** :
- `exact` : une valeur qui ne peut plus bouger. C'est l'**open** de la bougie en cours (lu dans l'en-tête, par exemple `O159.174`), ou un plus haut ou plus bas **étiqueté** sur l'échelle (par exemple `High 159.283`) quand la bougie qui le porte est terminée.
- `borne` : le H et le L de la bougie en cours sont seulement des bornes. Le vrai haut final est au moins égal au H lu, et le vrai bas final au plus égal au L lu. Ces points comptent comme justes si la source respecte la borne à 0,3 pip près.

Dater la bougie en cours : l'heure de la capture se lit en haut (`Aug 24, 2026 10:48 UTC`) et le compte à rebours à droite du prix (`00:31`). Fin de la bougie = heure de la capture + compte à rebours. `ts_open_utc` = fin de la bougie − durée de l'UT (1, 3 ou 5 minutes), arrondie à la minute. Contrôle : `ts_open_utc` doit tomber sur un multiple de l'UT (:00, :03, :06… pour le M3) et la bougie doit être la dernière visible sur l'axe du temps. Sinon, le point est écarté et noté dans la colonne `note`.

Calcul de l'écart : pour un point `exact`, écart = |prix de la source − prix de référence|. Pour un point `borne`, écart = 0 si la source respecte la borne, sinon le dépassement. Tous les points entrent dans le pourcentage, l'écart moyen absolu et l'écart maximum.

Validation et corrections : le trader valide le fichier avant la mesure (AC-1). Pour corriger un point plus tard, on modifie le CSV dans un commit qui explique pourquoi, puis on relance `feed compare`, qui réécrit le rapport.

**Interface du fournisseur** (`backend/src/hellofedge/data/`, suit l'interface `PriceFeed` de la spec 0001) :

| Fonction | Entrées | Sortie | Erreurs clés |
|---|---|---|---|
| `PriceFeed.history(start, end)` | deux `datetime` UTC, fin exclue | liste de `Candle` M1 bid, triée, minutes pleines | `FeedAuthError` (clé refusée), `FeedUnavailable` (réseau, 5xx), `FeedRateLimited` |
| `PriceFeed.closed_since(after)` | `datetime` UTC | bougies M1 **clôturées** après `after` (vide si la minute n'est pas encore disponible) | les mêmes |
| `PriceFeed.name` | aucune | identifiant stocké dans `candle_m1.source` | aucune |

Adaptateurs : `fxcm`, `finnhub_oanda`, `dukascopy` (historique seulement, pour la mesure). Aucun adaptateur n'expose de fonction d'ordre (AC-9).

Règles communes des adaptateurs :
- **Fuseau** : chaque adaptateur documente le fuseau de son fournisseur et convertit en UTC avec `zoneinfo`. Attention, les fichiers historiques FXCM sont souvent en heure de New York, pas en UTC. Un décalage fixe est interdit : il faut tenir compte du changement d'heure (AC-12).
- **Horodatage** : chaque adaptateur date la bougie à l'**ouverture** de sa minute, même si le fournisseur la date à la clôture (AC-12).
- **Bid ou mid** : chaque adaptateur déclare le prix qu'il fournit (`price_kind = "bid"` ou `"mid"`). Une source qui ne donne que le mid est notée « mid » dans le rapport, et elle n'est retenue que si elle reste première du classement. Dans ce cas, la spec le mentionne.
- **Limites des API** : sur `FeedRateLimited` ou `FeedUnavailable`, on attend de plus en plus longtemps (2, 4, 8, 16, 32, puis 60 secondes au plus) avant de réessayer. Les chargements d'historique et les rattrapages longs se font par tranches d'une semaine.

**Commandes et surface** :
| Élément | Forme | Entrées clés | Sortie | Accès | Erreurs clés |
|---|---|---|---|---|---|
| Mesure des sources | commande `hellofedge feed compare` | `--sources` (défaut : les 3), `--reference exemples/reference_oanda.csv` | écrit `exemples/mesure_sources.md` | local ou `docker compose run` | source injoignable : notée « indisponible » dans le rapport, la mesure continue |
| Test du direct | commande `hellofedge feed live-test` | `--source`, `--minutes` (défaut : 30) | nombre de minutes reçues, manquées et délai par minute, ajoutés au rapport | local, marché ouvert | source injoignable : test « échoué » |
| Chargement de l'historique | commande `hellofedge feed backfill` | `--from`, `--to` (défaut : 2 ans jusqu'à maintenant), source = `PRICE_SOURCE` | nombre de bougies insérées et ignorées | `docker compose run` | reprise possible, idempotente |
| Lecture du direct | boucle dans le `worker` | aucune | lignes `candle_m1`, coupures `feed_outage`, `NOTIFY candle_m1` avec le message `{"source": "fxcm", "ts_open": "2026-08-24T10:47:00Z"}` | processus interne | voir *Pannes* |
| État du flux | `GET /api/feed/status` | aucune | `{"source", "last_ts_open", "outage"}`. `last_ts_open` vaut `null` si aucune bougie n'existe encore. `outage` vaut `{"started_at", "cause"}` ou `null` | connecté (spec Connexion, scope n°6) | 401 non connecté |

**Pannes** (dans le `worker`) :
- À chaque minute, si `closed_since` échoue ou reste vide, on réessaie toutes les 2 secondes. Si l'on reste 2 minutes sans nouvelle bougie alors que le marché est ouvert et hors rollover, on ouvre une `feed_outage` avec sa cause (AC-5).
- Cause d'une coupure selon la dernière erreur : `FeedAuthError` → `auth`, `FeedRateLimited` → `limite_api`, `FeedUnavailable` dû au réseau (connexion, DNS) → `reseau`, réponse 5xx → `erreur_api`, pas de réponse dans le délai → `timeout`, réponse correcte mais sans bougie → `donnees_absentes`.
- Au retour, on appelle `history(dernière bougie stockée + 1 min, maintenant)`, on insère avec `backfilled = true`, et on ferme la coupure avec `closed_reason = retour_flux` et `bars_backfilled` (AC-6). On fait de même au démarrage du `worker`.
- Si une coupure est encore ouverte quand le marché ferme (week-end ou jour férié), elle est fermée à l'heure de fermeture avec `closed_reason = fermeture_marche`. Si le problème dure encore à la réouverture, une nouvelle coupure s'ouvre après 2 minutes.
- Chaque interrogation du fournisseur est journalisée avec son heure et la minute visée, pour la mesure de l'AC-4.
- L'envoi du message Telegram de panne et de retour à la normale appartient à la fonction « Surveillance de panne » (scope n°13), qui lit `feed_outage`.
- Les bougies `backfilled` passent dans le moteur pour que la structure reste juste, mais aucune alerte de setup n'est envoyée pour elles (règle à respecter par la fonction alertes, scope n°7).

**Value sourcing** :
| Action | Valeur produite ou affichée | Source |
|---|---|---|
| Mesure | prix OANDA de référence | `exemples/reference_oanda.csv`, lu sur les captures et validé par le trader |
| Mesure | prix de la source pour le même point | `PriceFeed.history` de chaque candidat. Pour un point M3 ou M5, agrégation du M1 (règle de la spec 0001) |
| Mesure | seuil « assez proche » | décidé ici : 90 % des points à 0,003 ou moins |
| Direct | minute attendue | horloge UTC du `worker` (chrony, spec 0001) : la minute qui vient de se terminer |
| Direct | marché ouvert ou fermé | dérivé de l'heure `America/New_York` : fermé du vendredi 17h00 au dimanche 17h00, plus `MARKET_HOLIDAYS` |
| Direct | fenêtre du rollover | décidé ici : de 16h58 à 17h10, heure de New York |
| Toutes | source active | `PRICE_SOURCE` |
| État du flux | dernière bougie, coupure en cours | `max(candle_m1.ts_open)` de la source active, `feed_outage` où `ended_at is null` |

**Key invariants** :
- Une seule bougie par `source` et par minute. Une bougie stockée n'est jamais modifiée ni supprimée par le code applicatif.
- Toutes les heures sont en UTC en base. Seul l'affichage convertit vers `Africa/Porto-Novo`.
- Le moteur ne lit que `PRICE_SOURCE`. Il ne mélange jamais deux sources dans une même série.
- Aucune UT autre que le M1 n'est demandée au fournisseur ni stockée.
- Au plus une coupure ouverte par source.

**Security model** :
- L'accès fournisseur est en **lecture seule** par construction : les adaptateurs n'implémentent que la lecture des prix. Le compte démo ne sert jamais à trader.
- Les clés vivent dans les variables d'environnement (`.env` sur le VPS, secrets GitHub). Elles ne sont jamais journalisées. `.env.example` ne contient que les noms.
- `GET /api/feed/status` exige la connexion. Il ne renvoie aucune clé ni aucun identifiant de compte.

**Configuration required** :
- `PRICE_SOURCE` : la source active (`fxcm`, `finnhub_oanda`…), fixée après la mesure.
- `FXCM_API_TOKEN` : jeton de l'API FXCM, obtenu avec un compte démo gratuit (prérequis : le trader crée le compte).
- `FXCM_ENV` : `demo`, pour que l'hôte de l'API corresponde au compte.
- `FINNHUB_API_KEY` : clé gratuite Finnhub, pour la mesure (prérequis : le trader crée le compte).
- `MARKET_HOLIDAYS` : les jours de fermeture du marché, par exemple `12-25,01-01`.
- Prérequis réseau : l'environnement de développement et le VPS doivent pouvoir joindre les domaines des fournisseurs (voir le suivi de la spec 0001).

**Critical test scenarios** :
- Chemin normal : sur une journée rejouée avec un faux fournisseur, chaque minute est stockée une seule fois et à temps. Vérifie **AC-3**, **AC-4**.
- Panne : le faux fournisseur se tait 5 minutes un mardi à 10h00 UTC. Une coupure s'ouvre à 2 minutes, les 5 bougies reviennent en `backfilled`, et la coupure se ferme avec `bars_backfilled = 5`. Vérifie **AC-5**, **AC-6**.
- Pas de fausse panne : le faux fournisseur se tait un samedi, puis à 17h02 heure de New York un mercredi. Aucune coupure ne s'ouvre. Vérifie **AC-5**.
- Révision : le fournisseur renvoie un autre `close` pour une minute déjà stockée. La base ne change pas et une révision est journalisée. Vérifie **AC-10**.
- Relance : `feed backfill` lancé deux fois sur la même période insère 0 bougie la seconde fois. Vérifie **AC-3**.
- M3 et M5 : l'agrégation d'un M1 connu donne les bons OHLC calés sur :00, :03, :06, y compris quand une minute manque. Vérifie **AC-7**.
- Fuseau : une bougie FXCM d'un jour de janvier et d'un jour de juillet donne le bon `ts_open` en UTC (5 h puis 4 h d'écart avec New York). Vérifie **AC-12**.
- Week-end : une coupure ouverte le vendredi à 16h50, heure de New York, est fermée à 17h00 avec `fermeture_marche`. Vérifie **AC-5**.
- Lecture seule : le test des mots interdits échoue si l'on ajoute `def place_order` dans un adaptateur. Vérifie **AC-9**.
- Accès : `GET /api/feed/status` sans connexion renvoie 401. Vérifie **AC-11**.

## Build plan

Approche Tracer Bullet : d'abord la mesure (sans base, parce qu'elle décide de tout le reste), puis un fil mince de bout en bout (le fournisseur retenu, la base, le `worker`), puis on épaissit (pannes, état du flux). Prérequis : le squelette de la spec 0001 est posé.

1. Lire les 19 captures et écrire `exemples/reference_oanda.csv` (points `exact` et `borne`), puis le faire valider par le trader. Satisfait **AC-1**.
2. Écrire le type `Candle`, l'interface `PriceFeed` et l'agrégation M1 vers M3 et M5 (fonctions pures, testées). Satisfait **AC-7**, **AC-8**.
3. Écrire les adaptateurs `history` de `fxcm`, `finnhub_oanda` et `dukascopy` (conversion UTC, date à l'ouverture, `price_kind`, attente croissante sur les limites), plus le test des mots interdits. Satisfait **AC-2**, **AC-9**, **AC-12**.
4. Écrire `closed_since` pour `fxcm` et `finnhub_oanda`, puis `hellofedge feed live-test`, et lancer 30 minutes de test par candidat, marché ouvert. Satisfait **AC-2**.
5. Écrire `hellofedge feed compare` (écart absolu, points `borne`, bougies voisines, classement), lancer la mesure, écrire `exemples/mesure_sources.md`, puis faire choisir la source au trader. Reporter la source retenue et l'écart mesuré dans la section *Decision* de cette spec. Satisfait **AC-2**, **AC-7**, **AC-12**.
6. Écrire la migration Alembic de `candle_m1`, `feed_outage` et `candle_revision`. Satisfait **AC-3**, **AC-5**, **AC-10**.
7. Écrire `hellofedge feed backfill` (par semaine, insertion idempotente, une bougie existante n'est pas réécrite, les révisions vont dans `candle_revision`), puis charger 2 ans. Satisfait **AC-3**, **AC-10**.
8. Écrire la boucle du direct dans le `worker` pour la source retenue (seconde 3, nouvelles tentatives, `NOTIFY` en JSON, journal des interrogations). Satisfait **AC-4**, **AC-8**.
9. Ajouter la détection de coupure (causes, marché ouvert, rollover, jours fériés, fermeture au début du week-end) et le rattrapage au retour et au démarrage. Satisfait **AC-5**, **AC-6**.
10. Ajouter `GET /api/feed/status`. Satisfait **AC-11**.
11. Mesurer le délai du direct pendant une journée complète, du mardi au jeudi, avec le détail par session, et le noter dans le rapport. Satisfait **AC-4**.

## Consequences

**Positive**:
- Le choix repose sur un écart mesuré, pas sur une réputation. Tu sais exactement quelle confiance accorder à un balayage de 0,2 pip.
- Coût prévu : 0 € par mois (comptes démo et offres gratuites). La marge du budget reste entière.
- Le rejeu et le direct lisent les mêmes bougies du même fournisseur, donc la validation des 10 trades vaut pour le direct.
- Changer de source plus tard (payante, ou FundedNext) ne touche qu'un adaptateur et une variable.

**Negative / tradeoffs**:
- Aucune source n'est OANDA, sauf Finnhub si ses bougies OANDA marchent. Un petit écart restera probablement, et la mesure le rendra visible, pas nul.
- La mesure repose sur des points lus sur des captures : il y en a peu (quelques dizaines), et les points `borne` sont moins forts que des bougies exportées.
- 2 à 10 secondes de retard après chaque clôture de minute.
- Les offres gratuites peuvent changer ou disparaître, et un compte démo FXCM peut expirer. Il faudra alors refaire le jeton, voire mesurer à nouveau.
- Les prix FundedNext (ceux qui touchent vraiment ton SL) ne sont pas contrôlés pendant le MVP.

**Neutral**:
- Trois nouvelles tables (`candle_m1`, `feed_outage`, `candle_revision`) et une migration.
- Les points de référence serviront aussi de test permanent pour l'agrégation M3 et M5.

## Follow-up

- [ ] Créer un compte démo FXCM et une clé gratuite Finnhub, puis les mettre dans les secrets (le trader, avant l'étape 3 du plan).
- [ ] Élargir l'accès réseau de l'environnement aux domaines de FXCM, Finnhub et Dukascopy (déjà noté dans la spec 0001).
- [ ] Après la mesure : reporter la source retenue et l'écart dans *Decision*. Si aucune source n'atteint le seuil, la tolérance des balayages sera revue au rejeu des 10 trades (scope n°12).
- [ ] Fonction différée : lire les prix FundedNext MT5 (via MetaApi, mot de passe investisseur, lecture seule) pour mesurer l'écart avec ce qui touche vraiment ton SL.
- [ ] La fonction alertes (scope n°7) doit respecter la règle « pas d'alerte de setup sur une bougie `backfilled` ».
- [ ] Agent Skills et serveurs MCP : aucun nouvel outil n'est encore fixé (la mesure décidera). La recherche reste celle prévue par la spec 0001.
