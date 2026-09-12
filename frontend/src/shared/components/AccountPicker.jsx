export function AccountPicker({ accounts, value, onChange }) {
  const selected = Array.isArray(value) ? value : value ? [value] : [];
  function toggle(id) {
    onChange(selected.includes(id) ? selected.filter((item) => item !== id) : [...selected, id]);
  }
  const label = selected.length === 0 ? "Все платформы и счета" : selected.length === 1
    ? accounts.find((account) => account.id === selected[0])?.name || "Выбранный счёт"
    : `Выбрано счетов: ${selected.length}`;
  return <details className="account-picker">
    <summary aria-label="Выбор платформ и счетов">{label}</summary>
    <div className="account-menu">
      <button type="button" onClick={() => onChange([])}>Все платформы и счета</button>
      {accounts.map((account) => <label key={account.id}>
        <input type="checkbox" checked={selected.includes(account.id)} onChange={() => toggle(account.id)} />
        {account.name}
      </label>)}
    </div>
  </details>;
}
