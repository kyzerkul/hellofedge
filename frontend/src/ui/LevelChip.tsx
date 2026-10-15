import type { ReactNode } from 'react'
import { cx } from './styles'

export type LevelKind = 'liquidite' | 'ipa' | 'extreme' | 'objectif'

// Table fixe de classes complètes : Tailwind ne génère pas une classe construite à la volée.
// La couleur du niveau ne colore jamais le texte : seulement la pastille et la bordure.
const LEVELS: Record<LevelKind, { nom: string; vivant: string; pris: string; pastille: string; pastillePrise: string }> = {
  liquidite: {
    nom: 'Liquidité',
    vivant: 'border-level-liquidity',
    pris: 'border-level-liquidity/50',
    pastille: 'bg-level-liquidity',
    pastillePrise: 'bg-level-liquidity/50',
  },
  ipa: {
    nom: 'IPA',
    vivant: 'border-level-ipa',
    pris: 'border-level-ipa/50',
    pastille: 'bg-level-ipa',
    pastillePrise: 'bg-level-ipa/50',
  },
  extreme: {
    nom: 'Extrême',
    vivant: 'border-level-extreme',
    pris: 'border-level-extreme/50',
    pastille: 'bg-level-extreme',
    pastillePrise: 'bg-level-extreme/50',
  },
  objectif: {
    nom: 'Objectif',
    vivant: 'border-level-target',
    pris: 'border-level-target/50',
    pastille: 'bg-level-target',
    pastillePrise: 'bg-level-target/50',
  },
}

export interface LevelChipProps {
  kind: LevelKind
  /** Niveau pris : bordure en pointillés, pastille et bordure à 50 %, mot « pris ». */
  pris?: boolean
  /** Précision facultative après le nom (un prix, une unité de temps…). */
  children?: ReactNode
  className?: string
}

/** Puce d'un niveau, au code couleur de TradingView, toujours nommée en toutes lettres. */
export function LevelChip({ kind, pris = false, children, className }: LevelChipProps) {
  const level = LEVELS[kind]
  return (
    <span
      data-kind={kind}
      data-pris={pris || undefined}
      className={cx(
        'inline-flex items-center gap-1.5 rounded-full border bg-panel-2 px-2.5 py-0.5 text-xs font-semibold whitespace-nowrap text-text',
        pris ? cx('border-dashed', level.pris) : level.vivant,
        className,
      )}
    >
      <span aria-hidden className={cx('size-2 shrink-0 rounded-full', pris ? level.pastillePrise : level.pastille)} />
      <span>
        {level.nom}
        {pris && ' · pris'}
      </span>
      {children}
    </span>
  )
}
