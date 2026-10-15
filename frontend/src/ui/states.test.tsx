import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { EmptyState } from './EmptyState'
import { ErrorState } from './ErrorState'
import { FeedBanner, OUTAGE_CAUSES } from './FeedBanner'
import { LiveStatus } from './LiveStatus'
import { Loading } from './Loading'

describe('Loading, EmptyState, ErrorState (AC-12)', () => {
  it('announces the loading with an icon and words', () => {
    render(<Loading />)

    const status = screen.getByRole('status')
    expect(status).toHaveTextContent('Chargement…')
    expect(status.querySelector('svg')).toBeInTheDocument()
  })

  it('shows an empty state with an icon, a title, a sentence and an action', () => {
    render(<EmptyState titre="Aucun setup" phrase="Rien pour l'instant." action={<button>Voir</button>} />)

    expect(screen.getByRole('heading', { level: 2, name: 'Aucun setup' })).toBeInTheDocument()
    expect(screen.getByText("Rien pour l'instant.")).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Voir' })).toBeInTheDocument()
    expect(document.querySelector('svg')).toBeInTheDocument()
  })

  it('shows an error as an alert with an icon and a sentence', () => {
    render(<ErrorState phrase="Le journal n'a pas pu être chargé." />)

    const alert = screen.getByRole('alert')
    expect(alert).toHaveTextContent("Le journal n'a pas pu être chargé.")
    expect(alert.querySelector('svg')).toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('offers « Réessayer » when it can retry', async () => {
    const user = userEvent.setup()
    const onRetry = vi.fn()
    render(<ErrorState phrase="Erreur." onRetry={onRetry} />)

    await user.click(screen.getByRole('button', { name: 'Réessayer' }))

    expect(onRetry).toHaveBeenCalledTimes(1)
  })
})

describe('LiveStatus (AC-12)', () => {
  it.each([
    ['direct', 'En direct'],
    ['coupe', 'Flux coupé'],
    ['ferme', 'Marché fermé'],
  ] as const)('says %s in words', (etat, texte) => {
    render(<LiveStatus etat={etat} />)

    expect(screen.getByRole('status')).toHaveTextContent(texte)
  })

  it('says how late the feed is', () => {
    render(<LiveStatus etat="retard" retardSecondes={35} />)

    expect(screen.getByRole('status')).toHaveTextContent('En retard de 35 s')
  })

  it('pulses only when live', () => {
    const { container, rerender } = render(<LiveStatus etat="direct" />)
    expect(container.querySelector('.animate-live-pulse')).toBeInTheDocument()

    rerender(<LiveStatus etat="ferme" />)
    expect(container.querySelector('.animate-live-pulse')).not.toBeInTheDocument()
  })
})

describe('FeedBanner (AC-12)', () => {
  const MAINTENANT = '2026-10-15T15:00:00Z'

  it.each(Object.entries(OUTAGE_CAUSES))('explains the cause %s in French, with the Benin time', (cause, libelle) => {
    render(<FeedBanner depuis="2026-10-15T13:05:00Z" cause={cause} maintenant={MAINTENANT} />)

    expect(screen.getByRole('alert')).toHaveTextContent(`Flux de prix coupé depuis 14:05. Cause : ${libelle}.`)
  })

  it('covers the six causes of spec 0002', () => {
    expect(Object.keys(OUTAGE_CAUSES).sort()).toEqual(
      ['auth', 'donnees_absentes', 'erreur_api', 'limite_api', 'reseau', 'timeout'].sort(),
    )
  })

  it('shows the code of an unknown cause', () => {
    render(<FeedBanner depuis="2026-10-15T13:05:00Z" cause="maintenance_x" maintenant={MAINTENANT} />)

    expect(screen.getByRole('alert')).toHaveTextContent('Cause : cause inconnue (maintenance_x).')
  })

  it('does not take an inherited name as a known cause', () => {
    render(<FeedBanner depuis="2026-10-15T13:05:00Z" cause="toString" maintenant={MAINTENANT} />)

    expect(screen.getByRole('alert')).toHaveTextContent('cause inconnue (toString)')
  })

  it('adds the date when the outage started another day in Benin', () => {
    render(<FeedBanner depuis="2026-10-14T21:40:00Z" cause="auth" maintenant={MAINTENANT} />)

    expect(screen.getByRole('alert')).toHaveTextContent('Flux de prix coupé depuis le 14 oct. à 22:40.')
  })

  it('uses the Benin day, not the UTC day', () => {
    // 23:30 UTC le 14 = 00:30 le 15 au Bénin : même jour que maintenant.
    render(<FeedBanner depuis="2026-10-14T23:30:00Z" cause="reseau" maintenant={MAINTENANT} />)

    expect(screen.getByRole('alert')).toHaveTextContent('Flux de prix coupé depuis 00:30.')
  })
})
