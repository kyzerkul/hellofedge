import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { Button } from './Button'
import { ToggleButton, ToggleButtonGroup } from './ToggleButton'

function Unites() {
  return (
    <>
      <Button>Avant</Button>
      <ToggleButtonGroup aria-label="Unité de temps" selectionMode="single" disallowEmptySelection defaultSelectedKeys={['M5']}>
        <ToggleButton id="M1">M1</ToggleButton>
        <ToggleButton id="M3">M3</ToggleButton>
        <ToggleButton id="M5">M5</ToggleButton>
      </ToggleButtonGroup>
    </>
  )
}

const pressed = (name: string) => screen.getByRole('radio', { name }).getAttribute('aria-checked')

describe('ToggleButtonGroup', () => {
  it('is reached by Tab right after the button before it (AC-5)', async () => {
    const user = userEvent.setup()
    render(<Unites />)

    await user.tab()
    expect(screen.getByRole('button', { name: 'Avant' })).toHaveFocus()
    await user.tab()

    expect(screen.getByRole('radio', { name: 'M1' })).toHaveFocus()
    expect(screen.getByRole('radio', { name: 'M1' })).toHaveAttribute('data-focus-visible')
    await user.tab()
    expect(document.body).toHaveFocus()
  })

  it('moves between items with the arrows and selects with Space (AC-5)', async () => {
    const user = userEvent.setup()
    render(<Unites />)

    await user.tab()
    await user.tab()
    await user.keyboard('{ArrowRight}')
    expect(screen.getByRole('radio', { name: 'M3' })).toHaveFocus()
    await user.keyboard(' ')

    expect(pressed('M3')).toBe('true')
    expect(pressed('M5')).toBe('false')
  })

  it('never leaves the time frame choice empty', async () => {
    const user = userEvent.setup()
    render(<Unites />)

    await user.click(screen.getByRole('radio', { name: 'M5' }))

    expect(pressed('M5')).toBe('true')
  })

  it('lets the layers be all switched off', async () => {
    const user = userEvent.setup()
    render(
      <ToggleButtonGroup aria-label="Calques" selectionMode="multiple" defaultSelectedKeys={['ipa']}>
        <ToggleButton id="liquidite">Liquidité</ToggleButton>
        <ToggleButton id="ipa">IPA</ToggleButton>
      </ToggleButtonGroup>,
    )
    const ipa = screen.getByRole('button', { name: 'IPA' })

    await user.click(screen.getByRole('button', { name: 'Liquidité' }))
    await user.click(ipa)
    await user.click(screen.getByRole('button', { name: 'Liquidité' }))

    expect(screen.getByRole('button', { name: 'Liquidité' })).toHaveAttribute('aria-pressed', 'false')
    expect(ipa).toHaveAttribute('aria-pressed', 'false')
  })
})
