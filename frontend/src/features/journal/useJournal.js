import { useEffect, useState } from "react";
import { useNotificationError } from "../../shared/notifications";
import { api } from "./api";

export function useJournal() {
  const [positions, setPositions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useNotificationError();
  const [selected, setSelected] = useState(() => new URLSearchParams(window.location.search).get("position") || "");
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api.journal({}).then((items) => { if (!cancelled) setPositions(items); })
      .catch((err) => { if (!cancelled) setError(err.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [setError]);

  useEffect(() => {
    if (!dirty) return;
    const guard = (event) => { event.preventDefault(); event.returnValue = ""; };
    window.addEventListener("beforeunload", guard);
    return () => window.removeEventListener("beforeunload", guard);
  }, [dirty]);

  function selectPosition(id) {
    if (saving || id === selected) return;
    if (dirty && !window.confirm("Есть несохранённые изменения. Перейти к другой позиции и отменить их?")) return;
    setDirty(false);
    setSelected(id);
    window.history.replaceState(null, "", `/journal?position=${encodeURIComponent(id)}`);
  }

  const position = positions.find((p) => p.id === selected);

  return { positions, setPositions, loading, error, selected, position,
    selectPosition, setDirty, setSaving };
}
