import {
  Tab as AriaTab,
  type TabListProps as AriaTabListProps,
  type TabPanelProps as AriaTabPanelProps,
  type TabProps as AriaTabProps,
  type TabsProps as AriaTabsProps,
  TabList as AriaTabList,
  TabPanel as AriaTabPanel,
  Tabs as AriaTabs,
} from 'react-aria-components'
import { cx, disabled, focusRing, quick, touchSize } from './styles'

type WithClass<P> = Omit<P, 'className'> & { className?: string }

/** Onglets (React Aria) : activation automatique aux flèches. */
export function Tabs({ className, ...props }: WithClass<AriaTabsProps>) {
  return <AriaTabs {...props} className={cx('flex flex-col gap-3', className)} />
}

export function TabList<T extends object>({ className, ...props }: WithClass<AriaTabListProps<T>>) {
  return (
    <AriaTabList
      {...props}
      className={cx('inline-flex max-w-full flex-wrap gap-1 self-start rounded-lg border border-line bg-panel p-1', className)}
    />
  )
}

export function Tab({ className, ...props }: WithClass<AriaTabProps>) {
  return (
    <AriaTab
      {...props}
      className={cx(
        'inline-flex cursor-default items-center justify-center rounded-md border border-transparent px-3 text-sm font-medium text-muted select-none',
        'demo-hovered:border-muted demo-hovered:text-text demo-pressed:bg-line demo-pressed:text-text',
        'data-[selected]:bg-accent-soft data-[selected]:text-accent',
        touchSize,
        focusRing,
        quick,
        disabled,
        className,
      )}
    />
  )
}

export function TabPanel({ className, ...props }: WithClass<AriaTabPanelProps>) {
  return <AriaTabPanel {...props} className={cx('rounded-md', focusRing, className)} />
}
