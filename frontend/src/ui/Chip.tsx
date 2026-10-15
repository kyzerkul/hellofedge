import type { ReactNode } from 'react'
import { cx } from './styles'

export type ChipTone = 'neutre' | 'accent'

const TONES: Record<ChipTone, string> = {
  neutre: 'border-line bg-panel-2 text-muted',
  accent: 'border-accent/40 bg-accent-soft text-accent',
}

/** Puce d'information, sans action. */
export function Chip({ tone = 'neutre', className, children }: { tone?: ChipTone; className?: string; children: ReactNode }) {
  return (
    <span
      className={cx(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold whitespace-nowrap',
        TONES[tone],
        className,
      )}
    >
      {children}
    </span>
  )
}
