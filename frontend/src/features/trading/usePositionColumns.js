import { useEffect, useRef, useState } from "react";
import { api } from "./api";
import { DEFAULT_COLUMNS } from "./columns";

export function usePositionColumns(setError) {
  const [visibleColumns, setVisibleColumns] = useState(DEFAULT_COLUMNS);
  const changed = useRef(false);

  useEffect(() => {
    let active = true;
    api.loadPositionTableSettings().then((settings) => {
      if (!active || changed.current) return;
      const available = settings.visible_columns?.filter((key) => DEFAULT_COLUMNS.includes(key));
      if (available?.length) setVisibleColumns(available);
    }).catch((error) => { if (active) setError(error.message); });
    return () => { active = false; };
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
