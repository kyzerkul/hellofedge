import { Inbox } from 'lucide-react'
import type { ReactNode } from 'react'
import { cx } from './styles'

export interface EmptyStateProps {
  titre: string
  phrase: string
  /** Niveau du titre dans la page (2 par défaut). */
  level?: 1 | 2 | 3 | 4
  action?: ReactNode
  className?: string
}

/** État vide : une icône, un titre, une phrase, une action facultative. */
export function EmptyState({ titre, phrase, level = 2, action, className }: EmptyStateProps) {
  const Heading = `h${level}` as const
  return (
    <div className={cx('flex flex-col items-center gap-2 px-4 py-8 text-center', className)}>
      <span aria-hidden className="mb-1 grid size-10 place-items-center rounded-full border border-line bg-panel-2 text-muted">
        <Inbox size={20} />
      </span>
      <Heading className="m-0 text-base">{titre}</Heading>
      <p className="m-0 max-w-prose text-sm text-muted">{phrase}</p>
      {action && <div className="mt-2">{action}</div>}
    </div>
  )
}
