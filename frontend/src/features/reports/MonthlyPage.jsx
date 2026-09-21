import { useMonthlyReport } from "./useMonthlyReport";
import { MonthlyTable } from "./components/MonthlyTable";
import { Button, TextInput } from "@mantine/core";
import { FilterSelect } from "../../shared/components/FilterSelect";
import { AccountPicker } from "../../shared/components/AccountPicker";
import "./reports.css";

import { Layout } from "../../app/Layout";
import { Message } from "../../shared/components/Message";
import { formatMoney, formatPercent as percent, resultClass } from "../../shared/format";

export function MonthlyPage() {
  const { accounts, tickers, filters, months, error, totals, updateFilter, clearFilters } = useMonthlyReport();

  if (!filters) {
    return <Layout title="Помесячный отчёт" subtitle="Загрузка…"><Message>{error ? "Не удалось загрузить отчёт. Обновите страницу, чтобы повторить." : "Загрузка отчёта…"}</Message></Layout>;
  }

  return (
    <Layout title="Помесячный отчёт" subtitle={`Месяцев: ${months.length}`}>
      <section className="filters report-filters">
        <AccountPicker accounts={accounts} value={filters.account} onChange={(value) => updateFilter("account", value)} />
        <FilterSelect value={filters.ticker_mode} onChange={(value) => updateFilter("ticker_mode", value || "all")} clearable={false} allowDeselect={false} aria-label="Фильтрация инструментов" placeholder="Все тикеры" data={[{"value": "all", "label": "Все тикеры"}, {"value": "only", "label": "Только инструмент"}, {"value": "exclude", "label": "Исключить инструмент"}]} />
        <FilterSelect disabled={filters.ticker_mode === "all"} value={filters.ticker} onChange={(value) => updateFilter("ticker", value)} aria-label="Инструмент" searchable placeholder="Выберите инструмент" data={tickers.map((ticker) => ({ value: ticker, label: ticker }))} />
        <TextInput aria-label="Месяц от" type="month" value={filters.month_from} onChange={(event) => updateFilter("month_from", event.target.value)} />
        <TextInput aria-label="Месяц до" type="month" value={filters.month_to} onChange={(event) => updateFilter("month_to", event.target.value)} />
        <Button onClick={clearFilters}>Очистить фильтры</Button>

        <div className="totals">
          <span className="metric">Чистыми {Object.entries(totals.net).map(([currency, value]) => <strong key={currency} className={resultClass(value)}>{formatMoney(value, currency)} </strong>)}</span>
          <span className="metric" title="Прибыльные после комиссии / все закрытые позиции, включая ручные и безубыточные">Итоговый винрейт <strong>{percent(totals.winRate)}</strong></span>
          <span className="metric" title="Тейки / (тейки + стопы). Ручные, смешанные и неопределённые выходы исключены">Чистый винрейт <strong>{percent(totals.cleanWinRate)}</strong> <small>Тейки: {totals.takes} · Стопы: {totals.stops}</small></span>
        </div>
      </section>

      <p className="summary">Итоговый: прибыльные после комиссии / все закрытые. Чистый: тейки / (тейки + стопы). Причины оцениваются по уровням плана из дневника; выходы без достаточных данных не входят в чистый винрейт.</p>
      <MonthlyTable months={months} error={error} />
    </Layout>
  );
}
