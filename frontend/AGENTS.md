# Frontend (cockpit)

Le cockpit : une appli React 19 et TypeScript construite par Vite. En production, ses fichiers construits (`dist/`) sont servis par l'`api` Python, sans serveur Node. Décision : spec [0001](../docs/specs/0001-stack-architecture/index.md).

## Fichiers
- `src/App.tsx` : squelette actuel, il affiche seulement l'état du serveur (`/api/health`).
- `vite.config.ts` : en développement, `/api` est relayé vers l'api locale (`http://localhost:8000`).
- `vitest.config.ts` et `src/test/setup.ts` : tests dans jsdom avec les assertions de Testing Library.

## Commandes (depuis `frontend/`)
- Installer : `npm ci`
- Développer : `npm run dev` (lancer aussi l'api du backend)
- Construire : `npm run build` (vérification TypeScript, puis `dist/`)
- Vérifier les types : `npm run typecheck`
- Tests : `npm test`

## Conventions
- Tous les textes affichés sont en français.
- Les appels à l'api utilisent des chemins relatifs (`/api/...`), jamais une adresse en dur.
- Tests à côté du fichier testé (`*.test.tsx`), avec Testing Library : on vérifie ce que la personne voit, et on simule `fetch` à la frontière.
- Styles provisoires dans `src/index.css`, jusqu'au design system (scope n°5).
- Tailwind, TanStack Query, Lightweight Charts et la PWA s'installent avec la fonction qui en a besoin. ESLint et Prettier (prévus par la spec) viendront avec `/audit`.

_Drafted by /sync from the introducing change, worth a quick human pass._
