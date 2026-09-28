import { request, queryString, download } from "../../shared/api/client";

export const api = {
  importTradingView: (body) => request("/api/imports/tradingview", { method: "POST", body }),
  exportPositions: (filters) => download(`/api/positions/export?${queryString(filters)}`),
};
