import { useEffect, useState } from "react";
import { notifySuccess, useNotificationError } from "../../shared/notifications";
import { loadAccounts } from "../../shared/api/accounts";
import { api } from "./api";
import { usePositionColumns } from "./usePositionColumns";

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

export function usePositions() {
  const [accounts, setAccounts] = useState([]);
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [positions, setPositions] = useState([]);
  const [error, setError] = useNotificationError();
  const { visibleColumns, toggleColumn, showAllColumns } = usePositionColumns(setError);
  const [syncing, setSyncing] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [showImport, setShowImport] = useState(false);
  const [importing, setImporting] = useState(false);

  async function importTradingView(importFiles, paperName) {
    setImporting(true);
    setError("");
    try {
      const body = new FormData();
      importFiles.forEach((file) => body.append("files", file));
      body.append("account_name", paperName);
      const result = await api.importTradingView(body);
      notifySuccess(`Добавлено: ${result.added}. Обновлено: ${result.updated}. Без изменений: ${result.unchanged}. В файле: ${result.closed} закрытых и ${result.open} открытых позиций.${result.ignored.length ? " Текущие заявки, снимок позиций и журнал активности не импортируются отдельно." : ""}`);
      setAccounts(await loadAccounts());
      setFilters({ ...DEFAULT_FILTERS, account: result.account_id });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setImporting(false);
    }
  }

  const [revision, setRevision] = useState(0);
  const reloadPositions = () => setRevision((value) => value + 1);

  useEffect(() => {
    let active = true;
    loadAccounts().then((items) => { if (active) setAccounts(items); })
      .catch((error) => { if (active) setError(error.message); });
    return () => { active = false; };
  }, [setError]);

  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      try {
        const items = await api.positions(filters, { signal: controller.signal });
        if (!controller.signal.aborted) {
          setPositions(items);
          setError("");
        }
      } catch (requestError) {
        if (!controller.signal.aborted) setError(requestError.message);
      }
    }, 120);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [filters, revision, setError]);

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
      const result = await api.sync();
      notifySuccess(`Синхронизация T-Bank завершена. Счетов: ${result.accounts}. Сделок добавлено: ${result.added}. Обновлено: ${result.updated}. Без изменений: ${result.unchanged}.`);
      setAccounts(await loadAccounts());
      reloadPositions();
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
      notifySuccess("JSON-файл подготовлен и передан браузеру для скачивания.", "Экспорт завершён");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setExporting(false);
    }
  }

  return { accounts, filters, positions, visibleColumns, error, syncing, exporting,
    showImport, setShowImport, importing, importTradingView, updateFilter, sortBy,
    synchronize, exportPositions, toggleColumn, showAllColumns };
}
