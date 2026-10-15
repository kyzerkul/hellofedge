import 'vitest'
import type { AxeMatchers } from 'vitest-axe/matchers'

// vitest-axe déclare ses assertions pour une ancienne version de Vitest : on les rebranche ici.
declare module 'vitest' {
  interface Assertion<T = any> extends AxeMatchers {}
  interface AsymmetricMatchersContaining extends AxeMatchers {}
}
