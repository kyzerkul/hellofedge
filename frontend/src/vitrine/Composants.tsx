import { Layers, RefreshCw } from 'lucide-react'
import { useState } from 'react'
import { ListBox } from 'react-aria-components'
import { formatNumber } from '../design/format'
import { Button, type ButtonVariant } from '../ui/Button'
import { Card } from '../ui/Card'
import { Checkbox } from '../ui/Checkbox'
import { Chip } from '../ui/Chip'
import { DirectionChip } from '../ui/DirectionChip'
import { LevelChip } from '../ui/LevelChip'
import { Price } from '../ui/Price'
import { Select, SelectItem } from '../ui/Select'
import { listBox } from '../ui/styles'
import { Table } from '../ui/Table'
import { Tab, TabList, TabPanel, Tabs } from '../ui/Tabs'
import { TextField } from '../ui/TextField'
import { Time } from '../ui/Time'
import { ToggleButton, ToggleButtonGroup } from '../ui/ToggleButton'
import { CALQUES, SESSIONS_CHOIX, type Setup, SETUPS, UNITES } from './donnees'
import { Etat, Section } from './Section'

const VARIANTES: ButtonVariant[] = ['primaire', 'secondaire', 'discret']

function Grille({ children }: { children: React.ReactNode }) {
  return <div className="flex flex-wrap items-start gap-x-6 gap-y-4">{children}</div>
}

function Boutons() {
  const [compte, setCompte] = useState(0)
  return (
    <Card titre="Button" level={3} actions={<Chip>primaire, secondaire, discret</Chip>} className="lg:col-span-2">
      <div className="flex flex-col gap-5">
        {VARIANTES.map((v) => (
          <Grille key={v}>
            <Etat nom={`${v} · normal`}>
              <Button variant={v} onPress={() => setCompte((c) => c + 1)}>
                Valider
              </Button>
            </Etat>
            <Etat nom="survol">
              <Button variant={v} data-demo="hovered">
                Valider
              </Button>
            </Etat>
            <Etat nom="appuyé">
              <Button variant={v} data-demo="pressed">
                Valider
              </Button>
            </Etat>
            <Etat nom="focus clavier">
              <Button variant={v} data-demo="focus-visible">
                Valider
              </Button>
            </Etat>
            <Etat nom="désactivé">
              <Button variant={v} isDisabled>
                Valider
              </Button>
            </Etat>
            <Etat nom="en cours">
              <Button variant={v} isPending>
                Valider
              </Button>
            </Etat>
          </Grille>
        ))}
        <Grille>
          <Etat nom="icône seule (aria-label)">
            <Button aria-label="Actualiser">
              <RefreshCw aria-hidden size={20} />
            </Button>
          </Etat>
          <Etat nom="icône et texte">
            <Button>
              <Layers aria-hidden size={20} />
              Calques
            </Button>
          </Etat>
        </Grille>
        <p className="m-0 text-xs text-muted" aria-live="polite">
          Essaie le premier bouton au clavier ou au doigt : {compte} appui{compte > 1 ? 's' : ''}.
        </p>
      </div>
    </Card>
  )
}

function Bascules() {
  return (
    <Card titre="ToggleButton, ToggleButtonGroup" level={3}>
      <div className="flex flex-col gap-5">
        <Grille>
          <Etat nom="choix unique, jamais vide (unités de temps)">
            <ToggleButtonGroup aria-label="Unité de temps" selectionMode="single" disallowEmptySelection defaultSelectedKeys={['M5']}>
              {UNITES.map((u) => (
                <ToggleButton key={u} id={u} className="font-mono">
                  {u}
                </ToggleButton>
              ))}
            </ToggleButtonGroup>
          </Etat>
          <Etat nom="choix multiple, vide permis (calques)">
            <ToggleButtonGroup aria-label="Calques" selectionMode="multiple" defaultSelectedKeys={['liquidite', 'ipa']}>
              {CALQUES.map((c) => (
                <ToggleButton key={c.id} id={c.id}>
                  {c.label}
                </ToggleButton>
              ))}
            </ToggleButtonGroup>
          </Etat>
        </Grille>
        <Grille>
          <Etat nom="normal">
            <ToggleButton>M15</ToggleButton>
          </Etat>
          <Etat nom="survol">
            <ToggleButton data-demo="hovered">M15</ToggleButton>
          </Etat>
          <Etat nom="appuyé">
            <ToggleButton data-demo="pressed">M15</ToggleButton>
          </Etat>
          <Etat nom="focus clavier">
            <ToggleButton data-demo="focus-visible">M15</ToggleButton>
          </Etat>
          <Etat nom="sélectionné">
            <ToggleButton defaultSelected>M15</ToggleButton>
          </Etat>
          <Etat nom="désactivé">
            <ToggleButton isDisabled>M15</ToggleButton>
          </Etat>
        </Grille>
      </div>
    </Card>
  )
}

function Onglets() {
  return (
    <Card titre="Tabs" level={3}>
      <div className="flex flex-col gap-5">
        <Tabs>
          <TabList aria-label="Vues du cockpit">
            <Tab id="graphique">Graphique</Tab>
            <Tab id="setups">Setups</Tab>
            <Tab id="journal">Journal</Tab>
            <Tab id="retours" isDisabled>
              Retours
            </Tab>
          </TabList>
          <TabPanel id="graphique" className="text-sm text-muted">
            Le graphique USD/JPY arrive avec le fil minimal.
          </TabPanel>
          <TabPanel id="setups" className="text-sm text-muted">
            Les setups repérés par le moteur.
          </TabPanel>
          <TabPanel id="journal" className="text-sm text-muted">
            Le journal de tes trades.
          </TabPanel>
          <TabPanel id="retours" className="text-sm text-muted">
            Bientôt.
          </TabPanel>
        </Tabs>
        <Tabs defaultSelectedKey="selectionne">
          <TabList aria-label="États des onglets">
            <Tab id="normal">normal</Tab>
            <Tab id="survol" data-demo="hovered">
              survol
            </Tab>
            <Tab id="focus" data-demo="focus-visible">
              focus clavier
            </Tab>
            <Tab id="selectionne">sélectionné</Tab>
            <Tab id="desactive" isDisabled>
              désactivé
            </Tab>
          </TabList>
          {['normal', 'survol', 'focus', 'selectionne', 'desactive'].map((id) => (
            <TabPanel key={id} id={id} className="text-xs text-muted">
              Chaque onglet est figé dans un état ; celui ci est sélectionné.
            </TabPanel>
          ))}
        </Tabs>
      </div>
    </Card>
  )
}

function Puces() {
  return (
    <Card titre="Chip, LevelChip, DirectionChip" level={3}>
      <div className="flex flex-col gap-5">
        <Grille>
          <Etat nom="neutre">
            <Chip>M5</Chip>
          </Etat>
          <Etat nom="accent">
            <Chip tone="accent">Données factices</Chip>
          </Etat>
          <Etat nom="achat">
            <DirectionChip direction="achat" />
          </Etat>
          <Etat nom="vente">
            <DirectionChip direction="vente" />
          </Etat>
        </Grille>
        <Grille>
          <Etat nom="liquidité vivante">
            <LevelChip kind="liquidite" />
          </Etat>
          <Etat nom="liquidité prise">
            <LevelChip kind="liquidite" pris />
          </Etat>
          <Etat nom="IPA">
            <LevelChip kind="ipa" />
          </Etat>
          <Etat nom="extrême">
            <LevelChip kind="extreme" />
          </Etat>
          <Etat nom="objectif">
            <LevelChip kind="objectif" />
          </Etat>
          <Etat nom="avec un prix">
            <LevelChip kind="ipa">
              <Price value="147.505" className="font-normal text-muted" />
            </LevelChip>
          </Etat>
        </Grille>
      </div>
    </Card>
  )
}

function Tableau() {
  return (
    <Card titre="Table, Price, Time" level={3} className="lg:col-span-2">
      <Table<Setup>
        legende="Setups de la journée (données factices)"
        rowKey={(s) => s.id}
        rows={SETUPS}
        columns={[
          { key: 'heure', titre: 'Heure', cell: (s) => <Time utc={s.heure} date /> },
          { key: 'sens', titre: 'Sens', cell: (s) => <DirectionChip direction={s.direction} /> },
          { key: 'niveau', titre: 'Niveau', cell: (s) => <LevelChip kind={s.niveau} /> },
          { key: 'entree', titre: 'Entrée', numerique: true, cell: (s) => <Price value={s.entree} /> },
          { key: 'stop', titre: 'Stop', numerique: true, cell: (s) => <Price value={s.stop} /> },
          { key: 'objectif', titre: 'Objectif', numerique: true, cell: (s) => <Price value={s.objectif} /> },
          { key: 'risque', titre: 'Risque', numerique: true, cell: (s) => formatNumber(s.risquePips, 'pip') },
          { key: 'r', titre: 'Résultat', numerique: true, cell: (s) => formatNumber(s.r, 'r') },
        ]}
      />
    </Card>
  )
}

function Saisie() {
  return (
    <Card titre="TextField, Checkbox, Select" level={3} className="lg:col-span-2">
      <div className="flex flex-col gap-6">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <TextField label="Adresse e-mail" type="email" placeholder="toi@exemple.fr" description="normal, avec une aide" />
          <TextField label="Mot de passe" type="password" demo="focus-visible" description="focus (à tout focus)" />
          <TextField label="Seuil de retard" defaultValue="vingt" isInvalid errorMessage="Écris un nombre de secondes, par exemple 20." />
          <TextField label="Fuseau d’affichage" defaultValue="Africa/Porto-Novo" isDisabled description="désactivé" />
        </div>
        <Grille>
          <Etat nom="non coché">
            <Checkbox>Alerte Telegram</Checkbox>
          </Etat>
          <Etat nom="coché">
            <Checkbox defaultSelected>Alerte Telegram</Checkbox>
          </Etat>
          <Etat nom="focus clavier">
            <Checkbox demo="focus-visible">Alerte Telegram</Checkbox>
          </Etat>
          <Etat nom="erreur">
            <Checkbox isInvalid errorMessage="Coche pour continuer.">
              J’ai lu les règles
            </Checkbox>
          </Etat>
          <Etat nom="désactivé">
            <Checkbox isDisabled defaultSelected>
              Son des alertes
            </Checkbox>
          </Etat>
        </Grille>
        <div className="grid items-start gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Select label="Session" options={SESSIONS_CHOIX} defaultSelectedKey="londres" description="fermé" />
          <Select label="Session (focus)" options={SESSIONS_CHOIX} demo="focus-visible" description="focus clavier" />
          <Select label="Session (erreur)" options={SESSIONS_CHOIX} isInvalid errorMessage="Choisis une session." />
          <Select label="Session (désactivé)" options={SESSIONS_CHOIX} isDisabled description="désactivé" />
          <div className="flex flex-col gap-1.5 sm:col-span-2 lg:col-span-1">
            <span className="text-sm font-medium">Liste ouverte</span>
            <ListBox aria-label="Exemple de liste ouverte" selectionMode="single" defaultSelectedKeys={['londres']} className={listBox}>
              {SESSIONS_CHOIX.map((s) => (
                <SelectItem key={s.id} id={s.id}>
                  {s.label}
                </SelectItem>
              ))}
            </ListBox>
            <span className="text-xs text-muted">ouvert</span>
          </div>
        </div>
      </div>
    </Card>
  )
}

export function Composants() {
  return (
    <Section
      id="composants"
      titre="Composants"
      intro="Chaque composant dans chacun de ses états, côte à côte. Les composants de la première ligne de chaque carte marchent pour de vrai : essaie Tab, les flèches, Entrée et Espace."
    >
      <div className="grid gap-4 lg:grid-cols-2">
        <Boutons />
        <Bascules />
        <Onglets />
        <Puces />
        <Tableau />
        <Saisie />
      </div>
    </Section>
  )
}
