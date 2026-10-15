import { formatPrice } from '../design/format'
import { Card } from '../ui/Card'
import { LevelChip, type LevelKind } from '../ui/LevelChip'
import { BOUGIES, LIGNES, SESSION } from './donnees'
import { Section } from './Section'

// Aperçu statique : des bougies factices et les styles de niveaux tracés avec les jetons.
// Le vrai graphique (Lightweight Charts) arrive avec le fil minimal (n°7), dans src/chart/.

const W = 720
const H = 320
const PLOT_RIGHT = 590
const PAD_TOP = 16
const PAD_BOTTOM = 16
const MIN = 147.38
const MAX = 147.78

const y = (price: number) => PAD_TOP + ((MAX - price) / (MAX - MIN)) * (H - PAD_TOP - PAD_BOTTOM)
const step = (PLOT_RIGHT - 16) / BOUGIES.length
const x = (i: number) => 16 + step * i + step / 2

// Classes complètes par niveau : jamais construites à la volée.
const TRAIT: Record<LevelKind, string> = {
  liquidite: 'stroke-level-liquidity',
  ipa: 'stroke-level-ipa',
  extreme: 'stroke-level-extreme',
  objectif: 'stroke-level-target',
}

const GRILLE = [147.4, 147.5, 147.6, 147.7]

export function Apercu() {
  const bandX = x(SESSION.debut) - step / 2
  return (
    <Section
      id="apercu"
      titre="Aperçu du graphique"
      intro="Bougies grises pour laisser la couleur aux niveaux. Niveau vivant en trait plein, niveau pris en pointillés estompés, chaque ligne nommée à son extrémité."
    >
      <Card titre="USD/JPY · M5 (données factices)" level={3}>
        <figure className="m-0 flex flex-col gap-3">
          <div className="overflow-hidden rounded-md border border-line-soft bg-ink">
            <svg
              viewBox={`0 0 ${W} ${H}`}
              role="img"
              aria-labelledby="apercu-svg-titre"
              className="block h-auto w-full font-sans"
            >
              <title id="apercu-svg-titre">
                Aperçu factice : vingt deux bougies M5, une liquidité prise sous {formatPrice('147.420')}, puis une remontée vers
                l’objectif, dans la session de Londres.
              </title>
              {GRILLE.map((p) => (
                <line key={p} x1={0} x2={PLOT_RIGHT} y1={y(p)} y2={y(p)} className="stroke-line-soft" strokeWidth={1} />
              ))}

              <rect x={bandX} y={0} width={PLOT_RIGHT - bandX} height={H} className="fill-session-london/12" />
              <text x={bandX + 8} y={H - 8} className="fill-text text-xs font-semibold">
                {SESSION.nom}
              </text>

              {BOUGIES.map((b, i) => {
                const hausse = b.close >= b.open
                const corps = hausse ? 'fill-candle-up stroke-candle-up' : 'fill-candle-down stroke-candle-down'
                const top = y(Math.max(b.open, b.close))
                const bas = y(Math.min(b.open, b.close))
                return (
                  <g key={i} className={corps}>
                    <line x1={x(i)} x2={x(i)} y1={y(b.high)} y2={y(b.low)} strokeWidth={1.5} />
                    <rect x={x(i) - step * 0.3} y={top} width={step * 0.6} height={Math.max(bas - top, 1.5)} rx={1} />
                  </g>
                )
              })}

              {LIGNES.map((l) => (
                <g key={l.nom} opacity={l.pris ? 0.5 : 1}>
                  <line
                    x1={0}
                    x2={PLOT_RIGHT}
                    y1={y(l.prix)}
                    y2={y(l.prix)}
                    className={TRAIT[l.kind]}
                    strokeWidth={l.pris ? 1 : 2}
                    strokeDasharray={l.pris ? '5 4' : undefined}
                  />
                </g>
              ))}
              {LIGNES.map((l) => (
                <text key={l.nom} x={PLOT_RIGHT + 8} y={y(l.prix) + 4} className="fill-text text-xs">
                  {l.nom}
                </text>
              ))}
            </svg>
          </div>
          <figcaption className="flex flex-wrap items-center gap-2 text-xs text-muted">
            <span className="me-1">Légende :</span>
            <LevelChip kind="liquidite" />
            <LevelChip kind="liquidite" pris />
            <LevelChip kind="ipa" />
            <LevelChip kind="extreme" />
            <LevelChip kind="objectif" />
          </figcaption>
        </figure>
      </Card>
    </Section>
  )
}
