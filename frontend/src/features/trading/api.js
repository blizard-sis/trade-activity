import { request, queryString, download } from "../../shared/api/client";

export const api = {
  importTradingView: (body) => request("/api/imports/tradingview", { method: "POST", body }),
  positions: (filters) => request(`/api/positions?${queryString(filters)}`),
  exportPositions: (filters) => download(`/api/positions/export?${queryString(filters)}`),
  loadPositionTableSettings: () => request("/api/position-table-settings"),
  savePositionTableSettings: (settings) => request("/api/position-table-settings", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settings),
  }),
  clearPositionTableSettings: () => request("/api/position-table-settings", { method: "DELETE" }),
  sync: () => request("/api/sync", { method: "POST" }),
};
