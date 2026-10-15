// DONNÉES FACTICES : la vitrine ne lit aucune api. Rien ici ne vient du marché.

import type { Direction } from '../ui/DirectionChip'
import type { LevelKind } from '../ui/LevelChip'

/** Instant présent figé de la vitrine (UTC), pour que les dates affichées ne bougent pas. */
export const MAINTENANT = '2026-10-15T15:00:00Z'

export interface Bougie {
  open: number
  high: number
  low: number
  close: number
}

/** Une vingtaine de bougies M5 inventées : une prise de liquidité sous 147.420, puis une remontée. */
export const BOUGIES: Bougie[] = [
  { open: 147.585, high: 147.612, low: 147.566, close: 147.6 },
  { open: 147.6, high: 147.634, low: 147.588, close: 147.622 },
  { open: 147.622, high: 147.641, low: 147.594, close: 147.601 },
  { open: 147.601, high: 147.607, low: 147.552, close: 147.561 },
  { open: 147.561, high: 147.578, low: 147.526, close: 147.534 },
  { open: 147.534, high: 147.551, low: 147.508, close: 147.547 },
  { open: 147.547, high: 147.556, low: 147.49, close: 147.497 },
  { open: 147.497, high: 147.512, low: 147.461, close: 147.468 },
  { open: 147.468, high: 147.483, low: 147.432, close: 147.444 },
  { open: 147.444, high: 147.452, low: 147.398, close: 147.431 },
  { open: 147.431, high: 147.476, low: 147.426, close: 147.47 },
  { open: 147.47, high: 147.518, low: 147.462, close: 147.511 },
  { open: 147.511, high: 147.531, low: 147.493, close: 147.502 },
  { open: 147.502, high: 147.548, low: 147.497, close: 147.541 },
  { open: 147.541, high: 147.589, low: 147.533, close: 147.582 },
  { open: 147.582, high: 147.596, low: 147.554, close: 147.563 },
  { open: 147.563, high: 147.611, low: 147.558, close: 147.604 },
  { open: 147.604, high: 147.648, low: 147.596, close: 147.641 },
  { open: 147.641, high: 147.672, low: 147.629, close: 147.664 },
  { open: 147.664, high: 147.669, low: 147.638, close: 147.645 },
  { open: 147.645, high: 147.684, low: 147.64, close: 147.677 },
  { open: 147.677, high: 147.693, low: 147.661, close: 147.688 },
]

export interface Ligne {
  kind: LevelKind
  prix: number
  pris?: boolean
  nom: string
}

/** Niveaux tracés sur l'aperçu, chacun nommé à son extrémité droite. */
export const LIGNES: Ligne[] = [
  { kind: 'extreme', prix: 147.758, nom: 'Extrême' },
  { kind: 'liquidite', prix: 147.722, nom: 'Liquidité' },
  { kind: 'objectif', prix: 147.7, nom: 'Objectif' },
  { kind: 'ipa', prix: 147.505, nom: 'IPA' },
  { kind: 'liquidite', prix: 147.42, pris: true, nom: 'Liquidité · pris' },
]

/** Bande de session de l'aperçu : Londres, de la 8e bougie à la fin. */
export const SESSION = { nom: 'Londres', debut: 7 }

export interface Setup {
  id: string
  heure: string
  direction: Direction
  niveau: LevelKind
  entree: string
  stop: string
  objectif: string
  risquePips: number
  r: number
}

export const SETUPS: Setup[] = [
  {
    id: 's1',
    heure: '2026-10-15T08:35:00Z',
    direction: 'achat',
    niveau: 'liquidite',
    entree: '147.431',
    stop: '147.395',
    objectif: '147.700',
    risquePips: 3.6,
    r: 7.5,
  },
  {
    id: 's2',
    heure: '2026-10-15T13:10:00Z',
    direction: 'vente',
    niveau: 'extreme',
    entree: '147.752',
    stop: '147.781',
    objectif: '147.505',
    risquePips: 2.9,
    r: 8.5,
  },
  {
    id: 's3',
    heure: '2026-10-14T23:55:00Z',
    direction: 'achat',
    niveau: 'ipa',
    entree: '147.5',
    stop: '147.47',
    objectif: '147.6125',
    risquePips: 3,
    r: -1,
  },
]

export const UNITES = ['M1', 'M3', 'M5', 'M15', 'H1', 'H4']

export const CALQUES = [
  { id: 'liquidite', label: 'Liquidité' },
  { id: 'ipa', label: 'IPA' },
  { id: 'extremes', label: 'Extrêmes' },
  { id: 'objectifs', label: 'Objectifs' },
  { id: 'sessions', label: 'Sessions' },
]

export const SESSIONS_CHOIX = [
  { id: 'tokyo', label: 'Tokyo' },
  { id: 'francfort', label: 'Francfort' },
  { id: 'londres', label: 'Londres' },
  { id: 'newyork', label: 'New York' },
]

/** Coupures inventées pour le bandeau : une du jour, une de la veille, une cause inconnue. */
export const COUPURES = [
  { depuis: '2026-10-15T13:05:00Z', cause: 'timeout' },
  { depuis: '2026-10-14T21:40:00Z', cause: 'auth' },
  { depuis: '2026-10-15T14:52:00Z', cause: 'maintenance_x' },
]
