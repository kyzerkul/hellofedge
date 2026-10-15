// Formats d'affichage du cockpit (spec 0003, *Formats*). Les heures arrivent en UTC de l'api
// et s'affichent à l'heure du Bénin ; les prix arrivent en chaîne décimale, jamais en flottant.

export const DISPLAY_TIME_ZONE = 'Africa/Porto-Novo'

const EMPTY = '—'
const MINUS = '−'
const PRICE = /^(-?)(\d+)(?:\.(\d+))?$/

/**
 * Prix comme sur le graphique du trader : point décimal, exactement 3 décimales.
 * Au delà de 3 décimales, arrondi au plus proche (la moitié vers le haut), calculé sur les chiffres.
 */
export function formatPrice(value: string | null | undefined): string {
  const match = value?.trim().match(PRICE)
  if (!match) return EMPTY
  const [, sign, whole, frac = ''] = match
  let digits = BigInt(whole + frac.slice(0, 3).padEnd(3, '0'))
  if (frac.length > 3 && frac[3] >= '5') digits += 1n
  const text = digits.toString().padStart(4, '0')
  const negative = sign === '-' && digits !== 0n
  return `${negative ? '-' : ''}${text.slice(0, -3)}.${text.slice(-3)}`
}

const timeFormats = new Map<string, Intl.DateTimeFormat>()

function displayParts(date: Date, withSeconds: boolean): Record<string, string> {
  const key = withSeconds ? 's' : 'm'
  let format = timeFormats.get(key)
  if (!format) {
    format = new Intl.DateTimeFormat('fr-FR', {
      timeZone: DISPLAY_TIME_ZONE,
      hourCycle: 'h23',
      year: 'numeric',
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
      ...(withSeconds ? { second: '2-digit' } : {}),
    })
    timeFormats.set(key, format)
  }
  return Object.fromEntries(format.formatToParts(date).map((p) => [p.type, p.value]))
}

function parseUtc(utc: string | Date): Date | null {
  const date = utc instanceof Date ? utc : new Date(utc)
  return Number.isNaN(date.getTime()) ? null : date
}

/** Heure du Bénin, 24 h : `14:05`, `14:05:09` avec les secondes, `15 oct. 14:05` avec la date. */
export function formatTime(utc: string | Date, options: { secondes?: boolean; date?: boolean } = {}): string {
  const date = parseUtc(utc)
  if (!date) return EMPTY
  const p = displayParts(date, Boolean(options.secondes))
  const time = options.secondes ? `${p.hour}:${p.minute}:${p.second}` : `${p.hour}:${p.minute}`
  return options.date ? `${p.day} ${p.month} ${time}` : time
}

/** Vrai si les deux instants tombent le même jour à l'heure du Bénin. */
export function sameDisplayDay(a: string | Date, b: string | Date): boolean {
  const x = parseUtc(a)
  const y = parseUtc(b)
  if (!x || !y) return false
  const px = displayParts(x, false)
  const py = displayParts(y, false)
  return px.year === py.year && px.month === py.month && px.day === py.day
}

const NUMBER_DIGITS = { pip: 1, r: 1, pct: 2 } as const
const numberFormats = new Map<string, Intl.NumberFormat>()

/**
 * Pips, R et pourcentages à la française : `0,3 pip`, `2 pips`, `+4,6 R`, `−1,5 R`, `+0,31 %`.
 * Pour `pct`, la valeur est déjà en pour cent (0.31 donne `+0,31 %`).
 */
export function formatNumber(value: number, kind: 'pip' | 'r' | 'pct'): string {
  if (!Number.isFinite(value)) return EMPTY
  let format = numberFormats.get(kind)
  if (!format) {
    format = new Intl.NumberFormat('fr-FR', {
      maximumFractionDigits: NUMBER_DIGITS[kind],
      signDisplay: kind === 'pip' ? 'negative' : 'exceptZero',
    })
    numberFormats.set(kind, format)
  }
  const number = format.format(value).replace('-', MINUS)
  if (kind === 'pip') return `${number} ${Math.abs(value) < 2 ? 'pip' : 'pips'}`
  if (kind === 'r') return `${number} R`
  return `${number} %`
}

/** Valeur d'un jeton du thème, lue à l'exécution (pour le graphique, qui veut ses couleurs en JavaScript). */
export function cssToken(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}
