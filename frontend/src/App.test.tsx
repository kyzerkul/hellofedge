import { render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'

// Le seul appel réseau du squelette est /api/health : on le simule à la frontière (fetch).
const fetchMock = vi.fn<typeof fetch>()

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
  fetchMock.mockReset()
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
