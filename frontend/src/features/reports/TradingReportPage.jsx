import { Button, SegmentedControl, TextInput } from "@mantine/core";
import { Layout } from "../../app/Layout";
import { AccountPicker } from "../../shared/components/AccountPicker";
import { FilterSelect } from "../../shared/components/FilterSelect";
import { Message } from "../../shared/components/Message";
import { formatMoney, formatPercent, resultClass } from "../../shared/format";
import { TradingReportTable } from "./components/TradingReportTable";
import { useTradingReport } from "./useTradingReport";
import "./reports.css";

export function TradingReportPage() {
  const { accounts, tickers, filters, rows, loading, error, totals, updateFilter, clearFilters } =
    useTradingReport();

  if (!filters) {
    return (
      <Layout title="Отчёт торговли" subtitle="Загрузка…">
        <Message>
          {error
            ? "Не удалось загрузить отчёт. Обновите страницу, чтобы повторить."
            : "Загрузка отчёта…"}
        </Message>
      </Layout>
    );
  }

  return (
    <Layout
      title="Отчёт торговли"
      subtitle={`${filters.group_by === "day" ? "Дней" : "Месяцев"}: ${new Set(rows.map((row) => row.period)).size}`}
    >
      <SegmentedControl
        mb="md"
        aria-label="Группировка отчёта"
        value={filters.group_by}
        onChange={(value) => updateFilter("group_by", value)}
        data={[
          { value: "month", label: "По месяцам" },
          { value: "day", label: "По дням" },
        ]}
      />
      <section className="filters report-filters">
        <AccountPicker
          accounts={accounts}
          value={filters.account}
          onChange={(value) => updateFilter("account", value)}
        />
        <FilterSelect
          value={filters.ticker_mode}
          onChange={(value) => updateFilter("ticker_mode", value || "all")}
          clearable={false}
          allowDeselect={false}
          aria-label="Фильтрация инструментов"
          placeholder="Все тикеры"
          data={[
            { value: "all", label: "Все тикеры" },
            { value: "only", label: "Только инструмент" },
            { value: "exclude", label: "Исключить инструмент" },
          ]}
        />
        <FilterSelect
          disabled={filters.ticker_mode === "all"}
          value={filters.ticker}
          onChange={(value) => updateFilter("ticker", value)}
          aria-label="Инструмент"
          searchable
          placeholder="Выберите инструмент"
          data={tickers.map((ticker) => ({ value: ticker, label: ticker }))}
        />
        <TextInput
          aria-label={filters.group_by === "day" ? "Дата от" : "Месяц от"}
          type={filters.group_by === "day" ? "date" : "month"}
          value={filters.period_from}
          onChange={(event) => updateFilter("period_from", event.target.value)}
        />
        <TextInput
          aria-label={filters.group_by === "day" ? "Дата до" : "Месяц до"}
          type={filters.group_by === "day" ? "date" : "month"}
          value={filters.period_to}
          onChange={(event) => updateFilter("period_to", event.target.value)}
        />
        <Button onClick={clearFilters}>Очистить фильтры</Button>

        <div className="totals">
          <span className="metric">
            Чистыми{" "}
            {Object.entries(totals.net).map(([currency, value]) => (
              <strong key={currency} className={resultClass(value)}>
                {formatMoney(value, currency)}{" "}
              </strong>
            ))}
          </span>
          <span
            className="metric"
            title="Прибыльные после комиссии / все закрытые позиции, включая ручные и безубыточные"
          >
            Итоговый винрейт <strong>{formatPercent(totals.winRate)}</strong>
          </span>
          <span
            className="metric"
            title="Тейки / (тейки + стопы). Ручные, смешанные и неопределённые выходы исключены"
          >
            Чистый винрейт <strong>{formatPercent(totals.cleanWinRate)}</strong>{" "}
            <small>
              Тейки: {totals.takes} · Стопы: {totals.stops}
            </small>
          </span>
        </div>
      </section>

      <p className="summary">
        Итоговый: прибыльные после комиссии / все закрытые. Чистый: тейки / (тейки + стопы). Периоды
        определяются по дате выхода. Причины оцениваются по уровням плана из дневника; выходы без
        достаточных данных не входят в чистый винрейт.
      </p>
      <TradingReportTable groupBy={filters.group_by} rows={rows} error={error} loading={loading} />
    </Layout>
  );
}
