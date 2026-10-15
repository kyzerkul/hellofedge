import {
  Input,
  Label,
  TextField as AriaTextField,
  type TextFieldProps as AriaTextFieldProps,
} from 'react-aria-components'
import { Description, FieldError } from './FieldError'
import { cx, fieldFocusRing, quick, touchSize } from './styles'

export interface TextFieldProps extends Omit<AriaTextFieldProps, 'className' | 'children' | 'type'> {
  label: string
  description?: string
  errorMessage?: string
  type?: 'text' | 'email' | 'password'
  placeholder?: string
  /** Vitrine seulement : fige un état (`hovered`, `focus-visible`). */
  demo?: string
  className?: string
}

/** Champ de saisie (React Aria) : libellé, aide, erreur ; texte à 16 px pour éviter le zoom du téléphone. */
export function TextField({
  label,
  description,
  errorMessage,
  type = 'text',
  placeholder,
  demo,
  className,
  ...props
}: TextFieldProps) {
  return (
    <AriaTextField {...props} type={type} className={cx('group flex flex-col gap-1.5', className)}>
      <Label className="text-sm font-medium text-text group-data-[disabled]:opacity-50">{label}</Label>
      <Input
        placeholder={placeholder}
        data-demo={demo}
        className={cx(
          'w-full rounded-md border border-muted bg-panel-2 px-3 py-1.5 text-md text-text placeholder:text-muted',
          'demo-hovered:border-text data-[invalid]:border-danger',
          'data-[disabled]:cursor-not-allowed data-[disabled]:opacity-50',
          touchSize,
          fieldFocusRing,
          quick,
        )}
      />
      {description && <Description>{description}</Description>}
      <FieldError>{errorMessage}</FieldError>
    </AriaTextField>
  )
}
