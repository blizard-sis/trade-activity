export function summarizeReport(rows) {
  let positions = 0;
  let wins = 0;
  let takes = 0;
  let stops = 0;
  const net = {};
  for (const row of rows) {
    positions += row.positions;
    wins += row.wins;
    takes += row.takes;
    stops += row.stops;
    net[row.currency] = (net[row.currency] || 0) + row.net_result;
  }
  return {
    takes,
    stops,
    net,
    winRate: positions ? (wins / positions) * 100 : null,
    cleanWinRate: takes + stops ? (takes / (takes + stops)) * 100 : null,
  };
}

export const DEFAULT_FILTERS = {
  account: "",
  ticker_mode: "all",
  ticker: "",
  group_by: "month",
  period_from: "",
  period_to: "",
};

export function normalizeFilters(saved) {
  return {
    ...DEFAULT_FILTERS,
    account: saved.account ?? "",
    ticker_mode: saved.ticker_mode ?? "all",
    ticker: saved.ticker ?? "",
    group_by: saved.group_by === "day" ? "day" : "month",
    period_from: saved.period_from ?? saved.month_from ?? "",
    period_to: saved.period_to ?? saved.month_to ?? "",
  };
}

export function changeGrouping(filters, groupBy) {
  if (filters.group_by === groupBy) return filters;
  const convert = (value, end) => {
    if (!value) return "";
    if (groupBy === "month") return value.slice(0, 7);
    const [year, month] = value.split("-").map(Number);
    const day = end ? new Date(year, month, 0).getDate() : 1;
    return `${value}-${String(day).padStart(2, "0")}`;
  };
  return {
    ...filters,
    group_by: groupBy,
    period_from: convert(filters.period_from, false),
    period_to: convert(filters.period_to, true),
  };
}
