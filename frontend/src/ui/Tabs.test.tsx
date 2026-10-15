import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { Tab, TabList, TabPanel, Tabs } from './Tabs'

function Vues() {
  return (
    <Tabs>
      <TabList aria-label="Vues">
        <Tab id="graphique">Graphique</Tab>
        <Tab id="setups">Setups</Tab>
        <Tab id="retours" isDisabled>
          Retours
        </Tab>
        <Tab id="journal">Journal</Tab>
      </TabList>
      <TabPanel id="graphique">Panneau graphique</TabPanel>
      <TabPanel id="setups">Panneau setups</TabPanel>
      <TabPanel id="retours">Panneau retours</TabPanel>
      <TabPanel id="journal">Panneau journal</TabPanel>
    </Tabs>
  )
}

describe('Tabs', () => {
  it('changes tab with the arrows, without pressing Enter (AC-5)', async () => {
    const user = userEvent.setup()
    render(<Vues />)

    await user.tab()
    expect(screen.getByRole('tab', { name: 'Graphique' })).toHaveAttribute('data-focus-visible')
    await user.keyboard('{ArrowRight}')

    expect(screen.getByRole('tab', { name: 'Setups' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByRole('tabpanel')).toHaveTextContent('Panneau setups')
  })

  it('skips a disabled tab', async () => {
    const user = userEvent.setup()
    render(<Vues />)

    await user.tab()
    await user.keyboard('{ArrowRight}{ArrowRight}')

    expect(screen.getByRole('tab', { name: 'Journal' })).toHaveAttribute('aria-selected', 'true')
  })
})
