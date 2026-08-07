async function request(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.error || `Ошибка запроса: ${response.status}`);
  }
  return response.status === 204 ? null : response.json();
}


function queryString(filters) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== "" && value !== null && value !== undefined) params.set(key, value);
  });
  return params.toString();
}


export const api = {
  accounts: () => request("/api/accounts"),
  tickers: (account = "") => request(`/api/tickers?${queryString({ account })}`),
  positions: (filters) => request(`/api/positions?${queryString(filters)}`),
  savePositionNotes: (positionId, notes) => request(
    `/api/positions/${encodeURIComponent(positionId)}/notes`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(notes),
    },
  ),
  loadPositionTableSettings: () => request("/api/position-table-settings"),
  savePositionTableSettings: (settings) => request("/api/position-table-settings", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settings),
  }),
  clearPositionTableSettings: () => request("/api/position-table-settings", { method: "DELETE" }),
  monthly: (filters) => request(`/api/monthly?${queryString(filters)}`),
  sync: () => request("/api/sync", { method: "POST" }),
  loadMonthlyFilters: () => request("/api/monthly-filters"),
  saveMonthlyFilters: (filters) => request("/api/monthly-filters", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(filters),
  }),
  clearMonthlyFilters: () => request("/api/monthly-filters", { method: "DELETE" }),
};
