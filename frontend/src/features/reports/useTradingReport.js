import { useEffect, useMemo, useRef, useState } from "react";
import { loadAccounts } from "../../shared/api/accounts";
import { useNotificationError } from "../../shared/notifications";
import { api } from "./api";
import { DEFAULT_FILTERS, normalizeFilters, changeGrouping, summarizeReport } from "./model";

export function useTradingReport() {
  const [accounts, setAccounts] = useState([]);
  const [tickers, setTickers] = useState([]);
  const [filters, setFilters] = useState(null);
  const [loading, setLoading] = useState(true);
  const [rows, setRows] = useState([]);
  const [error, setError] = useNotificationError();
  const pendingSave = useRef(false);

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      loadAccounts({ signal: controller.signal }),
      api.loadReportFilters({ signal: controller.signal }),
    ])
      .then(([loadedAccounts, saved]) => {
        if (controller.signal.aborted) return;
        setAccounts(loadedAccounts);
        setFilters(normalizeFilters(saved));
      })
      .catch((requestError) => {
        if (!controller.signal.aborted) setError(requestError.message);
      });
    return () => controller.abort();
  }, [setError]);

  useEffect(() => {
    if (!filters) return;
    const controller = new AbortController();
    api
      .tickers(filters.account, { signal: controller.signal })
      .then((items) => {
        if (!controller.signal.aborted) setTickers(items);
      })
      .catch((error) => {
        if (!controller.signal.aborted) setError(error.message);
      });
    return () => controller.abort();
  }, [filters?.account, setError]);

  useEffect(() => {
    if (!filters) return;
    setRows([]);
    setLoading(true);
    const controller = new AbortController();
    api
      .report(filters, { signal: controller.signal })
      .then((report) => {
        if (controller.signal.aborted) return;
        setRows(report);
        setError("");
      })
      .catch((requestError) => {
        if (!controller.signal.aborted) setError(requestError.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    if (pendingSave.current) {
      pendingSave.current = false;
      api.saveReportFilters(filters).catch((requestError) => setError(requestError.message));
    }
    return () => controller.abort();
  }, [filters, setError]);

  const totals = useMemo(() => summarizeReport(rows), [rows]);

  function updateFilter(name, value) {
    pendingSave.current = true;
    setFilters((current) =>
      name === "group_by" ? changeGrouping(current, value) : { ...current, [name]: value },
    );
  }

  async function clearFilters() {
    pendingSave.current = false;
    setFilters(DEFAULT_FILTERS);
    try {
      await api.clearReportFilters();
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  return { accounts, tickers, filters, rows, loading, error, totals, updateFilter, clearFilters };
}
