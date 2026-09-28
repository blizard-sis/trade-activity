import { request, queryString, writeJson } from "../../shared/api/client";

export const api = {
  journal: (filters, options) => request(`/api/journal?${queryString(filters)}`, options),
  saveJournal: (positionId, values) =>
    writeJson(`/api/journal/${encodeURIComponent(positionId)}`, "PUT", values),
};
