import { useCallback, useEffect, useState } from "react";
import { notifySuccess, useNotificationError } from "../../shared/notifications";
import { api } from "./api";

function updateSnapshots(links, updated) {
  const snapshots = [updated.forecast, updated.execution];
  const replace = (value) =>
    snapshots.find((item) => item.provider === value.provider && item.id === value.id) || value;
  return links.map((row) => ({
    ...row,
    forecast: replace(row.forecast),
    execution: replace(row.execution),
  }));
}

export function useInstrumentLinks() {
  const [links, setLinks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useNotificationError();
  const [attempt, setAttempt] = useState(0);
  const reload = useCallback(() => setAttempt((value) => value + 1), []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    api
      .links(controller.signal)
      .then((items) => {
        if (!controller.signal.aborted) setLinks(items);
      })
      .catch((err) => {
        if (!controller.signal.aborted) setError(err.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [attempt, setError]);

  async function mutate(operation, message) {
    setBusy(true);
    setError("");
    try {
      await operation();
      notifySuccess(message);
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    } finally {
      setBusy(false);
    }
  }

  function save(values, id) {
    return mutate(async () => {
      const item = await api.save(values, id);
      setLinks((items) =>
        updateSnapshots(
          id ? items.map((row) => (row.id === id ? item : row)) : [...items, item],
          item,
        ),
      );
    }, "Связка инструментов сохранена.");
  }

  function remove(id) {
    return mutate(async () => {
      await api.remove(id);
      setLinks((items) => items.filter((row) => row.id !== id));
    }, "Связка удалена.");
  }

  function refresh(id) {
    return mutate(async () => {
      const item = await api.refresh(id);
      // Catalog instruments can be shared by several links.
      setLinks((items) => updateSnapshots(items, item));
    }, "Данные инструментов обновлены через MCP Т-Банка.");
  }

  return { links, loading, busy, error, reload, save, remove, refresh };
}
