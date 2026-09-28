# 0002. Source de prix : cTrader (démo IC Markets), mesurée contre OANDA, bougies M1 bid

**Date**: 2026-09-26 · mise à jour le 2026-09-28 (FXCM, Finnhub et Dukascopy remplacés par cTrader)
**Status**: In Progress

## Summary

OANDA étant impossible, la source de prix sera l'API officielle et gratuite de **cTrader**, lue sur un **compte démo IC Markets** avec une autorisation en lecture seule. FXCM (jeton impossible à obtenir), Finnhub (bougies forex payantes) et Dukascopy (accès restreint) sont abandonnés. Avant de l'adopter, on mesure son écart avec les vrais prix OANDA lus sur tes captures. Ensuite, le moteur reçoit chaque bougie M1 **bid** (le prix de ton graphique) quelques secondes après sa clôture, garde l'historique que le courtier fournit (jusqu'à 2 ans), signale les coupures et rattrape les trous tout seul.

## Requirements

**User stories**:
- En tant que trader, je veux que le moteur voie des bougies aussi proches que possible de mon graphique OANDA, pour qu'un balayage de 0,2 pip vu par l'outil existe aussi sur mon écran.
- En tant que trader, je veux savoir de combien cTrader s'écarte d'OANDA, chiffres à l'appui, pour savoir quelle confiance accorder aux alertes.
- En tant que trader, je veux que l'outil me prévienne quand le flux s'arrête et comble le trou tout seul, pour ne jamais prendre un silence pour une absence de setup.

**Acceptance criteria**:
- **AC-1**: Le fichier `exemples/reference_oanda.csv` contient au moins un point de référence par capture des exemples (19 captures), dont au moins 5 points `ut=3` et 5 points `ut=5`. Chaque point est lu sur la capture et validé par le trader (voir *Points de référence*).
- **AC-2**: Un rapport `exemples/mesure_sources.md` donne pour cTrader, sur les jours des exemples : le pourcentage de points à 0,3 pip ou moins (0,003), l'écart moyen **absolu**, l'écart maximum, le prix fourni (bid), la **profondeur d'historique M1 obtenue** (date de la plus ancienne bougie) et le résultat du test du direct (30 minutes, marché ouvert). cTrader est adopté si son historique et son direct fonctionnent. S'il n'atteint pas 90 % des points à 0,3 pip, on le garde quand même, et le rapport ainsi que la spec l'indiquent avec l'écart mesuré (plan B inchangé).
- **AC-3**: Les bougies M1 bid de la source active sont en base, jusqu'à 2 ans en arrière **selon ce que le courtier fournit**, horodatées en UTC sur la minute pleine. Relancer le chargement ne crée aucun doublon (unicité `source` + `ts_open`).
- **AC-4**: Pendant les heures de marché, chaque bougie M1 clôturée est en base moins de 10 secondes après la fin de sa minute, pour 95 % des minutes. La mesure porte sur une journée complète, du mardi au jeudi, avec le résultat par session (Tokyo, Londres, New York).
- **AC-5**: Si aucune nouvelle bougie n'arrive pendant 2 minutes (heures de marché, hors fenêtre du rollover), une coupure `feed_outage` est ouverte avec sa cause. Elle est fermée au retour des bougies. Le week-end, les jours fériés configurés et la fenêtre du rollover n'ouvrent jamais de coupure.
- **AC-6**: Après une coupure ou un redémarrage, les bougies manquantes sont rechargées chez le fournisseur, stockées avec `backfilled = true`, et comptées dans `bars_backfilled`. Il n'y a ni doublon ni trou quand le fournisseur a bien la bougie.
- **AC-7**: Les bougies M3 et M5 reconstruites depuis le M1 stocké (calées sur :00, :03, :06… et :00, :05…) respectent le seuil de l'AC-2 sur les points de référence pris sur les captures M3 et M5.
- **AC-8**: Changer `PRICE_SOURCE` fait lire au moteur une autre source sans toucher au code du moteur. Les bougies des autres sources restent en base.
- **AC-9**: Aucun code de `data/` ne contient d'appel capable de passer, modifier ou annuler un ordre. Un test pytest lancé en CI parcourt le code de `data/` et échoue s'il trouve un mot interdit dans un nom de fonction, une URL ou un chemin d'API (`order`, `trade`, `position`, `close_trade`, `OpenTrade`, `entry`).
- **AC-10**: Une bougie déjà stockée n'est jamais réécrite. Si le fournisseur renvoie plus tard une valeur différente pour la même minute, la différence est enregistrée dans `candle_revision`, et la bougie stockée reste celle que le moteur a vue.
- **AC-11**: Le cockpit peut afficher l'état du flux : source active, heure de la dernière bougie, coupure en cours s'il y en a une.
- **AC-12**: L'adaptateur convertit l'heure cTrader (`utcTimestampInMinutes`, minutes Unix de l'ouverture) en UTC et date chaque bougie à l'**ouverture** de sa minute. Un test le vérifie sur une date d'hiver et une date d'été, et la mesure compare aussi chaque point aux bougies voisines (une minute avant et après) pour révéler un décalage d'une minute.
- **AC-13**: Le jeton cTrader est renouvelé tout seul avant son expiration (7 jours avant). Le nouveau jeton est enregistré en base avant tout usage, un seul renouvellement peut avoir lieu à la fois, et aucun jeton n'apparaît dans les journaux ni dans une réponse de l'API. Si le renouvellement est refusé, une coupure de cause `auth` s'ouvre.
- **AC-14**: Le client cTrader n'envoie que les messages de sa **liste blanche** (authentification de l'application et du compte, version, liste et détail des symboles, bougies historiques, renouvellement du jeton, maintien de connexion). Un test échoue si un autre type de message peut être envoyé.

## Decision

**Chosen option**: Option 5 : cTrader Open API sur un compte démo IC Markets, mesuré contre les points OANDA, puis un seul fournisseur pour l'historique et le direct, lu en bougies M1 clôturées.

Le fournisseur est cTrader, par son API officielle et gratuite (Spotware), en **JSON sur WebSocket** (`demo.ctraderapi.com`, port 5036), avec un petit client asynchrone écrit pour le projet (bibliothèque `websockets`). Le compte est un **démo cTrader chez IC Markets**, autorisé avec la seule portée `accounts` (lecture seule). La valeur de `candle_m1.source` est `ctrader_icmarkets`. Les bougies cTrader sont construites sur le **bid**, comme le graphique du trader. La mesure et le test du direct tournent **sur le VPS** (`docker compose run`), parce que cet environnement cloud ne joint pas les serveurs de prix cTrader.

Décisions prises avec le trader (tu peux les contester) :
- **Lecture du direct** : à la seconde 3 de chaque minute, on demande la bougie M1 clôturée par la même requête que l'historique, puis toutes les 2 secondes jusqu'à ce qu'elle soit disponible, pendant 60 secondes au plus. Le rejeu et le direct lisent ainsi exactement la même bougie. Le runner up, la bougie poussée en direct, est plus rapide mais peut différer légèrement de la bougie d'historique.
- **Profondeur d'historique** : on prend ce que le courtier fournit, jusqu'à 2 ans, et on note la profondeur obtenue dans le rapport. Les 10 trades (août 2026) sont couverts de toute façon.
- **Jeton** : le jeton d'accès expire après environ 30 jours, et le renouveler invalide l'ancien. Le premier jeton vient des variables d'environnement, puis le `worker` le renouvelle et garde le dernier dans la table `provider_token`. C'est une exception assumée à la règle « secrets dans l'environnement », acceptable parce que le jeton est en lecture seule sur un compte démo.
- **Révisions** : la première valeur stockée fait foi (AC-10). Le runner up, réécrire la bougie, changerait après coup ce que le moteur a vu.
- **Fenêtre du rollover** : de 16h58 à 17h10, heure de New York. À cette heure, beaucoup de fournisseurs n'ont pas de prix pendant quelques minutes. Sans cette fenêtre, une fausse panne tomberait chaque soir.
- **Minutes sans prix** : on ne fabrique pas de bougie artificielle. TradingView n'en affiche pas non plus. Une bougie M3 ou M5 dont une minute manque est construite avec les minutes présentes, comme TradingView.
- **Jours fériés** : `MARKET_HOLIDAYS` ne contient que des dates fixes (25/12 et 01/01 suffisent pour USD/JPY). C'est une limite assumée : un jour de faible activité (Vendredi saint, Thanksgiving) peut au pire déclencher une fausse coupure.
- **Prix** : les décimales sont stockées en `NUMERIC(10,3)`, jamais en nombre à virgule flottante, pour que 0,2 pip reste exactement 0,002.

## Rationale

Le raisonnement, les options et les résultats des vérifications web sont dans [rationale.md](rationale.md).

## Feature design

**Data model sketch** (validé par le trader) :

`candle_m1` : les bougies M1, la seule vérité en base.
| Champ | Type | Règle |
|---|---|---|
| `source` | `text` | clé primaire (1/2). Valeurs : `ctrader_icmarkets`, et plus tard d'autres (`fundednext`…) |
| `ts_open` | `timestamptz` | clé primaire (2/2). Minute pleine en UTC (secondes = 0) |
| `open`, `high`, `low`, `close` | `numeric(10,3)` | obligatoires, prix **bid**. Contrainte : `low <= least(open, close)` et `high >= greatest(open, close)` |
| `ask_close` | `numeric(10,3)` | facultatif, sert à connaître le spread (vide avec cTrader, qui ne donne que le bid) |
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

`provider_token` : le dernier jeton valable d'un fournisseur (AC-13).
| Champ | Type | Règle |
|---|---|---|
| `source` | `text` | clé primaire |
| `access_token` | `text` | obligatoire, jamais journalisé |
| `refresh_token` | `text` | obligatoire, jamais journalisé |
| `expires_at` | `timestamptz` | obligatoire |
| `updated_at` | `timestamptz` | obligatoire |

Relations : une source a 1:N bougies et 1:N coupures, et au plus un jeton. Une bougie a 0:N révisions. `source` n'a pas de table à elle : la liste des sources vit dans la configuration. Les UT M3, M5, M15, H1, H4, D1 et W ne sont **jamais stockées**, elles sont recalculées depuis `candle_m1`.

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
| `PriceFeed.history(start, end)` | deux `datetime` UTC, fin exclue | liste de `Candle` M1 bid, triée, minutes pleines | `FeedAuthError` (jeton refusé), `FeedUnavailable` (réseau, erreur serveur), `FeedRateLimited` |
| `PriceFeed.closed_since(after)` | `datetime` UTC | bougies M1 **clôturées** après `after` (vide si la minute n'est pas encore disponible) | les mêmes |
| `PriceFeed.name` | aucune | identifiant stocké dans `candle_m1.source` | aucune |

**Client et adaptateur cTrader** :
- **Connexion** : WebSocket sécurisé `wss://demo.ctraderapi.com:5036` (`CTRADER_ENV=demo`, adresse exacte à confirmer dans la doc officielle au moment de construire), messages JSON `{clientMsgId, payloadType, payload}`. Une connexion permanente dans le `worker`, et une connexion par commande ponctuelle.
- **Ouverture** : authentification de l'application (`CTRADER_CLIENT_ID`, `CTRADER_CLIENT_SECRET`), puis du compte (`CTRADER_ACCOUNT_ID` et le jeton de `provider_token`). `CTRADER_ACCOUNT_ID` est le `ctidTraderAccountId` : la commande `hellofedge feed ctrader-accounts` liste les comptes liés au jeton (message de la liste blanche), et le trader copie le bon numéro dans les secrets. Les numéros de `payloadType` sont pris dans la documentation officielle Spotware.
- **Symbole** : l'identifiant de `CTRADER_SYMBOL` (`USDJPY`) et son nombre de décimales sont lus par la liste des symboles à chaque connexion, jamais écrits en dur.
- **Maintien** : un message de maintien de connexion toutes les 10 secondes. Connexion coupée : on reconnecte en attendant 2, 4, 8, 16, 32, puis 60 secondes au plus.
- **Bougies** : requête de bougies historiques en période M1. Pour `closed_since`, la fin demandée est le début de la minute en cours (exclue) : seule la bougie de la minute attendue est acceptée, jamais celle en formation. Une correction ultérieure de cTrader passe par `candle_revision` (AC-10). Prix = (`low` + delta) / 100000, arrondi au nombre de décimales du symbole, converti en `Decimal`. Heure d'ouverture = `utcTimestampInMinutes` × 60 secondes, en UTC.
- **Limites** : au plus 5 requêtes de bougies par seconde et par connexion. Un seul limiteur par connexion, réglé à 4 requêtes par seconde, est partagé par toutes les tâches qui l'utilisent (direct et rattrapage dans le `worker`). Ensuite, et 14 000 bougies au plus par requête (au delà, cTrader tronque sans erreur). L'historique est donc demandé par tranches d'une semaine (environ 7 200 bougies M1), et une tranche trop pleine est redécoupée.
- **Erreurs** : jeton refusé → `FeedAuthError`. Limite atteinte → `FeedRateLimited`. Connexion impossible, coupure ou erreur serveur → `FeedUnavailable` avec sa cause. Sur `FeedRateLimited` ou `FeedUnavailable`, on attend de plus en plus longtemps (2, 4, 8, 16, 32, puis 60 secondes au plus) avant de réessayer.
- **Liste blanche** (AC-14) : le client refuse d'envoyer tout message hors de sa liste. Aucun message d'ordre, de position ou de compte en écriture n'y figure. La portée `accounts` du jeton l'interdit déjà côté cTrader, et la liste blanche l'interdit côté code.
- **Jeton** (AC-13) :
  - Au démarrage, si `provider_token` est vide, on l'initialise depuis `CTRADER_ACCESS_TOKEN` et `CTRADER_REFRESH_TOKEN`. Après une régénération manuelle, `hellofedge feed ctrader-token --reseed` remplace la ligne par les valeurs de l'environnement.
  - **Seul le `worker` renouvelle**, quand il reste moins de 7 jours, sous un verrou PostgreSQL (advisory lock) **qui lui est propre**, distinct du verrou « un seul `worker` » de la spec 0001, et tenu seulement le temps du renouvellement. Le nouveau couple est écrit en base avant d'être utilisé.
  - Si l'écriture en base échoue après un renouvellement réussi (l'ancien jeton est déjà invalide), on réessaie l'écriture plusieurs fois avec le jeton gardé en mémoire. En dernier recours, on ouvre une coupure `auth` et le journal indique la marche à suivre (régénérer le jeton, puis `--reseed`), sans jamais écrire le jeton.
  - Les commandes ponctuelles lisent le jeton en base et ne renouvellent jamais. S'il expire dans moins d'un jour, elles s'arrêtent avec un message clair.
  - Sur un refus d'authentification, on relit d'abord le jeton en base (il vient peut-être d'être renouvelé) et on réessaie une fois. La coupure `auth` ne s'ouvre qu'après ce second refus.

**Commandes et surface** :
| Élément | Forme | Entrées clés | Sortie | Accès | Erreurs clés |
|---|---|---|---|---|---|
| Mesure de la source | commande `hellofedge feed compare` | `--reference exemples/reference_oanda.csv` | écrit `exemples/mesure_sources.md` (écart, profondeur d'historique) | `docker compose run` sur le VPS | source injoignable : notée « indisponible » dans le rapport |
| Test du direct | commande `hellofedge feed live-test` | `--minutes` (défaut : 30) | nombre de minutes reçues, manquées et délai par minute, ajoutés au rapport | `docker compose run` sur le VPS, marché ouvert | source injoignable : test « échoué » |
| Comptes cTrader | commande `hellofedge feed ctrader-accounts` | aucune | liste des `ctidTraderAccountId` liés au jeton (courtier, démo ou réel) | `docker compose run` sur le VPS | jeton refusé |
| Réinitialiser le jeton | commande `hellofedge feed ctrader-token --reseed` | aucune | `provider_token` remplacé par les valeurs de l'environnement | `docker compose run` | variables absentes |
| Chargement de l'historique | commande `hellofedge feed backfill` | `--from`, `--to` (défaut : 2 ans jusqu'à maintenant), source = `PRICE_SOURCE` | nombre de bougies insérées et ignorées, date de la plus ancienne bougie obtenue | `docker compose run` | reprise possible, idempotente |
| Lecture du direct | boucle dans le `worker` | aucune | lignes `candle_m1`, coupures `feed_outage`, `NOTIFY candle_m1` avec le message `{"source": "ctrader_icmarkets", "ts_open": "2026-08-24T10:47:00Z"}` | processus interne | voir *Pannes* |
| État du flux | `GET /api/feed/status` | aucune | `{"source", "last_ts_open", "outage"}`. `last_ts_open` vaut `null` si aucune bougie n'existe encore. `outage` vaut `{"started_at", "cause"}` ou `null` | connecté (spec Connexion, scope n°6) | 401 non connecté |

**Pannes** (dans le `worker`) :
- À chaque minute, si `closed_since` échoue ou reste vide, on réessaie toutes les 2 secondes. Si l'on reste 2 minutes sans nouvelle bougie alors que le marché est ouvert et hors rollover, on ouvre une `feed_outage` avec sa cause (AC-5).
- Cause d'une coupure selon la dernière erreur : `FeedAuthError` → `auth`, `FeedRateLimited` → `limite_api`, `FeedUnavailable` dû au réseau (connexion, DNS, WebSocket coupé) → `reseau`, erreur renvoyée par le serveur → `erreur_api`, pas de réponse dans le délai → `timeout`, réponse correcte mais sans bougie → `donnees_absentes`.
- Au retour, on appelle `history(dernière bougie stockée + 1 min, maintenant)`, on insère avec `backfilled = true`, et on ferme la coupure avec `closed_reason = retour_flux` et `bars_backfilled` (AC-6). On fait de même au démarrage du `worker`.
- Si une coupure est encore ouverte quand le marché ferme (week-end ou jour férié), elle est fermée à l'heure de fermeture avec `closed_reason = fermeture_marche`. Si le problème dure encore à la réouverture, une nouvelle coupure s'ouvre après 2 minutes.
- Chaque interrogation du fournisseur est journalisée avec son heure et la minute visée, pour la mesure de l'AC-4. Aucun jeton n'est journalisé.
- L'envoi du message Telegram de panne et de retour à la normale appartient à la fonction « Surveillance de panne » (scope n°13), qui lit `feed_outage`.
- Les bougies `backfilled` passent dans le moteur pour que la structure reste juste, mais aucune alerte de setup n'est envoyée pour elles (règle à respecter par la fonction alertes, scope n°7).

**Value sourcing** :
| Action | Valeur produite ou affichée | Source |
|---|---|---|
| Mesure | prix OANDA de référence | `exemples/reference_oanda.csv`, lu sur les captures et validé par le trader |
| Mesure | prix cTrader pour le même point | `PriceFeed.history` de l'adaptateur `ctrader_icmarkets`. Pour un point M3 ou M5, agrégation du M1 (règle de la spec 0001) |
| Mesure | seuil « assez proche » | décidé ici : 90 % des points à 0,003 ou moins |
| Mesure, chargement | profondeur d'historique | la plus ancienne bougie renvoyée par cTrader sur la période demandée |
| Toutes | identifiant et décimales de USD/JPY | liste des symboles cTrader, lue à chaque connexion pour `CTRADER_SYMBOL` |
| Toutes | prix d'une bougie | `low` + deltas de cTrader, / 100000, arrondis aux décimales du symbole |
| Toutes | heure d'ouverture d'une bougie | `utcTimestampInMinutes` de cTrader |
| Toutes | jeton d'accès | `provider_token` (initialisé depuis `CTRADER_ACCESS_TOKEN` et `CTRADER_REFRESH_TOKEN`) |
| Toutes | compte lu | `CTRADER_ACCOUNT_ID` |
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
- Un seul renouvellement de jeton à la fois, et le nouveau jeton est en base avant d'être utilisé.

**Security model** :
- L'accès fournisseur est en **lecture seule** deux fois : le jeton cTrader n'a que la portée `accounts`, et le client n'envoie que les messages de sa liste blanche (AC-14). Le compte démo ne sert jamais à trader.
- Les identifiants de l'application et le premier jeton vivent dans les variables d'environnement (`.env` sur le VPS, secrets GitHub). Le jeton renouvelé vit dans `provider_token` (exception assumée, voir *Decision*) : il est donc aussi dans les sauvegardes de la base. Aucun jeton n'est journalisé ni renvoyé par l'API. `.env.example` ne contient que les noms.
- `GET /api/feed/status` exige la connexion. Il ne renvoie aucun jeton ni aucun identifiant de compte.

**Configuration required** :
- `PRICE_SOURCE` : la source active, `ctrader_icmarkets`.
- `CTRADER_ENV` : `demo`, pour que l'hôte corresponde au compte.
- `CTRADER_CLIENT_ID`, `CTRADER_CLIENT_SECRET` : identifiants de l'application enregistrée sur openapi.ctrader.com (prérequis : le trader l'enregistre).
- `CTRADER_ACCOUNT_ID` : identifiant du compte démo IC Markets dans cTrader.
- `CTRADER_ACCESS_TOKEN`, `CTRADER_REFRESH_TOKEN` : le premier jeton, obtenu avec la seule portée `accounts`. Ensuite, la base prend le relais.
- `CTRADER_SYMBOL` : `USDJPY`.
- `MARKET_HOLIDAYS` : les jours de fermeture du marché, par exemple `12-25,01-01`.
- Prérequis réseau : le VPS doit joindre `demo.ctraderapi.com` sur le port 5036 (cet environnement cloud ne le peut pas).

**Critical test scenarios** :
- Chemin normal : sur une journée rejouée avec un faux fournisseur, chaque minute est stockée une seule fois et à temps. Vérifie **AC-3**, **AC-4**.
- Panne : le faux fournisseur se tait 5 minutes un mardi à 10h00 UTC. Une coupure s'ouvre à 2 minutes, les 5 bougies reviennent en `backfilled`, et la coupure se ferme avec `bars_backfilled = 5`. Vérifie **AC-5**, **AC-6**.
- Pas de fausse panne : le faux fournisseur se tait un samedi, puis à 17h02 heure de New York un mercredi. Aucune coupure ne s'ouvre. Vérifie **AC-5**.
- Révision : le fournisseur renvoie un autre `close` pour une minute déjà stockée. La base ne change pas et une révision est journalisée. Vérifie **AC-10**.
- Relance : `feed backfill` lancé deux fois sur la même période insère 0 bougie la seconde fois. Vérifie **AC-3**.
- M3 et M5 : l'agrégation d'un M1 connu donne les bons OHLC calés sur :00, :03, :06, y compris quand une minute manque. Vérifie **AC-7**.
- Décodage cTrader : une bougie (`low` et deltas connus, `utcTimestampInMinutes` d'un jour de janvier puis de juillet) donne les bons prix à 3 décimales et le bon `ts_open` UTC. Vérifie **AC-12**.
- Troncature : une tranche qui renvoie 14 000 bougies est redécoupée, et il ne manque aucune minute. Vérifie **AC-3**.
- Jeton : à 6 jours de l'expiration, le faux serveur reçoit un seul renouvellement même si deux tâches le demandent en même temps, et le nouveau jeton est en base. Une commande ponctuelle ne renouvelle jamais. Un refus d'authentification relit la base et réessaie une fois avant d'ouvrir une coupure `auth`. Vérifie **AC-13**.
- Bougie en formation : le faux serveur renvoie aussi la bougie de la minute en cours. `closed_since` ne la retourne pas. Vérifie **AC-4**.
- Liste blanche : demander au client d'envoyer un message hors liste lève une erreur, et le test des mots interdits échoue si l'on ajoute `def place_order`. Vérifie **AC-9**, **AC-14**.
- Week-end : une coupure ouverte le vendredi à 16h50, heure de New York, est fermée à 17h00 avec `fermeture_marche`. Vérifie **AC-5**.
- Accès : `GET /api/feed/status` sans connexion renvoie 401. Vérifie **AC-11**.

## Build plan

Approche Tracer Bullet : d'abord la mesure (elle décide de l'adoption), puis un fil mince de bout en bout (cTrader, la base, le `worker`), puis on épaissit (pannes, état du flux). Prérequis : le squelette de la spec 0001 est posé. Les tests automatiques tournent contre un faux serveur WebSocket local, sans réseau. Seules les commandes qui parlent au vrai cTrader (`ctrader-accounts`, `compare`, `live-test`, `backfill`) se lancent sur le VPS.

1. Lire les 19 captures et écrire `exemples/reference_oanda.csv` (points `exact` et `borne`), puis le faire valider par le trader. Satisfait **AC-1**. (Fichier écrit, validation du trader en attente.)
2. Écrire le type `Candle`, l'interface `PriceFeed` et l'agrégation M1 vers M3 et M5 (fonctions pures, testées). Satisfait **AC-7**, **AC-8**. (Fait.)
3. Écrire le client cTrader JSON sur WebSocket : connexion, authentification de l'application et du compte, maintien toutes les 10 secondes, reconnexion, limiteur de 4 requêtes par seconde, liste blanche des messages, plus la commande `feed ctrader-accounts`, testé contre un faux serveur local. Satisfait **AC-9**, **AC-14**. (Fait.)
4. Écrire la migration de `provider_token`, le renouvellement du jeton par le seul `worker` sous son propre verrou, la relecture avant coupure `auth`, et la commande `feed ctrader-token --reseed`. Satisfait **AC-13**. (Fait.)
5. Écrire l'adaptateur `ctrader_icmarkets` : symbole et décimales, `history` par tranches d'une semaine avec redécoupage, décodage des prix et des heures, limite de 5 requêtes par seconde, `closed_since`. Satisfait **AC-2**, **AC-3**, **AC-12**. (Fait.)
6. Écrire `hellofedge feed live-test` et `hellofedge feed compare` (écart, bougies voisines, profondeur d'historique), les lancer sur le VPS, écrire `exemples/mesure_sources.md`, puis faire valider l'adoption par le trader. Reporter l'écart mesuré dans la section *Decision*. Satisfait **AC-2**, **AC-7**, **AC-12**.
7. Écrire la migration Alembic de `candle_m1`, `feed_outage` et `candle_revision`. Satisfait **AC-3**, **AC-5**, **AC-10**.
8. Écrire `hellofedge feed backfill` (par semaine, insertion idempotente, une bougie existante n'est pas réécrite, les révisions vont dans `candle_revision`), puis charger l'historique disponible, jusqu'à 2 ans. Satisfait **AC-3**, **AC-10**.
9. Écrire la boucle du direct dans le `worker` (seconde 3, nouvelles tentatives, `NOTIFY` en JSON, journal des interrogations). Satisfait **AC-4**, **AC-8**.
10. Ajouter la détection de coupure (causes, marché ouvert, rollover, jours fériés, fermeture au début du week-end) et le rattrapage au retour et au démarrage. Satisfait **AC-5**, **AC-6**.
11. Ajouter `GET /api/feed/status`. Satisfait **AC-11**.
12. Mesurer le délai du direct pendant une journée complète, du mardi au jeudi, avec le détail par session, et le noter dans le rapport. Satisfait **AC-4**.

## Consequences

**Positive**:
- Une API officielle, gratuite et documentée, en lecture seule par construction, avec des bougies bid comme ton graphique.
- Coût prévu : 0 € par mois (compte démo et API gratuite). La marge du budget reste entière.
- Le rejeu et le direct lisent les mêmes bougies du même fournisseur, donc la validation des 10 trades vaut pour le direct.
- L'écart avec OANDA reste mesuré, pas supposé. Changer de source plus tard (payante, ou FundedNext) ne touche qu'un adaptateur et une variable.

**Negative / tradeoffs**:
- Ce ne sont ni les prix OANDA ni ceux de FundedNext. Un petit écart restera probablement, et la mesure le rendra visible, pas nul.
- Plus de travail qu'une API REST : un client WebSocket à maintenir (maintien de connexion, reconnexion) et un jeton à renouveler.
- Le jeton renouvelé vit en base, donc aussi dans les sauvegardes.
- La profondeur d'historique n'est pas garantie : elle dépend d'IC Markets.
- La mesure et le test du direct ne peuvent pas tourner dans cet environnement : il faut d'abord un VPS.
- Il y a 2 à 10 secondes de retard après chaque clôture de minute, et un compte démo peut expirer (il faudra alors en recréer un et refaire le premier jeton).

**Neutral**:
- Quatre nouvelles tables (`candle_m1`, `feed_outage`, `candle_revision`, `provider_token`).
- Les points de référence serviront aussi de test permanent pour l'agrégation M3 et M5.

## Follow-up

- [ ] Le trader : ouvrir un compte démo cTrader chez IC Markets, créer son cTrader ID, enregistrer une application sur openapi.ctrader.com (le délai de validation par Spotware n'est pas documenté), puis générer le premier jeton avec la seule portée `accounts`. Tout va dans les secrets, jamais dans le chat.
- [ ] Créer le VPS de la spec 0001 avant l'étape 6 : la mesure et le test du direct tournent dessus.
- [ ] Valider `exemples/reference_oanda.csv` (AC-1) avant la mesure.
- [ ] Mettre à jour `.env.example` : retirer FXCM et Finnhub, ajouter les variables `CTRADER_*`. Retirer `FXCM_API_TOKEN` et `FINNHUB_API_KEY` de l'environnement cloud.
- [ ] Après la mesure : reporter l'écart dans *Decision*. Si le seuil n'est pas atteint, la tolérance des balayages sera revue au rejeu des 10 trades (scope n°12).
- [ ] Fonction différée : lire les prix FundedNext (cTrader ou MT5) pour mesurer l'écart avec ce qui touche vraiment ton SL.
- [ ] La fonction alertes (scope n°7) doit respecter la règle « pas d'alerte de setup sur une bougie `backfilled` ».
- [ ] Agent Skills et serveurs MCP pour la bibliothèque `websockets` : non recherchés (choix « plus tard » de la spec 0001).
