import { COLUMN_LABELS } from "../columns";

export function ColumnPicker({ visible, onToggle, onReset }) {
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
