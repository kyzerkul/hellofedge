import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { axe } from 'vitest-axe'
import Vitrine from './Vitrine'

describe('Vitrine (AC-7)', () => {
  it('is marked as fake data at the top', () => {
    render(<Vitrine />)

    expect(screen.getByRole('heading', { level: 1, name: 'Vitrine du design system' })).toBeInTheDocument()
    expect(screen.getAllByText('Données factices')[0]).toBeInTheDocument()
  })

  it.each(['Couleurs', 'Typographie', 'Espacements et rayons', 'Composants', 'États', 'Aperçu du graphique'])(
    'has the %s section, listed in the page summary',
    (titre) => {
      render(<Vitrine />)

      expect(screen.getByRole('heading', { level: 2, name: titre })).toBeInTheDocument()
      const sommaire = screen.getByRole('navigation', { name: 'Sur cette page' })
      expect(within(sommaire).getByRole('link', { name: titre })).toBeInTheDocument()
    },
  )

  it('shows every colour with its role', () => {
    render(<Vitrine />)

    const couleurs = screen.getByRole('region', { name: 'Couleurs' })
    for (const jeton of ['--color-ink', '--color-accent', '--color-level-liquidity', '--color-candle-down', '--color-session-asia']) {
      expect(within(couleurs).getAllByText(jeton, { exact: false })[0]).toBeInTheDocument()
    }
  })

  it('draws the chart preview with every level named at its end', () => {
    render(<Vitrine />)

    const apercu = screen.getByRole('img', { name: /Aperçu factice/ })
    for (const nom of ['Liquidité', 'Liquidité · pris', 'IPA', 'Extrême', 'Objectif', 'Londres']) {
      expect(within(apercu).getByText(nom)).toBeInTheDocument()
    }
    expect(apercu.querySelector('[stroke-dasharray]')).toBeInTheDocument()
  })

  it('shows the four feed states and the outage banners', () => {
    render(<Vitrine />)

    const etats = screen.getByRole('region', { name: 'États' })
    for (const texte of ['En direct', 'En retard de 35 s', 'Flux coupé', 'Marché fermé']) {
      expect(within(etats).getByText(texte)).toBeInTheDocument()
    }
    expect(within(etats).getByText(/depuis le 14 oct\. à 22:40/)).toBeInTheDocument()
  })

  it('has no accessibility violation that axe can find without a browser (AC-7)', async () => {
    const { container } = render(<Vitrine />)

    // Les contrastes réels se mesurent dans un vrai navigateur, pendant /check verify.
    expect(await axe(container, { rules: { 'color-contrast': { enabled: false } } })).toHaveNoViolations()
  }, 30_000)
})
