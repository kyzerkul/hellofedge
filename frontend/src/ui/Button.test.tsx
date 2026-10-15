import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { Button } from './Button'

describe('Button', () => {
  it('is reached by Tab and shows the keyboard focus ring (AC-5)', async () => {
    const user = userEvent.setup()
    render(<Button>Valider</Button>)

    await user.tab()

    const button = screen.getByRole('button', { name: 'Valider' })
    expect(button).toHaveFocus()
    expect(button).toHaveAttribute('data-focus-visible')
  })

  it.each(['{Enter}', ' '])('runs its action once with %s (AC-5)', async (key) => {
    const user = userEvent.setup()
    const onPress = vi.fn()
    render(<Button onPress={onPress}>Valider</Button>)

    await user.tab()
    await user.keyboard(key)

    expect(onPress).toHaveBeenCalledTimes(1)
  })

  it('runs its action once on a finger tap, without the focus ring (AC-5, AC-6)', async () => {
    const user = userEvent.setup()
    const onPress = vi.fn()
    render(<Button onPress={onPress}>Valider</Button>)
    const button = screen.getByRole('button', { name: 'Valider' })

    await user.pointer({ keys: '[TouchA]', target: button })

    expect(onPress).toHaveBeenCalledTimes(1)
    expect(button).not.toHaveAttribute('data-focus-visible')
  })

  it('never shows the focus ring after a mouse click (AC-5)', async () => {
    const user = userEvent.setup()
    render(<Button>Valider</Button>)
    const button = screen.getByRole('button', { name: 'Valider' })

    await user.click(button)

    expect(button).not.toHaveAttribute('data-focus-visible')
  })

  it('does nothing when disabled', async () => {
    const user = userEvent.setup()
    const onPress = vi.fn()
    render(
      <Button onPress={onPress} isDisabled>
        Valider
      </Button>,
    )

    await user.click(screen.getByRole('button', { name: 'Valider' }))

    expect(onPress).not.toHaveBeenCalled()
  })

  it('keeps its label and blocks its action while pending', async () => {
    const user = userEvent.setup()
    const onPress = vi.fn()
    render(
      <Button onPress={onPress} isPending>
        Valider
      </Button>,
    )
    const button = screen.getByRole('button', { name: /Valider/ })

    await user.click(button)

    expect(button).toHaveTextContent('Valider')
    expect(button).toHaveAttribute('data-pending')
    expect(onPress).not.toHaveBeenCalled()
  })

  it('freezes a state for the showcase with data-demo', () => {
    render(<Button data-demo="hovered">Valider</Button>)

    expect(screen.getByRole('button', { name: 'Valider' })).toHaveAttribute('data-demo', 'hovered')
  })
})
