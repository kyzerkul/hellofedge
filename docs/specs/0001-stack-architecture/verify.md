# Verify: Stack et architecture · spec 0001 · updated 2026-09-26
_La spec 0001 est une décision de stack, sans critères `AC-N`. Ces étapes viennent du « Done when » du scope (le squelette démarre et passe le build) et des règles d'exploitation de la spec. `/check verify` les rejoue ; `/test` fixe celles qui durent._

## Commandes (en local, avec une base PostgreSQL et `DATABASE_URL` défini)
- [ ] `cd backend && uv sync` → les dépendances s'installent sans erreur → Done when (build)
- [ ] `cd backend && uv run alembic upgrade head` → se termine sans erreur, la table `alembic_version` existe → règle « migrations »
- [ ] `cd backend && uv run uvicorn hellofedge.api.app:app` puis `curl localhost:8000/api/health` → `200` et `{"status":"ok","database":"ok"}` → Done when (démarre)
- [ ] Même appel avec PostgreSQL arrêté → `503` et `{"status":"error","database":"down"}` → contrôle de santé
- [ ] `cd backend && uv run hellofedge-worker` → une ligne JSON « worker démarré, verrou obtenu » → Done when (démarre)
- [ ] Une seconde copie `uv run hellofedge-worker` pendant que la première tourne → s'arrête avec le code 1 et « un autre worker tient déjà le verrou » → règle « un seul worker »
- [ ] `uv run hellofedge-worker --check` pendant que le worker tourne → code 0 ; worker arrêté depuis plus de 2 minutes → code 1 → règle « redémarrage » (santé du worker)
- [ ] Envoyer `SIGTERM` au worker → « worker arrêté proprement », le verrou est libéré → arrêt propre
- [ ] `cd frontend && npm ci && npm run build` → `frontend/dist/` est créé sans erreur TypeScript → Done when (build)
- [ ] `FRONTEND_DIST=../frontend/dist` puis `curl localhost:8000/` → la page `<title>Hellofedge</title>` ; `/api/health` répond toujours → le cockpit est servi par l'api

## Déploiement (Docker)
- [ ] `docker build -t ghcr.io/kyzerkul/hellofedge:local .` → l'image se construit (étape Node, puis image Python) → règle « image »
- [ ] Dans `deploy/`, avec un `.env` de test (`IMAGE_TAG=local`, `POSTGRES_PASSWORD`, `HELLOFEDGE_DOMAIN=localhost`) : `docker compose up -d postgres`, `docker compose run --rm migrate`, `docker compose up -d` → `api`, `worker` et `postgres` passent `healthy` → règles « migrations » et « redémarrage »
- [ ] `curl -k https://localhost/api/health` → `200` à travers Caddy ; `curl -k https://localhost/` → le cockpit → règle « HTTPS »
- [ ] `docker compose run --rm --no-deps worker hellofedge-worker` pendant que le worker tourne → code 1, verrou refusé → règle « un seul worker »
- [ ] `docker compose ps` → le service `postgres` n'expose aucun port → règle « base »
- [ ] Les journaux (`docker compose logs api worker`) sont des lignes JSON horodatées en UTC → règle « surveillance »

## Couverture
- Done when « démarre et passe le build » : étapes 1, 3, 5, 9, 10, 11, 12.
- Règles d'exploitation couvertes par le squelette : migrations (2, 12), image (11), base (15), un seul worker (6, 14), redémarrage et santé (4, 7, 12), HTTPS (13), journaux (16).
- Pas encore couvertes (elles viennent avec le déploiement réel ou une autre fonction) : GitHub Actions et GHCR, sauvegardes `pg_dump`, swap, chrony, écriture du `.env` au déploiement, message de maintien SSE toutes les 15 secondes.
