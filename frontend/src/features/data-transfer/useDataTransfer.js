import { useEffect, useState } from "react";
import { loadAccounts } from "../../shared/api/accounts";
import { notifySuccess, useNotificationError } from "../../shared/notifications";
import { DEFAULT_POSITION_FILTERS } from "../../shared/positions/filters";
import { api } from "./api";

export function useDataTransfer() {
  const [accounts, setAccounts] = useState([]);
  const [filters, setFilters] = useState(DEFAULT_POSITION_FILTERS);
  const [error, setError] = useNotificationError();
  const [importing, setImporting] = useState(false);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    loadAccounts({ signal: controller.signal })
      .then((items) => {
        if (!controller.signal.aborted) setAccounts(items);
      })
      .catch((error) => {
        if (!controller.signal.aborted) setError(error.message);
      });
    return () => controller.abort();
  }, [setError]);

  function updateFilter(name, value) {
    setFilters((current) => ({ ...current, [name]: value }));
  }

  async function importTradingView(importFiles, paperName) {
    setImporting(true);
    setError("");
    try {
      const body = new FormData();
      importFiles.forEach((file) => body.append("files", file));
      body.append("account_name", paperName);
      const result = await api.importTradingView(body);
      const summary = [
        `Добавлено: ${result.added}. Обновлено: ${result.updated}. Без изменений: ${result.unchanged}.`,
        `В файле: ${result.closed} закрытых и ${result.open} открытых позиций.`,
      ];
      if (result.ignored.length) {
        summary.push(
          "Текущие заявки, снимок позиций и журнал активности не импортируются отдельно.",
        );
      }
      notifySuccess(summary.join(" "));
      setAccounts(await loadAccounts());
      setFilters({ ...DEFAULT_POSITION_FILTERS, account: result.account_id });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setImporting(false);
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

  return {
    accounts,
    filters,
    error,
    importing,
    exporting,
    importTradingView,
    exportPositions,
    updateFilter,
  };
}
