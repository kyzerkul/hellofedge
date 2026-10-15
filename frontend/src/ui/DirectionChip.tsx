import { Triangle } from 'lucide-react'
import { cx } from './styles'

export type Direction = 'achat' | 'vente'

const DIRECTIONS: Record<Direction, { mot: string; icone: string }> = {
  achat: { mot: 'Achat', icone: 'fill-buy text-buy' },
  vente: { mot: 'Vente', icone: 'rotate-180 fill-sell text-sell' },
}

/** Sens d'un setup : toujours un triangle et le mot. La couleur est sur l'icône, le texte reste clair. */
export function DirectionChip({ direction, className }: { direction: Direction; className?: string }) {
  const d = DIRECTIONS[direction]
  return (
    <span
      data-direction={direction}
      className={cx(
        'inline-flex items-center gap-1.5 rounded-full border border-line bg-panel-2 px-2.5 py-0.5 text-xs font-semibold whitespace-nowrap text-text',
        className,
      )}
    >
      <Triangle aria-hidden size={12} strokeWidth={2.5} className={d.icone} />
      {d.mot}
    </span>
  )
}
