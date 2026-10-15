import { Card } from '../ui/Card'
import { Section } from './Section'

const PAS = [
  { classe: 'w-1', nom: '1', px: '4 px' },
  { classe: 'w-2', nom: '2', px: '8 px' },
  { classe: 'w-3', nom: '3', px: '12 px' },
  { classe: 'w-4', nom: '4', px: '16 px' },
  { classe: 'w-6', nom: '6', px: '24 px' },
  { classe: 'w-8', nom: '8', px: '32 px' },
]

const RAYONS = [
  { classe: 'rounded-sm', nom: 'sm', px: '4 px', usage: 'cases' },
  { classe: 'rounded-md', nom: 'md', px: '7 px', usage: 'boutons, champs' },
  { classe: 'rounded-lg', nom: 'lg', px: '10 px', usage: 'cartes' },
  { classe: 'rounded-full', nom: 'full', px: '', usage: 'puces' },
]

export function Espacements() {
  return (
    <Section id="espacements" titre="Espacements et rayons" intro="L’échelle de Tailwind, au pas de 4 px. Compact à la souris, 44 px au doigt.">
      <div className="grid gap-4 md:grid-cols-3">
        <Card titre="Espacements" level={3}>
          <ul className="m-0 flex list-none flex-col gap-2 p-0">
            {PAS.map((p) => (
              <li key={p.nom} className="flex items-center gap-3 text-xs text-muted">
                <span aria-hidden className={`h-3 rounded-sm bg-accent ${p.classe}`} />
                <code className="font-mono">{p.nom}</code> · {p.px}
              </li>
            ))}
          </ul>
        </Card>
        <Card titre="Rayons" level={3}>
          <ul className="m-0 grid list-none grid-cols-2 gap-3 p-0">
            {RAYONS.map((r) => (
              <li key={r.nom} className="flex flex-col gap-1.5">
                <span aria-hidden className={`h-10 w-16 border border-muted bg-panel-2 ${r.classe}`} />
                <span className="text-xs text-muted">
                  <code className="font-mono">{r.nom}</code> {r.px && `· ${r.px}`} · {r.usage}
                </span>
              </li>
            ))}
          </ul>
        </Card>
        <Card titre="Tailles et durées" level={3}>
          <div className="flex items-end gap-4">
            <span className="flex flex-col items-center gap-1.5">
              <span aria-hidden className="h-8 w-16 rounded-md border border-dashed border-muted" />
              <span className="text-xs text-muted">32 px souris</span>
            </span>
            <span className="flex flex-col items-center gap-1.5">
              <span aria-hidden className="size-11 rounded-md border border-dashed border-accent" />
              <span className="text-xs text-muted">44 px doigt</span>
            </span>
          </div>
          <p className="mt-4 mb-0 text-xs text-muted">
            Survol et focus en <code className="font-mono">120 ms</code>, ouverture d’une liste en{' '}
            <code className="font-mono">200 ms</code>. Aucune animation quand le système demande moins de mouvement.
          </p>
        </Card>
      </div>
    </Section>
  )
}
