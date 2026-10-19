import { queryString, request, writeJson } from "../../shared/api/client";

export const api = {
  plans: (filters, options) => request(`/api/plans?${queryString(filters)}`, options),
  plan: (id, options) => request(`/api/plans/${encodeURIComponent(id)}`, options),
  availablePositions: (filters, options) =>
    request(`/api/plans/available-positions?${queryString(filters)}`, options),
  create: (body) => writeJson("/api/plans", "POST", body),
  update: (id, body) => writeJson(`/api/plans/${encodeURIComponent(id)}`, "PUT", body),
  link: (id, positionId) =>
    writeJson(`/api/plans/${encodeURIComponent(id)}/positions`, "POST", {
      position_id: positionId,
    }),
  unlink: (id, positionId) =>
    request(`/api/plans/${encodeURIComponent(id)}/positions/${encodeURIComponent(positionId)}`, {
      method: "DELETE",
    }),
  upload: (id, formData) =>
    request(`/api/plans/${encodeURIComponent(id)}/attachments`, {
      method: "POST",
      body: formData,
    }),
  removeAttachment: (id) =>
    request(`/api/attachments/${encodeURIComponent(id)}`, { method: "DELETE" }),
  sync: () => request("/api/sync", { method: "POST" }),
};
