import { EmptyState } from '../ui/EmptyState'
import { link } from '../ui/styles'
import { Shell } from './Shell'

/** Toute adresse inconnue du cockpit. */
export default function Introuvable() {
  return (
    <Shell page="introuvable">
      <div className="mx-auto mt-10 max-w-lg rounded-lg border border-line bg-panel">
        <EmptyState
          level={1}
          titre="Page introuvable"
          phrase="Cette adresse ne mène à aucune page du cockpit."
          action={
            <a href="/" className={link}>
              Retour à l'accueil
            </a>
          }
        />
      </div>
    </Shell>
  )
}
