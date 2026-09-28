import { request, queryString, writeJson } from "../../shared/api/client";
import { createRequestQueue } from "../../shared/api/queue";

const enqueueSettings = createRequestQueue();

export const api = {
  tickers: (account, options) => request(`/api/tickers?${queryString({ account })}`, options),
  monthly: (filters, options) => request(`/api/monthly?${queryString(filters)}`, options),
  loadMonthlyFilters: (options) => request("/api/monthly-filters", options),
  saveMonthlyFilters: (filters) =>
    enqueueSettings(() => writeJson("/api/monthly-filters", "PUT", filters)),
  clearMonthlyFilters: () =>
    enqueueSettings(() => request("/api/monthly-filters", { method: "DELETE" })),
};
