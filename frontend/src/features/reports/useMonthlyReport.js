import { useEffect, useMemo, useRef, useState } from "react";
import { loadAccounts } from "../../shared/api/accounts";
import { useNotificationError } from "../../shared/notifications";
import { api } from "./api";
import { summarizeMonths } from "./model";

const DEFAULT_FILTERS = {
  account: "",
  ticker_mode: "all",
  ticker: "",
  month_from: "",
  month_to: "",
};

export function useMonthlyReport() {
  const [accounts, setAccounts] = useState([]);
  const [tickers, setTickers] = useState([]);
  const [filters, setFilters] = useState(null);
  const [months, setMonths] = useState([]);
  const [error, setError] = useNotificationError();
  const pendingSave = useRef(false);

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      loadAccounts({ signal: controller.signal }),
      api.loadMonthlyFilters({ signal: controller.signal }),
    ])
      .then(([loadedAccounts, saved]) => {
        if (controller.signal.aborted) return;
        setAccounts(loadedAccounts);
        setFilters({ ...DEFAULT_FILTERS, ...saved });
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
    const controller = new AbortController();
    api
      .monthly(filters, { signal: controller.signal })
      .then((report) => {
        if (controller.signal.aborted) return;
        setMonths(report);
        setError("");
      })
      .catch((requestError) => {
        if (!controller.signal.aborted) setError(requestError.message);
      });

    if (pendingSave.current) {
      pendingSave.current = false;
      api.saveMonthlyFilters(filters).catch((requestError) => setError(requestError.message));
    }
    return () => controller.abort();
  }, [filters, setError]);

  const totals = useMemo(() => summarizeMonths(months), [months]);

  function updateFilter(name, value) {
    pendingSave.current = true;
    setFilters((current) => ({ ...current, [name]: value }));
  }

  async function clearFilters() {
    pendingSave.current = false;
    setFilters(DEFAULT_FILTERS);
    try {
      await api.clearMonthlyFilters();
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  return { accounts, tickers, filters, months, error, totals, updateFilter, clearFilters };
}
