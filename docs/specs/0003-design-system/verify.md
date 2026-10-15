# Verify: Design system et base de l'interface · spec 0003 · mis à jour le 2026-10-15
_Étapes tirées des critères d'acceptation de la spec 0003. `/check verify` les déroule ; `/test` verrouille celles qui durent._

## Navigateur (cockpit construit, servi par l'`api`)
- [ ] Ouvrir `/vitrine`, la recharger, puis faire pareil sur `/vitrine/` → la vitrine s'affiche, avec le badge « Données factices » en haut → AC-7
- [ ] Ouvrir `/foo` → « Page introuvable », avec un lien « Retour à l'accueil » vers `/` → AC-7
- [ ] La vitrine montre chaque couleur avec son rôle (et sa valeur lue dans le thème), l'échelle typographique, chaque composant dans chacun de ses états côte à côte, et l'aperçu du graphique → AC-7
- [ ] Émuler un écran tactile (`pointer: coarse`) et lire `getBoundingClientRect()` de chaque élément interactif → au moins 44 × 44 px (une case à cocher compte par son étiquette entière) → AC-6
- [ ] À la souris (`pointer: fine`) → chaque élément interactif fait au moins 32 px de haut → AC-6
- [ ] Un appui au doigt sur « Valider » (premier bouton de la vitrine) → le compteur avance d'une seule unité → AC-6
- [ ] Lancer axe dans Chromium sur `/`, `/vitrine` et `/foo` (contrastes réels compris) → aucune violation → AC-4, AC-7
- [ ] Avancer avec Tab dans la vitrine → l'anneau violet de 2 px suit le focus dans l'ordre de lecture ; les flèches changent d'onglet et de bascule ; Entrée ouvre la liste de choix → AC-5
- [ ] Cliquer sur un bouton → aucun anneau ; cliquer dans un champ de saisie → l'anneau apparaît → AC-5
- [ ] Activer « réduire les animations » dans le système → la pastille « En direct » ne pulse plus, la liste de choix s'ouvre sans animation → AC-11
- [ ] Onglet réseau des outils du navigateur → aucune requête vers un autre domaine ; les polices viennent de `/assets/` → AC-8
- [ ] Bloquer les polices (ou les supprimer de `dist/assets/`) → la pile de secours prend le relais, la mise en page tient → AC-8
- [ ] Aperçu du graphique : bougies grises, liquidité vivante en trait plein, liquidité prise en pointillés estompés, IPA, extrême, objectif, bande de Londres, chaque ligne nommée à droite → AC-7, AC-10
- [ ] Le trader ouvre la vitrine sur son téléphone (Codespace) et valide l'aspect, en particulier le trait blanc d'extrême posé sur des bougies claires → AC-2, AC-10
- [ ] Tableau des setups : prix à 3 décimales en chasse fixe (`147.500`), heures à l'heure du Bénin (`2026-10-14T23:55Z` affiché `15 oct. 00:55`) → AC-9
- [ ] Bandeaux « flux coupé » : la coupure du jour affiche `depuis 14:05`, celle de la veille `depuis le 14 oct. à 22:40`, la cause inconnue affiche son code → AC-12

## Sources des valeurs (une étape par ligne du tableau *Value sourcing*)
- [ ] Couleur d'un niveau : `LevelChip kind="ipa"` porte `border-level-ipa`, et la valeur calculée est `#2962FF` → AC-2
- [ ] Trait plein ou pris : `LevelChip pris` passe en pointillés, à 50 %, avec le mot « pris » → AC-10
- [ ] Prix : `formatPrice('147.5845')` donne `147.585`, `formatPrice('147.5')` donne `147.500`, `null` donne `—` → AC-9
- [ ] Heure : changer le fuseau du navigateur (par exemple `America/New_York`) ne change pas l'heure affichée, toujours celle du Bénin → AC-9
- [ ] Pips, R, % : `0,3 pip`, `2 pips`, `−1,5 R`, `+0,31 %` (espace fine insécable avant `%`) → AC-9
- [ ] État du flux : `LiveStatus` affiche « En direct », « En retard de 35 s », « Flux coupé », « Marché fermé » selon `etat` → AC-12
- [ ] Bandeau : changer `maintenant` d'un jour fait apparaître la date ; le jour se compte à l'heure du Bénin, pas en UTC → AC-12
- [ ] Taille des zones : passer de `pointer: fine` à `pointer: coarse` fait grandir les boutons de 32 à 44 px → AC-6
- [ ] Animations : la règle `prefers-reduced-motion` de `theme.css` coupe tout → AC-11
- [ ] État figé : `data-demo="hovered"` sur un bouton lui donne le bord du survol sans souris → AC-7
- [ ] Couleur pour le graphique : `cssToken('--color-level-liquidity')` renvoie `#f23645` dans le navigateur → AC-2
- [ ] Contenu de la vitrine : tout vient de `src/vitrine/donnees.ts`, aucune requête `/api` n'est faite sur `/vitrine` → AC-7

## Commandes
- [ ] `cd frontend && npm run typecheck && npm test && npm run build` → tout passe (miroir, contraste, gardes, formats, composants, axe) → AC-1 à AC-12
- [ ] Changer `--color-muted` dans `theme.css` sans toucher `design.md` → le test du miroir et celui du contraste échouent → AC-1, AC-4
- [ ] Ajouter `bg-red-500` ou `#FF0000` dans un composant, ou `text-level-ipa` dans `src/ui/Button.tsx` → les gardes échouent → AC-2, AC-3
- [ ] Ajouter `https://fonts.googleapis.com` dans `index.html` → la garde des domaines tiers échoue → AC-8
- [ ] `cd backend && uv run pytest tests/test_api.py` → `/vitrine` et `/vitrine/` renvoient `index.html` avec `no-cache` ; `/api/inconnu`, `/assets/absent.js` et `/favicon.ico` restent en 404 → AC-7

## Couverture des critères d'acceptation
- AC-1 : commandes 1 et 2 · AC-2 : navigateur 14, sources 1 et 11, commande 3 · AC-3 : commande 3 · AC-4 : navigateur 7, commande 2 · AC-5 : navigateur 8 et 9 · AC-6 : navigateur 4 à 6, source 8 · AC-7 : navigateur 1 à 3, 7 et 13, sources 10 et 12, commande 5 · AC-8 : navigateur 11 et 12, commande 4 · AC-9 : navigateur 15, sources 3 à 5 · AC-10 : navigateur 13 et 14, source 2 · AC-11 : navigateur 10, source 9 · AC-12 : navigateur 16, sources 6 et 7
