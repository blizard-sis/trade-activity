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
    updateFilter,
    sortBy,
    toggleColumn,
    showAllColumns,
  } = usePositions();

  return (
    <Layout title="Торговля">
      <section className="filters trading-filters">
        <PositionFilters accounts={accounts} filters={filters} onChange={updateFilter} />
        <ColumnPicker visible={visibleColumns} onToggle={toggleColumn} onReset={showAllColumns} />
      </section>

      <PositionsTable
        loading={loading}
        positions={positions}
        visibleColumns={visibleColumns}
        onSort={sortBy}
        sort={filters.sort}
        sortDirection={filters.direction_sort}
        error={error}
      />
    </Layout>
  );
}
