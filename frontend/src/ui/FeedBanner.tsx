import { WifiOff } from 'lucide-react'
import { formatTime, sameDisplayDay } from '../design/format'
import { cx } from './styles'

/** Libellés des causes de coupure (`feed_outage.cause`, spec 0002). */
export const OUTAGE_CAUSES: Record<string, string> = {
  timeout: 'le fournisseur ne répond plus',
  erreur_api: 'le fournisseur renvoie une erreur',
  reseau: 'problème de réseau',
  auth: 'autorisation cTrader refusée ou expirée',
  limite_api: 'trop de demandes au fournisseur',
  donnees_absentes: "le fournisseur n'a pas la bougie",
}

export function outageCause(cause: string): string {
  return Object.hasOwn(OUTAGE_CAUSES, cause) ? OUTAGE_CAUSES[cause] : `cause inconnue (${cause})`
}

export interface FeedBannerProps {
  /** Début de la coupure, en UTC. */
  depuis: string
  /** Code de la cause (`feed_outage.cause`). */
  cause: string
  /** Instant présent, en UTC (l'horloge par défaut) : la date s'affiche si la coupure date d'un autre jour. */
  maintenant?: string | Date
  className?: string
}

/** Bandeau « flux coupé » : depuis quand, à l'heure du Bénin, et pourquoi. */
export function FeedBanner({ depuis, cause, maintenant = new Date(), className }: FeedBannerProps) {
  const quand = sameDisplayDay(depuis, maintenant)
    ? formatTime(depuis)
    : `le ${formatTime(depuis, { date: true }).replace(/ (\d\d:\d\d)$/, ' à $1')}`
  return (
    <div
      role="alert"
      className={cx(
        'flex items-start gap-3 rounded-md border border-danger/50 border-l-4 border-l-danger bg-panel px-3 py-2.5 text-sm text-text',
        className,
      )}
    >
      <WifiOff aria-hidden size={20} className="mt-px shrink-0 text-danger" />
      <p className="m-0">
        Flux de prix coupé depuis {quand}. Cause : {outageCause(cause)}.
      </p>
    </div>
  )
}
