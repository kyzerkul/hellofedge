# Review, claude/ecstatic-cray-ufenlh, 2026-09-29

**Reviewed by**: Sonnet 5.5 (author on a different model)
**Scope**: 83 files, branch vs origin/main (merge base 069d3a7)
**Verdict**: Changes requested

## Summary
La branche pose la pile (api, worker, migrations, cockpit) et la source de prix cTrader : client WebSocket en liste blanche, jeton renouvelé sous verrou, stockage M1 idempotent, boucle de flux avec coupures. Le code est propre, bien documenté et très testé. Deux problèmes réels demandent une correction avant la fusion : une erreur non prévue du fournisseur tue le worker sans ouvrir de coupure, et un `.env` copié depuis `.env.example` fait planter toute l'application.

## Major
### 🟠 Une erreur qui n'est pas une `FeedError` tue la boucle du flux, `backend/src/hellofedge/worker.py:216`
**Problem**: `FeedPump` ne rattrape que `FeedError`. `decode_bar` et `Candle.__post_init__` lèvent `ValueError` ou `KeyError` sur une bougie mal formée, `token.authorize_account` et `refresh_if_needed` lèvent `TokenMissing` (une `RuntimeError`) ou `KeyError` sur une réponse de renouvellement incomplète. Ces erreurs sortent de `_poll` et de `_maintain`, la tâche du flux se termine, et le worker s'arrête avec `PumpFailed`.
**Why it matters**: Docker relance le worker, qui reprend depuis la dernière bougie stockée, redemande la même bougie mauvaise et replante : boucle de redémarrage. Pendant ce temps aucune `feed_outage` n'est ouverte (seule la boucle le fait), donc la surveillance de panne future ne verra rien, et le trader n'a plus de prix. Une seule bougie invalide du fournisseur suffit.
**Suggested fix**: Convertir en `FeedError` (cause `erreur_api`) les erreurs de décodage et de forme des réponses dans l'adaptateur cTrader, et faire rattraper aussi `TokenMissing` et `TokenExpiringSoon` dans le pump (cause `auth`). Ajouter un test de pump avec un fournisseur qui renvoie une bougie invalide, et vérifier qu'une coupure s'ouvre au lieu d'un arrêt.

### 🟠 Un `.env` copié depuis `.env.example` plante l'api et le worker, `backend/src/hellofedge/config.py:78`
**Problem**: `.env.example` contient `CTRADER_ACCOUNT_ID=` vide. pydantic-settings lit la chaîne vide et échoue à la convertir en `int | None` (vérifié : `ValidationError int_parsing`). Comme `docker-compose.yml` charge `.env` par `env_file`, les deux processus échouent au démarrage. Aussi, `MARKET_HOLIDAYS=` vide écrase la valeur par défaut `12-25,01-01` : plus aucun jour férié, et `CTRADER_CLIENT_ID=` vide passe pour « renseigné ».
**Why it matters**: Le premier déploiement suivant la doc casse, et le message d'erreur (trace pydantic) ne dit rien au trader. Les jours fériés se perdent en silence, ce qui fausse les fausses coupures.
**Suggested fix**: Activer `env_ignore_empty=True` dans `SettingsConfigDict`, ou retirer les valeurs vides d'`.env.example` pour les réglages facultatifs. Ajouter un test de config avec des variables vides.

## Minor
### 🟡 Documentation OpenAPI ouverte sans connexion, `backend/src/hellofedge/api/app.py:36`
`/api/docs` et `/api/openapi.json` sont publics sur le domaine du trader alors que la garde des routes est fermée. Peu de fuite aujourd'hui, mais à désactiver en production (ou à protéger) avant d'ajouter de vraies routes.

### 🟡 Tâche créée sans référence, `backend/src/hellofedge/data/ctrader/client.py:572`
`create_task(self._ws.close())` n'est pas conservée : Python peut la ramasser avant la fin. Garder la référence dans un ensemble.

### 🟡 Heure `now` figée avant l'attente du verrou, `backend/src/hellofedge/data/ctrader/token.py:244`
`now` est pris avant `token_lock`, qui peut attendre (un `--reseed`). La date de fin du jeton renouvelé (`now + expiresIn`) est alors légèrement trop tôt. Sans gravité (on renouvelle plus tôt), mais relire l'horloge sous le verrou serait plus juste.

### 🟡 Réglages absents : trace brute, `backend/src/hellofedge/cli.py:210`
`get_settings()` est appelé hors du `try` : sans `DATABASE_URL`, la commande affiche une trace pydantic au lieu du message « Arrêt : ... » des autres erreurs.

### 🟡 Tests de base non exécutés ici
57 tests demandent `TEST_DATABASE_URL` et ont été sautés (156 réussis). Le stockage, les coupures, les migrations et le jeton reposent surtout sur eux : à faire tourner sur une vraie base avant la fusion.

### 🟡 `--forwarded-allow-ips "*"`, `Dockerfile:136`
Acceptable tant que l'api n'est joignable que par Caddy (aucun port publié), mais l'IP cliente devient falsifiable si quelqu'un publie le port 8000. Limiter au réseau Docker de Caddy.

## Nits
- ⚪ `backend/src/hellofedge/cli.py:29`, imports non triés (`data.ctrader.token` avant `data`).
- ⚪ `backend/src/hellofedge/data/ctrader/feed.py:29`, `token` importé avant `protocol` : ordre alphabétique cassé.
- ⚪ `backend/src/hellofedge/api/auth.py:20`, chaîne de doc après `SessionDep` (inutile) ; la garde fermée rend `/api/feed/status` inutilisable tant que la Connexion n'existe pas, c'est voulu mais à noter dans le scope.

## Strengths
- Lecture seule tenue de bout en bout : liste blanche de messages dans le client, plus un test AST qui interdit tout mot d'ordre dans `data/`.
- Jeton bien pensé : écrit en base avant usage, verrou dédié, nouvel essai après refus, `__repr__` sans secret, journaux sans contenu de message.
- Stockage M1 idempotent et honnête : jamais réécrit, différences dans `candle_revision`, prix en `Decimal` NUMERIC(10,3), contraintes en base (minute pleine, OHLC cohérent, une seule coupure ouverte).
- Fonctions de temps pures et injectables (horloge, sommeil), UTC partout, calendrier de marché ancré sur New York.

## Test coverage
Large : 156 tests passés localement (client, flux, jeton, pump, worker, mesure, migrations, garde lecture seule) et 6 tests Vitest. Manque : aucun test des erreurs non `FeedError` dans le pump ni du décodage d'une bougie invalide (majeur 1), ni des variables d'environnement vides (majeur 2). Les tests avec base sont sautés sans `TEST_DATABASE_URL`.
