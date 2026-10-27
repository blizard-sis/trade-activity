import { useEffect, useState } from "react";
import { loadAccounts } from "../../shared/api/accounts";
import { useNotificationError } from "../../shared/notifications";
import { DEFAULT_POSITION_FILTERS } from "../../shared/positions/filters";
import { api } from "./api";
import { usePositionColumns } from "./usePositionColumns";

export function usePositions() {
  const [accounts, setAccounts] = useState([]);
  const [filters, setFilters] = useState(DEFAULT_POSITION_FILTERS);
  const [positions, setPositions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useNotificationError();
  const { visibleColumns, toggleColumn, showAllColumns } = usePositionColumns(setError);
  const [revision, setRevision] = useState(0);
  const reloadPositions = () => setRevision((value) => value + 1);

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

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    const timer = setTimeout(async () => {
      try {
        const items = await api.positions(filters, { signal: controller.signal });
        if (!controller.signal.aborted) {
          setPositions(items);
          setError("");
        }
      } catch (requestError) {
        if (!controller.signal.aborted) setError(requestError.message);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }, 120);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
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

  return {
    accounts,
    filters,
    positions,
    loading,
    visibleColumns,
    error,
    updateFilter,
    sortBy,
    toggleColumn,
    showAllColumns,
  };
}
