import { useEffect, useState } from 'react'

type Health = 'chargement' | 'ok' | 'hors service'

// Squelette du cockpit : il prouve seulement que le cockpit joint l'api et la base.
export default function App() {
  const [health, setHealth] = useState<Health>('chargement')

  useEffect(() => {
    fetch('/api/health')
      .then((res) => setHealth(res.ok ? 'ok' : 'hors service'))
      .catch(() => setHealth('hors service'))
  }, [])

  return (
    <main>
      <h1>Hellofedge</h1>
      <p>Cockpit USD/JPY, squelette.</p>
      <p>État du serveur : {health}</p>
    </main>
  )
}
