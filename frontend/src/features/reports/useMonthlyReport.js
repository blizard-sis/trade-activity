import { summarizeMonths } from "./model";
import { useEffect, useMemo, useRef, useState } from "react";
import { useNotificationError } from "../../shared/notifications";
import { loadAccounts } from "../../shared/api/accounts";
import { api } from "./api";

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
    let active = true;
    Promise.all([loadAccounts(), api.loadMonthlyFilters()])
      .then(([loadedAccounts, saved]) => {
        if (!active) return;
        setAccounts(loadedAccounts);
        setFilters({ ...DEFAULT_FILTERS, ...saved });
      })
      .catch((requestError) => { if (active) setError(requestError.message); });
    return () => { active = false; };
  }, [setError]);

  useEffect(() => {
    if (!filters) return;
    let active = true;
    api.tickers(filters.account)
      .then((items) => { if (active) setTickers(items); })
      .catch((error) => { if (active) setError(error.message); });
    return () => { active = false; };
  }, [filters?.account, setError]);

  useEffect(() => {
    if (!filters) return;
    let active = true;
    api.monthly(filters)
      .then((report) => {
        if (!active) return;
        setMonths(report);
        setError("");
      })
      .catch((requestError) => { if (active) setError(requestError.message); });

    if (pendingSave.current) {
      pendingSave.current = false;
      api.saveMonthlyFilters(filters).catch((requestError) => setError(requestError.message));
    }
    return () => { active = false; };
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
