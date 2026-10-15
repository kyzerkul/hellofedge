import { TriangleAlert } from 'lucide-react'
import { FieldError as AriaFieldError, type FieldErrorProps, Text } from 'react-aria-components'
import { cx } from './styles'

/** Message d'erreur d'un champ : toujours une icône et une phrase, relié au champ par React Aria. */
export function FieldError({ className, children, ...props }: Omit<FieldErrorProps, 'className'> & { className?: string }) {
  return (
    <AriaFieldError {...props} className={cx('flex items-start gap-1.5 text-xs text-danger', className)}>
      {(validation) => (
        <>
          <TriangleAlert aria-hidden size={16} className="mt-px shrink-0" />
          <span>{typeof children === 'function' ? children(validation) : (children ?? validation.validationErrors.join(' '))}</span>
        </>
      )}
    </AriaFieldError>
  )
}

/** Aide d'un champ, reliée au champ par React Aria. */
export function Description({ children }: { children: string }) {
  return (
    <Text slot="description" className="text-xs text-muted">
      {children}
    </Text>
  )
}
