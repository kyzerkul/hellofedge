# Hellofedge

Compagnon de trading **USD/JPY uniquement** pour un trader SMC (méthode RedPillFX). Il analyse, surveille, alerte et journalise. **Il ne passe jamais d'ordre.**

## Langue
Tout ce qui est destiné au trader (messages, docs, scope, specs, interface) est **en français**, simple et clair. Le code et ses identifiants peuvent rester en anglais.

## Sources de vérité
- Stratégie et règles de détection : `docs/CAHIER_DES_CHARGES.md` (section 1, notamment 1.12 le modèle d'entrée).
- Cas de test réels du trader : `exemples/README.md` (10 trades annotés, règles confirmées en fin de fichier).
- Plan et phases : `docs/PLAN_DE_DEVELOPPEMENT.md`.

## Règles non négociables
- Aucun ordre de trading, jamais. L'accès courtier est en lecture seule.
- Aucun secret dans le code, les commits ou le chat. Les secrets vivent dans des variables d'environnement ; `.env.example` ne contient que les noms.
- Heures stockées et calculées en **UTC**. Affichage à l'heure du Bénin (`Africa/Porto-Novo`, UTC+1). Les sessions sont ancrées sur le fuseau de leur place (Europe/London, America/New_York, Asia/Tokyo).
- Prise de liquidité = **clôture du corps** au-delà du niveau (M1, M3, M5). IPA touché = une **mèche** suffit.
- Le M3 est reconstruit à partir du M1 (OANDA ne fournit pas de M3).

## Stack
Décidée dans la spec [0001](docs/specs/0001-stack-architecture/index.md) : un monolithe Python 3.13 (FastAPI, SQLAlchemy 2 et Alembic, PostgreSQL 17) avec deux processus tirés de la même image, `worker` (prix, moteur, alertes) et `api` (API et cockpit), plus un cockpit React et TypeScript (Vite) servi par l'`api`. Déploiement avec Docker Compose et Caddy sur un VPS.
- Le module `engine` est pur : aucun accès réseau, base ou horloge système. C'est ce qui rend le rejeu identique au direct.
- Tests : pytest dans `backend/`, Vitest dans `frontend/`. Les choix sont dans `test-preferences.json`.
- Une bibliothèque s'installe avec la fonction qui en a besoin, jamais en avance.

## Build approach
Tracer Bullet : un fil réel et fin à travers toutes les couches, puis on épaissit un segment à la fois (en tête de `docs/scope/scope.md`).

## Workflow
Skills du projet dans `.claude/skills/` : `/scope` → `/architect` → `/develop` → `/check verify` → `/test` → `/check review` → `/sync`. Décision coûteuse = plan présenté et validé par le trader avant tout code.

## Agent skills
- [fastapi](.claude/skills/fastapi/): `fastapi/fastapi`, conventions officielles de FastAPI (routes, Pydantic, dépendances, flux SSE, service du cockpit).
- MCP servers: pgEdge Postgres MCP (recommended), à connecter une fois la base de production en place.

## Context files
- [backend/AGENTS.md](backend/AGENTS.md) : serveur Python (modules, commandes uv, worker, migrations, tests pytest).
- [frontend/AGENTS.md](frontend/AGENTS.md) : cockpit React (commandes npm, tests Vitest).
- [deploy/AGENTS.md](deploy/AGENTS.md) : Docker Compose, Caddy et règles d'exploitation du VPS.

## Git
integration: off
Le trader valide les étapes sensibles. Branche de travail imposée par la session ; pas de push sans accord.
