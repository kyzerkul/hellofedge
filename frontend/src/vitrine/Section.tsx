import type { ReactNode } from 'react'

/** Section de la vitrine, ancrée pour la table des matières. */
export function Section({ id, titre, intro, children }: { id: string; titre: string; intro?: ReactNode; children: ReactNode }) {
  return (
    <section id={id} aria-labelledby={`${id}-titre`} className="scroll-mt-24">
      <div className="mb-4 flex flex-col gap-1">
        <h2 id={`${id}-titre`} className="m-0 text-lg">
          {titre}
        </h2>
        {intro && <p className="m-0 max-w-3xl text-sm text-muted">{intro}</p>}
      </div>
      {children}
    </section>
  )
}

/** Un état d'un composant, nommé dessous. */
export function Etat({ nom, children }: { nom: string; children: ReactNode }) {
  return (
    <figure className="m-0 flex min-w-0 flex-col items-start gap-2">
      <div className="flex min-h-11 items-center">{children}</div>
      <figcaption className="text-xs text-muted">{nom}</figcaption>
    </figure>
  )
}
