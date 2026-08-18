import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";

import { api } from "../api";
import { Layout } from "../components/Layout";
import { Message } from "../components/Message";
import { formatDate, formatMoney, formatPrice, formatQuantity, resultClass } from "../format";


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

const COLUMN_LABELS = {
  entry_at: "Вход",
  exit_at: "Выход",
  account: "Счёт",
  instrument: "Инструмент",
  direction: "Направление",
  entry_quantity: "Объём входа",
  remaining: "Остаток",
  entry_price: "Цена входа",
  exit_price: "Цена выхода",
  gross_result: "Результат",
  commission: "Комиссия",
  net_result: "Чистыми",
  status: "Статус",
  order_count: "Ордеров",
  entry_note: "Заметка к входу",
  exit_note: "Заметка к выходу",
};

const DEFAULT_COLUMNS = Object.keys(COLUMN_LABELS);


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
    Promise.all([api.accounts(), api.loadPositionTableSettings()])
      .then(([loadedAccounts, settings]) => {
        setAccounts(loadedAccounts);
        if (settings.visible_columns?.length) setVisibleColumns(settings.visible_columns);
      })
      .catch((requestError) => setError(requestError.message));
  }, []);

  useEffect(() => {
    const timer = setTimeout(loadPositions, 120);
    return () => clearTimeout(timer);
  }, [loadPositions]);

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
      setAccounts(await api.accounts());
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

  function updateNote(positionId, field, value) {
    setPositions((current) => current.map((position) => (
      position.id === positionId ? { ...position, [field]: value } : position
    )));
  }

  async function saveNotes(position) {
    try {
      await api.savePositionNotes(position.id, {
        entry_note: position.entry_note,
        exit_note: position.exit_note,
      });
    } catch (requestError) {
      setError(requestError.message);
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

  const columns = createColumns({ updateNote, saveNotes });
  const displayedColumns = columns.filter((column) => visibleColumns.includes(column.key));
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
    <Layout title="Позиции T‑Bank" subtitle={`Позиций: ${positions.length}`} action={actions}>
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
      <div className="table-card">
        <table className="positions-table">
          <thead><tr>
            {displayedColumns.map((column) => (
              <th
                key={column.key}
                className={`${column.sort ? "sortable" : ""} ${column.align || ""}`}
                onClick={column.sort ? () => sortBy(column.sort) : undefined}
              >
                {column.label}
              </th>
            ))}
          </tr></thead>
          <tbody>
            {positions.map((position) => (
              <tr key={position.id}>
                {displayedColumns.map((column) => (
                  <td key={column.key} className={column.align || ""}>{column.render(position)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {!error && positions.length === 0 && <Message>Нет позиций для выбранных фильтров</Message>}
      </div>
    </Layout>
  );
}


function createColumns({ updateNote, saveNotes }) {
  return [
    { key: "entry_at", label: "Вход", sort: "date", align: "text-left", render: (item) => formatDate(item.entry_at) },
    { key: "exit_at", label: "Выход", sort: "exit", align: "text-left", render: (item) => formatDate(item.exit_at) },
    { key: "account", label: "Счёт", sort: "account", align: "text-left", render: (item) => item.account_name },
    { key: "instrument", label: "Инструмент", sort: "ticker", align: "text-left", render: (item) => item.ticker || item.instrument_name },
    { key: "direction", label: "Направление", sort: "direction", render: (item) => <span className={item.direction}>{item.direction === "long" ? "Лонг" : "Шорт"}</span> },
    { key: "entry_quantity", label: "Объём входа", sort: "quantity", render: (item) => formatQuantity(item.entry_quantity) },
    { key: "remaining", label: "Остаток", render: (item) => formatQuantity(item.remaining) },
    { key: "entry_price", label: "Цена входа", sort: "entry", render: (item) => formatPrice(item.entry_price, item.price_precision, item.currency) },
    { key: "exit_price", label: "Цена выхода", render: (item) => formatPrice(item.exit_price, item.price_precision, item.currency) },
    { key: "gross_result", label: "Результат", render: (item) => formatMoney(item.gross_result) },
    { key: "commission", label: "Комиссия", render: (item) => formatMoney(item.commission) },
    { key: "net_result", label: "Чистыми", render: (item) => <span className={resultClass(item.net_result)}>{formatMoney(item.net_result)}</span> },
    { key: "status", label: "Статус", sort: "status", render: (item) => <span className={item.status}>{item.status === "closed" ? "Закрыта" : "Открыта"}</span> },
    { key: "order_count", label: "Ордеров", render: (item) => item.order_count },
    { key: "entry_note", label: "Заметка к входу", align: "text-left", render: (item) => <NoteField position={item} field="entry_note" onChange={updateNote} onSave={saveNotes} /> },
    { key: "exit_note", label: "Заметка к выходу", align: "text-left", render: (item) => <NoteField position={item} field="exit_note" onChange={updateNote} onSave={saveNotes} /> },
  ];
}


function ColumnPicker({ visible, onToggle, onReset }) {
  return (
    <details className="column-picker">
      <summary>Колонки</summary>
      <div className="column-menu">
        {Object.entries(COLUMN_LABELS).map(([key, label]) => (
          <label key={key}>
            <input type="checkbox" checked={visible.includes(key)} onChange={() => onToggle(key)} />
            {label}
          </label>
        ))}
        <button type="button" onClick={onReset}>Показать все</button>
      </div>
    </details>
  );
}


function NoteField({ position, field, onChange, onSave }) {
  const [editing, setEditing] = useState(false);
  const textarea = useRef(null);

  useLayoutEffect(() => {
    if (!editing || !textarea.current) return;
    resizeTextarea(textarea.current);
    textarea.current.focus();
  }, [editing]);

  if (!editing) {
    return (
      <button
        className={`note-view ${position[field] ? "" : "empty"}`}
        type="button"
        onClick={() => setEditing(true)}
      >
        {position[field] || "Добавить заметку"}
      </button>
    );
  }

  return (
    <textarea
      ref={textarea}
      className="note-input"
      rows="1"
      value={position[field]}
      placeholder="Добавить заметку"
      onChange={(event) => {
        onChange(position.id, field, event.target.value);
        resizeTextarea(event.currentTarget);
      }}
      onBlur={async () => {
        await onSave({ ...position, [field]: textarea.current.value });
        setEditing(false);
      }}
      onKeyDown={(event) => {
        if (event.ctrlKey && event.key === "Enter") event.currentTarget.blur();
      }}
    />
  );
}


function resizeTextarea(textarea) {
  textarea.style.height = "auto";
  textarea.style.height = `${textarea.scrollHeight}px`;
}
