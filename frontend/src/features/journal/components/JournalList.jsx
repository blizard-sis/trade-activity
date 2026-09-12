import { AccountPicker } from "../../../shared/components/AccountPicker";
import { useState } from "react";
import { Message } from "../../../shared/components/Message";
import { formatDate, formatMoney, resultClass } from "../../../shared/format";
import { FIELDS, exitLabel } from "../model";

export function JournalList({ positions, selected, onSelect }) {
  const [search, setSearch] = useState("");
  const [account, setAccount] = useState([]);
  const [review, setReview] = useState("");

  const accounts = [...new Map(positions.map((p) => [p.account_id, p.account_name])).entries()];
  const visible = positions.filter((p) => {
    const hasNotes = FIELDS.some((key) => p[key]);
    return (!account.length || account.includes(p.account_id))
      && `${p.ticker} ${p.instrument_name}`.toLowerCase().includes(search.toLowerCase())
      && (!review || (review === "filled" ? hasNotes : !hasNotes));
  });

  return (
    <section className="journal-list" aria-label="Позиции для разбора">
      <div className="journal-filters">
        <input aria-label="Поиск инструмента" type="search" placeholder="Тикер или инструмент" value={search} onChange={(e) => setSearch(e.target.value)} />
        <AccountPicker accounts={accounts.map(([id, name]) => ({ id, name }))} value={account} onChange={setAccount} />
        <select aria-label="Заполнение дневника" value={review} onChange={(e) => setReview(e.target.value)}><option value="">Все позиции</option><option value="empty">Без заметок</option><option value="filled">Есть заметки</option></select>
      </div>
      <div className="journal-items">
        {visible.map((p) => <button type="button" key={p.id} className={`journal-item ${selected === p.id ? "active" : ""}`} onClick={() => onSelect(p.id)} aria-pressed={selected === p.id}>
          <span className="journal-item-heading"><strong>{p.ticker || p.instrument_name}</strong><span className={resultClass(p.net_result)}>{formatMoney(p.net_result, p.result_currency)}</span></span>
          <span>{p.account_name} · <span className={p.direction}>{p.direction === "long" ? "Лонг" : "Шорт"}</span> · {p.status === "closed" ? "Закрыта" : "Открыта"}</span>
          <span className="summary">{formatDate(p.entry_at)}</span>
          <span className="summary">{exitLabel(p)}</span>
        </button>)}
        {!visible.length && <Message>{positions.length ? "Нет позиций для выбранных фильтров" : "Пока нет сделок. Синхронизируйте их в разделе «Торговля», затем добавьте разбор."}</Message>}
      </div>
    </section>
  );
}
