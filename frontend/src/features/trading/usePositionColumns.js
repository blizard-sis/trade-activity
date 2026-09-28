import { useEffect, useRef, useState } from "react";
import { api } from "./api";
import { DEFAULT_COLUMNS } from "./columns";

export function usePositionColumns(setError) {
  const [visibleColumns, setVisibleColumns] = useState(DEFAULT_COLUMNS);
  const changed = useRef(false);

  useEffect(() => {
    const controller = new AbortController();
    api
      .loadPositionTableSettings({ signal: controller.signal })
      .then((settings) => {
        if (controller.signal.aborted || changed.current) return;
        const available = settings.visible_columns?.filter((key) => DEFAULT_COLUMNS.includes(key));
        if (available?.length) setVisibleColumns(available);
      })
      .catch((error) => {
        if (!controller.signal.aborted) setError(error.message);
      });
    return () => controller.abort();
  }, [setError]);

  async function toggleColumn(column) {
    const next = visibleColumns.includes(column)
      ? visibleColumns.filter((item) => item !== column)
      : [...visibleColumns, column];
    if (next.length === 0) return;

    changed.current = true;
    setVisibleColumns(next);
    try {
      await api.savePositionTableSettings({ visible_columns: next });
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function showAllColumns() {
    changed.current = true;
    setVisibleColumns(DEFAULT_COLUMNS);
    try {
      await api.clearPositionTableSettings();
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  return { visibleColumns, toggleColumn, showAllColumns };
}
