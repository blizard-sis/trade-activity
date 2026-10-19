import { Tabs } from "@mantine/core";
import { Layout } from "../../app/Layout";
import { InstrumentLinksPanel } from "./InstrumentLinksPanel";
import { MainInstrumentsTable } from "./MainInstrumentsTable";

export function SettingsPage() {
  return (
    <Layout title="Настройки" subtitle="Инструменты, графики и связки для торговли">
      <Tabs defaultValue="main" keepMounted={false}>
        <Tabs.List>
          <Tabs.Tab value="main">Основные инструменты</Tabs.Tab>
          <Tabs.Tab value="links">Связки инструментов</Tabs.Tab>
        </Tabs.List>
        <Tabs.Panel value="main" pt="lg">
          <MainInstrumentsTable />
        </Tabs.Panel>
        <Tabs.Panel value="links" pt="lg">
          <InstrumentLinksPanel />
        </Tabs.Panel>
      </Tabs>
    </Layout>
  );
}
