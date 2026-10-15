import { Check } from 'lucide-react'
import { CheckboxButton, CheckboxField, type CheckboxFieldProps } from 'react-aria-components'
import { Description, FieldError } from './FieldError'
import { cx, quick } from './styles'

export interface CheckboxProps extends Omit<CheckboxFieldProps, 'className' | 'children'> {
  children: string
  description?: string
  errorMessage?: string
  /** Vitrine seulement : fige un état (`hovered`, `pressed`, `focus-visible`). */
  demo?: string
  className?: string
}

/** Case à cocher (React Aria) : case visible de 20 px, zone touchable de 44 px au doigt. */
export function Checkbox({ children, description, errorMessage, demo, className, ...props }: CheckboxProps) {
  return (
    <CheckboxField {...props} className={cx('flex flex-col gap-1', className)}>
      <CheckboxButton
        data-demo={demo}
        className={cx(
          'group inline-flex cursor-default items-center gap-2.5 self-start text-sm text-text select-none outline-hidden',
          'pointer-fine:min-h-8 pointer-coarse:min-h-11 pointer-coarse:min-w-11',
          'data-[disabled]:cursor-not-allowed data-[disabled]:opacity-50',
        )}
      >
        {({ isSelected }) => (
          <>
            <span
              aria-hidden
              className={cx(
                'flex size-5 shrink-0 items-center justify-center rounded-sm border-2 border-muted bg-panel-2',
                'group-demo-hovered:border-text group-demo-pressed:bg-line',
                'group-data-[selected]:border-accent group-data-[selected]:bg-accent',
                'group-data-[invalid]:border-danger',
                'group-demo-focus-visible:outline-2 group-demo-focus-visible:outline-solid group-demo-focus-visible:outline-offset-2 group-demo-focus-visible:outline-accent',
                quick,
              )}
            >
              {isSelected && <Check size={14} strokeWidth={3} className="text-ink" />}
            </span>
            {children}
          </>
        )}
      </CheckboxButton>
      {description && <Description>{description}</Description>}
      <FieldError className="ps-7.5">{errorMessage}</FieldError>
    </CheckboxField>
  )
}
