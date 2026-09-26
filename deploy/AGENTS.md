# Deploy (VPS)

La mise en production sur le VPS : `docker-compose.yml` et `Caddyfile` ici, `Dockerfile` à la racine du dépôt. Règles d'exploitation complètes : spec [0001](../docs/specs/0001-stack-architecture/index.md).

## Fichiers
- `../Dockerfile` : image unique en deux étapes (Node 22 construit le cockpit, puis l'image Python 3.13). Elle sert l'`api`, le `worker` et la migration.
- `docker-compose.yml` : `postgres`, `migrate` (ponctuel, profil `migrate`), `api`, `worker`, `caddy`.
- `Caddyfile` : HTTPS automatique pour `HELLOFEDGE_DOMAIN`, tout vers l'`api`.

## Déployer (depuis `deploy/`)
1. `docker compose pull`
2. `docker compose run --rm migrate`
3. `docker compose up -d`

## Règles
- Un fichier `.env` (droits `600`) à côté de `docker-compose.yml` fournit `IMAGE_TAG`, `POSTGRES_PASSWORD` et `HELLOFEDGE_DOMAIN`, plus les secrets de l'application. Les noms sont dans `../.env.example`.
- Une seule copie du `worker`, jamais `--scale worker=2`.
- La base n'expose aucun port hors du réseau Docker.
- Les versions des images sont fixées (pas de `latest`). L'image de l'application est `ghcr.io/kyzerkul/hellofedge:<commit>`.
- Le flux en direct (SSE) doit être servi sous `/api/stream` : c'est la seule route que Caddy relaie sans tampon ni compression.
- Pas encore en place : GitHub Actions, sauvegardes `pg_dump`, swap et chrony. Ils viendront avec le premier vrai déploiement.

_Drafted by /sync from the introducing change, worth a quick human pass._
