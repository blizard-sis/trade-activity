import { request, writeJson } from "../../shared/api/client";

export const api = {
  links: (signal) => request("/api/instruments/links", { signal }),
  search: (query, signal) =>
    request(`/api/instruments/search?q=${encodeURIComponent(query)}`, { signal }),
  select: (item, signal) =>
    writeJson("/api/instruments/select", "POST", { id: item.id, kind: item.kind }, { signal }),
  save: (values, id) =>
    writeJson(
      id ? `/api/instruments/links/${id}` : "/api/instruments/links",
      id ? "PUT" : "POST",
      values,
    ),
  remove: (id) => request(`/api/instruments/links/${id}`, { method: "DELETE" }),
  refresh: (id) => request(`/api/instruments/links/${id}/refresh`, { method: "POST" }),
};
