# 0001. Stack et architecture : raisonnement

## Context

Hellofedge doit tourner en permanence, parce que les bougies USD/JPY arrivent jour et nuit et que les alertes doivent partir même quand le trader dort ou n'a pas le cockpit ouvert. Il y a un seul utilisateur, au Bénin, qui trade sur mobile comme sur ordinateur. Le budget total (serveur, données, IA) est de moins de 30 € par mois (basis: scope, cadre du MVP).

Le trader ne code pas. C'est Claude qui construit et maintient, session après session, et le trader valide. La stack doit donc être connue, stable, bien documentée, avec peu de pièces, pour qu'une nouvelle session reprenne sans tout redécouvrir (basis: boring technology).

Le cœur de la valeur est un moteur de détection SMC déterministe, qui doit être rejoué à l'identique sur l'historique pour être validé sur 10 trades réels avant qu'on lui fasse confiance en direct (basis: `docs/PLAN_DE_DEVELOPPEMENT.md` phase 1, `.claude/rules/moteur-smc.md`). Les données sont petites (une seule paire, environ 3 millions de bougies M1 sur plusieurs années), mais le flux direct doit rester connecté en continu.

OANDA n'est pas disponible (compte impossible à créer). La source de prix doit donc pouvoir changer sans toucher au reste.

## Options considered

### Option 1 : monolithe Python + React statique + PostgreSQL sur un VPS (Docker Compose)

Un seul code Python (FastAPI) en deux processus, PostgreSQL et Caddy dans Docker Compose sur un VPS Hetzner, avec le cockpit React construit en fichiers statiques.

**Pros**:
- Le coût le plus bas (environ 8 € par mois) pour une machine qui tient tout (basis: tarifs Hetzner 2026).
- Python est le meilleur outillage pour le moteur, le rejeu et l'IA.
- Pas de limite de durée ni de mise en veille : le flux reste connecté.

**Cons**:
- Le serveur est à entretenir soi même, et c'est un point de panne unique.

### Option 2 : tout en TypeScript (Next.js) sur une plateforme gérée + base gérée

Next.js pour l'interface et l'API, un service Node pour le flux, et PostgreSQL géré (type Render).

**Pros**:
- Un seul langage partout, et moins d'entretien du système.

**Cons**:
- L'outillage d'analyse de séries de prix est bien plus pauvre qu'en Python.
- Il faut environ 25 à 30 $ par mois avec la base gérée, soit presque tout le budget.

### Option 3 : Django + HTMX sur une plateforme gérée

Django (admin et connexion intégrés), des pages rendues par le serveur, sur Render.

**Pros**:
- Beaucoup de choses sont fournies (admin, connexion, formulaires).

**Cons**:
- Il est moins naturel pour le temps réel et un graphique riche au doigt.
- Il y a le même coût de plateforme gérée que l'option 2.

### Option 4 : fonctions sans serveur + base hébergée

Des fonctions à la demande pour l'API, et une base PostgreSQL hébergée.

**Pros**:
- On ne paie presque rien quand rien ne tourne.

**Cons**:
- Il est incompatible avec un flux de prix connecté en continu (limite de durée, démarrages à froid) (basis: serverless for stateful workloads).

## Rationale

Les forces décisives sont le flux continu, le budget serré et un moteur qui doit être rejoué à l'identique. Le flux continu élimine l'option 4. Le budget rend les plateformes gérées (options 2 et 3) trop chères pour ce qu'elles apportent à un seul utilisateur. Le moteur de détection et son rejeu sont bien mieux servis par Python et pandas que par TypeScript.

Le monolithe en deux processus garde la simplicité d'un seul code tout en isolant ce qui compte le plus : les alertes ne dépendent jamais du cockpit (basis: monolith first). PostgreSQL `LISTEN/NOTIFY` suffit pour pousser le direct vers le cockpit, sans Redis. Un moteur pur, sans réseau ni horloge, garantit que le rejeu et le direct donnent le même résultat.

Le prix à payer est l'entretien d'un VPS et un point de panne unique. On le compense par la sonde externe, le déploiement automatisé et rejouable, et les sauvegardes. C'est acceptable pour un outil personnel, et bien moins coûteux que les alternatives.

## References

**Project sources**:
- `docs/scope/scope.md` : cadre du MVP, budget, approche Tracer Bullet, rigueur Beta.
- `AGENTS.md` : UTC partout, M3 reconstruit depuis le M1, aucun ordre de trading, pas de secrets dans le code.
- `docs/PLAN_DE_DEVELOPPEMENT.md` et `.claude/rules/moteur-smc.md` : moteur déterministe validé sur les 10 trades.
- `docs/.agent-cache/research/stack-hellofedge.md` : relevé des tarifs et des sources de prix (septembre 2026).

**Practices & standards**:
- Monolith first : extraire des services seulement face à un besoin mesuré.
- Boring technology : outils éprouvés, grande communauté.
- Serverless for stateful workloads : pas de fonctions à la demande pour une connexion permanente.
- Cœur fonctionnel pur (functional core, imperative shell) : le moteur sans effets de bord, testable et rejouable.

**Links** (vérifiés sur le web pendant l'étude) :
- Hetzner, ajustement des prix de juin 2026 : https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/
- Dukascopy, données historiques : https://www.dukascopy.com/swiss/english/marketwatch/historical/
- Twelve Data, forex : https://twelvedata.com/exchanges/physical_currency
