import { Layout } from "../../app/Layout";
import { Message } from "../../shared/components/Message";
import { JournalEditor } from "./components/JournalEditor";
import { JournalList } from "./components/JournalList";
import { useJournal } from "./useJournal";
import "./journal.css";

export function JournalPage() {
  const {
    positions,
    updatePosition,
    loading,
    error,
    selected,
    position,
    selectPosition,
    setDirty,
    setSaving,
  } = useJournal();

  return (
    <Layout title="Дневник трейдера" subtitle="План сделки и комментарии к выходу">
      {error ? (
        <Message>Не удалось загрузить дневник. Обновите страницу, чтобы повторить.</Message>
      ) : loading ? (
        <Message>Загрузка дневника…</Message>
      ) : (
        <div className="journal-workspace">
          <JournalList positions={positions} selected={selected} onSelect={selectPosition} />
          {position ? (
            <JournalEditor
              key={position.id}
              position={position}
              onDirty={setDirty}
              onSaving={setSaving}
              onSaved={updatePosition}
            />
          ) : (
            <div className="journal-placeholder">
              <h2>{selected ? "Позиция не найдена" : "Выберите позицию для разбора"}</h2>
              <p>Запишите план сделки и прокомментируйте выход.</p>
              <a href="/">Перейти в торговлю →</a>
            </div>
          )}
        </div>
      )}
    </Layout>
  );
}
