# 0002. Source de prix : raisonnement

## Context

Le trader lit ses graphiques sur TradingView avec le flux **OANDA:USDJPY** (prix bid, 3 décimales). Les 10 trades de référence de `exemples/README.md` ont été annotés sur ce flux, et le critère de succès du MVP est de les retrouver. Or ouvrir un compte OANDA est impossible pour le trader, et l'API OANDA était la source prévue par le cahier des charges.

L'écart entre deux sources compte beaucoup ici. Les balayages de la méthode font 0,2 à 1 pip et les stops 2,5 à 6 pips (`exemples/README.md`, bilan). Une mèche plus courte d'un dixième de pip chez une autre source peut faire disparaître une prise de liquidité, qui se définit par une clôture du corps au delà du niveau. Le trader exécute chez FundedNext (MT5), dont les prix diffèrent encore un peu.

Contraintes : un budget de moins de 30 € par mois pour tout le projet (il reste environ 20 € après la spec 0001), un serveur Linux en Python, un accès en lecture seule, pas d'export CSV possible depuis l'abonnement TradingView du trader, et 2 ans d'historique M1 voulus au départ. Il faut aussi un direct fiable 24 h/24, en semaine.

Sans décision, rien ne peut être construit au delà du squelette : le moteur, le rejeu et les alertes lisent tous des bougies.

## Options considered

### Option 1 : mesure comparative, puis un seul fournisseur (historique et direct)

On lit des points OANDA exacts sur les captures, on télécharge le M1 de FXCM, de Finnhub (flux OANDA) et de Dukascopy sur les mêmes jours, et on garde la source la plus proche dont l'historique et le direct fonctionnent.

**Pros**:
- Le choix est fondé sur l'écart réel, dans l'unité qui compte (le pip).
- Le rejeu et le direct lisent le même fournisseur.
- Le coût est probablement nul.

**Cons**:
- Il faut écrire trois adaptateurs d'historique, dont deux serviront peut-être seulement à la mesure.
- La référence est faite de points lus sur des captures, en petit nombre.

### Option 2 : FXCM directement (piste du trader)

Un compte démo FXCM gratuit donne un jeton d'API, l'historique M1 depuis 2012 et un direct.

**Pros**:
- C'est le plus rapide à brancher. Un seul fournisseur et un seul compte, gratuit.
- L'historique est long et facile à télécharger.

**Cons**:
- L'écart avec OANDA reste inconnu. Il pourrait dépasser les plus petits balayages.
- L'état de l'API de direct depuis le rachat de FXCM n'a pas pu être confirmé, et les comptes démo peuvent expirer.

### Option 3 : Finnhub (flux OANDA) directement

Finnhub relaie des symboles `OANDA:USD_JPY` : ce seraient les prix mêmes du graphique du trader, avec une clé gratuite.

**Pros**:
- Ce sont potentiellement les vrais prix OANDA, avec un écart proche de zéro.
- La clé est gratuite, et il y a un WebSocket.

**Cons**:
- Des problèmes de bougies OANDA sont signalés publiquement. La résolution M1 et la profondeur en offre gratuite ne sont pas confirmées.
- C'est un intermédiaire dont les conditions gratuites peuvent changer.

### Option 4 : historique Dukascopy, direct d'une autre source

Dukascopy fournit gratuitement, sans compte, un historique tick et M1 de très bonne qualité. Le direct viendrait d'ailleurs.

**Pros**:
- C'est le meilleur historique gratuit et le plus simple à obtenir.

**Cons**:
- Deux sources différentes : le rejeu validerait des bougies que le direct ne verra jamais exactement. Un niveau « pris » dans le rejeu peut ne pas l'être en direct.
- Le direct Dukascopy passe par JForex (Java), qui est lourd pour un VPS de 4 Go.

### Option 5 : cTrader Open API sur un compte démo (retenue le 28/09/2026)

L'API officielle et gratuite de Spotware donne les bougies M1 bid et un direct, avec un jeton de portée `accounts` (lecture seule), sur un compte démo d'un courtier cTrader (IC Markets).

**Pros**:
- API officielle, documentée et gratuite, en lecture seule par construction.
- Bougies construites sur le bid, comme le graphique du trader. Un seul fournisseur pour l'historique et le direct.
- Pas de terminal à faire tourner (contrairement à MT5).

**Cons**:
- Protocole plus lourd qu'une API REST : WebSocket permanent, maintien de connexion, jeton de 30 jours à renouveler.
- Profondeur d'historique non garantie (elle dépend du courtier), 14 000 bougies au plus par requête.
- Ce ne sont ni les prix OANDA ni ceux de FundedNext.

## Rationale

La force dominante est la taille des balayages (0,2 à 1 pip) face à un écart inconnu entre sources. Choisir directement FXCM (option 2, la piste du trader) pourrait très bien marcher, mais on ne le saurait qu'au rejeu des 10 trades, en confondant alors un défaut du moteur avec un défaut de données. L'option 1 coûte un script et deux adaptateurs de plus, et en échange chaque écart futur aura une explication chiffrée. FXCM reste le favori par défaut de la mesure : si son écart passe le seuil, c'est lui qu'on garde.

L'option 4 est écartée même si son historique est excellent. La condition de validité du projet est que le rejeu reproduise le direct, et deux fournisseurs cassent cette condition au niveau du dixième de pip. Dukascopy participe quand même à la mesure, parce qu'il sert d'étalon de qualité.

Le direct lit la bougie M1 clôturée du fournisseur plutôt que des ticks, pour la même raison : une bougie construite chez nous à partir des ticks peut différer de celle que le fournisseur livre en historique. Le retard de quelques secondes ne gêne pas une règle fondée sur la clôture du corps. Le prix bid est retenu parce que les graphiques forex de TradingView sont tracés au bid : c'est ce que le trader voit.

Une relecture a proposé de choisir la source en rejouant directement les 10 trades sur chaque candidat, ce qui mesurerait le vrai critère de succès. C'est écarté pour l'instant, parce que le moteur n'existe pas encore. Ce rejeu viendra au scope n°12 et servira de second contrôle de la source retenue.

## Options de direct et de pannes retenues avec le trader

- Direct : bougie M1 du fournisseur lue juste après la clôture (choix du trader).
- Panne : alerte, puis rattrapage automatique avec les bougies marquées `backfilled` (choix du trader). La bascule sur une source de secours est écartée, parce qu'elle mélangerait deux séries.
- Seuil : 90 % des points à 0,3 pip ou moins. Plan B si aucune source ne passe : garder la plus proche et le signaler (choix du trader).
- FundedNext : contrôle reporté après le MVP (choix du trader).

## Révision du 28/09/2026 : pourquoi cTrader remplace les trois candidats

Au moment de construire l'étape 3, les trois candidats se sont révélés inutilisables :

| Source | Constat | Cause |
|---|---|---|
| FXCM | jeton impossible à obtenir | Trading Station Web redirige vers la nouvelle plateforme `app.fxcm.com`, qui n'offre pas la gestion du jeton |
| Finnhub | bougies `OANDA:USD_JPY` refusées (« You don't have access to this resource ») | bougies forex réservées à l'offre payante |
| Dukascopy | fichiers M1 refusés (« Too Many Requests ») | accès restreint, renvoi vers un stockage Amazon S3 payé au téléchargement |

Pistes étudiées avec le trader :
- **MT5 (compte démo)** : pas d'API serveur officielle sous Linux. Il faudrait le terminal sous Wine sur le VPS (lourd pour 4 Go, fragile) ou un relais payant (MetaApi, qui détiendrait le mot de passe). Écarté.
- **cTrader** : API officielle, gratuite, lecture seule par portée. Retenu (option 5), sur un compte démo IC Markets. Un compte de prop firm n'est pas confirmé avec l'API.
- **Garder FXCM et Dukascopy comme candidats lancés depuis le VPS** : écarté par le trader pour garder un seul candidat simple.

Choix du trader pendant cette révision : JSON sur WebSocket avec un petit client maison (la bibliothèque officielle repose sur Twisted, qui s'accorde mal avec asyncio), jeton renouvelé et gardé en base, bougie clôturée demandée chaque minute plutôt que poussée, historique pris tel que le courtier le donne (jusqu'à 2 ans), mesure et test du direct lancés depuis le VPS.

La logique de l'option 1 reste : on mesure l'écart avec OANDA avant d'adopter, mais sur un seul candidat. Le plan B est inchangé : si cTrader n'atteint pas le seuil, on le garde et on l'indique.

Vérification des docs cTrader du 28/09/2026 (sous agent de recherche, notes dans `docs/.agent-cache/research/ctrader-open-api.md`) : bougies construites sur le bid, 14 000 bougies au plus par requête (troncature silencieuse au delà), pas de profondeur documentée (elle dépend du courtier), 5 requêtes d'historique par seconde et par connexion, jeton d'environ 30 jours dont le renouvellement invalide l'ancien, portées `accounts` (lecture) et `trading`, hôtes `demo.ctraderapi.com` et `live.ctraderapi.com` (5035 protobuf, 5036 JSON), maintien de connexion toutes les 10 secondes.

## Vérification web du 26/09/2026

Faite par un sous agent de recherche. Certaines pages officielles étaient bloquées par le réseau de l'environnement, donc les points marqués « non confirmé » sont à revérifier au moment de construire.

| Source | Historique M1 | Direct | Coût | Remarque |
|---|---|---|---|---|
| FXCM | gratuit depuis 2012 (fichiers hebdomadaires) | API REST et flux, avec un jeton de compte démo | gratuit | état du direct depuis le rachat : non confirmé |
| cTrader Open API | M1 limité par requête (profondeur à vérifier) | oui (protobuf) | gratuit | compte démo chez un courtier cTrader et application enregistrée |
| Dukascopy | gratuit, tick et M1, sans compte | seulement par JForex | gratuit | le meilleur historique gratuit |
| Finnhub | M1 annoncé | WebSocket gratuit | gratuit, offres payantes | bougies OANDA : problèmes signalés, non confirmé |
| MetaApi | selon le compte MT5 | oui | offre gratuite pour 1 compte : non confirmé | lit un compte MT5 existant (FundedNext) |
| Twelve Data | oui | 8 crédits WebSocket par jour en gratuit | 29 $ par mois et plus | gratuit insuffisant pour un direct continu |
| Polygon | oui | seulement la fin de journée en gratuit | 29 $ par mois et plus | trop cher pour le gain attendu |

## References

**Project sources**:
- `docs/specs/0001-stack-architecture/index.md` : interface `PriceFeed`, Python, PostgreSQL, `LISTEN/NOTIFY`, M3 reconstruit depuis le M1, heures en UTC.
- `docs/scope/scope.md`, fonction n°2 : priorité à des prix fidèles au graphique TradingView, budget sous 30 €.
- `exemples/README.md` : captures sur OANDA:USDJPY, en UTC, et taille des balayages (0,2 à 1 pip).
- `AGENTS.md` : lecture seule, secrets hors du code, clôture du corps pour la prise de liquidité.

**Practices & standards**:
- Choisir par la mesure plutôt que par la réputation (une comparaison sur des données de référence).
- Une seule source de vérité par série (ne pas mélanger deux flux dans une série).
- Insertion idempotente et données immuables une fois lues par le moteur.

**Links** (vérifiés par la recherche du 28/09/2026) :
- cTrader Open API, données de symboles et bougies : https://help.ctrader.com/open-api/symbol-data/
- cTrader Open API, authentification du compte : https://help.ctrader.com/open-api/account-authentication/
- cTrader Open API, hôtes et ports : https://help.ctrader.com/open-api/proxies-endpoints/
- cTrader Open API, messages JSON : https://help.ctrader.com/open-api/sending-receiving-json/

**Links** (trouvés par la recherche du 26/09/2026, historique) :
- cTrader Open API : https://openapi.ctrader.com/
- Dukascopy, données historiques : https://www.dukascopy.com/wiki/en/development/strategy-api/historical-data/
- Finnhub, problème de bougies OANDA : https://github.com/finnhubio/Finnhub-API/issues/100
- MetaApi : https://metaapi.cloud/
- Twelve Data, forex : https://twelvedata.com/forex
- Polygon, WebSocket forex : https://polygon.io/docs/websocket/forex/overview
- FXCM MarketData (historique) : https://github.com/fxcm/MarketData
