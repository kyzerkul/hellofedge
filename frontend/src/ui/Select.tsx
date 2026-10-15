import { Check, ChevronDown } from 'lucide-react'
import {
  Button,
  Label,
  ListBox,
  ListBoxItem,
  Popover,
  Select as AriaSelect,
  type SelectProps as AriaSelectProps,
  SelectValue,
} from 'react-aria-components'
import { Description, FieldError } from './FieldError'
import { cx, focusRing, listBox, listBoxItem, quick, touchSize } from './styles'

export interface SelectOption {
  id: string
  label: string
}

export interface SelectProps extends Omit<AriaSelectProps<SelectOption, 'single'>, 'className' | 'children'> {
  label: string
  options: SelectOption[]
  description?: string
  errorMessage?: string
  /** Vitrine seulement : fige un état du bouton (`hovered`, `pressed`, `focus-visible`). */
  demo?: string
  className?: string
}

/** Liste de choix (React Aria) : Entrée ou Espace l'ouvre, les flèches la parcourent. */
export function Select({
  label,
  options,
  description,
  errorMessage,
  placeholder = 'Choisir…',
  demo,
  className,
  ...props
}: SelectProps) {
  return (
    <AriaSelect {...props} placeholder={placeholder} className={cx('group flex flex-col gap-1.5', className)}>
      <Label className="text-sm font-medium text-text group-data-[disabled]:opacity-50">{label}</Label>
      <SelectTrigger demo={demo} />
      {description && <Description>{description}</Description>}
      <FieldError>{errorMessage}</FieldError>
      <Popover offset={4} className="min-w-(--trigger-width) data-[entering]:animate-list-open">
        <ListBox items={options} className={listBox}>
          {(option) => <SelectItem id={option.id}>{option.label}</SelectItem>}
        </ListBox>
      </Popover>
    </AriaSelect>
  )
}

/** Bouton qui ouvre la liste ; `data-demo` fige un état dans la vitrine. */
export function SelectTrigger({ demo }: { demo?: string }) {
  return (
    <Button
      data-demo={demo}
      className={cx(
        'flex w-full cursor-default items-center justify-between gap-3 rounded-md border border-muted bg-panel-2 px-3 text-left text-sm text-text select-none',
        'demo-hovered:border-text demo-pressed:bg-line group-data-[open]:border-accent group-data-[invalid]:border-danger',
        'data-[disabled]:cursor-not-allowed data-[disabled]:opacity-50',
        touchSize,
        focusRing,
        quick,
      )}
    >
      <SelectValue className="truncate data-[placeholder]:text-muted" />
      <ChevronDown aria-hidden size={16} className="shrink-0 text-muted" />
    </Button>
  )
}

/** Option d'une liste, avec une coche quand elle est choisie. */
export function SelectItem({ id, children }: { id: string; children: string }) {
  return (
    <ListBoxItem id={id} textValue={children} className={listBoxItem}>
      {({ isSelected }) => (
        <>
          <span className="flex-1">{children}</span>
          {isSelected && <Check aria-hidden size={16} />}
        </>
      )}
    </ListBoxItem>
  )
}
