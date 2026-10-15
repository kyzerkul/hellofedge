import { describe, expect, it } from 'vitest'
import indexHtml from '/index.html?raw'

// Gardes du design system (spec 0003, *Gardes*) : elles lisent les sources du cockpit
// comme du texte et échouent sur une couleur en dur, une couleur de niveau hors de sa place
// ou une adresse vers un domaine tiers. Les fichiers de test sont exclus.

const all = import.meta.glob<string>('/src/**/*.{ts,tsx,css}', { query: '?raw', import: 'default', eager: true })
const sources = Object.entries(all).filter(([path]) => !/\.test\.[^/]+$/.test(path))

const HARD_COLOUR = [/#[0-9a-fA-F]{3,8}\b/, /\b(rgb|rgba|hsl|hsla|hwb|lab|lch|oklab|oklch)\(/]
const DEFAULT_PALETTE =
  /\b(bg|text|border|ring|fill|stroke|from|to|via|outline|divide|shadow|accent|decoration)-(slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose|white|black)\b/
const LEVEL = /level-(liquidity|ipa|extreme|target)/
const LEVEL_ALLOWED = [/^\/src\/design\//, /^\/src\/ui\/LevelChip\.tsx$/, /^\/src\/vitrine\//, /^\/src\/chart\//]
const URL = /https?:\/\/([^\s"'`)<>/]*)/g
const URL_ALLOWED = new Set(['www.w3.org', 'localhost'])

function lines(content: string, pattern: RegExp): string[] {
  return content.split('\n').filter((line) => pattern.test(line))
}

function hardColours(path: string, content: string): string[] {
  if (path === '/src/design/theme.css') return []
  return HARD_COLOUR.flatMap((p) => lines(content, p)).concat(lines(content, DEFAULT_PALETTE))
}

function misplacedLevels(path: string, content: string): string[] {
  if (LEVEL_ALLOWED.some((p) => p.test(path))) return []
  return lines(content, LEVEL)
}

function thirdPartyUrls(content: string): string[] {
  return [...content.matchAll(URL)]
    .map((m) => m[1].split(':')[0])
    .filter((host) => !URL_ALLOWED.has(host))
}

describe('gardes, sur les sources du cockpit', () => {
  it('reads the cockpit sources', () => {
    expect(sources.map(([path]) => path)).toContain('/src/App.tsx')
  })

  it.each(sources)('%s has no hard coded colour nor default palette class (AC-3)', (path, content) => {
    expect(hardColours(path, content)).toEqual([])
  })

  it.each(sources)('%s uses level colours only where allowed (AC-2)', (path, content) => {
    expect(misplacedLevels(path, content)).toEqual([])
  })

  it.each(sources)('%s loads nothing from a third party domain (AC-8)', (_, content) => {
    expect(thirdPartyUrls(content)).toEqual([])
  })

  it('index.html loads nothing from a third party domain (AC-8)', () => {
    expect(thirdPartyUrls(indexHtml)).toEqual([])
  })
})

describe('gardes, sur des cas construits', () => {
  it.each(['color: #FF0000;', "fill='#f23645'", 'rgb(0 0 0)', 'oklch(0.7 0.1 200)', 'className="bg-red-500"', 'text-white'])(
    'catches %s in a component',
    (snippet) => {
      expect(hardColours('/src/ui/Button.tsx', snippet)).not.toEqual([])
    },
  )

  it('lets theme.css hold the colour values', () => {
    expect(hardColours('/src/design/theme.css', '--color-ink: #0C111C;')).toEqual([])
  })

  it('accepts token classes', () => {
    expect(hardColours('/src/ui/Button.tsx', 'className="bg-panel-2 text-muted border-line"')).toEqual([])
  })

  it('catches a level colour in a component', () => {
    expect(misplacedLevels('/src/ui/Button.tsx', 'className="text-level-ipa"')).not.toEqual([])
  })

  it.each(['/src/chart/Chart.tsx', '/src/ui/LevelChip.tsx', '/src/vitrine/Couleurs.tsx', '/src/design/format.ts'])(
    'lets %s use a level colour',
    (path) => {
      expect(misplacedLevels(path, 'className="text-level-ipa"')).toEqual([])
    },
  )

  it('catches a Google Fonts address in index.html', () => {
    const html = indexHtml.replace('</head>', '<link href="https://fonts.googleapis.com/css2" /></head>')
    expect(thirdPartyUrls(html)).toEqual(['fonts.googleapis.com'])
  })

  it('accepts the SVG namespace and localhost', () => {
    expect(thirdPartyUrls('xmlns="http://www.w3.org/2000/svg" http://localhost:8000/api')).toEqual([])
  })
})
