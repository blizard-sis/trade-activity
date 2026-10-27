import { request, queryString, writeJson } from "../../shared/api/client";
import { createRequestQueue } from "../../shared/api/queue";

const enqueueSettings = createRequestQueue();

export const api = {
  positions: (filters, options) => request(`/api/positions?${queryString(filters)}`, options),
  loadPositionTableSettings: (options) => request("/api/position-table-settings", options),
  savePositionTableSettings: (settings) =>
    enqueueSettings(() => writeJson("/api/position-table-settings", "PUT", settings)),
  clearPositionTableSettings: () =>
    enqueueSettings(() => request("/api/position-table-settings", { method: "DELETE" })),
};
