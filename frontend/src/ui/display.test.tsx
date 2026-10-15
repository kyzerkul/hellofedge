import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Card } from './Card'
import { Chip } from './Chip'
import { DirectionChip } from './DirectionChip'
import { LevelChip } from './LevelChip'
import { Price } from './Price'
import { Table } from './Table'
import { Time } from './Time'

describe('LevelChip (AC-10)', () => {
  it.each([
    ['liquidite', 'Liquidité', 'border-level-liquidity'],
    ['ipa', 'IPA', 'border-level-ipa'],
    ['extreme', 'Extrême', 'border-level-extreme'],
    ['objectif', 'Objectif', 'border-level-target'],
  ] as const)('names the %s level in words, its colour on the border only', (kind, nom, bord) => {
    render(<LevelChip kind={kind} />)

    const chip = screen.getByText(nom).parentElement!
    expect(chip).toHaveClass(bord, 'text-text')
    expect(chip).not.toHaveClass('border-dashed')
  })

  it('shows a taken liquidity dashed, faded, with the word « pris »', () => {
    render(<LevelChip kind="liquidite" pris />)

    const chip = screen.getByText('Liquidité · pris').parentElement!
    expect(chip).toHaveAttribute('data-pris')
    expect(chip).toHaveClass('border-dashed', 'border-level-liquidity/50', 'text-text')
  })
})

describe('DirectionChip (AC-10)', () => {
  it('shows a buy with the word and an upward triangle', () => {
    render(<DirectionChip direction="achat" />)

    const chip = screen.getByText('Achat')
    expect(chip).toHaveAttribute('data-direction', 'achat')
    expect(chip.querySelector('svg')).not.toHaveClass('rotate-180')
  })

  it('shows a sell with the word and a downward triangle', () => {
    render(<DirectionChip direction="vente" />)

    const chip = screen.getByText('Vente')
    expect(chip).toHaveAttribute('data-direction', 'vente')
    expect(chip.querySelector('svg')).toHaveClass('rotate-180', 'text-sell')
  })
})

describe('Price and Time (AC-9)', () => {
  it('shows a price with three decimals in monospace digits', () => {
    render(<Price value="147.5" />)

    expect(screen.getByText('147.500')).toHaveClass('font-mono', 'tabular-nums')
  })

  it('shows Benin time and keeps the exact UTC instant in the time element', () => {
    render(<Time utc="2026-10-15T23:05:00Z" />)

    const time = screen.getByText('00:05')
    expect(time.tagName).toBe('TIME')
    expect(time).toHaveAttribute('datetime', '2026-10-15T23:05:00.000Z')
  })
})

describe('Card and Chip', () => {
  it('names its section with its title, at level 2 by default', () => {
    render(<Card titre="Setups">contenu</Card>)

    expect(screen.getByRole('region', { name: 'Setups' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { level: 2, name: 'Setups' })).toBeInTheDocument()
  })

  it('takes another title level and actions', () => {
    render(
      <Card titre="Journal" level={3} actions={<Chip tone="accent">M5</Chip>}>
        contenu
      </Card>,
    )

    expect(screen.getByRole('heading', { level: 3, name: 'Journal' })).toBeInTheDocument()
    expect(screen.getByText('M5')).toHaveClass('text-accent')
  })
})

describe('Table', () => {
  const rows = [
    { id: 'a', heure: '09:35', prix: '147.431' },
    { id: 'b', heure: '14:10', prix: '147.752' },
  ]

  function Setups() {
    return (
      <Table
        legende="Setups du jour"
        rows={rows}
        rowKey={(r) => r.id}
        columns={[
          { key: 'heure', titre: 'Heure', cell: (r) => r.heure },
          { key: 'prix', titre: 'Entrée', numerique: true, cell: (r) => r.prix },
        ]}
      />
    )
  }

  it('has a caption and column headers', () => {
    render(<Setups />)

    expect(screen.getByRole('table', { name: 'Setups du jour' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Entrée' })).toHaveClass('text-right')
  })

  it('aligns numbers to the right in monospace digits', () => {
    render(<Setups />)

    expect(screen.getByRole('cell', { name: '147.431' })).toHaveClass('text-right', 'font-mono')
  })

  it('scrolls from the keyboard: a named region in the tab order', () => {
    render(<Setups />)

    const region = screen.getByRole('region', { name: 'Setups du jour' })
    expect(region).toHaveAttribute('tabindex', '0')
  })
})
