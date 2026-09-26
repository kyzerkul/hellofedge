# 0001. Stack et architecture : monolithe Python sur un petit serveur

**Date**: 2026-09-26
**Status**: In Progress

## Summary

Hellofedge sera un seul programme Python (FastAPI), organisé en modules, qui tourne 24 h/24 sur un petit serveur loué (VPS Hetzner, environ 8 € par mois) avec une base PostgreSQL. Deux processus partagent le même code : l'un reçoit les prix, fait tourner le moteur SMC et envoie les alertes Telegram, l'autre sert le cockpit (une appli React installable sur téléphone, avec le graphique Lightweight Charts). Tout est simple, très répandu et bien outillé, pour que Claude puisse le maintenir seul et que le coût total reste sous 30 € par mois.

## Decision

**Chosen option**: Option 1 : monolithe Python (FastAPI) + cockpit React statique + PostgreSQL, sur un VPS avec Docker Compose.

Un seul dépôt, une seule image Docker pour le serveur, deux processus (`worker` et `api`), une base PostgreSQL, Caddy devant pour le HTTPS. Le tout est déployé par GitHub Actions.

## Proposed stack

| Couche | Choix | Raison |
|---|---|---|
| Architecture | Monolithe modulaire : modules `data`, `engine`, `alerts`, `api`, `scheduler` | Un seul utilisateur et un seul mainteneur : c'est le plus simple à déployer, surveiller et déboguer (basis: monolith first). |
| Processus | Deux processus depuis la même image : `worker` (flux de prix, moteur, planificateur, alertes) et `api` (API + fichiers du cockpit) | Si l'API plante ou redémarre, les alertes continuent. Le moteur ne dépend jamais du cockpit. |
| Langage serveur | Python 3.13 | La référence pour l'analyse de séries de prix et le backtest, avec les meilleures bibliothèques. |
| Framework API | FastAPI (asynchrone) + Pydantic | Validation et doc automatiques, et gère bien les flux en direct. |
| Calcul du moteur | pandas + numpy | Standard, il reconstruit M3, M5, M15, H1, H4, D1 et W depuis le M1 en une ligne, et c'est assez rapide pour une paire. |
| Base de données | PostgreSQL 17 (sans extension) | Environ 3 millions de bougies M1, c'est petit. TimescaleDB pourra s'ajouter plus tard sans casser le schéma. |
| Accès base | SQLAlchemy 2 + Alembic (migrations) | La référence Python. Chaque changement de schéma est versionné et rejouable. SQL écrit à la main pour les requêtes lourdes du rejeu. |
| Temps réel vers le cockpit | Server Sent Events (flux à sens unique), alimentés par `LISTEN/NOTIFY` de PostgreSQL | Le `worker` publie dans la base et l'`api` relaie au navigateur. Il n'y a pas de Redis ni de courtier de messages à faire tourner. |
| Tâches planifiées | APScheduler dans le `worker`, fuseaux `zoneinfo` | Il connaît Europe/London, America/New_York et Asia/Tokyo, y compris les changements d'heure, sans pièce en plus. |
| Source de prix | Interface `PriceFeed` (historique + direct) avec un adaptateur par fournisseur | Le fournisseur est choisi dans la spec « Source de prix » (scope n°2). Le reste du code ne dépend jamais du fournisseur. |
| Alertes | API Bot Telegram appelée directement avec `httpx` | Envoyer un texte, une image ou des boutons se fait en quelques requêtes. Il n'y a pas de bibliothèque de bot tant que l'outil ne fait qu'envoyer. |
| Image des alertes | mplfinance / matplotlib côté serveur, aux couleurs du design | C'est léger en mémoire et fonctionne sans navigateur ni cockpit ouvert. |
| Cockpit | React + TypeScript + Vite, appli statique installable (PWA), servie par l'`api` | Il n'y a pas de second serveur Node à faire tourner. Node sert seulement à construire les fichiers, dans la CI. |
| Données du cockpit | TanStack Query pour les lectures, `EventSource` natif pour le direct | Le cache, les nouvelles tentatives et les états de chargement sont gérés sans code maison. |
| Graphique | Lightweight Charts (TradingView, licence Apache 2.0) | Un rendu proche de TradingView, fluide au doigt. La mention « TradingView » doit rester visible. |
| Style | Tailwind CSS branché sur les variables du design system | Il est cohérent avec le design system (scope n°5), qui fixera les valeurs. |
| Connexion | Décidée dans la spec « Connexion » (scope n°6) | Contrainte fixée ici : une bibliothèque éprouvée, jamais de code d'authentification écrit de zéro. |
| IA (fonctions différées) | SDK officiel `anthropic` pour Python | Il sert quand les agents arriveront. Le modèle et le plafond de coût seront choisis dans leur spec. |
| Hébergement | 1 VPS Hetzner Cloud CX23 (2 vCPU, 4 Go de RAM) en Allemagne, Docker Compose | Environ 8 € par mois, et tout tient dessus : PostgreSQL, deux processus Python et Caddy. |
| HTTPS | Caddy (certificats automatiques) | Le HTTPS est obligatoire pour une PWA, et la configuration est minimale. |
| Domaine | Nom de domaine acheté par le trader | Environ 10 à 15 € par an. Il est pointé vers le VPS au moment du déploiement. |
| Déploiement | GitHub Actions : tests, construction de l'image, puis mise à jour du VPS par SSH (`docker compose pull && up -d`) | C'est rejouable, et on revient à la version précédente en redéployant l'image d'avant. |
| Secrets | GitHub Actions Secrets, puis un fichier `.env` sur le VPS (droits `600`) écrit au déploiement | Rien n'est dans le code ni dans le chat. `.env.example` ne liste que les noms. |
| Surveillance | Journaux structurés (JSON sur la sortie standard), plus une sonde externe gratuite (type Healthchecks.io) pingée par le `worker`, plus l'alerte Telegram interne (scope n°13) | Tu es prévenu même si le serveur entier tombe. |
| Qualité Python | uv (dépendances), Ruff (lint + format), mypy (types), pytest | Les détails et les hooks seront fixés par `/audit` (scope n°3). |
| Qualité cockpit | TypeScript strict, ESLint, Prettier, Vitest | Les détails seront fixés par `/audit`. |

**Organisation du dépôt** (le squelette la crée, `/develop` affine) :

```
backend/            code Python (src/hellofedge/{data,engine,alerts,api,scheduler}), tests/
frontend/           cockpit React (Vite)
deploy/             docker-compose.yml, Caddyfile
.github/workflows/  CI et déploiement
```

**Règles d'architecture que le code doit respecter :**
- Le module `engine` est pur : il reçoit des bougies et renvoie des détections. Il ne fait aucun accès réseau, base ou horloge système. C'est ce qui rend le rejeu des 10 trades identique au direct.
- Les heures sont stockées et calculées en UTC (`timestamptz`). La conversion vers `Africa/Porto-Novo` se fait seulement à l'affichage et dans les messages.
- Le M3 est reconstruit depuis le M1, calé sur :00, :03, :06, etc. Aucune unité de temps n'est demandée toute faite au fournisseur, sauf le M1.
- Aucun code ne passe d'ordre. Tout accès courtier éventuel est en lecture seule.

**Règles d'exploitation** (issues du contrôle croisé, à respecter dès le squelette) :
- **Migrations** : une étape dédiée du déploiement lance `alembic upgrade head` (conteneur ponctuel) avant `docker compose up -d`. Ni `worker` ni `api` ne migrent au démarrage.
- **Image** : un Dockerfile en plusieurs étapes. Une étape Node 22 LTS construit `frontend/dist`, qui est copié dans l'image finale Python 3.13 servie par l'`api`.
- **Base** : image `postgres:17` avec version fixée, données dans un volume Docker nommé. La base n'est pas exposée hors du réseau Docker.
- **Un seul `worker`** : une seule copie à la fois, par règle écrite. Il prend en plus un verrou PostgreSQL (advisory lock) au démarrage. Une seconde copie qui ne l'obtient pas s'arrête, ce qui empêche les alertes en double.
- **Direct fiable** : `LISTEN/NOTIFY` sert seulement à réveiller, la base reste la seule source de vérité. Les messages ne portent qu'un identifiant (la limite est de 8000 octets). À chaque (re)connexion, le cockpit relit l'état par l'API, puis s'abonne au flux SSE. `EventSource` se reconnecte seul, et l'`api` envoie un message de maintien toutes les 15 secondes.
- **Caddy** : pas de mise en tampon (`flush_interval -1`) ni de compression sur la route SSE.
- **Heure** : la synchronisation d'horloge (chrony) est activée sur le VPS.
- **Sauvegardes dès le déploiement** : une copie `pg_dump` chaque nuit (7 jours gardés) sur le disque, plus l'option de sauvegarde automatique Hetzner. La copie hors site viendra avec la fonction « Sauvegardes quotidiennes ».
- **Registre** : GitHub Container Registry (GHCR), chaque image étiquetée par son commit. Revenir en arrière consiste à redéployer l'étiquette précédente, et les 10 dernières sont gardées.
- **Redémarrage** : `restart: unless-stopped` et un contrôle de santé (healthcheck) sur `postgres`, `api` et `worker`. Le `worker` signale sa santé par l'heure de sa dernière bougie reçue.
- **Secrets** : le job de déploiement écrit `.env` depuis les secrets GitHub dans un fichier temporaire, puis le remplace d'un seul coup (droits `600`).
- **Mémoire** : 2 Go de swap sur le VPS. Le rejeu et le backtest sur tout l'historique tournent comme une commande ponctuelle (`docker compose run`), jamais dans le `worker` permanent. Les images d'alerte sont générées une à la fois.

## Consequences

**Positive**:
- Coût prévu : environ 8 € de serveur, plus 1 € par mois pour le domaine, plus la source de prix et l'IA. Il reste environ 20 € de marge.
- Un seul langage côté serveur et une seule base : chaque session de Claude reprend vite le projet.
- Le moteur pur se teste et se rejoue sans serveur, ce qui est la condition pour valider les 10 trades.

**Negative / tradeoffs**:
- Le VPS est à entretenir (mises à jour du système, disque, sauvegardes). Il n'y a pas d'équipe d'hébergeur derrière comme sur une plateforme gérée.
- C'est un seul serveur, donc un point de panne unique. S'il tombe, il n'y a plus d'alertes jusqu'au redémarrage (la sonde externe te prévient).
- La base est sauvegardée chaque nuit, mais pas hors site tant que la fonction « Sauvegardes quotidiennes » n'est pas faite.
- 4 Go de mémoire, c'est juste pour tout faire tourner ensemble : les calculs lourds doivent rester des commandes ponctuelles.
- Deux écosystèmes (Python et Node pour le cockpit) : il y a deux jeux d'outils à tenir à jour.
- La mention TradingView est imposée par la licence de Lightweight Charts.

**Neutral**:
- Le fournisseur de prix reste interchangeable derrière `PriceFeed`. Le changer ne touche qu'un adaptateur.
- TimescaleDB, Redis ou une vraie file de tâches pourront s'ajouter si un besoin mesuré apparaît.

## Follow-up

- [ ] Choisir la source de prix (historique et direct) : `/architect source de prix` (scope n°2). Il faut des prix fidèles au flux OANDA de TradingView.
- [ ] Choisir la méthode de connexion : `/architect connexion` (scope n°6).
- [ ] Au déploiement : acheter le nom de domaine, créer le VPS et le bot Telegram, et vérifier le prix du CX23 au moment de commander (Hetzner a changé ses tarifs en juin 2026).
- [ ] Activer l'option de sauvegarde automatique du VPS à sa création (voir les règles d'exploitation).
- [ ] Agent Skills et serveurs MCP pour cette stack (FastAPI, SQLAlchemy, React, Tailwind, Lightweight Charts, PostgreSQL) : le trader a choisi « plus tard ». Il faut les chercher une fois l'accès réseau de l'environnement élargi, avant la première construction. Une skill FastAPI ou React donnerait les conventions à jour, et un serveur MCP PostgreSQL donnerait un accès direct à la base.
- [ ] Élargir l'accès réseau de l'environnement de développement (domaine de la source de prix et registre npm) avant de construire le squelette.

## Rationale

Le raisonnement et les options comparées sont dans [rationale.md](rationale.md).
