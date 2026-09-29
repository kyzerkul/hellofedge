# Review, claude/ecstatic-cray-ufenlh, 2026-09-29 (deuxième passe)

**Reviewed by**: Sonnet (author on Opus)
**Scope**: 210 fichiers (dont 70 dans backend, deploy, Dockerfile, .env.example), branche contre origin/main (merge base 069d3a7). Deuxième revue, après les commits 670ec99 et 3fc6133.
**Verdict**: Approve with nits

## Summary
Les deux majeurs de la première revue sont réellement corrigés, avec des tests qui échouaient sur l'ancien code. Les deux nouveaux commits (journal des essais manqués, délai de connexion à part, attente plafonnée à l'ouverture de la coupure) sont corrects et testés. La suite complète passe sur une vraie base : 230 réussis, 0 sauté. Il reste quelques mineurs, dont la plupart viennent de la première revue.

## Suivi des deux majeurs précédents

### Majeur 1 (erreur non `FeedError` qui tue la boucle) : résolu pour le cas cité
- `feed.py` `_load_symbol` et `_range` convertissent `KeyError`, `TypeError`, `ValueError` en `FeedUnavailable` (cause `erreur_api`). `decode_bar` et `Candle.__post_init__` sont donc couverts (test `test_ctrader_feed.py:465` à `517`, avec prix illisible).
- `token.py` : une réponse de renouvellement incomplète devient `FeedUnavailable` (test `test_ctrader_token.py:402`). `TokenMissing` et `TokenExpiringSoon` sont maintenant des `FeedAuthError` (test ligne 423), et `test_pump.py:452` vérifie qu'une coupure `auth` s'ouvre.
- Chemins qui peuvent encore sortir du pump, jugés hors périmètre ou mineurs :
  1. Erreurs de base (`store_candles`, `outages.open_outage`, `last_ts_open`) : elles arrêtent le worker. C'est acceptable, une base absente ne permet pas d'écrire une coupure de toute façon, et Docker relance. Hors périmètre.
  2. Forme inattendue de la réponse : voir le mineur « AttributeError » plus bas. Petit trou restant.
  3. `MessageNotAllowed` (garde lecture seule) n'est pas une `FeedError` : c'est voulu, c'est une erreur de programmation qui doit être bruyante.

### Majeur 2 (`.env` vide plante la config) : résolu
`env_ignore_empty=True` dans `config.py:16`. Les variables vides comptent comme absentes, `MARKET_HOLIDAYS` garde sa valeur par défaut, `DATABASE_URL` vide est refusée avec un message clair. Test dans `test_config.py` (dont `MARKET_HOLIDAYS` vide, ligne 88).

## Revue des deux nouveaux commits
- **670ec99** : le calcul `wake` plafonné à `silence_since + SILENCE_LIMIT` est juste. Il ne s'applique qu'hors rollover et sans coupure ouverte. Si `wake` dépasse la limite d'attente, `next_try_at` est bien posé quand il y a eu échec. Le journal d'un essai manqué porte maintenant `minute` et `demande`. Le `open_timeout` séparé (5 s) n'affecte que `connect`. Aucun bug trouvé.
- **3fc6133** : les `except (KeyError, TypeError, ValueError)` ne masquent pas les `FeedError` déjà levées (elles ne sont pas de ces types). Le message inclut `str(exc)` pour la bougie : il vient du fournisseur, sans secret, acceptable.

## Minor
### 🟡 `AttributeError` non rattrapée sur une réponse de forme inattendue, `backend/src/hellofedge/data/ctrader/feed.py:145`
**Problem**: les conversions ne couvrent pas `AttributeError`. Si `payload` n'est pas un dictionnaire (`_check_response` fait `frame.get("payload") or {}` sans vérifier le type), ou si une bougie est autre chose qu'un objet et qu'on appelle `.get`, l'erreur sort du pump.
**Why it matters**: même effet que l'ancien majeur (arrêt du worker), mais seulement si cTrader renvoie un JSON de forme absurde. Très improbable.
**Suggested fix**: vérifier que `payload` est un dictionnaire dans `_check_response` (sinon `FeedUnavailable` `erreur_api`), ou ajouter `AttributeError` aux `except`.

### 🟡 Documentation OpenAPI ouverte sans connexion, `backend/src/hellofedge/api/app.py:35`
Still present. `/api/docs` et `/api/openapi.json` sont publics alors que la garde est fermée. À désactiver en production avant d'ajouter de vraies routes.

### 🟡 Tâche créée sans référence, `backend/src/hellofedge/data/ctrader/client.py:278`
Still present. `create_task(self._ws.close())` n'est pas conservée. Garder la référence.

### 🟡 Heure `now` figée avant l'attente du verrou, `backend/src/hellofedge/data/ctrader/token.py`
Still present. `now` est pris avant `token_lock` : la fin du jeton renouvelé peut être un peu trop tôt. Sans gravité.

### 🟡 Réglages absents : trace brute, `backend/src/hellofedge/cli.py:210`
Still present. `get_settings()` est appelé hors du `try` : sans `DATABASE_URL`, trace pydantic au lieu du message « Arrêt : ... ».

### 🟡 `--forwarded-allow-ips "*"`, `Dockerfile:36`
Still present. Acceptable tant que seul Caddy joint l'api, à limiter au réseau Docker de Caddy.

### 🟡 Test de non régression du plafond d'attente couvre un seul scénario, `backend/tests/test_pump.py`
Le plafond `wake = opens_at` est testé sur le cas simple. Le cas « rollover en cours » et le cas « coupure déjà ouverte » (où le plafond ne doit pas s'appliquer) ne sont pas testés directement. Ajouter deux cas courts.

## Nits
- ⚪ `backend/src/hellofedge/cli.py:29` et `backend/src/hellofedge/data/ctrader/feed.py:29`, ordre des imports (still present).
- ⚪ `backend/src/hellofedge/api/auth.py:20`, chaîne de doc après `SessionDep` inutile (still present). La garde fermée est un choix voulu.
- ⚪ `.env.example`, `CTRADER_CLIENT_ID=` vide passe désormais pour absent : bien. Un commentaire « laisser vide = valeur par défaut » aiderait le trader.

## Strengths
- Lecture seule tenue de bout en bout : liste blanche de messages dans le client et test AST interdisant les mots d'ordre dans `data/`.
- Les correctifs sont accompagnés de tests de non régression précis, y compris le lien de classe `TokenMissing` vers `FeedAuthError`.
- Jeton bien pensé (écrit en base avant usage, verrou dédié, journaux sans secret), stockage M1 idempotent, temps pur et injectable, UTC partout.

## Test coverage
230 tests réussis sur la vraie base de test (`TEST_DATABASE_URL`), aucun sauté : client, flux, jeton, pump, worker, mesure, migrations, config, garde lecture seule. Les nouveaux comportements (bougie illisible, symboles illisibles, renouvellement incomplet, jeton absent en coupure `auth`, variables vides, journal d'essai manqué, délai de connexion, plafond d'attente) sont tous couverts. Petit manque : cas limites du plafond d'attente (rollover, coupure déjà ouverte) et réponse de forme non dictionnaire.
