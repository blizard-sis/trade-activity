import { request, queryString, writeJson } from "../../shared/api/client";
import { createRequestQueue } from "../../shared/api/queue";

const enqueueSettings = createRequestQueue();

export const api = {
  tickers: (account, options) => request(`/api/tickers?${queryString({ account })}`, options),
  report: (filters, options) => request(`/api/reports/trading?${queryString(filters)}`, options),
  loadReportFilters: (options) => request("/api/report-filters", options),
  saveReportFilters: (filters) =>
    enqueueSettings(() => writeJson("/api/report-filters", "PUT", filters)),
  clearReportFilters: () =>
    enqueueSettings(() => request("/api/report-filters", { method: "DELETE" })),
};
