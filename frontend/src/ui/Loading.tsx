import { LoaderCircle } from 'lucide-react'
import { cx } from './styles'

/** Chargement : un indicateur qui tourne et le mot, annoncés aux lecteurs d'écran. */
export function Loading({ texte = 'Chargement…', className }: { texte?: string; className?: string }) {
  return (
    <div role="status" className={cx('flex items-center gap-2 text-sm text-muted', className)}>
      <LoaderCircle aria-hidden size={20} className="animate-spin text-accent" />
      {texte}
    </div>
  )
}

/** Bloc squelette : la place d'un contenu qui arrive. Décoratif, `Loading` porte l'annonce. */
export function Skeleton({ className }: { className?: string }) {
  return <div aria-hidden className={cx('animate-pulse rounded-md bg-panel-2', className)} />
}
