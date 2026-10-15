import { FlaskConical } from 'lucide-react'
import { I18nProvider } from 'react-aria-components'
import { Shell } from '../pages/Shell'
import { Chip } from '../ui/Chip'
import { link } from '../ui/styles'
import { Apercu } from './Apercu'
import { Composants } from './Composants'
import { Couleurs } from './Couleurs'
import { Espacements } from './Espacements'
import { Etats } from './Etats'
import { Typographie } from './Typographie'

const SOMMAIRE = [
  { id: 'couleurs', titre: 'Couleurs' },
  { id: 'typographie', titre: 'Typographie' },
  { id: 'espacements', titre: 'Espacements et rayons' },
  { id: 'composants', titre: 'Composants' },
  { id: 'etats', titre: 'États' },
  { id: 'apercu', titre: 'Aperçu du graphique' },
]

/** Vitrine du design system (spec 0003) : tout le langage visuel, sur des données factices. */
export default function Vitrine() {
  return (
    <I18nProvider locale="fr-FR">
      <Shell page="vitrine">
        <div className="mb-8 flex flex-col gap-3">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="m-0 text-2xl">Vitrine du design system</h1>
            <Chip tone="accent">
              <FlaskConical aria-hidden size={16} />
              Données factices
            </Chip>
          </div>
          <p className="m-0 max-w-3xl text-base text-muted">
            Les couleurs, les polices et les composants du cockpit, avant les vrais écrans. Rien ici ne vient du marché.
            Les valeurs sont décrites dans <code className="font-mono text-text">docs/design.md</code>.
          </p>
          <nav aria-label="Sur cette page">
            <ul className="m-0 flex list-none flex-wrap gap-x-4 gap-y-1 p-0 text-sm">
              {SOMMAIRE.map((s) => (
                <li key={s.id}>
                  <a href={`#${s.id}`} className={link}>
                    {s.titre}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        </div>
        <div className="flex flex-col gap-12">
          <Couleurs />
          <Typographie />
          <Espacements />
          <Composants />
          <Etats />
          <Apercu />
        </div>
      </Shell>
    </I18nProvider>
  )
}
