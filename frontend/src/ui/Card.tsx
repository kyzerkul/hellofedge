import { type ReactNode, useId } from 'react'
import { cx } from './styles'

export interface CardProps {
  titre: ReactNode
  /** Niveau du titre dans la page (2 par défaut). */
  level?: 2 | 3 | 4
  /** Actions facultatives, à droite du titre. */
  actions?: ReactNode
  className?: string
  children?: ReactNode
}

/** Carte : une section nommée par son titre, avec une zone d'actions facultative. */
export function Card({ titre, level = 2, actions, className, children }: CardProps) {
  const id = useId()
  const Heading = `h${level}` as const
  return (
    <section aria-labelledby={id} className={cx('min-w-0 rounded-lg border border-line bg-panel p-4', className)}>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2.5">
        <Heading id={id} className="m-0 text-base">
          {titre}
        </Heading>
        {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
      </div>
      {children}
    </section>
  )
}
