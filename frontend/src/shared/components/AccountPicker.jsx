import { useState } from "react";

export function AccountPicker({ accounts, value, onChange }) {
  const [search, setSearch] = useState("");
  const filtered = accounts.filter((account) => account.name.toLocaleLowerCase("ru").includes(search.trim().toLocaleLowerCase("ru")));
  const selected = Array.isArray(value) ? value : value ? [value] : [];
  function toggle(id) {
    onChange(selected.includes(id) ? selected.filter((item) => item !== id) : [...selected, id]);
  }
  const label = selected.length === 0 ? "Все платформы и счета" : selected.length === 1
    ? accounts.find((account) => account.id === selected[0])?.name || "Выбранный счёт"
    : `Выбрано счетов: ${selected.length}`;
  return <details className="account-picker" onToggle={(event) => { if (!event.currentTarget.open) setSearch(""); }} onKeyDown={(event) => {
    if (event.key === "Escape") {
      event.currentTarget.open = false;
      event.currentTarget.querySelector("summary").focus();
    }
  }}>
    <summary aria-label="Выбор платформ и счетов">{label}</summary>
    <div className="account-menu">
      <input className="dropdown-search" type="search" aria-label="Поиск платформы или счёта" placeholder="Платформа или счёт" value={search} onChange={(event) => setSearch(event.target.value)} />
      <button type="button" onClick={() => onChange([])}>Все платформы и счета</button>
      {filtered.map((account) => <label key={account.id}>
        <input type="checkbox" checked={selected.includes(account.id)} onChange={() => toggle(account.id)} />
        {account.name}
      </label>)}
      {!filtered.length && <p className="summary" role="status">Ничего не найдено</p>}
    </div>
  </details>;
}
