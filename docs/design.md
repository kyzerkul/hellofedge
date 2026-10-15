---
name: Hellofedge, cockpit USD/JPY
source: spec 0003 (docs/specs/0003-design-system/index.md), à partir du prototype docs/prototype/hellofedge-cockpit.html
tokens: frontend/src/design/theme.css
---

# Design system du cockpit

Ce document décrit le langage visuel du cockpit. Les valeurs vivent dans `frontend/src/design/theme.css`, la seule source. Ce fichier en est le miroir exact : un test (`frontend/src/design/theme.test.ts`) échoue si une valeur diffère, si un jeton du thème manque ici, ou si une ligne d'ici n'existe pas dans le thème. Pour changer une valeur, change les deux dans le même commit.

La page `/vitrine` du cockpit montre tout ce qui est décrit ici, sur des données factices.

## Caractère

Un poste de travail calme, sombre et précis, pensé pour de longues heures devant le graphique. Le fond est une encre indigo, les surfaces sont des cartes à peine plus claires, les chiffres sont en chasse fixe et s'alignent en colonne. Rien ne brille sans raison : la couleur vive est réservée à ce qui compte pour le trade.

## Mandat

- **Ton code couleur TradingView est la règle de toute l'appli** : rouge = liquidité, bleu = IPA, blanc = extrêmes, jaune = objectif. Ces quatre couleurs ne servent à rien d'autre, nulle part.
- **Jamais une information portée par la couleur seule** : toujours un mot, et une icône ou un triangle quand il y a un sens.
- **Une couleur de niveau ou de session ne colore jamais un texte.** Une puce de niveau a un texte clair, avec une pastille et une bordure de la couleur du niveau.
- **Compact à la souris, 44 px au doigt.**
- **Thème sombre uniquement.**
- **Rien depuis un domaine tiers** : les polices sont livrées avec le cockpit.

## Couleurs

Les quatre couleurs de niveaux sont celles de TradingView, lues dans les pixels des captures du trader. Aucune autre couleur du thème n'a l'une de ces valeurs.

| Jeton | Valeur | Rôle |
|---|---|---|
| `--color-ink` | `#0C111C` | fond de la page et du graphique ; texte sur l'accent et sur l'orange |
| `--color-panel` | `#121A29` | fond des cartes |
| `--color-panel-2` | `#172136` | fond des éléments dans une carte, survol |
| `--color-line` | `#22304A` | bordures décoratives, fond appuyé |
| `--color-line-soft` | `#1B263B` | séparateurs discrets, grille du graphique |
| `--color-text` | `#E4E8F1` | texte principal |
| `--color-muted` | `#8A95AD` | texte secondaire, bord des champs et des cases |
| `--color-accent` | `#B39DFF` | focus, sélection, bouton principal |
| `--color-accent-soft` | `rgb(179 157 255 / 0.14)` | fond d'un élément sélectionné |
| `--color-buy` | `#3DBFA3` | achat ; état « en direct » |
| `--color-sell` | `#E05FB4` | vente |
| `--color-danger` | `#FF8A3D` | erreur, flux coupé |
| `--color-level-liquidity` | `#F23645` | liquidité (réservé) |
| `--color-level-ipa` | `#2962FF` | IPA (réservé) |
| `--color-level-extreme` | `#FFFFFF` | plus haut ou plus bas d'une session précédente (réservé) |
| `--color-level-target` | `#FFEB3B` | objectif (réservé) |
| `--color-candle-up` | `#B8C2D6` | bougie haussière (corps, mèche, bord) |
| `--color-candle-down` | `#5B6782` | bougie baissière (sur le fond `ink` seulement) |
| `--color-session-asia` | `#7B6CF0` | Tokyo (bande à 12 %) |
| `--color-session-frankfurt` | `#A56A8C` | Francfort |
| `--color-session-london` | `#3F8FD1` | Londres |
| `--color-session-trap` | `#6B7489` | heure piège |
| `--color-session-newyork` | `#D98C3E` | New York |
| `--color-session-londonclose` | `#4FA58A` | clôture de Londres |

La palette par défaut de Tailwind est retirée (`--color-*: initial;`) : `bg-red-500` ou `text-white` n'existent pas. Pour une couleur, utilise un jeton (`bg-panel`, `text-muted`, `border-line`). Le futur graphique lit les couleurs à l'exécution avec `cssToken('--color-…')` (`frontend/src/design/format.ts`).

## Typographie

| Jeton | Valeur | Usage |
|---|---|---|
| `--font-display` | `"Zen Kaku Gothic New", "Hiragino Sans", "Segoe UI", system-ui, sans-serif` | titres (graisses 500, 700) |
| `--font-sans` | `"IBM Plex Sans", "Segoe UI", system-ui, sans-serif` | texte courant (400, 500, 600) |
| `--font-mono` | `"JetBrains Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace` | prix, heures, chiffres (400, 500, 600, `tabular-nums`) |

Les polices viennent de Fontsource, sous ensemble `latin` (accents français et `¥` compris), importées dans `frontend/src/index.css`. Si elles manquent, la pile de secours prend le relais.

| Jeton | Valeur | Usage |
|---|---|---|
| `--text-xs` | `0.75rem` | 12 px, notes, légendes |
| `--text-sm` | `0.8125rem` | 13 px, boutons, onglets, tableaux |
| `--text-base` | `0.875rem` | 14 px, corps à la souris (15 px sous `pointer: coarse`) |
| `--text-md` | `1rem` | 16 px, champs de saisie, toujours (évite le zoom du téléphone) |
| `--text-lg` | `1.125rem` | 18 px, titre de page |
| `--text-xl` | `1.375rem` | 22 px, prix principal |
| `--text-2xl` | `1.75rem` | 28 px, grands titres de la vitrine |

Interligne 1,45 partout (porté par le corps de la page). Les tailles par défaut de Tailwind sont retirées (`--text-*: initial;`). L'étiquette (`text-label`) fait 11 px, en majuscules, graisse 600, espacement 0,09em, en `muted`.

## Espacements, rayons, durées

Espacements : l'échelle de Tailwind, au pas de 4 px (`p-3` = 12 px, `gap-4` = 16 px). Les cartes ont un espace intérieur de 14 à 16 px et sont séparées de 14 à 16 px.

| Jeton | Valeur | Usage |
|---|---|---|
| `--radius-sm` | `4px` | petites pastilles, cases à cocher |
| `--radius-md` | `7px` | boutons, champs |
| `--radius-lg` | `10px` | cartes |

`rounded-full` reste fourni par Tailwind (puces, pastilles).

| Jeton | Valeur | Usage |
|---|---|---|
| `--duration-fast` | `120ms` | survol, focus (`duration-(--duration-fast)`) |
| `--duration-base` | `200ms` | ouverture d'une liste |

Animations : `animate-live-pulse`, le halo de la pastille « en direct » (1,6 s, en boucle) ; `animate-list-open`, l'ouverture d'une liste de choix (200 ms, la durée `--duration-base`).

**Mouvement réduit** : quand le système demande moins d'animations (`prefers-reduced-motion: reduce`), une règle globale de `theme.css` coupe toutes les animations et transitions, y compris celles de React Aria.

## Tailles tactiles

- À la souris (`pointer-fine`) : chaque élément interactif fait au moins 32 px de haut.
- Au doigt (`pointer-coarse`) : chaque zone touchable fait au moins 44 × 44 px, même si la partie visible est plus petite (la case à cocher visible fait 20 px, sa zone touchable 44).
- Rien n'est accessible seulement au survol.
- Points d'arrêt : ceux de Tailwind (640, 768, 1024, 1280 px). La mise en page du téléphone viendra avec la fonction n°14.

## États communs des composants interactifs

| État | Rendu |
|---|---|
| normal | fond `panel-2`, bord `line`, texte `text` (bouton principal : fond `accent`, texte `ink`) |
| survol | bord `muted` (principal : opacité 90 %) |
| appuyé | fond `line`, texte `text` |
| focus clavier | contour 2 px `accent`, décalé de 2 px ; jamais au clic ni au toucher, sauf dans un champ de saisie |
| sélectionné | fond `accent-soft`, texte `accent` |
| désactivé | opacité 50 %, curseur interdit (exception voulue au contraste) |
| erreur | bord `danger`, icône `TriangleAlert` et message |
| en cours | `Button` seulement : indicateur qui tourne, libellé gardé, action bloquée |

Les composants posent ces états avec les variantes `demo-hovered`, `demo-pressed` et `demo-focus-visible` de `theme.css`. Elles suivent les attributs de React Aria (`data-hovered`…) ou l'attribut `data-demo`, que la vitrine pose pour figer un état.

## Styles de niveaux

- Niveau vivant : trait plein de 2 px, dans sa couleur.
- Niveau pris : pointillés de 1 px, opacité 50 %, et toujours le mot « pris » (exception voulue au contraste).
- Chaque ligne porte son nom à son extrémité droite : « Liquidité », « Liquidité · pris », « IPA », « Extrême », « Objectif ». Le nom est écrit en `text`, jamais dans la couleur du niveau.
- Bougies grises : haussière `candle-up`, baissière `candle-down`.
- Bandes de session à 12 % d'opacité, nom de la session en `text`.
- Sens d'un setup : toujours un triangle et le mot. Achat : triangle vers le haut, sarcelle. Vente : triangle vers le bas, magenta.

## Contraste

Texte : au moins 4,5:1 sur son fond. Élément graphique utile (trait de niveau, bougie, anneau de focus, bord d'un champ ou d'une case) : au moins 3:1. Le test `theme.test.ts` recalcule chaque rapport à partir du thème (en composant un fond transparent sur son support) et échoue sous le seuil, si un rapport écrit ici est faux, ou si une paire obligatoire manque.

| Premier plan | Fond | Type | Seuil | Rapport |
|---|---|---|---|---|
| `text` | `ink` | texte | 4,5 | 15,38 |
| `text` | `panel` | texte | 4,5 | 14,19 |
| `text` | `panel-2` | texte | 4,5 | 13,09 |
| `muted` | `ink` | texte | 4,5 | 6,28 |
| `muted` | `panel` | texte | 4,5 | 5,79 |
| `muted` | `panel-2` | texte | 4,5 | 5,34 |
| `accent` | `ink` | texte | 4,5 | 8,25 |
| `accent` | `panel` | texte | 4,5 | 7,62 |
| `accent` | `panel-2` | texte | 4,5 | 7,03 |
| `buy` | `ink` | texte | 4,5 | 8,25 |
| `buy` | `panel` | texte | 4,5 | 7,61 |
| `buy` | `panel-2` | texte | 4,5 | 7,02 |
| `sell` | `ink` | texte | 4,5 | 5,81 |
| `sell` | `panel` | texte | 4,5 | 5,36 |
| `sell` | `panel-2` | texte | 4,5 | 4,95 |
| `danger` | `ink` | texte | 4,5 | 8,05 |
| `danger` | `panel` | texte | 4,5 | 7,43 |
| `danger` | `panel-2` | texte | 4,5 | 6,85 |
| `text` | `accent-soft` sur `panel` | texte | 4,5 | 11,05 |
| `accent` | `accent-soft` sur `panel` | texte | 4,5 | 5,93 |
| `ink` | `accent` | texte | 4,5 | 8,25 |
| `ink` | `danger` | texte | 4,5 | 8,05 |
| `level-liquidity` | `ink` | graphique | 3 | 4,84 |
| `level-liquidity` | `panel-2` | graphique | 3 | 4,12 |
| `level-ipa` | `ink` | graphique | 3 | 3,85 |
| `level-ipa` | `panel-2` | graphique | 3 | 3,28 |
| `level-extreme` | `ink` | graphique | 3 | 18,88 |
| `level-extreme` | `panel-2` | graphique | 3 | 16,06 |
| `level-target` | `ink` | graphique | 3 | 15,46 |
| `level-target` | `panel-2` | graphique | 3 | 13,16 |
| `candle-up` | `ink` | graphique | 3 | 10,54 |
| `candle-down` | `ink` | graphique | 3 | 3,33 |
| `muted` | `panel` | graphique | 3 | 5,79 |
| `muted` | `panel-2` | graphique | 3 | 5,34 |
| `accent` | `ink` | graphique | 3 | 8,25 |
| `accent` | `panel` | graphique | 3 | 7,62 |
| `accent` | `panel-2` | graphique | 3 | 7,03 |

**Combinaisons interdites** (jamais dans le tableau ci dessus, jamais dans le code) :
- `muted` sur `line` (4,39) : pas de texte secondaire sur un fond appuyé.
- `sell` sur un fond teinté de `sell`.
- `candle-down` sur `panel-2` (2,84) : les bougies se posent sur `ink`.
- une couleur de niveau comme couleur de texte (le bleu IPA ne fait que 3,85:1 sur le fond, assez pour un trait, pas pour lire un mot).
- un nom de session écrit dans sa couleur.

Ce tableau ne garde que les paires écrites. Une combinaison réelle non listée n'est attrapée que par axe dans le navigateur, pendant `/check verify`.

## Composants

Dans `frontend/src/ui/`, un fichier par composant, textes en français. Les composants interactifs reposent sur React Aria Components (clavier, toucher, lecteur d'écran), stylés avec les jetons. Icônes Lucide, `aria-hidden`, 16 px dans les puces et les textes, 20 px dans les boutons et les états ; une icône seule dans un bouton exige un `aria-label`.

| Composant | Base | États et variantes |
|---|---|---|
| `Button` | React Aria `Button` | `primaire`, `secondaire`, `discret` ; normal, survol, appuyé, focus, désactivé, en cours |
| `ToggleButton`, `ToggleButtonGroup` | React Aria | choix unique sans vide (unités de temps) ou multiple, vide permis (calques) ; normal, survol, appuyé, focus, sélectionné, désactivé |
| `Tabs` | React Aria `Tabs` | activation automatique aux flèches ; normal, survol, focus, sélectionné, désactivé |
| `Card` | `section` | titre avec prop `level` (2 par défaut), zone d'actions facultative |
| `Chip` | `span` | `neutre`, `accent` |
| `LevelChip` | `span` | `kind` : `liquidite`, `ipa`, `extreme`, `objectif` ; `pris` (bordure en pointillés, pastille et bordure à 50 %, mot « pris », texte à pleine opacité) |
| `DirectionChip` | `span` + Lucide `Triangle` | `achat` (triangle vers le haut, sarcelle), `vente` (triangle vers le bas, magenta) ; texte en `text`, couleur sur l'icône ; attribut `data-direction` |
| `LiveStatus` | `span role="status"` | `direct`, `retard`, `coupe`, `ferme` (voir *État du flux*) |
| `Table` | `table` | légende obligatoire ; colonnes numériques à droite en chasse fixe ; défilement horizontal au clavier (`tabindex="0"`, `role="region"`, `aria-label`) |
| `Price`, `Time` | `span`, `time` | voir *Formats* |
| `TextField` | React Aria `TextField` | libellé, aide, erreur ; `text`, `email`, `password` ; normal, focus (à tout focus), erreur, désactivé |
| `Checkbox` | React Aria `Checkbox` | coché, non coché, focus, erreur, désactivé ; case de 20 px, zone de 44 px au doigt |
| `Select` | React Aria `Select` | fermé, ouvert, focus, erreur, désactivé |
| `Loading` | `role="status"` | indicateur et « Chargement… » ; bloc squelette |
| `EmptyState` | `div` | icône `Inbox`, titre, phrase, action facultative |
| `ErrorState` | `div role="alert"` | icône `TriangleAlert`, phrase, bouton « Réessayer » facultatif |
| `FeedBanner` | `div role="alert"` | icône `WifiOff`, « Flux de prix coupé depuis 14:05. Cause : … » |

Les fenêtres (boîte de dialogue, notification passagère) viendront avec la fonction qui en aura besoin.

### État du flux

| État | Rendu |
|---|---|
| `direct` | pastille sarcelle qui pulse, « En direct » |
| `retard` | anneau creux `muted`, « En retard de N s » |
| `coupe` | icône `WifiOff` orange, « Flux coupé » |
| `ferme` | pastille `muted` sans pulsation, « Marché fermé » |

Le bandeau « flux coupé » dit depuis quand (heure du Bénin, avec la date si ce n'est pas le même jour) et pourquoi, pour chacune des six causes de la spec 0002 : `timeout` « le fournisseur ne répond plus », `erreur_api` « le fournisseur renvoie une erreur », `reseau` « problème de réseau », `auth` « autorisation cTrader refusée ou expirée », `limite_api` « trop de demandes au fournisseur », `donnees_absentes` « le fournisseur n'a pas la bougie ». Cause inconnue : « cause inconnue (code) ».

## Formats

Dans `frontend/src/design/format.ts`.
- **Prix** (`formatPrice`) : comme sur le graphique du trader, chiffres à chasse fixe, point décimal, exactement 3 décimales (`147.584` ; `147.5` devient `147.500`). Arrondi au plus proche, la moitié vers le haut, calculé sur les chiffres. Vide ou invalide : `—`.
- **Heure** (`formatTime`) : heure du Bénin (`Africa/Porto-Novo`), 24 h, à partir d'une heure UTC : `14:05`, `14:05:09` avec les secondes, `15 oct. 14:05` avec la date.
- **Pips, R, pourcentages** (`formatNumber`) : écriture française. `0,3 pip`, `2 pips`, `+4,6 R`, `−1,5 R`, `+0,31 %`. Une décimale pour les pips et les R, deux pour les pourcentages ; « pip » au singulier sous 2.

## À faire, à ne pas faire

- Fais : une couleur par jeton (`bg-panel`, `text-muted`) ; un mot avec chaque couleur porteuse de sens ; les états de chargement, vide et erreur sur chaque écran.
- Ne fais pas : une couleur en dur hors de `theme.css` (un test l'interdit) ; une couleur de niveau hors de `src/design/`, `src/ui/LevelChip.tsx`, `src/vitrine/` et `src/chart/` (un test l'interdit) ; une classe construite à la volée (`` `bg-${x}` ``), que Tailwind ne génère pas ; une adresse `http://` ou `https://` vers un domaine tiers (un test l'interdit).
