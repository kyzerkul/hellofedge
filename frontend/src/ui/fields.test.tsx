import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { Checkbox } from './Checkbox'
import { Select } from './Select'
import { TextField } from './TextField'

const SESSIONS = [
  { id: 'tokyo', label: 'Tokyo' },
  { id: 'londres', label: 'Londres' },
  { id: 'newyork', label: 'New York' },
]

describe('TextField', () => {
  it('ties its label and its help to the input', () => {
    render(<TextField label="Adresse e-mail" type="email" description="Celle de ton compte." />)

    const input = screen.getByRole('textbox', { name: 'Adresse e-mail' })
    expect(input).toHaveAttribute('type', 'email')
    expect(input).toHaveAccessibleDescription('Celle de ton compte.')
  })

  it('shows the focus ring at any focus, even on a click (AC-5)', async () => {
    const user = userEvent.setup()
    render(<TextField label="Nom" />)
    const input = screen.getByRole('textbox', { name: 'Nom' })

    await user.click(input)

    expect(input).toHaveAttribute('data-focused')
  })

  it('shows its error with an icon and ties it to the input', () => {
    render(<TextField label="Seuil" isInvalid errorMessage="Écris un nombre." />)

    const input = screen.getByRole('textbox', { name: 'Seuil' })
    expect(input).toHaveAttribute('aria-invalid', 'true')
    expect(input).toHaveAccessibleDescription('Écris un nombre.')
  })

  it('cannot be typed in when disabled', async () => {
    const user = userEvent.setup()
    render(<TextField label="Fuseau" isDisabled />)

    await user.type(screen.getByRole('textbox', { name: 'Fuseau' }), 'abc')

    expect(screen.getByRole('textbox', { name: 'Fuseau' })).toHaveValue('')
  })
})

describe('Checkbox', () => {
  it('is checked with Space after Tab (AC-5)', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<Checkbox onChange={onChange}>Alerte Telegram</Checkbox>)

    await user.tab()
    await user.keyboard(' ')

    expect(screen.getByRole('checkbox', { name: 'Alerte Telegram' })).toBeChecked()
    expect(onChange).toHaveBeenCalledWith(true)
  })

  it('is checked once by a finger tap on its label (AC-6)', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<Checkbox onChange={onChange}>Alerte Telegram</Checkbox>)

    await user.pointer({ keys: '[TouchA]', target: screen.getByText('Alerte Telegram') })

    expect(onChange).toHaveBeenCalledTimes(1)
    expect(screen.getByRole('checkbox')).toBeChecked()
  })

  it('shows its error', () => {
    render(
      <Checkbox isInvalid errorMessage="Coche pour continuer.">
        J'ai lu les règles
      </Checkbox>,
    )

    expect(screen.getByText('Coche pour continuer.')).toBeInTheDocument()
    expect(screen.getByRole('checkbox')).toHaveAttribute('aria-invalid', 'true')
  })
})

describe('Select', () => {
  it('opens with Enter, moves with the arrows and picks with Enter (AC-5)', async () => {
    const user = userEvent.setup()
    const onSelectionChange = vi.fn()
    render(<Select label="Session" options={SESSIONS} onSelectionChange={onSelectionChange} />)

    await user.tab()
    const trigger = screen.getByRole('button', { name: /Session/ })
    expect(trigger).toHaveAttribute('data-focus-visible')
    await user.keyboard('{Enter}')
    const listbox = await screen.findByRole('listbox')
    expect(within(listbox).getAllByRole('option')).toHaveLength(3)
    await user.keyboard('{ArrowDown}{Enter}')

    expect(onSelectionChange).toHaveBeenCalledWith('londres')
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
    expect(trigger).toHaveTextContent('Londres')
  })

  it('says what to do when nothing is chosen', () => {
    render(<Select label="Session" options={SESSIONS} />)

    expect(screen.getByRole('button', { name: /Session/ })).toHaveTextContent('Choisir…')
  })

  it('shows its error', () => {
    render(<Select label="Session" options={SESSIONS} isInvalid errorMessage="Choisis une session." />)

    expect(screen.getByText('Choisis une session.')).toBeInTheDocument()
  })

  it('does not open when disabled', async () => {
    const user = userEvent.setup()
    render(<Select label="Session" options={SESSIONS} isDisabled />)

    await user.click(screen.getByRole('button', { name: /Session/ }))

    expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  })
})
