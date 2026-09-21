import { createRequestQueue } from "../../shared/api/queue";
import { request, queryString, download } from "../../shared/api/client";

const enqueueSettings = createRequestQueue();

export const api = {
  importTradingView: (body) => request("/api/imports/tradingview", { method: "POST", body }),
  positions: (filters, options) => request(`/api/positions?${queryString(filters)}`, options),
  exportPositions: (filters) => download(`/api/positions/export?${queryString(filters)}`),
  loadPositionTableSettings: () => request("/api/position-table-settings"),
  savePositionTableSettings: (settings) => enqueueSettings(() => request("/api/position-table-settings", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settings),
  })),
  clearPositionTableSettings: () => enqueueSettings(() => request("/api/position-table-settings", { method: "DELETE" })),
  sync: () => request("/api/sync", { method: "POST" }),
};
