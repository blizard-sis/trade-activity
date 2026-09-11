import { request, queryString } from "../../shared/api/client";

export const api = {
  tickers: (account = "") => request(`/api/tickers?${queryString({ account })}`),
  monthly: (filters) => request(`/api/monthly?${queryString(filters)}`),
  loadMonthlyFilters: () => request("/api/monthly-filters"),
  saveMonthlyFilters: (filters) => request("/api/monthly-filters", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(filters),
  }),
  clearMonthlyFilters: () => request("/api/monthly-filters", { method: "DELETE" }),
};
