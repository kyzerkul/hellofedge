import { useEffect, useState } from 'react'
import { cssToken } from '../design/format'
import { Card } from '../ui/Card'
import { Section } from './Section'

interface Nuance {
  jeton: string
  /** Classe complète du fond, écrite en entier pour Tailwind. */
  fond: string
  role: string
}

const GROUPES: { titre: string; nuances: Nuance[] }[] = [
  {
    titre: 'Surfaces et texte',
    nuances: [
      { jeton: '--color-ink', fond: 'bg-ink', role: 'Fond de la page et du graphique' },
      { jeton: '--color-panel', fond: 'bg-panel', role: 'Fond des cartes' },
      { jeton: '--color-panel-2', fond: 'bg-panel-2', role: 'Éléments dans une carte, survol' },
      { jeton: '--color-line', fond: 'bg-line', role: 'Bordures, fond appuyé' },
      { jeton: '--color-line-soft', fond: 'bg-line-soft', role: 'Séparateurs, grille du graphique' },
      { jeton: '--color-text', fond: 'bg-text', role: 'Texte principal' },
      { jeton: '--color-muted', fond: 'bg-muted', role: 'Texte secondaire, bord des champs' },
    ],
  },
  {
    titre: 'Interface',
    nuances: [
      { jeton: '--color-accent', fond: 'bg-accent', role: 'Focus, sélection, bouton principal' },
      { jeton: '--color-accent-soft', fond: 'bg-accent-soft', role: 'Fond d’un élément sélectionné' },
      { jeton: '--color-buy', fond: 'bg-buy', role: 'Achat ; état « en direct »' },
      { jeton: '--color-sell', fond: 'bg-sell', role: 'Vente' },
      { jeton: '--color-danger', fond: 'bg-danger', role: 'Erreur, flux coupé' },
    ],
  },
  {
    titre: 'Niveaux (réservés)',
    nuances: [
      { jeton: '--color-level-liquidity', fond: 'bg-level-liquidity', role: 'Liquidité' },
      { jeton: '--color-level-ipa', fond: 'bg-level-ipa', role: 'IPA' },
      { jeton: '--color-level-extreme', fond: 'bg-level-extreme', role: 'Extrême d’une session précédente' },
      { jeton: '--color-level-target', fond: 'bg-level-target', role: 'Objectif' },
    ],
  },
  {
    titre: 'Bougies',
    nuances: [
      { jeton: '--color-candle-up', fond: 'bg-candle-up', role: 'Bougie haussière' },
      { jeton: '--color-candle-down', fond: 'bg-candle-down', role: 'Bougie baissière (sur le fond seulement)' },
    ],
  },
  {
    titre: 'Sessions (bandes à 12 %)',
    nuances: [
      { jeton: '--color-session-asia', fond: 'bg-session-asia', role: 'Tokyo' },
      { jeton: '--color-session-frankfurt', fond: 'bg-session-frankfurt', role: 'Francfort' },
      { jeton: '--color-session-london', fond: 'bg-session-london', role: 'Londres' },
      { jeton: '--color-session-trap', fond: 'bg-session-trap', role: 'Heure piège' },
      { jeton: '--color-session-newyork', fond: 'bg-session-newyork', role: 'New York' },
      { jeton: '--color-session-londonclose', fond: 'bg-session-londonclose', role: 'Clôture de Londres' },
    ],
  },
]

export function Couleurs() {
  // Les valeurs sont lues dans le thème à l'exécution : jamais recopiées ici.
  const [valeurs, setValeurs] = useState<Record<string, string>>({})
  useEffect(() => {
    const lues: Record<string, string> = {}
    for (const g of GROUPES) for (const n of g.nuances) lues[n.jeton] = cssToken(n.jeton)
    setValeurs(lues)
  }, [])

  return (
    <Section
      id="couleurs"
      titre="Couleurs"
      intro="Rouge = liquidité, bleu = IPA, blanc = extrêmes, jaune = objectif : ces quatre couleurs ne servent à rien d’autre, et ne colorent jamais un texte."
    >
      <div className="grid gap-4 lg:grid-cols-2">
        {GROUPES.map((g) => (
          <Card key={g.titre} titre={g.titre} level={3}>
            <ul className="m-0 grid list-none gap-2.5 p-0 sm:grid-cols-2">
              {g.nuances.map((n) => (
                <li key={n.jeton} className="flex min-w-0 items-center gap-3">
                  <span aria-hidden className={`size-10 shrink-0 rounded-md border border-line ${n.fond}`} />
                  <span className="flex min-w-0 flex-col">
                    <span className="text-sm font-medium">{n.role}</span>
                    <code className="truncate font-mono text-xs text-muted">
                      {n.jeton}
                      {valeurs[n.jeton] ? ` · ${valeurs[n.jeton]}` : ''}
                    </code>
                  </span>
                </li>
              ))}
            </ul>
          </Card>
        ))}
      </div>
    </Section>
  )
}
