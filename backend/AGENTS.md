# Backend (Python)

Le serveur de Hellofedge : un seul paquet `hellofedge`, deux processus (`worker` et `api`). Décision : spec [0001](../docs/specs/0001-stack-architecture/index.md).

## Fichiers
- `src/hellofedge/config.py` : réglages lus dans l'environnement (`get_settings()`, mis en cache). `DATABASE_URL` est obligatoire, sans elle rien ne démarre.
- `src/hellofedge/db.py` : moteur SQLAlchemy asynchrone (pilote psycopg 3, chaque connexion en UTC) et `Base` avec une convention de noms pour les contraintes.
- `src/hellofedge/logs.py` : journaux JSON sur la sortie standard, horodatés en UTC (ceux d'uvicorn compris).
- `src/hellofedge/worker.py` : processus `worker` (verrou unique, fichier témoin de santé).
- `src/hellofedge/api/app.py` : processus `api` (`/api/health`, puis les fichiers du cockpit si `FRONTEND_DIST` existe).
- `src/hellofedge/api/auth.py` : garde `SessionDep` des routes réservées au trader. Fermée (401 pour tous) tant que la Connexion (scope n°6) n'existe pas.
- `src/hellofedge/api/feed.py` : `GET /api/feed/status`, l'état du flux de prix.
- `src/hellofedge/cli.py` : commande `hellofedge` pour les opérations ponctuelles de la source de prix.
- `src/hellofedge/data/` : source de prix (spec [0002](../docs/specs/0002-source-de-prix/index.md)). `feed.py` (interface `PriceFeed`), `sources.py` (choix par `PRICE_SOURCE`), `ctrader/` (client WebSocket, jeton, adaptateur `ctrader_icmarkets`), `candle.py` et `timeframes.py` (bougie M1, M3 et M5 reconstruits), `pump.py` et `live.py` (direct), `outages.py` et `market.py` (coupures, heures d'ouverture), `store.py`, `backfill.py`, `models.py`, `reference.py` et `measure.py` (points OANDA et mesure).
- `src/hellofedge/{engine,alerts,scheduler}/` : modules prévus par la spec, encore vides.
- `migrations/` : Alembic, URL lue dans `DATABASE_URL` (jamais dans `alembic.ini`).

## Commandes (depuis `backend/`)
- Installer : `uv sync`
- Lancer l'api : `uv run uvicorn hellofedge.api.app:app --reload`
- Lancer le worker : `uv run hellofedge-worker` (santé : `uv run hellofedge-worker --check`, code 0 ou 1)
- Source de prix : `uv run hellofedge feed <ctrader-accounts | ctrader-token --reseed | compare | live-test | backfill>` (le vrai cTrader, donc sur le VPS)
- Migrations : `uv run alembic upgrade head` ; nouvelle migration : `uv run alembic revision --autogenerate -m "<sujet>"`
- Tests : `TEST_DATABASE_URL=<base jetable> uv run pytest`

## Conventions
- Dépendances avec `uv add`, jamais `pip`. Une dépendance arrive avec la fonction qui en a besoin.
- Réglages uniquement par `get_settings()`, jamais `os.environ` lu en dur. Toute nouvelle variable va aussi dans `.env.example` (nom seul).
- Journaux par `logging.getLogger("hellofedge.<module>")`. Champs en plus avec `extra={"data": {...}}`. Jamais de secret dans un message.
- Modèles : ils héritent de `hellofedge.db.Base`. Alembic ne les voit que s'ils sont importés au moment où `migrations/env.py` lit `Base.metadata`.
- Les migrations se lancent à part (`alembic upgrade head`), jamais au démarrage du `worker` ou de l'`api`.
- Un seul `worker` : il tient le verrou PostgreSQL `WORKER_LOCK_KEY` tant qu'il tourne ; une seconde copie s'arrête avec le code 1.
- Santé du `worker` : `touch_heartbeat()`, appelé à chaque tour de boucle tant que la boucle du flux (`FeedPump`) a tourné depuis moins de `PUMP_STALL`. Une panne du fournisseur ouvre une coupure `feed_outage`, elle n'arrête pas le `worker`.
- `engine` reste pur : il reçoit des bougies, il renvoie des détections.
- Prix en `Decimal` à 3 décimales (`NUMERIC(10,3)` en base), jamais en nombre à virgule flottante.
- Le reste du code lit les prix par `PriceFeed` (`sources.open_feed`), jamais le fournisseur directement. Nouvelle source = un adaptateur et une ligne dans `open_feed`.
- Lecture seule : `tests/test_readonly_guard.py` refuse tout nom lié aux ordres (order, trade, position…) dans `data/`. Le client cTrader n'envoie que les messages de `protocol.SENDABLE`.
- Seul le `worker` renouvelle le jeton cTrader (table `provider_token`). Les commandes `hellofedge` ne le renouvellent pas et n'affichent jamais un jeton.
- Chaque nouvelle bougie M1 envoie `NOTIFY candle_m1` (JSON).
- Route réservée au trader : ajouter la dépendance `SessionDep`.

## Tests
- `tests/test_*.py`, avec pytest et pytest-asyncio (`@pytest.mark.asyncio`).
- Un test qui demande une vraie base prend la fixture `db_url` (lit `TEST_DATABASE_URL`, sinon le test est sauté).
- Les fixtures automatiques de `tests/conftest.py` vident le cache des réglages et remettent les journaux en place après chaque test.
- cTrader se teste contre le faux serveur WebSocket local `tests/fake_ctrader.py`, jamais sur le réseau.
- Le `worker` se teste en vrai processus (`python -m hellofedge.worker`), pas en appelant sa boucle.

_Drafted by /sync from the introducing change, worth a quick human pass._
