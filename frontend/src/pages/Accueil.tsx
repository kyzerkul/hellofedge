import { CircleCheck, LoaderCircle, TriangleAlert } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Card } from '../ui/Card'
import { Chip } from '../ui/Chip'
import { LevelChip } from '../ui/LevelChip'
import { link } from '../ui/styles'
import { Shell } from './Shell'

type Health = 'chargement' | 'ok' | 'hors service'

const HEALTH_ICON = {
  chargement: <LoaderCircle aria-hidden size={20} className="animate-spin text-muted" />,
  ok: <CircleCheck aria-hidden size={20} className="text-buy" />,
  'hors service': <TriangleAlert aria-hidden size={20} className="text-danger" />,
}

const HEALTH_NOTE = {
  chargement: 'Vérification en cours.',
  ok: "L'api et sa base répondent. Les prix en direct arriveront avec le fil minimal.",
  'hors service': "L'api ou sa base ne répond pas. Recharge la page dans un instant ; si ça dure, regarde les journaux du serveur.",
}

const NEXT = [
  { nom: 'Connexion', detail: 'un seul compte, depuis ton ordinateur comme depuis ton téléphone' },
  { nom: 'Fil minimal', detail: 'bougie, prise de liquidité, alerte Telegram et graphique dans le cockpit' },
  { nom: 'Moteur SMC', detail: 'structure, FVG, IPA, AMD, puis le modèle d’entrée complet' },
]

/** Accueil : l'état du serveur, ce que fait l'outil, ce qui arrive. */
export default function Accueil() {
  const [health, setHealth] = useState<Health>('chargement')

  useEffect(() => {
    fetch('/api/health')
      .then((res) => setHealth(res.ok ? 'ok' : 'hors service'))
      .catch(() => setHealth('hors service'))
  }, [])

  return (
    <Shell page="accueil">
      <div className="mb-6 flex flex-col gap-2">
        <p className="m-0 text-label text-muted">Cockpit USD/JPY</p>
        <p className="m-0 max-w-2xl font-display text-xl leading-snug font-bold text-text">
          Le graphique lu selon ta méthode, les setups repérés, les alertes au bon moment.
        </p>
        <div className="mt-1 flex flex-wrap gap-2">
          <LevelChip kind="liquidite" />
          <LevelChip kind="ipa" />
          <LevelChip kind="extreme" />
          <LevelChip kind="objectif" />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card titre="État du serveur" actions={<Chip>squelette</Chip>}>
          <div role="status" className="flex items-center gap-2.5">
            {HEALTH_ICON[health]}
            <p className="m-0 text-base">État du serveur : {health}</p>
          </div>
          <p className="mt-3 mb-0 text-sm text-muted">{HEALTH_NOTE[health]}</p>
        </Card>

        <Card titre="Ce que fait Hellofedge">
          <ul className="m-0 flex list-none flex-col gap-2 p-0 text-sm">
            <li>Analyse le graphique USD/JPY selon la méthode SMC (RedPillFX).</li>
            <li>Surveille les niveaux et t'alerte sur Telegram.</li>
            <li>Journalise chaque setup pour l'étude.</li>
            <li className="text-muted">Il ne passe jamais d'ordre : l'accès au courtier est en lecture seule.</li>
          </ul>
        </Card>

        <Card titre="Ce qui arrive" className="md:col-span-2 lg:col-span-1">
          <ol className="m-0 flex list-none flex-col gap-2.5 p-0 text-sm">
            {NEXT.map((n, i) => (
              <li key={n.nom} className="grid grid-cols-[1.5rem_1fr] gap-2">
                <span className="font-mono text-xs leading-5 text-muted">{i + 1}.</span>
                <span>
                  <strong className="font-semibold">{n.nom}</strong>
                  <span className="text-muted"> : {n.detail}</span>
                </span>
              </li>
            ))}
          </ol>
          <p className="mt-4 mb-0 text-sm">
            <a href="/vitrine" className={link}>
              Voir la vitrine du design system
            </a>
          </p>
        </Card>
      </div>
    </Shell>
  )
}
