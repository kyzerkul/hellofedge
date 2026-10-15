import type { ReactNode } from 'react'
import { cx, focusRing } from './styles'

export interface Column<Row> {
  key: string
  titre: string
  /** Colonne numérique : alignée à droite, en chasse fixe. */
  numerique?: boolean
  cell: (row: Row) => ReactNode
}

export interface TableProps<Row> {
  /** Légende obligatoire : elle nomme le tableau et sa zone de défilement. */
  legende: string
  columns: Column<Row>[]
  rows: Row[]
  rowKey: (row: Row) => string
  className?: string
}

/** Tableau sémantique ; sur un petit écran il défile à l'horizontale, au clavier compris. */
export function Table<Row>({ legende, columns, rows, rowKey, className }: TableProps<Row>) {
  return (
    <div
      role="region"
      aria-label={legende}
      tabIndex={0}
      className={cx(
        'max-w-full overflow-x-auto rounded-md',
        focusRing,
        // Pas de React Aria ici : l'anneau suit :focus-visible, que le navigateur réserve au clavier.
        'focus-visible:outline-2 focus-visible:outline-solid focus-visible:outline-offset-2 focus-visible:outline-accent',
        className,
      )}
    >
      <table className="w-full border-collapse text-sm">
        <caption className="mb-2 text-left text-label text-muted">{legende}</caption>
        <thead>
          <tr>
            {columns.map((c) => (
              <th
                key={c.key}
                scope="col"
                className={cx(
                  'border-b border-line px-2 py-1.5 text-label whitespace-nowrap text-muted',
                  c.numerique ? 'text-right' : 'text-left',
                )}
              >
                {c.titre}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={rowKey(row)} className="border-b border-line-soft last:border-b-0">
              {columns.map((c) => (
                <td
                  key={c.key}
                  className={cx('px-2 py-2 align-top', c.numerique && 'text-right font-mono whitespace-nowrap tabular-nums')}
                >
                  {c.cell(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
