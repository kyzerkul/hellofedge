import { TriangleAlert } from 'lucide-react'
import { Button } from './Button'
import { cx } from './styles'

export interface ErrorStateProps {
  phrase: string
  /** Facultatif : affiche le bouton « Réessayer ». */
  onRetry?: () => void
  className?: string
}

/** Erreur : une icône et une phrase, jamais une couleur seule ; « Réessayer » si on peut. */
export function ErrorState({ phrase, onRetry, className }: ErrorStateProps) {
  return (
    <div
      role="alert"
      className={cx('flex flex-wrap items-center gap-3 rounded-md border border-danger/50 bg-panel-2 px-3 py-2.5 text-sm text-text', className)}
    >
      <TriangleAlert aria-hidden size={20} className="shrink-0 text-danger" />
      <p className="m-0 min-w-0 flex-1">{phrase}</p>
      {onRetry && (
        <Button variant="secondaire" onPress={onRetry}>
          Réessayer
        </Button>
      )}
    </div>
  )
}
