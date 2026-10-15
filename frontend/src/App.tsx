import { lazy, Suspense } from 'react'
import Accueil from './pages/Accueil'
import Introuvable from './pages/Introuvable'
import { Loading } from './ui/Loading'

// La vitrine est chargée à part : React Aria ne pèse pas sur l'accueil.
const Vitrine = lazy(() => import('./vitrine/Vitrine'))

/** Page choisie selon l'adresse (pas de bibliothèque de routage, spec 0003). */
export function pageFor(pathname: string): 'accueil' | 'vitrine' | 'introuvable' {
  const path = pathname.replace(/\/+$/, '') || '/'
  if (path === '/') return 'accueil'
  if (path === '/vitrine') return 'vitrine'
  return 'introuvable'
}

export default function App() {
  const page = pageFor(window.location.pathname)
  if (page === 'accueil') return <Accueil />
  if (page === 'vitrine') {
    return (
      <Suspense fallback={<Loading className="p-6" />}>
        <Vitrine />
      </Suspense>
    )
  }
  return <Introuvable />
}
