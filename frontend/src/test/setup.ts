import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, expect } from 'vitest'
import * as axeMatchers from 'vitest-axe/matchers'

// Audit d'accessibilité (axe) : `expect(await axe(container)).toHaveNoViolations()`.
expect.extend(axeMatchers)

afterEach(() => {
  cleanup()
})
