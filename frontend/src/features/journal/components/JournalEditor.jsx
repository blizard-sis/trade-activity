import { notifySuccess, useNotificationError } from "../../../shared/notifications";
import { Button, TextInput, Textarea, Paper } from "@mantine/core";
import { useState } from "react";
import { api } from "../api";
import { FIELDS, exitLabel, exitTone } from "../model";
import { formatMoney, formatPrice, resultClass } from "../../../shared/format";

export function JournalEditor({ position, onDirty, onSaving, onSaved }) {
  const [values, setValues] = useState(() => Object.fromEntries(FIELDS.map((key) => [key, position[key] || ""])));
  const [baseline, setBaseline] = useState(values);
  const [saving, setSaving] = useState(false);
  const [, setError] = useNotificationError();
  const changed = FIELDS.some((key) => values[key] !== baseline[key]);

  function update(key, value) {
    const next = { ...values, [key]: value };
    setValues(next);
    onDirty(FIELDS.some((field) => next[field] !== baseline[field]));
  }

  async function save(event) {
    event.preventDefault();
    setSaving(true); onSaving(true); setError("");
    try {
      const result = await api.saveJournal(position.id, values);
      setBaseline(result); onSaved(result); onDirty(false); notifySuccess("Разбор сделки сохранён.");
    } catch (err) { setError(err.message); }
    finally { setSaving(false); onSaving(false); }
  }

  function textField(key, label, placeholder) {
    return <Textarea className="journal-field" label={label} aria-label={label} minRows={4} maxLength={20000} value={values[key]} placeholder={placeholder} onChange={(e) => update(key, e.target.value)} />;
  }

  return (
    <Paper component="form" withBorder p="lg" className="journal-editor" onSubmit={save}>
      <header className="journal-editor-header"><div><h2>{position.ticker || position.instrument_name}</h2><span className="summary">{position.account_name} · <span className={position.direction}>{position.direction === "long" ? "Лонг" : "Шорт"}</span></span></div><a href={`/?position=${encodeURIComponent(position.id)}#${encodeURIComponent(`position-${position.id}`)}`}>Факты сделки ↗</a></header>
      <div className="journal-facts"><span>Вход <strong>{formatPrice(position.entry_price, position.price_precision, position.currency)}</strong></span><span>Выход <strong>{formatPrice(position.exit_price, position.price_precision, position.currency)}</strong></span><span>Чистыми <strong className={resultClass(position.net_result)}>{formatMoney(position.net_result, position.result_currency)}</strong></span></div>
      <fieldset disabled={saving}>
        <legend>План и вход</legend>
        {textField("entry_note", "Причины входа", "Сетап, сигналы, что ожидал от сделки")}
        <div className="journal-plan">
          <TextInput className="journal-field" label="Плановый стоп-лосс" aria-label="Плановый стоп-лосс" inputMode="decimal" maxLength={20000} value={values.planned_stop} onChange={(e) => update("planned_stop", e.target.value)} placeholder="Цена в единицах инструмента" />
          <TextInput className="journal-field" label="Плановый тейк-профит" aria-label="Плановый тейк-профит" inputMode="decimal" maxLength={20000} value={values.planned_take} onChange={(e) => update("planned_take", e.target.value)} placeholder="Цена в единицах инструмента" />
        </div>
        <h3>Выход и разбор</h3>
        <div className={`exit-assessment ${exitTone(position)}`} aria-label="Причина выхода">
          <strong>{exitLabel(position)}</strong>
        </div>
        {textField("exit_note", "Комментарий к выходу", "Почему закрыл позицию, менял ли план")}
      </fieldset>
      <footer className="journal-save"><span role="status">{changed ? "Есть несохранённые изменения" : ""}</span><Button variant="filled" disabled={saving || !changed} type="submit">{saving ? "Сохранение…" : "Сохранить разбор"}</Button></footer>
    </Paper>
  );
}
