import { WifiOff } from 'lucide-react'
import { cx } from './styles'

export type FeedState = 'direct' | 'retard' | 'coupe' | 'ferme'

export interface LiveStatusProps {
  etat: FeedState
  /** Retard en secondes, pour l'état `retard`. */
  retardSecondes?: number
  className?: string
}

/**
 * État du flux de prix (spec 0003, *État du flux*). Composant pur : le fil minimal (n°7)
 * calcule `etat` à partir de `GET /api/feed/status` et de l'horloge.
 */
export function LiveStatus({ etat, retardSecondes = 0, className }: LiveStatusProps) {
  return (
    <span
      role="status"
      data-etat={etat}
      className={cx('inline-flex items-center gap-2 text-sm whitespace-nowrap text-text', className)}
    >
      {etat === 'direct' && <span aria-hidden className="size-2 rounded-full bg-buy animate-live-pulse" />}
      {etat === 'retard' && <span aria-hidden className="size-2.5 rounded-full border-2 border-muted" />}
      {etat === 'coupe' && <WifiOff aria-hidden size={16} className="text-danger" />}
      {etat === 'ferme' && <span aria-hidden className="size-2 rounded-full bg-muted" />}
      {etat === 'direct' && 'En direct'}
      {etat === 'retard' && `En retard de ${Math.round(retardSecondes)} s`}
      {etat === 'coupe' && 'Flux coupé'}
      {etat === 'ferme' && 'Marché fermé'}
    </span>
  )
}
