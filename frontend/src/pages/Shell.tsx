import type { ReactNode } from 'react'
import { cx, link } from '../ui/styles'

export type Page = 'accueil' | 'vitrine' | 'introuvable'

const NAV: { page: Page; href: string; label: string }[] = [
  { page: 'accueil', href: '/', label: 'Accueil' },
  { page: 'vitrine', href: '/vitrine', label: 'Vitrine' },
]

/** Cadre commun des pages : marque, navigation, contenu, pied de page. */
export function Shell({ page, children }: { page: Page; children: ReactNode }) {
  // Sur l'accueil, la marque est le titre de la page.
  const Brand = page === 'accueil' ? 'h1' : 'p'
  return (
    <div className="flex min-h-screen flex-col">
      <a
        href="#contenu"
        className="sr-only rounded-md bg-accent px-3 py-2 font-semibold text-ink focus:not-sr-only focus:absolute focus:top-3 focus:left-3 focus:z-30"
      >
        Aller au contenu
      </a>
      <header className="sticky top-0 z-20 border-b border-line-soft bg-ink/95 backdrop-blur-sm">
        <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3 sm:px-6">
          <a href="/" className="mr-auto flex items-center gap-3 rounded-md pointer-coarse:min-h-11 outline-hidden focus-visible:outline-2 focus-visible:outline-solid focus-visible:outline-offset-2 focus-visible:outline-accent">
            <span
              aria-hidden
              className="grid size-9 place-items-center rounded-lg border border-accent/35 bg-accent-soft font-display text-lg font-bold text-accent"
            >
              H
            </span>
            <span className="flex flex-col">
              <Brand className="m-0 font-display text-lg leading-tight font-bold text-text">Hellofedge</Brand>
              <span className="text-xs text-muted">Compagnon de trading USD/JPY</span>
            </span>
          </a>
          <nav aria-label="Navigation principale">
            <ul className="m-0 flex list-none gap-1 p-0">
              {NAV.map((item) => (
                <li key={item.page}>
                  <a
                    href={item.href}
                    aria-current={item.page === page ? 'page' : undefined}
                    className={cx(
                      'inline-flex items-center rounded-md px-3 text-sm font-medium text-muted no-underline',
                      'pointer-fine:min-h-8 pointer-coarse:min-h-11',
                      'hover:text-text aria-[current=page]:bg-panel-2 aria-[current=page]:text-text',
                      'outline-hidden focus-visible:outline-2 focus-visible:outline-solid focus-visible:outline-offset-2 focus-visible:outline-accent',
                    )}
                  >
                    {item.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </header>
      <main id="contenu" tabIndex={-1} className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 outline-hidden sm:px-6">
        {children}
      </main>
      <footer className="border-t border-line-soft">
        <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center justify-between gap-2 px-4 py-4 text-xs text-muted sm:px-6">
          <p className="m-0">Hellofedge analyse, surveille, alerte et journalise. Il ne passe jamais d'ordre.</p>
          <p className="m-0">
            Heures à l'heure du Bénin (UTC+1) ·{' '}
            <a href="/vitrine" className={link}>
              design system
            </a>
          </p>
        </div>
      </footer>
    </div>
  )
}
