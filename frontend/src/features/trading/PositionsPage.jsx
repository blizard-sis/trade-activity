import { Button } from "@mantine/core";
import { Layout } from "../../app/Layout";
import { PositionFilters } from "../../shared/positions/PositionFilters";
import { ColumnPicker } from "./components/ColumnPicker";
import { PositionsTable } from "./components/PositionsTable";
import { usePositions } from "./usePositions";
import "./trading.css";

export function PositionsPage() {
  const {
    accounts,
    filters,
    positions,
    loading,
    visibleColumns,
    error,
    syncing,
    updateFilter,
    sortBy,
    synchronize,
    toggleColumn,
    showAllColumns,
  } = usePositions();

  const actions = (
    <div className="header-actions">
      <Button variant="filled" disabled={syncing} onClick={synchronize}>
        {syncing ? "Синхронизация…" : "Синхронизировать"}
      </Button>
    </div>
  );

  return (
    <Layout title="Торговля" action={actions}>
      <section className="filters trading-filters">
        <PositionFilters accounts={accounts} filters={filters} onChange={updateFilter} />
        <ColumnPicker visible={visibleColumns} onToggle={toggleColumn} onReset={showAllColumns} />
      </section>

      <PositionsTable
        loading={loading}
        positions={positions}
        visibleColumns={visibleColumns}
        onSort={sortBy}
        error={error}
      />
    </Layout>
  );
}
