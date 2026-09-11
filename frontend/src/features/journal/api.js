import { request, queryString } from "../../shared/api/client";

export const api = {
  journal: (filters) => request(`/api/journal?${queryString(filters)}`),
  saveJournal: (positionId, values) => request(`/api/journal/${encodeURIComponent(positionId)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(values),
  }),
};
