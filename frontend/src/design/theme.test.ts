import { describe, expect, it } from 'vitest'
import designMd from '../../../docs/design.md?raw'
import themeCss from './theme.css?raw'

// Le thème est la source des valeurs, design.md son miroir (spec 0003, AC-1, AC-4, AC-11).

const MIRRORED = /^--(color|font|text|radius|duration)-/

/** Déclarations posées directement dans le bloc `@theme` (sans les `initial` ni les @keyframes). */
function themeTokens(css: string): Map<string, string> {
  const start = css.indexOf('@theme')
  if (start < 0) throw new Error('theme.css sans bloc @theme')
  const tokens = new Map<string, string>()
  let depth = 0
  let decl = ''
  for (const char of css.slice(css.indexOf('{', start))) {
    if (char === '{') {
      depth += 1
      decl = ''
    } else if (char === '}') {
      depth -= 1
      decl = ''
      if (depth === 0) break
    } else if (char === ';' && depth === 1) {
      const clean = decl.replace(/\/\*[\s\S]*?\*\//g, '').trim()
      const sep = clean.indexOf(':')
      const name = clean.slice(0, sep).trim()
      const value = clean.slice(sep + 1).trim()
      if (MIRRORED.test(name) && value !== 'initial') tokens.set(name, value)
      decl = ''
    } else {
      decl += char
    }
  }
  return tokens
}

/** Lignes de tableau de design.md dont la première cellule est un jeton : `| `--x` | `valeur` | … |`. */
function documentedTokens(md: string): Map<string, string> {
  const tokens = new Map<string, string>()
  for (const line of md.split('\n')) {
    const match = line.match(/^\|\s*`(--[a-z0-9-]+)`\s*\|\s*`([^`]+)`\s*\|/)
    if (match && MIRRORED.test(match[1])) tokens.set(match[1], match[2].trim())
  }
  return tokens
}

const theme = themeTokens(themeCss)
const documented = documentedTokens(designMd)

describe('design.md, miroir du thème (AC-1)', () => {
  it('reads every token family from the theme', () => {
    const families = new Set([...theme.keys()].map((name) => name.split('-')[2]))
    expect(families).toEqual(new Set(['color', 'font', 'text', 'radius', 'duration']))
  })

  it.each([...theme])('documents %s with the same value', (name, value) => {
    expect(documented.get(name)).toBe(value)
  })

  it.each([...documented])('finds the documented %s in the theme with the same value', (name, value) => {
    expect(theme.get(name)).toBe(value)
  })

  it('detects a value changed in the theme only', () => {
    const changed = themeTokens(themeCss.replace('--color-muted: #8A95AD;', '--color-muted: #5B6782;'))
    expect(changed.get('--color-muted')).not.toBe(documented.get('--color-muted'))
  })

  it('detects a theme token missing from design.md', () => {
    const added = themeTokens(themeCss.replace('--color-ink:', '--color-nouveau: #000000;\n  --color-ink:'))
    expect(documented.has('--color-nouveau')).toBe(false)
    expect(added.has('--color-nouveau')).toBe(true)
  })
})

// Contraste WCAG 2 : luminance relative, puis (L1 + 0,05) / (L2 + 0,05).

type Rgba = [number, number, number, number]

function parseColor(value: string): Rgba {
  const hex = value.match(/^#([0-9a-f]{6})$/i)
  if (hex) {
    const n = parseInt(hex[1], 16)
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255, 1]
  }
  const rgb = value.match(/^rgb\((\d+) (\d+) (\d+) \/ ([\d.]+)\)$/)
  if (rgb) return [Number(rgb[1]), Number(rgb[2]), Number(rgb[3]), Number(rgb[4])]
  throw new Error(`couleur illisible : ${value}`)
}

function over(top: Rgba, under: Rgba): Rgba {
  const a = top[3]
  return [0, 1, 2].map((i) => top[i] * a + under[i] * (1 - a)).concat(1) as Rgba
}

function luminance([r, g, b]: Rgba): number {
  const lin = (c: number) => {
    const s = c / 255
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4
  }
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
}

function ratio(a: Rgba, b: Rgba): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x)
  return (hi + 0.05) / (lo + 0.05)
}

function color(token: string, tokens: Map<string, string> = theme): Rgba {
  const value = tokens.get(`--color-${token}`)
  if (!value) throw new Error(`jeton inconnu : --color-${token}`)
  return parseColor(value)
}

/** Fond d'une ligne : un jeton, ou `transparent` sur `support` (composé). */
function background(tokens: string[], themeMap: Map<string, string> = theme): Rgba {
  return tokens.reduceRight<Rgba | null>((under, token) => {
    const top = color(token, themeMap)
    return under ? over(top, under) : top
  }, null)!
}

interface Pair {
  fg: string
  bg: string[]
  kind: string
  threshold: number
  written: number
}

function contrastTable(md: string): Pair[] {
  const section = md.slice(md.indexOf('## Contraste'))
  const end = section.indexOf('\n## ', 3)
  const rows = (end > 0 ? section.slice(0, end) : section).split('\n').filter((l) => l.startsWith('| `'))
  return rows.map((row) => {
    const cells = row.split('|').slice(1, -1).map((c) => c.trim())
    const tokens = (cell: string) => [...cell.matchAll(/`([^`]+)`/g)].map((m) => m[1])
    return {
      fg: tokens(cells[0])[0],
      bg: tokens(cells[1]),
      kind: cells[2],
      threshold: Number(cells[3].replace(',', '.')),
      written: Number(cells[4].replace(',', '.')),
    }
  })
}

const pairs = contrastTable(designMd)
const key = (fg: string, bg: string[], kind: string) => `${fg} sur ${bg.join(' sur ')} (${kind})`

const REQUIRED: string[] = [
  ...['text', 'muted', 'accent', 'buy', 'sell', 'danger'].flatMap((fg) =>
    ['ink', 'panel', 'panel-2'].map((bg) => key(fg, [bg], 'texte')),
  ),
  key('text', ['accent-soft', 'panel'], 'texte'),
  key('accent', ['accent-soft', 'panel'], 'texte'),
  key('ink', ['accent'], 'texte'),
  key('ink', ['danger'], 'texte'),
  ...['level-liquidity', 'level-ipa', 'level-extreme', 'level-target'].flatMap((fg) =>
    ['ink', 'panel-2'].map((bg) => key(fg, [bg], 'graphique')),
  ),
  key('candle-up', ['ink'], 'graphique'),
  key('candle-down', ['ink'], 'graphique'),
  key('muted', ['panel'], 'graphique'),
  key('muted', ['panel-2'], 'graphique'),
  ...['ink', 'panel', 'panel-2'].map((bg) => key('accent', [bg], 'graphique')),
]

const FORBIDDEN: [string, string][] = [
  ['muted', 'line'],
  ['candle-down', 'panel-2'],
]

describe('tableau de contraste (AC-4)', () => {
  it('lists every mandatory pair', () => {
    const listed = new Set(pairs.map((p) => key(p.fg, p.bg, p.kind)))
    expect(REQUIRED.filter((k) => !listed.has(k))).toEqual([])
  })

  it('uses the right threshold for each kind of pair', () => {
    for (const p of pairs) expect(p.threshold, key(p.fg, p.bg, p.kind)).toBe(p.kind === 'texte' ? 4.5 : 3)
  })

  it.each(pairs.map((p) => [key(p.fg, p.bg, p.kind), p] as const))('%s reaches its threshold', (_, p) => {
    expect(ratio(color(p.fg), background(p.bg))).toBeGreaterThanOrEqual(p.threshold)
  })

  it.each(pairs.map((p) => [key(p.fg, p.bg, p.kind), p] as const))('%s shows the true ratio', (_, p) => {
    expect(p.written).toBeCloseTo(ratio(color(p.fg), background(p.bg)), 2)
  })

  it('never lists a forbidden combination as allowed', () => {
    for (const [fg, bg] of FORBIDDEN) {
      expect(pairs.some((p) => p.fg === fg && p.bg.length === 1 && p.bg[0] === bg)).toBe(false)
    }
  })

  it('fails when muted goes back to the old faint grey', () => {
    const faint = themeTokens(themeCss.replace('--color-muted: #8A95AD;', '--color-muted: #5B6782;'))
    expect(ratio(color('muted', faint), background(['panel-2'], faint))).toBeLessThan(4.5)
  })
})

describe('couleurs de niveaux (AC-2)', () => {
  const LEVELS = {
    '--color-level-liquidity': '#F23645',
    '--color-level-ipa': '#2962FF',
    '--color-level-extreme': '#FFFFFF',
    '--color-level-target': '#FFEB3B',
  }

  it('are the TradingView colours read on the screenshots', () => {
    for (const [name, value] of Object.entries(LEVELS)) expect(theme.get(name)).toBe(value)
  })

  it('are used by no other token', () => {
    const reserved = new Set(Object.values(LEVELS).map((v) => v.toLowerCase()))
    const others = [...theme].filter(([name]) => !(name in LEVELS))
    expect(others.filter(([, value]) => reserved.has(value.toLowerCase()))).toEqual([])
  })
})

describe('theme.css', () => {
  it('removes the default Tailwind palette and radii (AC-3)', () => {
    expect(themeCss).toContain('--color-*: initial;')
    expect(themeCss).toContain('--radius-*: initial;')
  })

  it('stops every animation and transition when less motion is asked (AC-11)', () => {
    const rule = themeCss.slice(themeCss.indexOf('@media (prefers-reduced-motion: reduce)'))
    expect(rule).toMatch(/^@media \(prefers-reduced-motion: reduce\) \{\s*\*,\s*::before,\s*::after \{/)
    expect(rule).toContain('animation: none !important;')
    expect(rule).toContain('transition-duration: 0.01ms !important;')
  })

  it('declares the dark colour scheme', () => {
    expect(themeCss).toMatch(/:root \{\s*color-scheme: dark;/)
  })
})
