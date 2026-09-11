import { useState } from "react";
import { api } from "../api";
import { FIELDS, exitLabel, exitTone } from "../model";
import { Message } from "../../../shared/components/Message";
import { formatMoney, formatPrice, resultClass } from "../../../shared/format";

export function JournalEditor({ position, onDirty, onSaving, onSaved }) {
  const [values, setValues] = useState(() => Object.fromEntries(FIELDS.map((key) => [key, position[key] || ""])));
  const [baseline, setBaseline] = useState(values);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const changed = FIELDS.some((key) => values[key] !== baseline[key]);

  function update(key, value) {
    const next = { ...values, [key]: value };
    setValues(next); setSaved(false);
    onDirty(FIELDS.some((field) => next[field] !== baseline[field]));
  }

  async function save(event) {
    event.preventDefault();
    setSaving(true); onSaving(true); setError(""); setSaved(false);
    try {
      const result = await api.saveJournal(position.id, values);
      setBaseline(result); onSaved(result); onDirty(false); setSaved(true);
    } catch (err) { setError(err.message); }
    finally { setSaving(false); onSaving(false); }
  }

  function textField(key, label, placeholder) {
    return <label className="journal-field">{label}<textarea aria-label={label} rows="4" maxLength={20000} value={values[key]} placeholder={placeholder} onChange={(e) => update(key, e.target.value)} /></label>;
  }

  return (
    <form className="journal-editor" onSubmit={save}>
      <header className="journal-editor-header"><div><h2>{position.ticker || position.instrument_name}</h2><span className="summary">{position.account_name} · <span className={position.direction}>{position.direction === "long" ? "Лонг" : "Шорт"}</span></span></div><a href={`/?position=${encodeURIComponent(position.id)}#${encodeURIComponent(`position-${position.id}`)}`}>Факты сделки ↗</a></header>
      <div className="journal-facts"><span>Вход <strong>{formatPrice(position.entry_price, position.price_precision, position.currency)}</strong></span><span>Выход <strong>{formatPrice(position.exit_price, position.price_precision, position.currency)}</strong></span><span>Чистыми <strong className={resultClass(position.net_result)}>{formatMoney(position.net_result)}</strong></span></div>
      <fieldset disabled={saving}>
        <legend>План и вход</legend>
        {textField("entry_note", "Причины входа", "Сетап, сигналы, что ожидал от сделки")}
        <div className="journal-plan">
          <label className="journal-field">Плановый стоп-лосс<input aria-label="Плановый стоп-лосс" inputMode="decimal" maxLength={20000} value={values.planned_stop} onChange={(e) => update("planned_stop", e.target.value)} placeholder="Цена в единицах инструмента" /></label>
          <label className="journal-field">Плановый тейк-профит<input aria-label="Плановый тейк-профит" inputMode="decimal" maxLength={20000} value={values.planned_take} onChange={(e) => update("planned_take", e.target.value)} placeholder="Цена в единицах инструмента" /></label>
        </div>
        <h3>Выход и разбор</h3>
        <div className={`exit-assessment ${exitTone(position)}`} aria-label="Причина выхода">
          <strong>{exitLabel(position)}</strong>
        </div>
        {textField("exit_note", "Комментарий к выходу", "Почему закрыл позицию, менял ли план")}
      </fieldset>
      {error && <Message type="error">{error}</Message>}
      <footer className="journal-save"><span role="status">{saved ? "Сохранено" : changed ? "Есть несохранённые изменения" : ""}</span><button className="primary" disabled={saving || !changed} type="submit">{saving ? "Сохранение…" : "Сохранить разбор"}</button></footer>
    </form>
  );
}
