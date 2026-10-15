import { formatPrice } from '../design/format'
import { cx } from './styles'

/** Prix comme sur le graphique du trader : chasse fixe, exactement 3 décimales. */
export function Price({ value, className }: { value: string | null | undefined; className?: string }) {
  return <span className={cx('font-mono tabular-nums', className)}>{formatPrice(value)}</span>
}
