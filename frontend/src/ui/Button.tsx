import { LoaderCircle } from 'lucide-react'
import { Button as AriaButton, type ButtonProps as AriaButtonProps, composeRenderProps } from 'react-aria-components'
import { cx, disabled, focusRing, quick, touchSize } from './styles'

export type ButtonVariant = 'primaire' | 'secondaire' | 'discret'

export interface ButtonProps extends Omit<AriaButtonProps, 'className'> {
  variant?: ButtonVariant
  className?: string
}

const VARIANTS: Record<ButtonVariant, string> = {
  primaire: 'border-accent bg-accent font-semibold text-ink demo-hovered:opacity-90',
  secondaire: 'border-line bg-panel-2 font-medium text-text demo-hovered:border-muted',
  discret: 'border-transparent bg-transparent font-medium text-text demo-hovered:border-muted',
}

/** Bouton d'action (React Aria) : clavier, souris et doigt, état « en cours » compris. */
export function Button({ variant = 'secondaire', className, children, ...props }: ButtonProps) {
  return (
    <AriaButton
      {...props}
      className={cx(
        'inline-flex cursor-default items-center justify-center gap-2 rounded-md border px-3 text-sm select-none',
        VARIANTS[variant],
        'demo-pressed:border-line demo-pressed:bg-line demo-pressed:text-text demo-pressed:opacity-100',
        'data-[pending]:cursor-wait',
        touchSize,
        focusRing,
        quick,
        disabled,
        className,
      )}
    >
      {composeRenderProps(children, (children, { isPending }) => (
        <>
          {isPending && <LoaderCircle aria-hidden size={20} className="animate-spin" />}
          {children}
          {isPending && <span className="sr-only"> (en cours)</span>}
        </>
      ))}
    </AriaButton>
  )
}
