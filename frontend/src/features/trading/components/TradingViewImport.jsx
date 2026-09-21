import { useState } from "react";
import { Button, TextInput, FileInput } from "@mantine/core";

export function TradingViewImport({ importing, onImport }) {
  const [importFiles, setImportFiles] = useState([]);
  const [paperName, setPaperName] = useState("Paper Trading");
  function importTradingView(event) {
    event.preventDefault();
    onImport(importFiles, paperName);
  }
  return (
    <form className="tradingview-import" onSubmit={importTradingView}>
        <strong>TradingView Paper Trading</strong>
        <p>Выберите CSV «История сделок» (trade-history). Можно выбрать сразу все 6 файлов: история заявок уточнит время, история баланса — результат и валюту цены.</p>
        <p>Для повторной загрузки используйте то же название счёта. Для другого демо-счёта или после сброса баланса укажите новое. Время сохраняется как в выгрузке.</p>
        <TextInput label="Название демо-счёта" required maxLength={100} value={paperName} disabled={importing} onChange={(event) => setPaperName(event.target.value)} />
        <FileInput label="CSV-файлы" accept=".csv,text/csv" multiple required disabled={importing} value={importFiles} onChange={setImportFiles} placeholder="Выберите CSV-файлы" aria-label="CSV-файлы TradingView" />
        <Button type="submit" variant="filled" loading={importing} disabled={!importFiles.length}>{importing ? "Загрузка…" : "Импортировать"}</Button>
      </form>
  );
}
