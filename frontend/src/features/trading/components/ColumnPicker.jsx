import { COLUMN_LABELS } from "../columns";
import { useState } from "react";

export function ColumnPicker({ visible, onToggle, onReset }) {
  const [search, setSearch] = useState("");
  const columns = Object.entries(COLUMN_LABELS).filter(([, label]) => label.toLocaleLowerCase("ru").includes(search.trim().toLocaleLowerCase("ru")));
  return (
    <details className="column-picker" onToggle={(event) => { if (!event.currentTarget.open) setSearch(""); }} onKeyDown={(event) => {
      if (event.key === "Escape") {
        event.currentTarget.open = false;
        event.currentTarget.querySelector("summary").focus();
      }
    }}>
      <summary>Колонки</summary>
      <div className="column-menu">
        <input className="dropdown-search" type="search" placeholder="Найти колонку" aria-label="Поиск колонки" value={search} onChange={(event) => setSearch(event.target.value)} />
        {columns.map(([key, label]) => (
          <label key={key}>
            <input type="checkbox" checked={visible.includes(key)} onChange={() => onToggle(key)} />
            {label}
          </label>
        ))}
        {!columns.length && <p className="summary" role="status">Ничего не найдено</p>}
        <button type="button" onClick={onReset}>Показать все</button>
      </div>
    </details>
  );
}
