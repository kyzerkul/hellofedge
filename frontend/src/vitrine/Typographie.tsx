import { Card } from '../ui/Card'
import { Section } from './Section'

const FAMILLES = [
  { nom: 'Zen Kaku Gothic New', jeton: '--font-display', classe: 'font-display font-bold', usage: 'Titres', exemple: 'Liquidité prise à Londres' },
  { nom: 'IBM Plex Sans', jeton: '--font-sans', classe: 'font-sans', usage: 'Texte courant', exemple: 'Le prix revient dans la zone IPA du M5.' },
  { nom: 'JetBrains Mono', jeton: '--font-mono', classe: 'font-mono', usage: 'Prix, heures, chiffres', exemple: '147.584 · 14:05 · ¥' },
]

const ECHELLE = [
  { classe: 'text-2xl', jeton: '--text-2xl', px: '28 px', usage: 'Grand titre' },
  { classe: 'text-xl', jeton: '--text-xl', px: '22 px', usage: 'Prix principal' },
  { classe: 'text-lg', jeton: '--text-lg', px: '18 px', usage: 'Titre de page' },
  { classe: 'text-md', jeton: '--text-md', px: '16 px', usage: 'Champs de saisie' },
  { classe: 'text-base', jeton: '--text-base', px: '14 px (15 au doigt)', usage: 'Corps' },
  { classe: 'text-sm', jeton: '--text-sm', px: '13 px', usage: 'Boutons, tableaux' },
  { classe: 'text-xs', jeton: '--text-xs', px: '12 px', usage: 'Notes' },
]

export function Typographie() {
  return (
    <Section id="typographie" titre="Typographie" intro="Trois polices livrées avec le cockpit, rien depuis un domaine tiers. Interligne 1,45.">
      <div className="grid gap-4 lg:grid-cols-[2fr_3fr]">
        <Card titre="Familles" level={3}>
          <ul className="m-0 flex list-none flex-col gap-4 p-0">
            {FAMILLES.map((f) => (
              <li key={f.nom} className="flex flex-col gap-1">
                <span className={`text-xl leading-snug ${f.classe}`}>{f.exemple}</span>
                <span className="text-xs text-muted">
                  {f.nom} · <code className="font-mono">{f.jeton}</code> · {f.usage}
                </span>
              </li>
            ))}
          </ul>
        </Card>
        <Card titre="Échelle" level={3}>
          <ul className="m-0 flex list-none flex-col gap-2 p-0">
            {ECHELLE.map((t) => (
              <li key={t.jeton} className="grid grid-cols-[minmax(0,1fr)_auto] items-baseline gap-3 border-b border-line-soft pb-2 last:border-b-0">
                <span className={`truncate ${t.classe}`}>Prise de liquidité · 147.584</span>
                <span className="text-right text-xs whitespace-nowrap text-muted">
                  <code className="font-mono">{t.jeton}</code> · {t.px} · {t.usage}
                </span>
              </li>
            ))}
            <li className="grid grid-cols-[minmax(0,1fr)_auto] items-baseline gap-3">
              <span className="text-label text-muted">Étiquette de section</span>
              <span className="text-right text-xs whitespace-nowrap text-muted">
                <code className="font-mono">text-label</code> · 11 px, majuscules
              </span>
            </li>
          </ul>
        </Card>
      </div>
    </Section>
  )
}
