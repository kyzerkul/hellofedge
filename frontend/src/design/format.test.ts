import { afterEach, describe, expect, it } from 'vitest'
import { cssToken, DISPLAY_TIME_ZONE, formatNumber, formatPrice, formatTime, sameDisplayDay } from './format'

describe('formatPrice (AC-9)', () => {
  it.each([
    ['147.584', '147.584'],
    ['147.5840', '147.584'],
    ['147.5', '147.500'],
    ['147', '147.000'],
    ['147.5845', '147.585'],
    ['147.5844999', '147.584'],
    ['147.9995', '148.000'],
    ['0.0004', '0.000'],
    [' 147.584 ', '147.584'],
  ])('%s gives %s', (value, expected) => {
    expect(formatPrice(value)).toBe(expected)
  })

  it.each([null, undefined, '', 'abc', '147,5', '1e3', 'NaN'])('%s gives an em dash', (value) => {
    expect(formatPrice(value)).toBe('—')
  })

  it('keeps every digit of a long price, without float rounding', () => {
    expect(formatPrice('12345678901234.0005')).toBe('12345678901234.001')
  })
})

describe('formatTime (AC-9)', () => {
  it('shows Benin time, UTC plus one hour', () => {
    expect(DISPLAY_TIME_ZONE).toBe('Africa/Porto-Novo')
    expect(formatTime('2026-10-15T13:05:00Z')).toBe('14:05')
  })

  it('shows midnight as 00, never 24', () => {
    expect(formatTime('2026-10-15T23:05:00Z')).toBe('00:05')
  })

  it('adds the seconds when asked', () => {
    expect(formatTime('2026-10-15T13:05:09Z', { secondes: true })).toBe('14:05:09')
  })

  it('adds the Benin date when asked', () => {
    expect(formatTime('2026-10-15T13:05:00Z', { date: true })).toBe('15 oct. 14:05')
    expect(formatTime('2026-10-15T23:30:00Z', { date: true })).toBe('16 oct. 00:30')
  })

  it('gives an em dash for an invalid time', () => {
    expect(formatTime('pas une heure')).toBe('—')
  })
})

describe('sameDisplayDay', () => {
  it('compares days in Benin time, not in UTC', () => {
    expect(sameDisplayDay('2026-10-15T22:30:00Z', '2026-10-15T23:30:00Z')).toBe(false)
    expect(sameDisplayDay('2026-10-15T00:30:00Z', '2026-10-15T22:30:00Z')).toBe(true)
  })
})

describe('formatNumber (AC-9)', () => {
  it.each([
    [0.3, 'pip', '0,3 pip'],
    [1.9, 'pip', '1,9 pip'],
    [2, 'pip', '2 pips'],
    [12.25, 'pip', '12,3 pips'],
    [-0.3, 'pip', '−0,3 pip'],
    [-2.5, 'pip', '−2,5 pips'],
    [4.6, 'r', '+4,6 R'],
    [-1.5, 'r', '−1,5 R'],
    [0, 'r', '0 R'],
    [0.31, 'pct', '+0,31 %'],
    [-0.5, 'pct', '−0,5 %'],
  ] as const)('%s %s gives %s', (value, kind, expected) => {
    expect(formatNumber(value, kind)).toBe(expected)
  })

  it('gives an em dash for a value that is not a number', () => {
    expect(formatNumber(Number.NaN, 'r')).toBe('—')
  })
})

describe('cssToken', () => {
  afterEach(() => {
    document.documentElement.style.removeProperty('--color-ink')
  })

  it('reads a theme variable at run time', () => {
    document.documentElement.style.setProperty('--color-ink', ' #0C111C ')
    expect(cssToken('--color-ink')).toBe('#0C111C')
  })
})
