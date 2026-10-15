# 0003. Design system du cockpit : le langage du prototype, ton code couleur réservé aux niveaux

**Date**: 2026-10-15
**Status**: Proposed

## Summary

Le cockpit reprend le langage visuel du prototype (fond encre sombre, trois polices, cartes et puces), mais ton code couleur TradingView devient la règle de toute l'appli : **rouge = liquidité, bleu = IPA, blanc = extrêmes, jaune = objectif**, et ces quatre couleurs ne servent à rien d'autre. Pour leur laisser la place, les bougies sont grises, l'achat est vert sarcelle et la vente magenta, l'accent de l'interface passe au violet. Les composants de base (boutons, onglets, champs, états…) sont construits avec React Aria pour marcher au clavier comme au doigt, stylés avec Tailwind, et montrés sur une page `/vitrine`. `docs/design.md` décrit tout, et des tests vérifient qu'il dit la même chose que le code.

## Requirements

**User stories**:
- En tant que trader, je veux retrouver sur le cockpit le même code couleur que sur mes graphiques TradingView, pour lire un niveau d'un coup d'œil sans réfléchir.
- En tant que trader, je veux que chaque bouton, onglet ou champ marche aussi bien au doigt sur mon téléphone qu'au clavier sur mon ordinateur.
- En tant que trader, je veux voir et valider le style (couleurs, polices, composants) sur une page de démonstration avant que les vrais écrans arrivent.

**Acceptance criteria**:
- **AC-1**: `docs/design.md` couvre les couleurs (valeur et rôle de chacune), les typographies, les espacements, les rayons, les tailles tactiles, les styles de niveaux et chaque composant de base avec ses états. Chaque couleur listée dans son tableau a exactement la valeur définie dans `frontend/src/design/theme.css`. Un test Vitest échoue sinon.
- **AC-2**: Les quatre couleurs de niveaux sont celles de TradingView lues sur les captures du trader : liquidité `#F23645`, IPA `#2962FF`, extrême `#FFFFFF`, objectif `#FFEB3B`. Aucun autre jeton du thème n'a l'une de ces valeurs, et un test échoue si une classe ou variable `level-*` est utilisée dans `frontend/src` hors de `src/design/`, `src/ui/LevelChip.tsx` et `src/vitrine/`.
- **AC-3**: Aucune couleur n'est écrite en dur dans le code du cockpit : les valeurs hexadécimales ou `rgb()` n'apparaissent que dans `src/design/theme.css`, et la palette par défaut de Tailwind est désactivée (une classe comme `bg-red-500` ne produit rien). Un test parcourt `frontend/src` et échoue sinon.
- **AC-4**: Tout texte a un contraste d'au moins 4,5:1 sur le fond où il est posé, et tout élément graphique utile (trait de niveau, bougie, anneau de focus, bord d'un champ ou d'une case) au moins 3:1 sur son fond. Un test calcule ces rapports pour chaque paire listée dans `design.md` et échoue sous le seuil.
- **AC-5**: Au clavier, chaque composant interactif est atteint par Tab dans l'ordre de lecture, s'active par Entrée ou Espace, et les onglets, groupes de bascules et listes de choix se parcourent aux flèches. L'anneau de focus (2 px violet) apparaît au clavier et jamais au clic ou au toucher. Des tests Testing Library le vérifient pour chaque composant interactif.
- **AC-6**: Au doigt, sur un écran tactile, chaque zone interactive mesure au moins 44 × 44 px ; à la souris, au moins 32 px de haut. Un appui au doigt déclenche l'action une seule fois, et aucune information ni action n'est accessible seulement au survol. Le déclenchement unique est testé ; les tailles sont mesurées dans un vrai navigateur pendant `/check verify` et sur le téléphone du trader.
- **AC-7**: La page `/vitrine` montre chaque couleur avec son rôle, l'échelle typographique, chaque composant dans tous ses états (normal, survol, focus, appuyé, sélectionné, désactivé, erreur, chargement) et un aperçu statique de graphique (bougies grises, niveau de liquidité vivant et pris, IPA, extrême, objectif, bande de session). Tout y est marqué « Données factices ». Elle s'ouvre par son adresse, en développement comme sur le serveur, et un rechargement de la page sur `/vitrine` fonctionne.
- **AC-8**: Les polices (Zen Kaku Gothic New, IBM Plex Sans, JetBrains Mono) sont livrées avec le cockpit : aucune requête ne part vers un domaine tiers pour les charger. Si elles manquent, une police du système prend le relais sans casser la mise en page. Un test échoue si `fonts.googleapis.com` ou `fonts.gstatic.com` apparaît dans `frontend/`.
- **AC-9**: Un prix s'affiche comme sur le graphique du trader : chiffres à chasse fixe, point décimal et 3 décimales (`147.584`). Une heure s'affiche à l'heure du Bénin au format 24 h (`14:05`), à partir d'une heure UTC. Les autres nombres (pips, pourcentages, R) suivent l'écriture française (`0,3 pip`, `4,6 R`). Des tests le vérifient.
- **AC-10**: Le sens d'un setup s'affiche toujours avec la flèche et le mot : « ▲ Achat » en sarcelle, « ▼ Vente » en magenta. Un niveau de liquidité pris s'affiche en pointillés et estompé (opacité 50 %), un niveau vivant en trait plein.
- **AC-11**: Quand le système demande moins d'animations (`prefers-reduced-motion`), aucune animation ni pulsation ne joue.
- **AC-12**: Les états de chargement, vide et erreur, ainsi que le bandeau « flux coupé », ont chacun un composant. Le bandeau dit depuis quand (heure du Bénin) et pourquoi, en français, pour chacune des causes de coupure de la spec 0002. Les états d'erreur portent toujours une icône et une phrase, jamais une couleur seule.

## Decision

**Chosen option**: Option 2 : jetons dans le thème Tailwind v4, composants React Aria stylés par le projet, couleurs de niveaux réservées.

Le design system vit dans `frontend/src/design/` (le thème, la source unique des valeurs) et `frontend/src/ui/` (les composants). `docs/design.md` en est la description lisible, gardée identique au thème par un test.

**Implementation skills**: `react-aria` (`react-aria.adobe.com`, `.claude/skills/react-aria/`) · `tailwind-4-docs` (`lombiq/tailwind-agent-skills`, `.claude/skills/tailwind-4-docs/`)

Décisions prises avec le trader :
- Source du design : le prototype `docs/prototype/hellofedge-cockpit.html`, renforcé.
- Bougies sobres (grises), pour laisser le rouge, le bleu, le blanc et le jaune aux niveaux.
- Ces quatre couleurs gardent leur sens **partout** dans l'appli, pas seulement sur le graphique.
- Teintes exactes de TradingView (vérifiées dans les captures `exemples/`).
- Thème sombre uniquement.
- Achat en sarcelle, vente en magenta, toujours avec flèche et mot.
- Polices du prototype, livrées avec l'appli (pas de Google Fonts).
- Compact à la souris, 44 px au doigt.
- Composants de cette version : actions et affichage, saisie, états. Les fenêtres (boîte de dialogue, notification passagère) viendront avec la fonction qui en aura besoin.
- React Aria Components pour le clavier et le toucher, icônes Lucide.
- Liquidité prise : pointillés et estompée.
- Page vitrine dans le cockpit, aussi sur le serveur, derrière la connexion dès qu'elle existe (n°6).

Décisions prises par l'architecte (tu peux les contester) :
- **Source unique des valeurs** : les variables `@theme` de `theme.css`. Le futur graphique (Lightweight Charts, qui veut des couleurs en JavaScript) les lit à l'exécution par un petit utilitaire `cssToken()`, au lieu d'une copie en TypeScript qui finirait par diverger. Runner up : un fichier `tokens.json` qui génère le CSS, plus outillé pour un gain nul à un seul consommateur.
- **Accent violet `#B39DFF`** (focus, onglet actif, bouton principal), assez loin du bleu IPA. Runner up : un accent blanc cassé, qui se confondrait avec les extrêmes.
- **Erreurs en orange `#FF8A3D`, toujours avec icône et phrase** : ni rouge (liquidité), ni jaune (objectif). Runner up : erreurs sans couleur, moins visibles pour le bandeau « flux coupé ».
- **Texte discret relevé** de `#5B6782` (prototype, 3,3:1) à `#808CA6` pour passer le seuil de 4,5:1.
- **Les couleurs de niveaux ne colorent jamais un texte** : une puce de niveau a un texte clair, avec une pastille et une bordure de la couleur du niveau. Le bleu IPA ne fait que 3,9:1 sur le fond, assez pour un trait, pas pour lire un mot.
- **Couleurs des sessions du prototype gardées**, seulement pour les bandes de fond et le ruban, jamais pour un trait.
- **Points d'arrêt de Tailwind par défaut** (640, 768, 1024, 1280 px). La mise en page du téléphone est la fonction n°14.
- **Page vitrine sans bibliothèque de routage** : `App` choisit la page selon l'adresse. Côté serveur, l'`api` renvoie `index.html` pour toute adresse hors `/api` qui n'est pas un fichier, sinon un rechargement de `/vitrine` donnerait une erreur 404. Runner up : une adresse en `/#/vitrine`, qui évite le changement côté serveur mais qu'il faudrait défaire à la connexion (n°6), qui aura besoin de vraies adresses.
- **Audit d'accessibilité automatique** de la vitrine avec `vitest-axe` (libellés, rôles, structure). Runner up : rien d'automatique, et chaque oubli de libellé passe en silence.
- **Tests du clavier et du toucher avec `user-event`** (déjà installé). Runner up : `@react-aria/test-utils`, une dépendance de plus pour ce que `user-event` couvre déjà ici.
- **Polices par Fontsource**, sous ensemble `latin` seulement (accents français et `¥` compris), graisses utilisées seulement.

## Rationale

Raisonnement et options : voir [rationale.md](rationale.md).

## Feature design

**Jetons** (`frontend/src/design/theme.css`, bloc `@theme`, après `--color-*: initial;` qui retire la palette de Tailwind) :

| Jeton | Valeur | Rôle |
|---|---|---|
| `--color-ink` | `#0C111C` | fond de la page et du graphique |
| `--color-panel` | `#121A29` | fond des cartes |
| `--color-panel-2` | `#172136` | fond des éléments dans une carte, onglet actif |
| `--color-line` | `#22304A` | bordures |
| `--color-line-soft` | `#1B263B` | séparateurs discrets, grille du graphique |
| `--color-text` | `#E4E8F1` | texte principal |
| `--color-muted` | `#8A95AD` | texte secondaire |
| `--color-faint` | `#808CA6` | texte discret (graduations, légendes) |
| `--color-accent` | `#B39DFF` | focus, sélection, bouton principal |
| `--color-accent-soft` | `rgb(179 157 255 / 0.14)` | fond d'un élément sélectionné |
| `--color-buy` | `#3DBFA3` | achat, et état « en direct » |
| `--color-sell` | `#E05FB4` | vente |
| `--color-danger` | `#FF8A3D` | erreur, flux coupé |
| `--color-level-liquidity` | `#F23645` | liquidité (réservé) |
| `--color-level-ipa` | `#2962FF` | IPA (réservé) |
| `--color-level-extreme` | `#FFFFFF` | plus haut ou plus bas d'une session précédente (réservé) |
| `--color-level-target` | `#FFEB3B` | objectif (réservé) |
| `--color-candle-up` | `#B8C2D6` | bougie haussière (corps, mèche, bord) |
| `--color-candle-down` | `#5B6782` | bougie baissière |
| `--color-session-asia` | `#7B6CF0` | session de Tokyo (bandes seulement) |
| `--color-session-frankfurt` | `#A56A8C` | Francfort |
| `--color-session-london` | `#3F8FD1` | Londres |
| `--color-session-trap` | `#6B7489` | heure piège |
| `--color-session-newyork` | `#D98C3E` | New York |
| `--color-session-londonclose` | `#4FA58A` | clôture de Londres |

Autres jetons : polices `--font-display` (Zen Kaku Gothic New 500 et 700), `--font-sans` (IBM Plex Sans 400, 500, 600), `--font-mono` (JetBrains Mono 400, 500, 600, chiffres `tabular-nums`), chacune suivie d'une pile de secours système. Tailles : `label` 11 px (majuscules, graisse 600, espacement 0,09em), `xs` 12, `sm` 13, `base` 14 (corps du texte à la souris, 15 au doigt), `md` 16 (champs de saisie, toujours, pour éviter le zoom automatique du téléphone), `lg` 18 (titre de page), `xl` 22 (prix principal), `2xl` 28. Interligne 1,45. Espacements : l'échelle de Tailwind (pas de 4 px). Rayons : `sm` 4 px, `md` 7 px (boutons, champs), `lg` 10 px (cartes), `full` (puces). Durées : 120 ms (survol, focus), 200 ms (ouverture d'une liste).

**Styles de niveaux** (pour le graphique de la n°7 et l'aperçu de la vitrine) : niveau vivant en trait plein de 2 px ; niveau pris en pointillés de 1 px, opacité 50 %. Les bandes de session sont à 12 % d'opacité, avec leur nom.

**Composants** (`frontend/src/ui/`, un fichier par composant, textes en français) :

| Composant | Base | États et variantes |
|---|---|---|
| `Button` | React Aria `Button` | `primaire`, `secondaire`, `discret` ; désactivé ; en cours (`isPending`, avec indicateur) |
| `ToggleButton`, `ToggleButtonGroup` | React Aria | choix unique (unités de temps) ou multiple (calques) ; sélectionné ; désactivé |
| `Tabs` | React Aria `Tabs` | onglet actif ; flèches gauche et droite |
| `Card` | `section` | titre `h2`, zone d'actions facultative |
| `Chip` | `span` | `neutre`, `accent` |
| `LevelChip` | `span` | `liquidite`, `ipa`, `extreme`, `objectif` ; `pris` (pointillés, estompée) |
| `DirectionChip` | `span` + Lucide | `achat` (▲, sarcelle), `vente` (▼, magenta) |
| `LiveStatus` | `span role="status"` | `direct` (pastille sarcelle qui pulse), `retard`, `coupe` (orange, icône) ; texte toujours visible |
| `Table` | `table` sémantique | légende obligatoire, colonnes numériques à droite en chasse fixe, défilement horizontal si trop large |
| `Price` | `span` | 3 décimales, point, chasse fixe |
| `Time` | `time` | heure du Bénin `HH:MM`, option secondes ou date |
| `TextField` | React Aria `TextField` | libellé, aide, erreur ; `text`, `email`, `password` |
| `Checkbox` | React Aria `Checkbox` | coché, non coché, désactivé, erreur |
| `Select` | React Aria `Select` | ouvert, fermé, désactivé, erreur |
| `Loading` | `role="status"` | indicateur et texte « Chargement… », bloc squelette |
| `EmptyState` | `div` | icône, titre, phrase, action facultative |
| `ErrorState` | `div role="alert"` | icône, phrase, bouton « Réessayer » facultatif |
| `FeedBanner` | `div role="alert"` | « Flux de prix coupé depuis HH:MM. » + cause en français |

Règles communes : le bord d'un champ ou d'une case est en `--color-muted` (les bordures `--color-line` des cartes sont décoratives et trop pâles pour délimiter une zone à remplir) ; hauteur minimale 32 px (`pointer-fine`) et 44 × 44 px (`pointer-coarse`) pour toute zone interactive ; anneau de focus `outline` 2 px `accent`, décalé de 2 px, sur `data-focus-visible` seulement ; aucune action ni information disponible au seul survol.

**Libellés des causes de coupure** (`FeedBanner`, depuis `feed_outage.cause` de la spec 0002) : `timeout` « le fournisseur ne répond plus », `erreur_api` « le fournisseur renvoie une erreur », `reseau` « problème de réseau », `auth` « autorisation cTrader refusée ou expirée », `limite_api` « trop de demandes au fournisseur », `donnees_absentes` « le fournisseur n'a pas la bougie ». Une cause inconnue affiche « cause inconnue » et son code.

**Vitrine** (`frontend/src/vitrine/`) : sections Couleurs, Typographie, Espacements et rayons, Composants (chaque état côte à côte), Aperçu du graphique (SVG statique d'une vingtaine de bougies factices, tracé avec les jetons). Données dans `src/vitrine/donnees.ts`. Le squelette actuel (état du serveur) reste la page d'accueil, restylé avec les jetons, avec un lien discret vers la vitrine.

**Data model sketch** : aucun. Cette fonction ne lit ni n'écrit en base.

**API surface** :

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/{chemin}` (hors `/api`, sans fichier correspondant) | GET | chemin | `index.html` du cockpit | aucune pour l'instant ; la connexion (n°6) l'ajoutera | `/api/...` inconnu reste un 404 JSON ; un fichier statique absent avec extension (`.js`, `.css`…) reste un 404 |

**Value sourcing** :

| Action | Value produced / displayed | Source |
|---|---|---|
| Afficher un niveau | sa couleur | `kind` du composant → jeton `--color-level-<kind>` (`theme.css`) |
| Afficher un niveau | trait plein ou pointillé | prop `pris` (plus tard : l'état « pris » donné par le moteur, n°7) |
| Afficher un prix | texte `147.584` | prop `value` (chaîne décimale de l'api, `NUMERIC(10,3)` de la spec 0002), formatée à 3 décimales, sans passer par un flottant pour l'arrondi |
| Afficher une heure | `HH:MM` | prop `utc` (ISO 8601 UTC de l'api) + fuseau `Africa/Porto-Novo` (`AGENTS.md`), constante `DISPLAY_TIME_ZONE` dans `src/design/format.ts` |
| Afficher un nombre (pips, %, R) | `0,3` | prop `value` + `Intl.NumberFormat('fr-FR')` |
| Afficher l'état du flux | `direct`, `retard`, `coupe` | prop `etat` (plus tard : `GET /api/feed/status`, spec 0002 AC-11, branché par la n°7) |
| Bandeau « flux coupé » | heure de début, cause | props `depuis` (UTC) et `cause` (`feed_outage.cause`), libellé du tableau ci dessus |
| Taille des zones tactiles | 32 px ou 44 px | requête média `pointer` du navigateur (variantes `pointer-fine` et `pointer-coarse` de Tailwind), sans JavaScript |
| Animations | jouées ou non | requête média `prefers-reduced-motion` |
| Couleur du graphique (n°7) | valeur hexadécimale | `cssToken('--color-…')` lit la variable calculée sur `document.documentElement` |
| Contenu de la vitrine | bougies, niveaux, tableaux | constantes de `src/vitrine/donnees.ts`, marquées factices |

**Key invariants** :
- `theme.css` est la seule source des valeurs ; `design.md` en est le miroir, vérifié par test.
- Les quatre couleurs de niveaux sont uniques dans le thème et réservées aux niveaux.
- Aucune couleur en dur hors de `theme.css` ; la palette par défaut de Tailwind n'existe pas.
- Une couleur de niveau ne colore jamais un texte ; une information n'est jamais portée par la couleur seule (toujours un mot, une flèche ou une icône avec).
- Le cockpit ne charge rien depuis un domaine tiers.

**Security model** : la vitrine ne montre que des données factices et n'appelle aucune api. Dès la connexion (n°6), elle est protégée comme toutes les pages. Le renvoi vers `index.html` ne s'applique jamais sous `/api`, donc il ne masque aucune route de l'api et n'ouvre aucune donnée. Aucune ressource tierce (polices locales).

**Configuration required** : aucune variable d'environnement nouvelle.

**Critical test scenarios** :
- Happy path : la vitrine s'affiche avec chaque section et le badge « Données factices », et l'audit `vitest-axe` ne trouve aucune violation, verifies **AC-7**, **AC-12**
- Miroir : changer une valeur dans `theme.css` sans toucher `design.md` fait échouer le test du miroir, verifies **AC-1**
- Couleur réservée : une classe `text-level-ipa` ajoutée dans un autre fichier de `src/` fait échouer le garde, verifies **AC-2**
- Couleur en dur : un `#FF0000` ajouté dans un composant fait échouer le garde, verifies **AC-3**
- Contraste : abaisser `--color-faint` à `#5B6782` fait échouer le test de contraste, verifies **AC-4**
- Clavier : Tab atteint le bouton puis le groupe de bascules ; les flèches changent d'onglet ; Espace coche la case ; Entrée ouvre la liste de choix et les flèches la parcourent, verifies **AC-5**
- Toucher : un appui `touch` sur `Button` appelle `onPress` une seule fois et n'affiche pas l'anneau de focus, verifies **AC-5**, **AC-6**
- Formats : `Price` de `"147.5840"` donne `147.584` ; `Time` de `2026-10-15T13:05:00Z` donne `14:05` ; `0.3` pip donne `0,3`, verifies **AC-9**
- Rechargement : `GET /vitrine` sur l'api renvoie le `index.html` du cockpit ; `GET /api/inconnu` renvoie un 404 ; `GET /assets/absent.js` renvoie un 404, verifies **AC-7**
- Polices : aucune mention de `fonts.googleapis.com` ni `fonts.gstatic.com` sous `frontend/` (hors `node_modules`), verifies **AC-8**
- Sens et niveaux : `DirectionChip vente` affiche « ▼ Vente » ; `LevelChip liquidite pris` porte le style pointillé, verifies **AC-10**
- Mouvement réduit : avec `prefers-reduced-motion: reduce`, la pastille `LiveStatus` ne pulse pas, verifies **AC-11**
- Bandeau : `FeedBanner` avec `cause="auth"` affiche l'heure du Bénin et « autorisation cTrader refusée ou expirée » ; une cause inconnue affiche son code, verifies **AC-12**

## Build plan

Tracer Bullet : on fait d'abord passer un fil fin du jeton jusqu'au navigateur (thème, Tailwind, polices, page servie par l'`api`), puis on épaissit composant par composant.

1. Installer Tailwind v4 (`tailwindcss`, `@tailwindcss/vite`) et les trois polices Fontsource ; écrire `src/design/theme.css` (tous les jetons, palette par défaut retirée) ; remplacer `src/index.css` ; restyler le squelette d'accueil avec les jetons. Le build passe et l'`api` sert le cockpit restylé, satisfies **AC-1**, **AC-8**
2. Écrire `docs/design.md` (couleurs, typographies, espacements, rayons, tailles tactiles, styles de niveaux, paires de contraste, composants) et les tests du miroir, du contraste, des couleurs réservées, des couleurs en dur et des polices tierces, satisfies **AC-1**, **AC-2**, **AC-3**, **AC-4**, **AC-8**
3. Ajouter le renvoi vers `index.html` dans l'`api` (avec ses tests pytest) et la page `/vitrine` avec ses sections Couleurs et Typographie, choisie par `App` selon l'adresse, satisfies **AC-7**
4. Écrire `src/design/format.ts` (`Price`, `Time`, nombres français, `DISPLAY_TIME_ZONE`) et `cssToken()`, avec leurs tests, satisfies **AC-9**
5. Installer `react-aria-components` et `lucide-react` ; construire `Button`, `ToggleButton`, `ToggleButtonGroup`, `Tabs`, `Card`, `Chip`, `LevelChip`, `DirectionChip`, `LiveStatus`, `Table`, `Price`, `Time`, avec leurs tests clavier et toucher, et les ajouter à la vitrine, satisfies **AC-5**, **AC-6**, **AC-10**, **AC-11**
6. Construire `TextField`, `Checkbox`, `Select` avec leurs tests, et les ajouter à la vitrine, satisfies **AC-5**, **AC-6**
7. Construire `Loading`, `EmptyState`, `ErrorState`, `FeedBanner` avec leurs tests, et les ajouter à la vitrine, satisfies **AC-11**, **AC-12**
8. Ajouter l'aperçu statique du graphique à la vitrine, puis installer `vitest-axe` et auditer la page vitrine entière, satisfies **AC-7**, **AC-10**

## Consequences

**Positive**:
- Le trader lit le cockpit avec le code couleur qu'il connaît déjà, et un niveau ne se confond jamais avec une bougie ou un bouton.
- Le clavier, le toucher et l'accessibilité sont portés par une bibliothèque éprouvée plutôt que réécrits à la main.
- Les tests empêchent le code, `design.md` et les contrastes de diverger sans qu'on le voie.

**Negative / tradeoffs**:
- Les bougies grises ne ressemblent pas à TradingView : il faudra un temps d'habitude.
- React Aria alourdit le cockpit (de l'ordre de quelques dizaines de ko compressés pour ces composants) et impose sa façon de styler (attributs `data-*`).
- Trois teintes chaudes coexistent (rouge liquidité, magenta vente, orange erreur) : la règle « toujours un mot ou une icône » est ce qui les distingue, elle doit être tenue partout.
- Le renvoi vers `index.html` est une petite règle de plus côté serveur, à garder hors de `/api`.
- Un seul thème : un passage au clair plus tard demandera de revoir toutes les paires de contraste.

**Neutral**:
- Tailwind, React Aria, Lucide, Fontsource et `vitest-axe` entrent dans `frontend/package.json` avec cette fonction ; Lightweight Charts attend le fil minimal (n°7).
- Les tailles tactiles se vérifient dans un vrai navigateur, pas dans jsdom.

## Follow-up

- [ ] Fil minimal (n°7) : le graphique Lightweight Charts lit ses couleurs avec `cssToken()` (bougies, niveaux, styles vivant et pris), et l'image des alertes (mplfinance, côté serveur) reprend les mêmes valeurs. Prévoir un test pytest qui compare la palette Python à `theme.css`.
- [ ] Connexion (n°6) : protéger `/vitrine` comme le reste, et choisir alors une vraie bibliothèque de routage si les pages se multiplient.
- [ ] La skill `tailwind-4-docs` attend un instantané de la documentation de Tailwind (`python .claude/skills/tailwind-4-docs/scripts/sync_tailwind_docs.py --accept-docs-license`). Cette documentation est « source available », pas libre : c'est au trader d'accepter sa licence. Sans elle, la skill retombe sur ses fiches `gotchas.md` et `engineering-playbook.md`. L'instantané est exclu de git.
- [ ] `/sync` : ajouter les skills `react-aria` et `tailwind-4-docs` à la section `## Agent skills` de `frontend/AGENTS.md` (elles ne concernent que le cockpit), noter le serveur MCP React Aria comme refusé (`Declined:`), et remplacer la ligne « Styles provisoires… jusqu'au design system » par un renvoi à `docs/design.md`.
- [ ] Skill Lightweight Charts (`tradingview/lightweight-charts`, officielle) : proposée, à installer avec le fil minimal (n°7).
