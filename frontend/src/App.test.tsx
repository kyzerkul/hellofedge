import { render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App, { pageFor } from './App'

// Le seul appel réseau du squelette est /api/health : on le simule à la frontière (fetch).
const fetchMock = vi.fn<typeof fetch>()

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
  fetchMock.mockReset()
  window.history.pushState({}, '', '/')
})

function answer(status: number) {
  fetchMock.mockResolvedValue(new Response('{}', { status }))
}

describe('App (squelette du cockpit)', () => {
  it('shows the product name as the main heading', () => {
    answer(200)

    render(<App />)

    expect(screen.getByRole('heading', { level: 1, name: 'Hellofedge' })).toBeInTheDocument()
  })

  it('asks the api for its health once, at /api/health', () => {
    answer(200)

    render(<App />)

    expect(fetchMock).toHaveBeenCalledWith('/api/health')
  })

  it('shows a loading state before the api answers', () => {
    fetchMock.mockReturnValue(new Promise(() => {}))

    render(<App />)

    expect(screen.getByText('État du serveur : chargement')).toBeInTheDocument()
  })

  it('shows ok when the api and the database answer', async () => {
    answer(200)

    render(<App />)

    expect(await screen.findByText('État du serveur : ok')).toBeInTheDocument()
  })

  it('shows hors service when the database is down (503)', async () => {
    answer(503)

    render(<App />)

    expect(await screen.findByText('État du serveur : hors service')).toBeInTheDocument()
  })

  it('shows hors service when the server cannot be reached at all', async () => {
    fetchMock.mockRejectedValue(new TypeError('Failed to fetch'))

    render(<App />)

    expect(await screen.findByText('État du serveur : hors service')).toBeInTheDocument()
  })
})

describe('pages du cockpit (AC-7)', () => {
  it.each([
    ['/', 'accueil'],
    ['/vitrine', 'vitrine'],
    ['/vitrine/', 'vitrine'],
    ['/vitrine//', 'vitrine'],
    ['/foo', 'introuvable'],
    ['/vitrine/foo', 'introuvable'],
  ] as const)('%s leads to the %s page', (path, page) => {
    expect(pageFor(path)).toBe(page)
  })

  it('links the home page to the showcase', () => {
    answer(200)

    render(<App />)

    expect(screen.getAllByRole('link', { name: /vitrine/i })[0]).toHaveAttribute('href', '/vitrine')
  })

  it('opens the showcase at /vitrine/', async () => {
    window.history.pushState({}, '', '/vitrine/')

    render(<App />)

    expect(
      await screen.findByRole('heading', { level: 1, name: 'Vitrine du design system' }, { timeout: 5000 }),
    ).toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('shows « Page introuvable » with a way back home at an unknown address', () => {
    window.history.pushState({}, '', '/foo')

    render(<App />)

    expect(screen.getByRole('heading', { level: 1, name: 'Page introuvable' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: "Retour à l'accueil" })).toHaveAttribute('href', '/')
    expect(fetchMock).not.toHaveBeenCalled()
  })
})
