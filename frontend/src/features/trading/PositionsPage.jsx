import { AccountPicker } from "../../shared/components/AccountPicker";
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
  const [showImport, setShowImport] = useState(false);
  const [importing, setImporting] = useState(false);
  const [importFiles, setImportFiles] = useState([]);
  const [paperName, setPaperName] = useState("Paper Trading");
  const [importMessage, setImportMessage] = useState("");

  async function importTradingView(event) {
    event.preventDefault();
    setImporting(true);
    setError("");
    setImportMessage("");
    try {
      const body = new FormData();
      importFiles.forEach((file) => body.append("files", file));
      body.append("account_name", paperName);
      const result = await api.importTradingView(body);
      setImportMessage(`Добавлено: ${result.added}. Обновлено: ${result.updated}. Без изменений: ${result.unchanged}. В файле: ${result.closed} закрытых и ${result.open} открытых позиций.${result.ignored.length ? " Текущие заявки, снимок позиций и журнал активности не импортируются отдельно." : ""}`);
      setAccounts(await loadAccounts());
      setFilters({ ...DEFAULT_FILTERS, account: result.account_id });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setImporting(false);
    }
  }

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
      <button onClick={() => setShowImport(!showImport)} aria-expanded={showImport}>Загрузить TradingView</button>
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
      {showImport && <form className="tradingview-import" onSubmit={importTradingView}>
        <strong>TradingView Paper Trading</strong>
        <p>Выберите CSV «История сделок» (trade-history). Можно выбрать сразу все 6 файлов: история заявок уточнит время, история баланса — результат и валюту цены.</p>
        <p>Для повторной загрузки используйте то же название счёта. Для другого демо-счёта или после сброса баланса укажите новое. Время сохраняется как в выгрузке.</p>
        <label>Название демо-счёта <input required maxLength={100} value={paperName} disabled={importing} onChange={(event) => setPaperName(event.target.value)} /></label>
        <label>CSV-файлы <input type="file" accept=".csv,text/csv" multiple required disabled={importing} onChange={(event) => setImportFiles(Array.from(event.target.files))} /></label>
        <button className="primary" disabled={importing || !importFiles.length}>{importing ? "Загрузка…" : "Импортировать"}</button>
      </form>}
      {importMessage && <Message>{importMessage}</Message>}
      <section className="filters">
        <AccountPicker accounts={accounts} value={filters.account} onChange={(value) => updateFilter("account", value)} />
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
