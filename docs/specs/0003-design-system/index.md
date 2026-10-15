# 0003. Design system du cockpit : le langage du prototype, ton code couleur réservé aux niveaux

**Date**: 2026-10-15 · révisée le 2026-10-15 après relecture croisée (25 trous comblés)
**Status**: In Progress

## Summary

Le cockpit reprend le langage visuel du prototype (fond encre sombre, trois polices, cartes et puces), mais ton code couleur TradingView devient la règle de toute l'appli : **rouge = liquidité, bleu = IPA, blanc = extrêmes, jaune = objectif**, et ces quatre couleurs ne servent à rien d'autre. Pour leur laisser la place, les bougies sont grises, l'achat est vert sarcelle et la vente magenta, l'accent de l'interface passe au violet. Les composants de base (boutons, onglets, champs, états…) sont construits avec React Aria pour marcher au clavier comme au doigt, stylés avec Tailwind, et montrés sur une page `/vitrine`. `docs/design.md` décrit tout, et des tests vérifient qu'il dit la même chose que le code.

## Requirements

**User stories**:
- En tant que trader, je veux retrouver sur le cockpit le même code couleur que sur mes graphiques TradingView, pour lire un niveau d'un coup d'œil sans réfléchir.
- En tant que trader, je veux que chaque bouton, onglet ou champ marche aussi bien au doigt sur mon téléphone qu'au clavier sur mon ordinateur.
- En tant que trader, je veux voir et valider le style (couleurs, polices, composants) sur une page de démonstration avant que les vrais écrans arrivent.

**Acceptance criteria**:
- **AC-1**: `docs/design.md` couvre les couleurs (valeur et rôle de chacune), les typographies, les espacements, les rayons, les durées, les tailles tactiles, les styles de niveaux, le tableau de contraste et chaque composant avec ses états. Le test du miroir compare `design.md` et `frontend/src/design/theme.css` dans les deux sens (chaque jeton `--color-*`, `--font-*`, `--text-*`, `--radius-*`, `--duration-*` du thème est dans `design.md` avec la même valeur, et chaque ligne de `design.md` existe dans le thème) et échoue sinon.
- **AC-2**: Les quatre couleurs de niveaux sont celles de TradingView lues sur les captures du trader : liquidité `#F23645`, IPA `#2962FF`, extrême `#FFFFFF`, objectif `#FFEB3B`. Aucun autre jeton du thème n'a l'une de ces valeurs (comparaison insensible à la casse). Un test échoue si `level-(liquidity|ipa|extreme|target)` apparaît dans un fichier de `frontend/src` (tests exclus) hors de `src/design/`, `src/ui/LevelChip.tsx`, `src/vitrine/` et `src/chart/` (le futur graphique, n°7).
- **AC-3**: Aucune couleur n'est écrite en dur dans le code du cockpit, et la palette par défaut de Tailwind est retirée. Un test vérifie que `theme.css` contient `--color-*: initial;`, puis parcourt les fichiers de `frontend/src` (hors `*.test.*` et `theme.css`) et échoue s'il y trouve une couleur hexadécimale, une fonction de couleur CSS ou une classe de la palette par défaut (motifs exacts dans *Gardes*).
- **AC-4**: Tout texte a un contraste d'au moins 4,5:1 sur son fond, et tout élément graphique utile (trait de niveau, bougie, anneau de focus, bord d'un champ ou d'une case) au moins 3:1 sur son fond. Deux exceptions voulues : un composant désactivé (opacité 50 %) et un niveau pris (opacité 50 %, toujours accompagné du mot « pris » et des pointillés). Le tableau de contraste de `design.md` contient au moins les paires listées dans *Contraste* ; le test calcule chaque rapport (en composant les fonds transparents sur leur support) et échoue sous le seuil, ou si une paire obligatoire manque.
- **AC-5**: Au clavier, chaque composant interactif est atteint par Tab dans l'ordre de lecture, s'active par Entrée ou Espace, et les onglets, groupes de bascules et listes de choix se parcourent aux flèches. L'anneau de focus (2 px violet) apparaît au focus clavier et jamais au clic ni au toucher, sauf dans un champ de saisie, où il apparaît à tout focus. Les tests vérifient l'attribut `data-focus-visible` posé par React Aria.
- **AC-6**: Au doigt, sur un écran tactile, chaque zone interactive mesure au moins 44 × 44 px (la zone touchable, même si la case visible est plus petite) ; à la souris, au moins 32 px de haut. Un appui au doigt déclenche l'action une seule fois, et aucune information ni action n'est accessible seulement au survol. Le déclenchement unique est testé ; les tailles sont mesurées pendant `/check verify` (voir *Vérification*).
- **AC-7**: La page `/vitrine` montre chaque couleur avec son rôle, l'échelle typographique, chaque composant dans chacun des états de son tableau (côte à côte), et un aperçu statique de graphique (bougies grises, liquidité vivante et prise, IPA, extrême, objectif, bande de session, chaque ligne nommée à son extrémité). Tout y est marqué « Données factices ». Elle s'ouvre par son adresse, en développement comme sur le serveur, et un rechargement sur `/vitrine` ou `/vitrine/` fonctionne. Une adresse inconnue affiche « Page introuvable » avec un lien vers l'accueil.
- **AC-8**: Les polices (Zen Kaku Gothic New, IBM Plex Sans, JetBrains Mono) sont livrées avec le cockpit, et le cockpit ne charge rien depuis un domaine tiers. Si elles manquent, la pile de secours prend le relais sans casser la mise en page. Un test parcourt `frontend/index.html` et `frontend/src` (tests exclus) et échoue sur toute adresse `http://` ou `https://` hors liste autorisée (`www.w3.org`, `localhost`).
- **AC-9**: Un prix s'affiche comme sur le graphique du trader : chiffres à chasse fixe, point décimal, exactement 3 décimales (`147.584`, `147.5` devient `147.500`). Une heure s'affiche à l'heure du Bénin au format 24 h (`14:05`, minuit donne `00:05`), à partir d'une heure UTC. Les pips, R et pourcentages suivent l'écriture française (`0,3 pip`, `2 pips`, `4,6 R`, `+0,31 %`). Les règles exactes sont dans *Formats* ; des tests les vérifient.
- **AC-10**: Le sens d'un setup s'affiche toujours avec un triangle et le mot : achat (triangle vers le haut, sarcelle), vente (triangle vers le bas, magenta). Un niveau de liquidité pris s'affiche en pointillés, estompé (opacité 50 %) et porte le mot « pris » ; un niveau vivant est en trait plein.
- **AC-11**: Quand le système demande moins d'animations (`prefers-reduced-motion: reduce`), aucune animation ni transition ne joue, y compris l'ouverture des listes de React Aria. Une règle globale de `theme.css` le garantit, et un test vérifie qu'elle est présente.
- **AC-12**: Les états de chargement, vide et erreur ont chacun un composant, toujours avec une icône et une phrase, jamais une couleur seule. L'état du flux a quatre états (en direct, en retard, coupé, marché fermé). Le bandeau « flux coupé » dit depuis quand (heure du Bénin, avec la date si ce n'est pas le même jour) et pourquoi, en français, pour chacune des six causes de coupure de la spec 0002.

## Decision

**Chosen option**: Option 2 : jetons dans le thème Tailwind v4, composants React Aria stylés par le projet, couleurs de niveaux réservées.

Le design system vit dans `frontend/src/design/` (le thème, source unique des valeurs, et les formats) et `frontend/src/ui/` (les composants). `docs/design.md` en est la description lisible, gardée identique au thème par un test.

**Implementation skills**: `react-aria` (`react-aria.adobe.com`, `.claude/skills/react-aria/`) · `tailwind-4-docs` (`lombiq/tailwind-agent-skills`, `.claude/skills/tailwind-4-docs/`)

Décisions prises avec le trader :
- Source du design : le prototype `docs/prototype/hellofedge-cockpit.html`, renforcé.
- Bougies sobres (grises), pour laisser le rouge, le bleu, le blanc et le jaune aux niveaux.
- Ces quatre couleurs gardent leur sens **partout** dans l'appli, pas seulement sur le graphique.
- Teintes exactes de TradingView (vérifiées dans les pixels des captures `exemples/`).
- Thème sombre uniquement.
- Achat en sarcelle, vente en magenta, toujours avec triangle et mot.
- Polices du prototype, livrées avec l'appli (pas de Google Fonts).
- Compact à la souris, 44 px au doigt.
- Composants de cette version : actions et affichage, saisie, états. Les fenêtres (boîte de dialogue, notification passagère) viendront avec la fonction qui en aura besoin.
- React Aria Components pour le clavier et le toucher, icônes Lucide.
- Liquidité prise : pointillés et estompée à 50 %, avec le mot « pris » (exception voulue à la règle de contraste).
- Page vitrine dans le cockpit, aussi sur le serveur, derrière la connexion dès qu'elle existe (n°6).
- Corrections de la relecture croisée acceptées en bloc (état « marché fermé », un seul gris de texte secondaire, règles de formats, gardes précises).

Décisions prises par l'architecte (tu peux les contester) :
- **Source unique des valeurs** : les variables `@theme` de `theme.css`. Le futur graphique (Lightweight Charts, qui veut des couleurs en JavaScript) les lit à l'exécution par `cssToken()`, au lieu d'une copie en TypeScript qui finirait par diverger. Runner up : un `tokens.json` qui génère le CSS, plus outillé pour un gain nul à un seul consommateur.
- **Accent violet `#B39DFF`** (focus, sélection, bouton principal, texte sombre dessus), loin du bleu IPA. Runner up : un accent blanc cassé, qui se confondrait avec les extrêmes.
- **Erreurs en orange `#FF8A3D`, toujours avec icône et phrase** : ni rouge (liquidité), ni jaune (objectif). Runner up : erreurs sans couleur, moins visibles pour le bandeau « flux coupé ».
- **Un seul gris de texte secondaire** (`--color-muted`, `#8A95AD`) : le `faint` du prototype, une fois relevé au seuil de lisibilité, ne s'en distinguait plus à l'œil. Runner up : deux gris, dont un illisible.
- **Les couleurs de niveaux ne colorent jamais un texte** : une puce de niveau a un texte clair, avec une pastille et une bordure de la couleur du niveau. Le bleu IPA ne fait que 3,9:1 sur le fond, assez pour un trait, pas pour lire un mot.
- **« En direct » partage le sarcelle de l'achat** : jamais seul, toujours avec le mot « En direct ». Runner up : un vert de plus, une teinte de plus à distinguer.
- **Couleurs des sessions du prototype gardées**, seulement pour des bandes de fond à 12 % ; le nom de la session est écrit en `--color-text`. Le ruban des sessions du prototype est hors de cette fonction.
- **Points d'arrêt de Tailwind par défaut** (640, 768, 1024, 1280 px). La mise en page du téléphone est la fonction n°14.
- **Pas de bibliothèque de routage** : `App` choisit la page selon l'adresse ; l'`api` renvoie `index.html` pour les adresses de pages (règles dans *Renvoi vers le cockpit*). Runner up : `/#/vitrine`, à défaire dès la connexion (n°6).
- **Vitrine chargée à part** (`React.lazy`), pour que React Aria ne pèse pas sur l'accueil tant qu'il n'y sert pas.
- **Tests sans `node:fs`** : les tests lisent `theme.css`, `design.md` et les sources par les imports `?raw` et `import.meta.glob` de Vite, déjà typés par `vite/client`, pour ne pas casser `tsc -b`.
- **Audit d'accessibilité** : `vitest-axe` sur la vitrine (libellés, rôles, structure), plus un passage d'axe dans un vrai navigateur pendant `/check verify` pour les contrastes réels, que jsdom ne calcule pas. Runner up : rien d'automatique.
- **Tests du clavier et du toucher avec `user-event`** (déjà installé). Runner up : `@react-aria/test-utils`.
- **Polices par Fontsource**, sous ensemble `latin` (accents français et `¥` compris), graisses utilisées seulement.
- **Versions minimales** : `tailwindcss` et `@tailwindcss/vite` 4.3, `react-aria-components` 1.22 (`ToggleButtonGroup` et `isPending` sont récents), `lucide-react` 1.57, Fontsource 5.3. La compatibilité de `@tailwindcss/vite` avec Vite 8 et de `vitest-axe` avec Vitest 5 se vérifie à l'installation ; en cas de refus, on le signale au lieu de forcer.

## Rationale

Raisonnement et options : voir [rationale.md](rationale.md).

## Feature design

**Jetons** (`frontend/src/design/theme.css`, bloc `@theme`, après `--color-*: initial;` et `--radius-*: initial;` qui retirent les valeurs par défaut de Tailwind ; `:root` porte `color-scheme: dark`) :

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

Polices : `--font-display` = `"Zen Kaku Gothic New", "Hiragino Sans", "Segoe UI", system-ui, sans-serif` (500, 700) ; `--font-sans` = `"IBM Plex Sans", "Segoe UI", system-ui, sans-serif` (400, 500, 600) ; `--font-mono` = `"JetBrains Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace` (400, 500, 600, chiffres `tabular-nums`).
Tailles (`--text-*`) : `xs` 12 px, `sm` 13, `base` 14 (corps à la souris ; 15 sous `pointer: coarse`), `md` 16 (champs de saisie, toujours, pour éviter le zoom du téléphone), `lg` 18 (titre de page), `xl` 22 (prix principal), `2xl` 28 ; interligne 1,45. L'étiquette (11 px, majuscules, graisse 600, espacement 0,09em) est une `@utility text-label`.
Rayons (`--radius-*`) : `sm` 4 px, `md` 7 px (boutons, champs), `lg` 10 px (cartes) ; `rounded-full` reste fourni par Tailwind. Espacements : l'échelle de Tailwind (pas de 4 px).
Durées : `--duration-fast` 120 ms (survol, focus), `--duration-base` 200 ms (ouverture d'une liste). Animation `--animate-live-pulse` (halo de la pastille « en direct », 1,6 s, avec ses `@keyframes`).
Mouvement réduit : `@media (prefers-reduced-motion: reduce) { *, ::before, ::after { animation: none !important; transition-duration: 0.01ms !important; } }` dans `theme.css`.

**Variantes de démonstration** (`theme.css`) : `@custom-variant demo-hovered`, `demo-pressed`, `demo-focus-visible` qui s'appliquent avec `[data-hovered]` (ou `[data-pressed]`, `[data-focus-visible]`) **ou** `[data-demo~="hovered"]` (etc.). Les composants utilisent ces variantes ; la vitrine pose `data-demo` pour figer un état côte à côte.

**États communs des composants interactifs** (aucun nouveau jeton) :

| État | Rendu |
|---|---|
| normal | fond `panel-2`, bord `line`, texte `text` (bouton principal : fond `accent`, texte `ink`) |
| survol | bord `muted` (principal : léger éclaircissement par opacité 90 %) |
| appuyé | fond `line`, texte `text` |
| focus clavier | `outline` 2 px `accent`, décalé de 2 px |
| sélectionné | fond `accent-soft`, texte `accent` |
| désactivé | opacité 50 %, `cursor: not-allowed` (exception au contraste) |
| erreur | bord `danger`, icône `TriangleAlert` et message |
| en cours | `Button` seulement : indicateur qui tourne, libellé gardé, action bloquée |

Taille : hauteur minimale 32 px (`pointer-fine`) et zone touchable de 44 × 44 px (`pointer-coarse`), y compris pour `Checkbox` dont la case visible fait 20 px.

**Composants** (`frontend/src/ui/`, un fichier par composant, textes en français) :

| Composant | Base | États et variantes |
|---|---|---|
| `Button` | React Aria `Button` | `primaire`, `secondaire`, `discret` ; tous les états communs |
| `ToggleButton`, `ToggleButtonGroup` | React Aria | choix unique avec `disallowEmptySelection` (unités de temps) ou multiple, vide permis (calques) ; normal, survol, appuyé, focus, sélectionné, désactivé |
| `Tabs` | React Aria `Tabs` | activation automatique aux flèches ; normal, survol, focus, sélectionné, désactivé |
| `Card` | `section` | titre avec prop `level` (2 par défaut), zone d'actions facultative |
| `Chip` | `span` | `neutre`, `accent` |
| `LevelChip` | `span` | `kind` : `liquidite`, `ipa`, `extreme`, `objectif` ; `pris` (bordure en pointillés, pastille et bordure à 50 %, mot « pris » ajouté, texte toujours à pleine opacité) |
| `DirectionChip` | `span` + Lucide `Triangle` | `achat` (triangle plein vers le haut, sarcelle), `vente` (triangle tourné de 180°, magenta) ; le texte « Achat » ou « Vente » est en `text`, la couleur est sur l'icône ; attribut `data-direction` |
| `LiveStatus` | `span role="status"` | voir *État du flux* |
| `Table` | `table` sémantique | légende obligatoire ; colonnes numériques à droite en chasse fixe ; enveloppe de défilement horizontal avec `tabindex="0"`, `role="region"` et `aria-label` |
| `Price`, `Time` | `span`, `time` | voir *Formats* |
| `TextField` | React Aria `TextField` | libellé, aide, erreur ; `text`, `email`, `password` ; normal, focus (à tout focus), erreur, désactivé |
| `Checkbox` | React Aria `Checkbox` | coché, non coché, focus, erreur, désactivé |
| `Select` | React Aria `Select` | fermé, ouvert, focus, erreur, désactivé |
| `Loading` | `role="status"` | indicateur et texte « Chargement… » ; bloc squelette |
| `EmptyState` | `div` | icône `Inbox`, titre, phrase, action facultative |
| `ErrorState` | `div role="alert"` | icône `TriangleAlert`, phrase, bouton « Réessayer » facultatif |
| `FeedBanner` | `div role="alert"` | icône `WifiOff`, phrase de *Bandeau* |

Icônes : Lucide, `aria-hidden`, 16 px dans les puces et les textes, 20 px dans les boutons et les états. Une icône seule dans un bouton exige un `aria-label`.

`LevelChip` utilise une table fixe de classes complètes (`liquidite` → classes `…-level-liquidity`, `ipa` → `…-level-ipa`, `extreme` → `…-level-extreme`, `objectif` → `…-level-target`), jamais une classe construite à la volée, que Tailwind ne générerait pas.

**État du flux** (`LiveStatus`, composant pur : prop `etat`, plus `retardSecondes` pour `retard`). Règle de calcul, à appliquer par le fil minimal (n°7) à partir de `GET /api/feed/status` (spec 0002) et de l'horloge :

| `etat` | Quand | Rendu |
|---|---|---|
| `direct` | marché ouvert, pas de coupure, maintenant − (`last_ts_open` + 60 s) ≤ 20 s | pastille sarcelle qui pulse, « En direct » |
| `retard` | marché ouvert, pas de coupure, plus de 20 s | anneau creux `muted`, « En retard de N s » |
| `coupe` | une coupure est ouverte | icône `WifiOff` orange, « Flux coupé » |
| `ferme` | week end, jour férié configuré ou fenêtre du rollover (calendrier de la spec 0002) | pastille `muted` sans pulsation, « Marché fermé » |

**Bandeau** (`FeedBanner`, props `depuis` en UTC et `cause`) : « Flux de prix coupé depuis 14:05. Cause : {libellé}. » ; si `depuis` n'est pas le même jour au Bénin : « depuis le 15 oct. à 14:05 ». Libellés (depuis `feed_outage.cause`, spec 0002) : `timeout` « le fournisseur ne répond plus », `erreur_api` « le fournisseur renvoie une erreur », `reseau` « problème de réseau », `auth` « autorisation cTrader refusée ou expirée », `limite_api` « trop de demandes au fournisseur », `donnees_absentes` « le fournisseur n'a pas la bougie ». Cause inconnue : « cause inconnue ({code}) ».

**Formats** (`frontend/src/design/format.ts`) :
- `formatPrice(value: string | null)` : chaîne décimale de l'api seulement (`NUMERIC(10,3)`, spec 0002). Plus de 3 décimales : arrondi au plus proche, la moitié vers le haut, calculé sur les chiffres (jamais par un flottant) ; moins de 3 : complété par des zéros. Vide, `null` ou invalide : `—`.
- `formatTime(utc: string, options?: { secondes?: boolean; date?: boolean })` : fuseau `DISPLAY_TIME_ZONE = 'Africa/Porto-Novo'`, `Intl.DateTimeFormat('fr-FR', { hourCycle: 'h23' })`. Sorties : `14:05`, `14:05:09` avec secondes, `15 oct. 14:05` avec date. Le `<time>` porte la valeur ISO dans `dateTime`.
- `formatNumber(value: number, kind: 'pip' | 'r' | 'pct')` : `Intl.NumberFormat('fr-FR')`. Décimales : pip 1, R 1, pourcentage 2. Unités : « pip » au singulier sous 2 en valeur absolue, « pips » sinon ; « R » ; « % ». Signe : `+` devant un gain pour R et pourcentage, vrai signe moins (U+2212) devant une perte. Les tests comparent les caractères exacts, y compris l'espace fine insécable (U+202F) que `Intl` met avant `%`.
- `cssToken(name: string)` : `getComputedStyle(document.documentElement).getPropertyValue(name).trim()`.

**Contraste** (tableau de `design.md`, colonnes `Premier plan | Fond | Type | Seuil`, jetons entre accents graves ; minimum obligatoire vérifié par le test) :
- Texte, seuil 4,5 : `text`, `muted`, `accent`, `buy`, `sell`, `danger` sur `ink`, `panel` et `panel-2` ; `text` et `accent` sur `accent-soft` posé sur `panel` ; `ink` sur `accent` ; `ink` sur `danger`.
- Graphique, seuil 3 : `level-liquidity`, `level-ipa`, `level-extreme`, `level-target` sur `ink` et `panel-2` ; `candle-up` et `candle-down` sur `ink` ; `muted` (bord de champ) sur `panel` et `panel-2` ; `accent` (anneau) sur `ink`, `panel` et `panel-2`.
- Combinaisons interdites, listées dans `design.md` et jamais dans le tableau des paires autorisées : `muted` sur `line` (4,39), `sell` sur un fond teinté de `sell`, `candle-down` sur `panel-2` (2,84), une couleur de niveau comme couleur de texte, un nom de session écrit dans sa couleur.

**Styles de niveaux** (graphique de la n°7 et aperçu de la vitrine) : niveau vivant en trait plein de 2 px ; niveau pris en pointillés de 1 px, opacité 50 % ; chaque ligne porte son nom à son extrémité droite (« Liquidité », « Liquidité · pris », « IPA », « Extrême », « Objectif »). Bandes de session à 12 % d'opacité, nom en `text`.

**Gardes** (tests Vitest, sources lues par `import.meta.glob('/src/**/*.{ts,tsx,css}', { query: '?raw', eager: true })`, `design.md` par un import `?raw` relatif, fichiers `*.test.*` exclus) :
- Couleurs en dur (hors `theme.css`) : `#[0-9a-fA-F]{3,8}\b` et `\b(rgb|rgba|hsl|hsla|hwb|lab|lch|oklab|oklch)\(`.
- Palette par défaut : `\b(bg|text|border|ring|fill|stroke|from|to|via|outline|divide|shadow|accent|decoration)-(slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose|white|black)\b`.
- Couleurs réservées : `level-(liquidity|ipa|extreme|target)` hors des dossiers autorisés (AC-2).
- Domaines tiers : `https?://` hors `www.w3.org` et `localhost`, dans `index.html` et `src` (AC-8).

**Vitrine** (`frontend/src/vitrine/`, chargée par `React.lazy`) : sections Couleurs, Typographie, Espacements et rayons, Composants (états côte à côte par `data-demo`), Aperçu du graphique (SVG statique d'une vingtaine de bougies factices tracées avec les jetons). Données dans `src/vitrine/donnees.ts`. Badge « Données factices » en haut.

**Pages** (`App`) : `/` l'accueil (le squelette actuel, restylé, avec un lien `<a href="/vitrine">` discret), `/vitrine` et `/vitrine/` la vitrine, toute autre adresse « Page introuvable » (`EmptyState` avec un lien vers l'accueil).

**Renvoi vers le cockpit** (`backend/src/hellofedge/api/app.py`) : une sous classe de `StaticFiles` dont `get_response` attrape le 404 et renvoie `index.html` seulement si le chemin ne commence ni par `api` ni par `assets` et que son dernier segment ne contient pas de point. `index.html` part avec `Cache-Control: no-cache` (les fichiers de `assets/` ont un nom haché et restent en cache). Les tests construisent l'app par `create_app()` avec un `dist` temporaire (variable `FRONTEND_DIST`, cache de `get_settings` vidé).

**Data model sketch** : aucun. Cette fonction ne lit ni n'écrit en base.

**API surface** :

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/{chemin}` (adresse de page, voir *Renvoi*) | GET | chemin | `index.html`, `Cache-Control: no-cache` | aucune pour l'instant ; la connexion (n°6) l'ajoutera | `/api/...` inconnu : 404 JSON ; `/assets/absent.js` ou tout chemin avec un point : 404 |

**Value sourcing** :

| Action | Value produced / displayed | Source |
|---|---|---|
| Afficher un niveau | sa couleur | prop `kind` → table fixe de classes → jeton `--color-level-<liquidity·ipa·extreme·target>` |
| Afficher un niveau | trait plein ou pris | prop `pris` (plus tard : l'état donné par le moteur, n°7) |
| Afficher un prix | `147.584` | prop `value` (chaîne de l'api) + règles de `formatPrice` |
| Afficher une heure | `14:05` | prop `utc` (ISO UTC de l'api) + `DISPLAY_TIME_ZONE` (`AGENTS.md`) |
| Afficher pips, R, % | `0,3 pip` | prop `value` + `kind` + règles de `formatNumber` |
| Afficher l'état du flux | `direct`, `retard`, `coupe`, `ferme` et N secondes | props `etat`, `retardSecondes` ; règle de calcul dans *État du flux* (n°7, depuis `GET /api/feed/status` et le calendrier de marché de la spec 0002) |
| Bandeau « flux coupé » | heure, date éventuelle, cause | props `depuis` (UTC), `cause` (`feed_outage.cause`) + libellés de *Bandeau* |
| Taille des zones tactiles | 32 px ou 44 px | requête média `pointer` (variantes `pointer-fine`, `pointer-coarse`) |
| Animations | jouées ou non | règle `prefers-reduced-motion` de `theme.css` |
| État figé dans la vitrine | survol, appuyé, focus | attribut `data-demo` + variantes `demo-*` |
| Couleur du graphique (n°7) | valeur hexadécimale | `cssToken('--color-…')` |
| Contenu de la vitrine | bougies, niveaux, tableaux | `src/vitrine/donnees.ts`, marqué factice |

**Key invariants** :
- `theme.css` est la seule source des valeurs ; `design.md` en est le miroir exact, dans les deux sens.
- Les quatre couleurs de niveaux sont uniques dans le thème et réservées aux niveaux.
- Aucune couleur en dur hors de `theme.css` ; la palette et les rayons par défaut de Tailwind n'existent pas.
- Une couleur de niveau ou de session ne colore jamais un texte ; une information n'est jamais portée par la couleur seule (toujours un mot, et une icône ou un triangle quand il y a un sens).
- Le cockpit ne charge rien depuis un domaine tiers.
- Le renvoi vers `index.html` ne touche jamais `/api` ni `/assets`.

**Security model** : la vitrine ne montre que des données factices et n'appelle aucune api. Dès la connexion (n°6), elle est protégée comme toutes les pages. Le renvoi vers `index.html` ne s'applique jamais sous `/api`, donc il ne masque aucune route ni ne sert de donnée. Aucune ressource tierce.

**Configuration required** : aucune variable d'environnement nouvelle (`FRONTEND_DIST` existe déjà, les tests s'en servent).

**Vérification** (pour `/check verify`, en plus des tests) : ouvrir `/vitrine` dans Chromium ; émuler un écran tactile (`pointer: coarse`) et lire `getBoundingClientRect()` de chaque élément interactif (au moins 44 × 44 px), puis à la souris (au moins 32 px de haut) ; lancer axe dans le navigateur (contrastes réels compris) ; puis le trader ouvre la vitrine sur son téléphone (Codespace) et valide l'aspect, en particulier un trait blanc d'extrême posé sur des bougies claires.

**Critical test scenarios** :
- Happy path : la vitrine s'affiche avec ses sections et le badge « Données factices », et `vitest-axe` ne trouve aucune violation, verifies **AC-7**, **AC-12**
- Miroir : changer une valeur dans `theme.css` sans toucher `design.md`, ou ajouter un jeton absent de `design.md`, fait échouer le test, verifies **AC-1**
- Couleur réservée : `text-level-ipa` dans `src/ui/Button.tsx` fait échouer le garde ; dans `src/chart/` il passe, verifies **AC-2**
- Couleur en dur : `#FF0000` ou `bg-red-500` dans un composant fait échouer le garde ; un `#F23645` dans un fichier de test passe, verifies **AC-3**
- Contraste : remettre `--color-muted` à `#5B6782` fait échouer le test ; retirer une paire obligatoire du tableau aussi, verifies **AC-4**
- Clavier : Tab atteint le bouton puis le groupe de bascules ; les flèches changent d'onglet ; Espace coche la case ; Entrée ouvre la liste de choix et les flèches la parcourent ; `data-focus-visible` est posé au clavier, verifies **AC-5**
- Toucher : un appui `touch` sur `Button` appelle `onPress` une seule fois et ne pose pas `data-focus-visible`, verifies **AC-5**, **AC-6**
- Formats : `formatPrice('147.5840')` donne `147.584`, `'147.5'` donne `147.500`, `'147.5845'` donne `147.585`, `null` donne `—` ; `formatTime('2026-10-15T23:05:00Z')` donne `00:05` ; `formatNumber(0.3,'pip')` donne `0,3 pip`, `formatNumber(2,'pip')` donne `2 pips`, `formatNumber(-1.5,'r')` donne `−1,5 R`, verifies **AC-9**
- Pages : `GET /vitrine` et `GET /vitrine/` renvoient `index.html` avec `no-cache` ; `GET /api/inconnu` renvoie 404 ; `GET /assets/absent.js` renvoie 404 ; dans le cockpit, `/foo` affiche « Page introuvable », verifies **AC-7**
- Domaines tiers : une adresse `https://fonts.googleapis.com` ajoutée dans `index.html` fait échouer le garde, verifies **AC-8**
- Sens et niveaux : `DirectionChip` vente affiche « Vente » avec `data-direction="vente"` ; `LevelChip` liquidité prise affiche « pris » et porte le style pointillé, verifies **AC-10**
- Mouvement réduit : `theme.css` contient la règle `prefers-reduced-motion` globale, verifies **AC-11**
- États du flux : `LiveStatus` affiche « En direct », « En retard de 35 s », « Flux coupé », « Marché fermé » ; `FeedBanner` passe sur les six causes (`it.each`) avec l'heure du Bénin, une cause inconnue affiche son code, un début la veille affiche la date, verifies **AC-12**

## Build plan

Tracer Bullet : on fait d'abord passer un fil fin du jeton jusqu'au navigateur (thème, Tailwind, polices, page servie par l'`api`), puis on épaissit composant par composant.

1. Installer Tailwind v4 (`tailwindcss`, `@tailwindcss/vite`) et les trois polices Fontsource ; écrire `src/design/theme.css` (tous les jetons, valeurs par défaut retirées, `color-scheme`, `text-label`, variantes `demo-*`, règle de mouvement réduit) ; remplacer `src/index.css` ; restyler l'accueil avec les jetons. Le build passe et l'`api` sert le cockpit restylé, satisfies **AC-1**, **AC-8**, **AC-11**
2. Écrire `docs/design.md` (jetons, polices, tailles, rayons, durées, tailles tactiles, états communs, styles de niveaux, tableau de contraste et combinaisons interdites, composants) et les gardes : miroir, contraste, couleurs réservées, couleurs en dur et palette, domaines tiers, mouvement réduit, satisfies **AC-1**, **AC-2**, **AC-3**, **AC-4**, **AC-8**, **AC-11**
3. Ajouter le renvoi vers `index.html` dans l'`api` avec ses tests pytest, puis les pages de `App` (accueil, `/vitrine` chargée à part, « Page introuvable ») et les sections Couleurs et Typographie de la vitrine, satisfies **AC-7**
4. Écrire `src/design/format.ts` (`formatPrice`, `formatTime`, `formatNumber`, `DISPLAY_TIME_ZONE`, `cssToken`) avec leurs tests, satisfies **AC-9**
5. Installer `react-aria-components` et `lucide-react` ; construire `Button`, `ToggleButton`, `ToggleButtonGroup`, `Tabs`, `Card`, `Chip`, `LevelChip`, `DirectionChip`, `LiveStatus`, `Table`, `Price`, `Time`, avec leurs tests clavier et toucher, et les ajouter à la vitrine, satisfies **AC-5**, **AC-6**, **AC-10**, **AC-12**
6. Construire `TextField`, `Checkbox`, `Select` avec leurs tests, et les ajouter à la vitrine, satisfies **AC-5**, **AC-6**
7. Construire `Loading`, `EmptyState`, `ErrorState`, `FeedBanner` avec leurs tests, et les ajouter à la vitrine, satisfies **AC-12**
8. Ajouter l'aperçu statique du graphique à la vitrine, puis installer `vitest-axe` et auditer la vitrine entière, satisfies **AC-7**, **AC-10**

## Consequences

**Positive**:
- Le trader lit le cockpit avec le code couleur qu'il connaît déjà, et un niveau ne se confond jamais avec une bougie ou un bouton.
- Le clavier, le toucher et l'accessibilité sont portés par une bibliothèque éprouvée plutôt que réécrits à la main.
- Les gardes empêchent le code, `design.md` et les contrastes de diverger sans qu'on le voie.

**Negative / tradeoffs**:
- Les bougies grises ne ressemblent pas à TradingView : il faudra un temps d'habitude. Un trait blanc d'extrême se détache moins sur des bougies claires (1,8:1) : à juger à l'œil sur le vrai graphique (n°7).
- React Aria alourdit le cockpit (quelques dizaines de ko compressés pour ces composants, chargés seulement là où ils servent) et impose sa façon de styler (attributs `data-*`).
- Trois teintes chaudes coexistent (rouge liquidité, magenta vente, orange erreur) et l'orange est proche du jaune objectif (1,9:1 entre eux) : la règle « toujours un mot ou une icône » est ce qui les distingue, elle doit être tenue partout.
- Le tableau de contraste ne garde que les paires écrites : une combinaison réelle non listée n'est attrapée que par axe dans le navigateur, pendant `/check verify`.
- Un seul thème : un passage au clair plus tard demandera de revoir toutes les paires.

**Neutral**:
- Tailwind, React Aria, Lucide, Fontsource et `vitest-axe` entrent dans `frontend/package.json` avec cette fonction ; Lightweight Charts attend le fil minimal (n°7).
- Les tailles tactiles et les contrastes réels se vérifient dans un vrai navigateur, pas dans jsdom.

## Follow-up

- [ ] Fil minimal (n°7) : le graphique lit ses couleurs avec `cssToken()` et vit dans `src/chart/` ; il calcule l'état du flux selon *État du flux* ; l'image des alertes (mplfinance, côté serveur) reprend les mêmes valeurs, avec un test pytest qui compare la palette Python à `theme.css`.
- [ ] Connexion (n°6) : protéger `/vitrine` comme le reste, et choisir alors une vraie bibliothèque de routage si les pages se multiplient.
- [ ] La skill `tailwind-4-docs` attend un instantané de la documentation de Tailwind (`python .claude/skills/tailwind-4-docs/scripts/sync_tailwind_docs.py --accept-docs-license`). Cette documentation est « source available », pas libre : c'est au trader d'accepter sa licence. Sans elle, la skill retombe sur `gotchas.md` et `engineering-playbook.md`. L'instantané est exclu de git.
- [ ] `/sync` : ajouter les skills `react-aria` et `tailwind-4-docs` à la section `## Agent skills` de `frontend/AGENTS.md`, noter le serveur MCP React Aria comme refusé (`Declined:`), et remplacer la ligne « Styles provisoires… jusqu'au design system » par un renvoi à `docs/design.md`.
- [ ] Skill Lightweight Charts (`tradingview/lightweight-charts`, officielle) : à installer avec le fil minimal (n°7).
- [ ] Ruban des sessions du prototype : à reprendre avec la fonction qui affichera l'horloge des sessions.
