import { formatTime } from '../design/format'
import { cx } from './styles'

export interface TimeProps {
  /** Instant UTC, tel que l'api le donne (ISO 8601). */
  utc: string
  secondes?: boolean
  date?: boolean
  className?: string
}

/** Heure à l'heure du Bénin, 24 h. Le `<time>` garde l'instant UTC exact. */
export function Time({ utc, secondes, date, className }: TimeProps) {
  const parsed = new Date(utc)
  const iso = Number.isNaN(parsed.getTime()) ? undefined : parsed.toISOString()
  return (
    <time dateTime={iso} className={cx('font-mono whitespace-nowrap tabular-nums', className)}>
      {formatTime(utc, { secondes, date })}
    </time>
  )
}
