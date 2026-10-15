import { Button } from '../ui/Button'
import { Card } from '../ui/Card'
import { EmptyState } from '../ui/EmptyState'
import { ErrorState } from '../ui/ErrorState'
import { FeedBanner } from '../ui/FeedBanner'
import { LiveStatus } from '../ui/LiveStatus'
import { Loading, Skeleton } from '../ui/Loading'
import { COUPURES, MAINTENANT } from './donnees'
import { Etat, Section } from './Section'

export function Etats() {
  return (
    <Section
      id="etats"
      titre="États"
      intro="Chargement, vide, erreur et flux de prix : toujours une icône et une phrase, jamais une couleur seule."
    >
      <div className="grid gap-4 lg:grid-cols-3">
        <Card titre="Loading" level={3}>
          <div className="flex flex-col gap-3">
            <Loading />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-24 w-full" />
          </div>
        </Card>
        <Card titre="EmptyState" level={3}>
          <EmptyState
            level={4}
            titre="Aucun setup pour l’instant"
            phrase="Le moteur n’a encore rien repéré aujourd’hui. Tu seras alerté sur Telegram dès qu’un setup se forme."
            action={<Button variant="discret">Voir les règles du moteur</Button>}
          />
        </Card>
        <Card titre="ErrorState" level={3}>
          <div className="flex flex-col gap-3">
            <ErrorState phrase="Le journal n’a pas pu être chargé." onRetry={() => {}} />
            <ErrorState phrase="Ce setup n’existe plus." />
          </div>
        </Card>
        <Card titre="LiveStatus" level={3}>
          <div className="flex flex-wrap gap-x-6 gap-y-4">
            <Etat nom="direct">
              <LiveStatus etat="direct" />
            </Etat>
            <Etat nom="retard">
              <LiveStatus etat="retard" retardSecondes={35} />
            </Etat>
            <Etat nom="coupé">
              <LiveStatus etat="coupe" />
            </Etat>
            <Etat nom="fermé">
              <LiveStatus etat="ferme" />
            </Etat>
          </div>
        </Card>
        <Card titre="FeedBanner" level={3} className="lg:col-span-2">
          <div className="flex flex-col gap-3">
            {COUPURES.map((c) => (
              <FeedBanner key={c.depuis} depuis={c.depuis} cause={c.cause} maintenant={MAINTENANT} />
            ))}
          </div>
        </Card>
      </div>
    </Section>
  )
}
