# Backend (Python)

Le serveur de Hellofedge : un seul paquet `hellofedge`, deux processus (`worker` et `api`). Décision : spec [0001](../docs/specs/0001-stack-architecture/index.md).

## Fichiers
- `src/hellofedge/config.py` : réglages lus dans l'environnement (`get_settings()`, mis en cache). `DATABASE_URL` est obligatoire, sans elle rien ne démarre.
- `src/hellofedge/db.py` : moteur SQLAlchemy asynchrone (pilote psycopg 3, chaque connexion en UTC) et `Base` avec une convention de noms pour les contraintes.
- `src/hellofedge/logs.py` : journaux JSON sur la sortie standard, horodatés en UTC (ceux d'uvicorn compris).
- `src/hellofedge/worker.py` : processus `worker` (verrou unique, fichier témoin de santé).
- `src/hellofedge/api/app.py` : processus `api` (`/api/health`, puis les fichiers du cockpit si `FRONTEND_DIST` existe).
- `src/hellofedge/{data,engine,alerts,scheduler}/` : modules prévus par la spec, encore vides.
- `migrations/` : Alembic, URL lue dans `DATABASE_URL` (jamais dans `alembic.ini`).

## Commandes (depuis `backend/`)
- Installer : `uv sync`
- Lancer l'api : `uv run uvicorn hellofedge.api.app:app --reload`
- Lancer le worker : `uv run hellofedge-worker` (santé : `uv run hellofedge-worker --check`, code 0 ou 1)
- Migrations : `uv run alembic upgrade head` ; nouvelle migration : `uv run alembic revision --autogenerate -m "<sujet>"`
- Tests : `TEST_DATABASE_URL=<base jetable> uv run pytest`

## Conventions
- Dépendances avec `uv add`, jamais `pip`. Une dépendance arrive avec la fonction qui en a besoin.
- Réglages uniquement par `get_settings()`, jamais `os.environ` lu en dur. Toute nouvelle variable va aussi dans `.env.example` (nom seul).
- Journaux par `logging.getLogger("hellofedge.<module>")`. Champs en plus avec `extra={"data": {...}}`. Jamais de secret dans un message.
- Modèles : ils héritent de `hellofedge.db.Base`. Alembic ne les voit que s'ils sont importés au moment où `migrations/env.py` lit `Base.metadata`.
- Les migrations se lancent à part (`alembic upgrade head`), jamais au démarrage du `worker` ou de l'`api`.
- Un seul `worker` : il tient le verrou PostgreSQL `WORKER_LOCK_KEY` tant qu'il tourne ; une seconde copie s'arrête avec le code 1.
- Santé du `worker` : `touch_heartbeat()`. Pour l'instant il est appelé à chaque tour de boucle ; il devra l'être à chaque bougie reçue (scope n°2).
- `engine` reste pur : il reçoit des bougies, il renvoie des détections.

## Tests
- `tests/test_*.py`, avec pytest et pytest-asyncio (`@pytest.mark.asyncio`).
- Un test qui demande une vraie base prend la fixture `db_url` (lit `TEST_DATABASE_URL`, sinon le test est sauté).
- Les fixtures automatiques de `tests/conftest.py` vident le cache des réglages et remettent les journaux en place après chaque test.
- Le `worker` se teste en vrai processus (`python -m hellofedge.worker`), pas en appelant sa boucle.

_Drafted by /sync from the introducing change, worth a quick human pass._
