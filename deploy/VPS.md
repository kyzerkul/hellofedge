# Mettre Hellofedge en ligne : le guide pas à pas

Ce guide te mène de « rien » à « le `worker` reçoit les prix cTrader sur le VPS ». Tout ce qui pouvait être préparé l'est déjà dans le dépôt. Il reste les étapes qui demandent ton compte, ta carte ou ta validation : elles sont marquées **Toi**. Les autres, je peux les faire avec toi.

Décisions de départ : spec [0001](../docs/specs/0001-stack-architecture/index.md) (VPS Hetzner, Docker Compose, GitHub Actions) et spec [0002](../docs/specs/0002-source-de-prix/index.md) (cTrader).

Aucun secret ne doit passer dans le chat : ils vont seulement dans les secrets GitHub.

---

## Vue d'ensemble

| # | Étape | Qui | Durée |
|---|---|---|---|
| 1 | Attendre la validation de l'application cTrader | Spotware | quelques heures à quelques jours |
| 2 | Acheter le nom de domaine | Toi | 10 min |
| 3 | Créer le VPS Hetzner | Toi | 15 min |
| 4 | Préparer le VPS (`provision.sh`) | Toi, une commande | 5 min |
| 5 | Pointer le domaine vers le VPS | Toi | 5 min, puis jusqu'à 1 h |
| 6 | Créer les secrets GitHub | Toi | 15 min |
| 7 | Premier déploiement | Automatique à la fusion sur `main` | 10 min |
| 8 | Après la validation cTrader : identifiants, jeton, compte | Toi, puis moi | 20 min |
| 9 | Mesure, test du direct, historique | Nous deux | 1 h, plus une journée de mesure |

Les étapes 2 à 7 n'attendent pas cTrader : tu peux les faire tout de suite.

---

## 1. L'application cTrader (déjà envoyée)

Ton application **Hell Of Edge** est « Submitted » sur openapi.ctrader.com. Spotware envoie un e‑mail quand elle passe à « Active ». Rien à faire d'ici là. La suite est à l'étape 8.

## 2. Le nom de domaine (**Toi**)

Achète un nom de domaine chez un registraire (OVH, Gandi, Namecheap, Cloudflare…), environ 10 à 15 € par an. Garde de côté l'accès à sa zone DNS : tu y ajouteras une ligne à l'étape 5.

## 3. Le VPS Hetzner (**Toi**)

1. Crée un compte sur console.hetzner.cloud et un projet `hellofedge`.
2. **Avant de créer le serveur**, prépare la clé SSH du déploiement, sur ton ordinateur :
   ```
   ssh-keygen -t ed25519 -f hellofedge_deploy -C deploy@hellofedge -N ""
   ```
   Tu obtiens deux fichiers : `hellofedge_deploy` (clé privée, secret, elle ira dans GitHub) et `hellofedge_deploy.pub` (clé publique). Prépare aussi ta propre clé SSH pour te connecter en root, si tu n'en as pas.
3. **Add Server** :
   - Localisation : Allemagne (Falkenstein ou Nuremberg).
   - Image : **Ubuntu 24.04**.
   - Type : **CX23** (2 vCPU, 4 Go). Vérifie le prix affiché, Hetzner a changé ses tarifs en juin 2026 : on vise environ 8 € par mois.
   - SSH keys : ajoute **ta** clé publique (pour root).
   - **Backups : coche l'option** (sauvegarde automatique Hetzner, environ 20 % du prix du serveur).
   - Nom : `hellofedge`.
4. Note l'adresse IPv4 du serveur.

## 4. Préparer le VPS (**Toi**, une seule commande)

Depuis ton ordinateur :
```
scp deploy/provision.sh root@<IP>:/root/
ssh root@<IP> "bash /root/provision.sh '$(cat hellofedge_deploy.pub)'"
```
Le script installe les mises à jour automatiques, chrony (heure exacte), le pare feu (22, 80, 443 seulement), 2 Go de swap, Docker, l'utilisateur `deploy` (clé SSH seule), le dossier `/opt/hellofedge` et la sauvegarde de la base chaque nuit (7 jours gardés). On peut le relancer sans risque. Il finit par « VPS prêt ».

Puis récupère l'empreinte du serveur, pour que GitHub soit sûr de parler au bon serveur :
```
ssh-keyscan -t ed25519 <IP>
```
Garde la ligne affichée : c'est le secret `VPS_KNOWN_HOSTS`.

## 5. Pointer le domaine (**Toi**)

Dans la zone DNS du domaine, ajoute un enregistrement **A** : nom `@` (ou un sous domaine comme `app`), valeur `<IP>`. Le certificat HTTPS sera créé tout seul par Caddy au premier démarrage, une fois le DNS propagé.

## 6. Les secrets GitHub (**Toi**)

Sur github.com/kyzerkul/hellofedge : **Settings > Environments > New environment** `production`, puis ajoute ces secrets dans l'environnement `production` :

| Secret | Valeur |
|---|---|
| `VPS_HOST` | l'IP du serveur |
| `VPS_KNOWN_HOSTS` | la ligne de `ssh-keyscan` (étape 4) |
| `VPS_SSH_KEY` | tout le contenu du fichier `hellofedge_deploy` (clé privée) |
| `POSTGRES_PASSWORD` | un long mot de passe au hasard (par exemple `openssl rand -base64 32`) |
| `HELLOFEDGE_DOMAIN` | le domaine, par exemple `app.mondomaine.fr` |
| `CTRADER_CLIENT_ID`, `CTRADER_CLIENT_SECRET`, `CTRADER_ACCESS_TOKEN`, `CTRADER_REFRESH_TOKEN`, `CTRADER_ACCOUNT_ID` | à l'étape 8, après la validation cTrader |

Sans `VPS_HOST`, le workflow fait seulement les tests : rien ne part vers un serveur.

## 7. Premier déploiement (automatique)

Le workflow `.github/workflows/ci-deploy.yml` tourne à chaque push. Sur `main`, après les tests, il construit l'image, la publie sur `ghcr.io/kyzerkul/hellofedge`, copie les fichiers de `deploy/` sur le VPS, écrit le `.env` depuis les secrets (droits 600), lance la migration, redémarre les services, puis vérifie que `https://<domaine>/api/health` répond.

Il suffit donc de fusionner la branche de travail dans `main` (une pull request que tu valides). Ensuite, sur le VPS :
```
ssh deploy@<IP>
cd /opt/hellofedge && docker compose ps
```
Tu dois voir `api`, `worker` et `postgres` en « healthy », et `caddy` en « running ». Tant que les secrets cTrader manquent, le `worker` tourne sans flux et le dit dans son journal : c'est normal.

## 8. Après la validation de cTrader (**Toi**, puis moi)

1. Sur openapi.ctrader.com, ouvre **Credentials** : copie le *Client ID* et le *Client Secret* dans les secrets `CTRADER_CLIENT_ID` et `CTRADER_CLIENT_SECRET`.
2. Ouvre **Sandbox** et génère un jeton avec la seule portée **`accounts`** (lecture seule, jamais `trading`), connecté à ton compte démo IC Markets. Copie *access token* et *refresh token* dans `CTRADER_ACCESS_TOKEN` et `CTRADER_REFRESH_TOKEN`.
3. Relance le déploiement (Actions > ci-deploy > Run workflow sur `main`), puis trouve le numéro du compte :
   ```
   cd /opt/hellofedge && docker compose run --rm tools hellofedge feed ctrader-accounts
   ```
   Copie le numéro du compte **démo IC Markets** dans le secret `CTRADER_ACCOUNT_ID`, et relance le déploiement une dernière fois.
4. Dans l'heure, le `worker` renouvelle le jeton et reçoit sa vraie date de fin :
   ```
   docker compose logs worker | grep "jeton cTrader renouvelé"
   ```

## 9. Mesure et validation (nous deux)

Depuis `/opt/hellofedge` sur le VPS :
```
docker compose run --rm tools hellofedge feed compare          # écart avec OANDA, profondeur d'historique
docker compose run --rm tools hellofedge feed live-test        # 30 minutes de direct, marché ouvert
docker compose run --rm tools hellofedge feed backfill         # historique disponible, jusqu'à 2 ans
```
Le rapport est écrit dans `/opt/hellofedge/exemples/mesure_sources.md`. Rapatrie le dans le dépôt :
```
scp deploy@<IP>:/opt/hellofedge/exemples/mesure_sources.md exemples/
```
Puis `/check verify source de prix` pour fermer la fonction n°2 (avec ta validation de `exemples/reference_oanda.csv`).

---

## Au quotidien

- État : `docker compose ps` ; journaux : `docker compose logs -f worker`.
- Sauvegardes : `/opt/hellofedge/backups/` (une par nuit, 7 jours). Restaurer : voir l'en tête de `backup.sh`.
- Revenir à la version précédente : relancer le workflow sur le commit d'avant.
- Si le jeton cTrader est perdu ou refusé : régénère le dans le Sandbox, mets à jour les deux secrets, redéploie, puis `docker compose run --rm tools hellofedge feed ctrader-token --reseed`.
