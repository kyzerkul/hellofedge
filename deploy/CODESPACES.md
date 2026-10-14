# Faire la recherche cTrader sans VPS : GitHub Codespaces

Un Codespace est un ordinateur Linux dans ton navigateur, fourni par GitHub, avec le dépôt déjà dedans. Sa connexion internet est normale : il peut joindre cTrader. Il sert à la **recherche** (mesure de l'écart avec OANDA, test du direct, chargement de l'historique). Il ne remplace pas le VPS : il s'éteint quand tu ne t'en sers plus, donc pas d'alertes 24 h/24.

Coût : gratuit dans le quota d'un compte personnel GitHub (environ 60 heures par mois sur une machine à 2 cœurs), sans carte bancaire. Pense à l'arrêter après usage (étape 5).

Tout est en lecture seule : aucune commande ne passe d'ordre.

---

## 1. Les secrets cTrader (une seule fois)

Les secrets Codespaces sont **séparés** des secrets du déploiement (environnement `production`). Il faut donc les créer ici aussi.

Sur github.com/kyzerkul/hellofedge : **Settings** › **Secrets and variables** › **Codespaces** › **New repository secret**. Crée ces cinq secrets, un par un (nom exact, valeur seule) :

| Nom | Valeur |
|---|---|
| `CTRADER_CLIENT_ID` | page **Credentials** de ton application sur openapi.ctrader.com |
| `CTRADER_CLIENT_SECRET` | page **Credentials** |
| `CTRADER_ACCOUNT_ID` | `48949650` (ton compte démo IC Markets) |
| `CTRADER_ACCESS_TOKEN` | « Access token » (portée **Account info**) |
| `CTRADER_REFRESH_TOKEN` | « Refresh token » du même jeton |

Jamais dans un fichier, jamais dans le chat.

## 2. Créer le Codespace

1. Sur la page du dépôt, clique sur le bouton vert **Code** › onglet **Codespaces**.
2. Clique sur **…** › **New with options…**
3. **Branch** : `claude/ecstatic-cray-ufenlh` (la configuration n'existe que sur cette branche pour l'instant).
4. **Machine type** : **2-core**.
5. **Create codespace**.

Le premier démarrage prend 3 à 5 minutes : il installe Python, les dépendances, une base PostgreSQL, et crée les tables. C'est prêt quand le terminal affiche **« Codespace prêt. »** S'il ne s'ouvre pas tout seul : menu ☰ › **Terminal** › **New Terminal**.

Si tu as ajouté les secrets **après** avoir créé le Codespace, reconstruis le : touche **F1**, tape `Rebuild Container`, Entrée.

## 3. Lancer la mesure

Dans le terminal :
```
bash .devcontainer/mesure.sh
```
Ça fait deux choses :
1. **Comptes** : la liste des comptes liés au jeton. Le compte `48949650` (démo) doit y être. C'est la preuve que la connexion à cTrader marche.
2. **Mesure** : pour chacun des 77 points lus sur tes captures OANDA, le prix que donne cTrader, l'écart, et la profondeur d'historique M1 disponible. Ça marche même week-end, marché fermé.

Le résultat est écrit dans **`exemples/mesure_sources.md`** (clique dessus dans la liste des fichiers à gauche).

## 4. Les autres commandes

```
bash .devcontainer/mesure.sh direct            # 30 minutes de direct (marché ouvert : du dimanche 23h au vendredi 22h, heure de Cotonou)
bash .devcontainer/mesure.sh direct 10         # pareil, sur 10 minutes
bash .devcontainer/mesure.sh historique        # charge les 7 derniers jours de bougies M1 en base
bash .devcontainer/mesure.sh historique 2026-08-17 2026-08-29   # les jours des 10 trades d'exemple
bash .devcontainer/mesure.sh comptes           # seulement la liste des comptes
```

Pour le direct, garde l'onglet ouvert pendant toute la durée : un Codespace inactif s'arrête au bout de 30 minutes.

## 5. Garder le rapport, puis arrêter

Pour que je puisse lire le rapport, enregistre le dans le dépôt, depuis le terminal du Codespace :
```
git add exemples/mesure_sources.md
git commit -m "Mesure cTrader depuis Codespaces"
git push
```
Puis dis-moi « la mesure est poussée ».

Ensuite, arrête le Codespace pour ne pas consommer ton quota : github.com/codespaces › **…** à côté du Codespace › **Stop codespace**. Tu pourras le relancer plus tard (les bougies chargées sont gardées tant que tu ne le supprimes pas).

---

## Si ça ne marche pas

| Message | Ce qu'il faut faire |
|---|---|
| `Arrêt : secrets Codespaces absents` | Étape 1, puis **Rebuild Container** (étape 2). |
| `cTrader refuse … CH_CLIENT_AUTH_FAILURE` | Client ID ou Client Secret faux : vérifie la page Credentials. |
| `cTrader refuse … CH_ACCESS_TOKEN_INVALID` ou `OA_AUTH_TOKEN_EXPIRED` | Jeton faux ou expiré : régénère le (Get token, portée Account info), mets à jour les deux secrets, puis Rebuild Container et `cd backend && uv run hellofedge feed ctrader-token --reseed`. |
| `le jeton cTrader expire dans moins d'un jour` | Même chose : nouveau jeton, puis `--reseed`. |
| `délai de connexion dépassé` | Réseau : relance la commande. Si ça persiste, dis-le moi. |

Les commandes ponctuelles ne renouvellent jamais le jeton (seul le `worker` le fera, sur le VPS). Un jeton tient environ 30 jours.
