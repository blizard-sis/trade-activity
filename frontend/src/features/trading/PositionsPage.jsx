import { useCallback, useEffect, useState } from "react";

import { api } from "./api";
import { Layout } from "../../app/Layout";
import { Message } from "../../shared/components/Message";
import { loadAccounts } from "../../shared/api/accounts";
import { DEFAULT_COLUMNS } from "./columns";
import { ColumnPicker } from "./components/ColumnPicker";
import { PositionsTable } from "./components/PositionsTable";
import "./trading.css";


const DEFAULT_FILTERS = {
  account: "",
  direction: "",
  status: "",
  from: "",
  to: "",
  search: "",
  sort: "date",
  direction_sort: "desc",
};

export function PositionsPage() {
  const [accounts, setAccounts] = useState([]);
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [positions, setPositions] = useState([]);
  const [visibleColumns, setVisibleColumns] = useState(DEFAULT_COLUMNS);
  const [error, setError] = useState("");
  const [syncing, setSyncing] = useState(false);
  const [exporting, setExporting] = useState(false);

  const loadPositions = useCallback(async () => {
    try {
      setPositions(await api.positions(filters));
      setError("");
    } catch (requestError) {
      setError(requestError.message);
    }
  }, [filters]);

  useEffect(() => {
    Promise.all([loadAccounts(), api.loadPositionTableSettings()])
      .then(([loadedAccounts, settings]) => {
        setAccounts(loadedAccounts);
        if (settings.visible_columns?.length) {
          const available = settings.visible_columns.filter((key) => DEFAULT_COLUMNS.includes(key));
          if (available.length) setVisibleColumns(available);
        }
      })
      .catch((requestError) => setError(requestError.message));
  }, []);

  useEffect(() => {
    const timer = setTimeout(loadPositions, 120);
    return () => clearTimeout(timer);
  }, [loadPositions]);

  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get("position");
    if (id) document.getElementById(`position-${id}`)?.scrollIntoView({ block: "center" });
  }, [positions]);

  function updateFilter(name, value) {
    setFilters((current) => ({ ...current, [name]: value }));
  }

  function sortBy(field) {
    setFilters((current) => ({
      ...current,
      sort: field,
      direction_sort: current.sort === field && current.direction_sort === "desc" ? "asc" : "desc",
    }));
  }

  async function synchronize() {
    try {
      setSyncing(true);
      setError("");
      await api.sync();
      setAccounts(await loadAccounts());
      await loadPositions();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSyncing(false);
    }
  }

  async function exportPositions() {
    try {
      setExporting(true);
      setError("");
      const blob = await api.exportPositions(filters);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `trade-activity-${new Date().toISOString().slice(0, 10)}.json`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setExporting(false);
    }
  }

  async function toggleColumn(column) {
    const next = visibleColumns.includes(column)
      ? visibleColumns.filter((item) => item !== column)
      : [...visibleColumns, column];
    if (next.length === 0) return;

    setVisibleColumns(next);
    await api.savePositionTableSettings({ visible_columns: next });
  }

  async function showAllColumns() {
    setVisibleColumns(DEFAULT_COLUMNS);
    await api.clearPositionTableSettings();
  }

  const actions = (
    <div className="header-actions">
      <button disabled={exporting} onClick={exportPositions}>
        {exporting ? "Выгрузка…" : "Выгрузить JSON"}
      </button>
      <button className="primary" disabled={syncing} onClick={synchronize}>
        {syncing ? "Синхронизация…" : "Синхронизировать"}
      </button>
    </div>
  );

  return (
    <Layout title="Торговля" subtitle={`Позиций: ${positions.length}`} action={actions}>
      <section className="filters">
        <select value={filters.account} onChange={(event) => updateFilter("account", event.target.value)}>
          <option value="">Все счета</option>
          {accounts.map((account) => <option key={account.id} value={account.id}>{account.name}</option>)}
        </select>
        <select value={filters.direction} onChange={(event) => updateFilter("direction", event.target.value)}>
          <option value="">Лонг и шорт</option><option value="long">Лонг</option><option value="short">Шорт</option>
        </select>
        <select value={filters.status} onChange={(event) => updateFilter("status", event.target.value)}>
          <option value="">Все позиции</option><option value="closed">Закрытые</option><option value="open">Открытые</option>
        </select>
        <input type="date" title="Дата входа от" value={filters.from} onChange={(event) => updateFilter("from", event.target.value)} />
        <input type="date" title="Дата входа до" value={filters.to} onChange={(event) => updateFilter("to", event.target.value)} />
        <input className="search" type="search" placeholder="Тикер или инструмент" value={filters.search} onChange={(event) => updateFilter("search", event.target.value)} />
        <ColumnPicker visible={visibleColumns} onToggle={toggleColumn} onReset={showAllColumns} />
      </section>

      {error && <Message type="error">{error}</Message>}
      <PositionsTable positions={positions} visibleColumns={visibleColumns} onSort={sortBy} error={error} />
    </Layout>
  );
}
