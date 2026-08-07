import { useEffect, useMemo, useRef, useState } from "react";

import { api } from "../api";
import { Layout } from "../components/Layout";
import { Message } from "../components/Message";
import { formatMoney, formatMonth, resultClass } from "../format";


const DEFAULT_FILTERS = {
  account: "",
  ticker_mode: "all",
  ticker: "",
  month_from: "",
  month_to: "",
};


export function MonthlyPage() {
  const [accounts, setAccounts] = useState([]);
  const [tickers, setTickers] = useState([]);
  const [filters, setFilters] = useState(null);
  const [months, setMonths] = useState([]);
  const [error, setError] = useState("");
  const skipSave = useRef(false);

  useEffect(() => {
    Promise.all([api.accounts(), api.loadMonthlyFilters()])
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
    return {
      net: months.reduce((sum, row) => sum + row.net_result, 0),
      winRate: positions ? wins / positions * 100 : 0,
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
        <select value={filters.account} onChange={(event) => updateFilter("account", event.target.value)}>
          <option value="">Все счета</option>
          {accounts.map((account) => <option key={account.id} value={account.id}>{account.name}</option>)}
        </select>
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
          <span className="metric">Чистыми <strong className={resultClass(totals.net)}>{formatMoney(totals.net)}</strong></span>
          <span className="metric">Винрейт <strong>{totals.winRate.toLocaleString("ru-RU", { maximumFractionDigits: 2 })}%</strong></span>
        </div>
      </section>

      {error && <Message type="error">{error}</Message>}
      <div className="table-card">
        <table>
          <thead><tr>
            <th>Месяц</th><th>Позиций</th><th>Прибыльных</th><th>Убыточных</th>
            <th>Винрейт</th><th>Результат</th><th>Комиссия</th><th>Чистыми</th>
          </tr></thead>
          <tbody>
            {months.map((row) => (
              <tr key={row.month}>
                <td>{formatMonth(row.month)}</td><td>{row.positions}</td><td>{row.wins}</td><td>{row.losses}</td>
                <td>{row.win_rate.toLocaleString("ru-RU", { maximumFractionDigits: 2 })}%</td>
                <td className={resultClass(row.gross_result)}>{formatMoney(row.gross_result)}</td>
                <td>{formatMoney(row.commission)}</td>
                <td className={resultClass(row.net_result)}>{formatMoney(row.net_result)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!error && months.length === 0 && <Message>Нет закрытых позиций для выбранных фильтров</Message>}
      </div>
    </Layout>
  );
}

