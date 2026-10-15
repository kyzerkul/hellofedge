import {
  ToggleButton as AriaToggleButton,
  type ToggleButtonProps as AriaToggleButtonProps,
  ToggleButtonGroup as AriaToggleButtonGroup,
  type ToggleButtonGroupProps as AriaToggleButtonGroupProps,
} from 'react-aria-components'
import { cx, disabled, focusRing, quick, touchSize } from './styles'

export interface ToggleButtonProps extends Omit<AriaToggleButtonProps, 'className'> {
  className?: string
}

/** Bouton à bascule (React Aria) : une unité de temps, un calque. */
export function ToggleButton({ className, ...props }: ToggleButtonProps) {
  return (
    <AriaToggleButton
      {...props}
      className={cx(
        'inline-flex cursor-default items-center justify-center gap-1.5 rounded-md border border-line bg-panel-2 px-2.5 text-sm font-medium text-text select-none',
        'demo-hovered:border-muted demo-pressed:bg-line demo-pressed:text-text',
        'data-[selected]:border-accent data-[selected]:bg-accent-soft data-[selected]:text-accent',
        touchSize,
        focusRing,
        quick,
        disabled,
        className,
      )}
    />
  )
}

export interface ToggleButtonGroupProps extends Omit<AriaToggleButtonGroupProps, 'className'> {
  className?: string
}

/**
 * Groupe de bascules (React Aria) : les flèches passent d'un bouton à l'autre.
 * Choix unique sans vide (`disallowEmptySelection`, unités de temps) ou multiple (calques).
 */
export function ToggleButtonGroup({ className, ...props }: ToggleButtonGroupProps) {
  return <AriaToggleButtonGroup {...props} className={cx('flex flex-wrap gap-1.5', className)} />
}
