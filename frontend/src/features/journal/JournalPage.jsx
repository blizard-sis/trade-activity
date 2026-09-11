import { useEffect, useState } from "react";
import { api } from "./api";
import { Layout } from "../../app/Layout";
import { Message } from "../../shared/components/Message";
import { JournalList } from "./components/JournalList";
import { JournalEditor } from "./components/JournalEditor";
import "./journal.css";

export function JournalPage() {
  const [positions, setPositions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState(() => new URLSearchParams(window.location.search).get("position") || "");
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api.journal({}).then((items) => { if (!cancelled) setPositions(items); })
      .catch((err) => { if (!cancelled) setError(err.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

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

  return (
    <Layout title="Дневник трейдера" subtitle="План сделки и комментарии к выходу">
      {error && <Message type="error">{error}</Message>}
      {loading ? <Message>Загрузка дневника…</Message> : (
        <div className="journal-workspace">
          <JournalList positions={positions} selected={selected} onSelect={selectPosition} />
          {position ? <JournalEditor key={position.id} position={position} onDirty={setDirty} onSaving={setSaving} onSaved={(values) => setPositions((items) => items.map((p) => p.id === position.id ? { ...p, ...values } : p))} />
            : <div className="journal-placeholder"><h2>{selected ? "Позиция не найдена" : "Выберите позицию для разбора"}</h2><p>Запишите план сделки и прокомментируйте выход.</p><a href="/">Перейти в торговлю →</a></div>}
        </div>
      )}
    </Layout>
  );
}
