import { usePositions } from "./usePositions";
import { TradingViewImport } from "./components/TradingViewImport";
import { Button, TextInput } from "@mantine/core";
import { FilterSelect } from "../../shared/components/FilterSelect";
import { AccountPicker } from "../../shared/components/AccountPicker";

import { Layout } from "../../app/Layout";
import { ColumnPicker } from "./components/ColumnPicker";
import { PositionsTable } from "./components/PositionsTable";
import "./trading.css";

export function PositionsPage() {
  const { accounts, filters, positions, visibleColumns, error, syncing, exporting,
    showImport, setShowImport, importing, importTradingView, updateFilter, sortBy,
    synchronize, exportPositions, toggleColumn, showAllColumns } = usePositions();

  const actions = (
    <div className="header-actions">
      <Button onClick={() => setShowImport(!showImport)} aria-expanded={showImport}>Загрузить TradingView</Button>
      <Button disabled={exporting} onClick={exportPositions}>
        {exporting ? "Выгрузка…" : "Выгрузить JSON"}
      </Button>
      <Button variant="filled" disabled={syncing} onClick={synchronize}>
        {syncing ? "Синхронизация…" : "Синхронизировать"}
      </Button>
    </div>
  );

  return (
    <Layout title="Торговля" action={actions}>
      {showImport && <TradingViewImport importing={importing} onImport={importTradingView} />}
      <section className="filters trading-filters">
        <AccountPicker accounts={accounts} value={filters.account} onChange={(value) => updateFilter("account", value)} />
        <FilterSelect value={filters.direction} onChange={(value) => updateFilter("direction", value)} aria-label="Направление" placeholder="Лонг и шорт" data={[{"value": "long", "label": "Лонг"}, {"value": "short", "label": "Шорт"}]} />
        <FilterSelect value={filters.status} onChange={(value) => updateFilter("status", value)} aria-label="Статус позиции" placeholder="Все позиции" data={[{"value": "closed", "label": "Закрытые"}, {"value": "open", "label": "Открытые"}]} />
        <TextInput type="date" aria-label="Дата входа от" value={filters.from} onChange={(event) => updateFilter("from", event.target.value)} />
        <TextInput type="date" aria-label="Дата входа до" value={filters.to} onChange={(event) => updateFilter("to", event.target.value)} />
        <TextInput className="search" aria-label="Поиск инструмента" type="search" placeholder="Тикер или инструмент" value={filters.search} onChange={(event) => updateFilter("search", event.target.value)} />
        <ColumnPicker visible={visibleColumns} onToggle={toggleColumn} onReset={showAllColumns} />
      </section>

      <PositionsTable positions={positions} visibleColumns={visibleColumns} onSort={sortBy} error={error} />
    </Layout>
  );
}
