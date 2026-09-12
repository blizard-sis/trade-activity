import { AccountPicker } from "../../shared/components/AccountPicker";
import { loadAccounts } from "../../shared/api/accounts";
import "./reports.css";
import { useEffect, useMemo, useRef, useState } from "react";

import { api } from "./api";
import { Layout } from "../../app/Layout";
import { Message } from "../../shared/components/Message";
import { formatMoney, formatMonth, resultClass } from "../../shared/format";


const DEFAULT_FILTERS = {
  account: "",
  ticker_mode: "all",
  ticker: "",
  month_from: "",
  month_to: "",
};


const percent = (value) => value == null ? "—" : `${value.toLocaleString("ru-RU", { maximumFractionDigits: 2 })}%`;

export function MonthlyPage() {
  const [accounts, setAccounts] = useState([]);
  const [tickers, setTickers] = useState([]);
  const [filters, setFilters] = useState(null);
  const [months, setMonths] = useState([]);
  const [error, setError] = useState("");
  const skipSave = useRef(false);

  useEffect(() => {
    Promise.all([loadAccounts(), api.loadMonthlyFilters()])
      .then(([loadedAccounts, saved]) => {
        setAccounts(loadedAccounts);
        setFilters({ ...DEFAULT_FILTERS, ...saved });
      })
      .catch((requestError) => setError(requestError.message));
  }, []);

  useEffect(() => {
    if (!filters) return;
    api.tickers(filters.account)
      .then(setTickers)
      .catch((requestError) => setError(requestError.message));
  }, [filters?.account]);

  useEffect(() => {
    if (!filters) return;
    api.monthly(filters)
      .then((report) => {
        setMonths(report);
        setError("");
      })
      .catch((requestError) => setError(requestError.message));

    if (skipSave.current) {
      skipSave.current = false;
    } else {
      api.saveMonthlyFilters(filters).catch((requestError) => setError(requestError.message));
    }
  }, [filters]);

  const totals = useMemo(() => {
    const positions = months.reduce((sum, row) => sum + row.positions, 0);
    const wins = months.reduce((sum, row) => sum + row.wins, 0);
    const takes = months.reduce((sum, row) => sum + row.takes, 0);
    const stops = months.reduce((sum, row) => sum + row.stops, 0);
    return {
      takes, stops,
      net: months.reduce((sums, row) => ({ ...sums, [row.currency]: (sums[row.currency] || 0) + row.net_result }), {}),
      winRate: positions ? wins / positions * 100 : null,
      cleanWinRate: takes + stops ? takes / (takes + stops) * 100 : null,
    };
  }, [months]);

  function updateFilter(name, value) {
    setFilters((current) => ({ ...current, [name]: value }));
  }

  async function clearFilters() {
    skipSave.current = true;
    setFilters(DEFAULT_FILTERS);
    await api.clearMonthlyFilters();
  }

  if (!filters) {
    return <Layout title="Помесячный отчёт" subtitle="Загрузка…"><Message>Загрузка отчёта…</Message></Layout>;
  }

  return (
    <Layout title="Помесячный отчёт" subtitle={`Месяцев: ${months.length}`}>
      <section className="filters report-filters">
        <AccountPicker accounts={accounts} value={filters.account} onChange={(value) => updateFilter("account", value)} />
        <select value={filters.ticker_mode} onChange={(event) => updateFilter("ticker_mode", event.target.value)}>
          <option value="all">Все тикеры</option><option value="only">Только инструмент</option><option value="exclude">Исключить инструмент</option>
        </select>
        <select disabled={filters.ticker_mode === "all"} value={filters.ticker} onChange={(event) => updateFilter("ticker", event.target.value)}>
          <option value="">Выберите инструмент</option>
          {tickers.map((ticker) => <option key={ticker} value={ticker}>{ticker}</option>)}
        </select>
        <label>С <input type="month" value={filters.month_from} onChange={(event) => updateFilter("month_from", event.target.value)} /></label>
        <label>По <input type="month" value={filters.month_to} onChange={(event) => updateFilter("month_to", event.target.value)} /></label>
        <button onClick={clearFilters}>Очистить фильтры</button>

        <div className="totals">
          <span className="metric">Чистыми {Object.entries(totals.net).map(([currency, value]) => <strong key={currency} className={resultClass(value)}>{formatMoney(value, currency)} </strong>)}</span>
          <span className="metric" title="Прибыльные после комиссии / все закрытые позиции, включая ручные и безубыточные">Итоговый винрейт <strong>{percent(totals.winRate)}</strong></span>
          <span className="metric" title="Тейки / (тейки + стопы). Ручные, смешанные и неопределённые выходы исключены">Чистый винрейт <strong>{percent(totals.cleanWinRate)}</strong> <small>Тейки: {totals.takes} · Стопы: {totals.stops}</small></span>
        </div>
      </section>

      <p className="summary">Итоговый: прибыльные после комиссии / все закрытые. Чистый: тейки / (тейки + стопы). Причины оцениваются по уровням плана из дневника; выходы без достаточных данных не входят в чистый винрейт.</p>
      {error && <Message type="error">{error}</Message>}
      <div className="table-card">
        <table>
          <thead><tr>
            <th>Месяц</th><th>Позиций</th><th>Прибыльных</th><th>Убыточных</th>
            <th>Итоговый винрейт</th><th>Чистый винрейт</th><th>Тейки</th><th>Стопы</th><th>Ручные</th><th>Смешанные</th><th>Не определено</th><th>Результат</th><th>Комиссия</th><th>Чистыми</th>
          </tr></thead>
          <tbody>
            {months.map((row) => (
              <tr key={`${row.month}-${row.currency}`}>
                <td>{formatMonth(row.month)}</td><td>{row.positions}</td><td>{row.wins}</td><td>{row.losses}</td>
                <td>{percent(row.win_rate)}</td><td>{percent(row.clean_win_rate)}</td>
                <td>{row.takes}</td><td>{row.stops}</td><td>{row.manual}</td><td>{row.mixed}</td><td>{row.unknown}</td>
                <td className={resultClass(row.gross_result)}>{formatMoney(row.gross_result, row.currency)}</td>
                <td>{formatMoney(row.commission, row.currency)}</td>
                <td className={resultClass(row.net_result)}>{formatMoney(row.net_result, row.currency)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!error && months.length === 0 && <Message>Нет закрытых позиций для выбранных фильтров</Message>}
      </div>
    </Layout>
  );
}
