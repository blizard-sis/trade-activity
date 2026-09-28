import { useEffect, useState } from "react";
import { useNotificationError } from "../../shared/notifications";
import { api } from "./api";

export function useJournal() {
  const [positions, setPositions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useNotificationError();
  const [selected, setSelected] = useState(
    () => new URLSearchParams(window.location.search).get("position") || "",
  );
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    api
      .journal({}, { signal: controller.signal })
      .then((items) => {
        if (!controller.signal.aborted) setPositions(items);
      })
      .catch((err) => {
        if (!controller.signal.aborted) setError(err.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [setError]);

  useEffect(() => {
    if (!dirty) return;
    const guard = (event) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", guard);
    return () => window.removeEventListener("beforeunload", guard);
  }, [dirty]);

  function selectPosition(id) {
    if (saving || id === selected) return;
    if (
      dirty &&
      !window.confirm("Есть несохранённые изменения. Перейти к другой позиции и отменить их?")
    )
      return;
    setDirty(false);
    setSelected(id);
    window.history.replaceState(null, "", `/journal?position=${encodeURIComponent(id)}`);
  }

  function updatePosition(values) {
    setPositions((items) =>
      items.map((item) => (item.id === selected ? { ...item, ...values } : item)),
    );
  }

  const position = positions.find((item) => item.id === selected);

  return {
    positions,
    updatePosition,
    loading,
    error,
    selected,
    position,
    selectPosition,
    setDirty,
    setSaving,
  };
}
