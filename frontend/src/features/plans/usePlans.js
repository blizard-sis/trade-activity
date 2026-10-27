import { useCallback, useEffect, useRef, useState } from "react";
import { loadAccounts } from "../../shared/api/accounts";
import { notifySuccess, useNotificationError } from "../../shared/notifications";
import { api } from "./api";

const EMPTY_FILTERS = { search: "", account: "" };

function replaceUrl(params) {
  const query = params.toString();
  window.history.replaceState(null, "", query ? `/journal?${query}` : "/journal");
}

export function usePlans() {
  const [accounts, setAccounts] = useState([]);
  const [plans, setPlans] = useState([]);
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [selectedId, setSelectedId] = useState(
    () => new URLSearchParams(window.location.search).get("plan") || "",
  );
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [mode, setMode] = useState("empty");
  const [seed, setSeed] = useState(null);
  const [available, setAvailable] = useState([]);
  const [availableLoading, setAvailableLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useNotificationError();
  const [revision, setRevision] = useState(0);
  const openedPosition = useRef("");

  const refresh = useCallback(() => setRevision((value) => value + 1), []);

  useEffect(() => {
    const controller = new AbortController();
    loadAccounts({ signal: controller.signal })
      .then((items) => {
        if (!controller.signal.aborted) setAccounts(items);
      })
      .catch((err) => {
        if (!controller.signal.aborted) setError(err.message);
      });
    return () => controller.abort();
  }, [setError]);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    api
      .plans(filters, { signal: controller.signal })
      .then((items) => {
        if (!controller.signal.aborted) {
          setPlans(items);
          setError("");
        }
      })
      .catch((err) => {
        if (!controller.signal.aborted) setError(err.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [filters, revision, setError]);

  useEffect(() => {
    if (!selectedId) {
      setDetail(null);
      return undefined;
    }
    const controller = new AbortController();
    setDetailLoading(true);
    api
      .plan(selectedId, { signal: controller.signal })
      .then((item) => {
        if (!controller.signal.aborted) {
          setDetail(item);
          setMode("detail");
        }
      })
      .catch((err) => {
        if (!controller.signal.aborted) setError(err.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setDetailLoading(false);
      });
    return () => controller.abort();
  }, [selectedId, revision, setError]);

  function selectPlan(id) {
    if (id === selectedId) {
      refresh();
      return;
    }
    setSelectedId(id);
    setSeed(null);
    setDetail(null);
    setMode("detail");
    const params = new URLSearchParams();
    params.set("plan", id);
    replaceUrl(params);
  }

  function openCreate(position = null) {
    setSelectedId("");
    setDetail(null);
    setSeed(position);
    setMode("create");
    const params = new URLSearchParams();
    if (position) params.set("position", position.id);
    replaceUrl(params);
  }

  function cancelCreate() {
    setMode("empty");
    setSeed(null);
    setSelectedId("");
    setDetail(null);
    replaceUrl(new URLSearchParams());
  }

  async function openCreateFromPosition(positionId) {
    try {
      const items = await api.availablePositions({});
      const position = items.find((item) => item.id === positionId);
      if (!position) {
        setError("Позиция не найдена или уже привязана к плану");
        setMode("empty");
        return;
      }
      openCreate(position);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    if (openedPosition.current || loading) return;
    const positionId = new URLSearchParams(window.location.search).get("position");
    if (!positionId || selectedId) return;
    const match = plans.find((plan) => (plan.position_ids || []).includes(positionId));
    openedPosition.current = positionId;
    if (match) {
      selectPlan(match.id);
      return;
    }
    openCreateFromPosition(positionId);
    // The selectors are stable enough for this one-time deep-link resolution.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [plans, loading, selectedId]);

  async function run(operation, successMessage) {
    try {
      setBusy(true);
      setError("");
      const result = await operation();
      if (successMessage) notifySuccess(successMessage);
      return result;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setBusy(false);
    }
  }

  async function createPlan(values, files = []) {
    const created = await run(() => api.create(values));
    if (!created) return null;

    let result = created;
    let uploaded = false;
    if (files.length) {
      setBusy(true);
      setError("");
      try {
        for (const file of files) {
          const form = new FormData();
          form.append("file", file);
          await api.upload(created.id, form);
        }
        result = await api.plan(created.id);
        uploaded = true;
      } catch (err) {
        setError(err.message);
      } finally {
        setBusy(false);
      }
    }

    setSeed(null);
    selectPlan(created.id);
    setDetail(result);
    refresh();
    notifySuccess(uploaded ? "План создан, скриншоты добавлены." : "План создан.");
    return result;
  }

  async function deletePlan() {
    if (!selectedId) return null;
    const result = await run(() => api.deletePlan(selectedId), "План удалён.");
    if (result) {
      setSelectedId("");
      setDetail(null);
      setMode("empty");
      setSeed(null);
      replaceUrl(new URLSearchParams());
      refresh();
    }
    return result;
  }

  async function updatePlan(values) {
    if (!selectedId) return;
    const updated = await run(() => api.update(selectedId, values), "План сохранён.");
    if (updated) {
      setDetail(updated);
      refresh();
      return updated;
    }
    return null;
  }

  async function linkPosition(positionId) {
    if (!selectedId) return;
    const updated = await run(() => api.link(selectedId, positionId), "Позиция привязана к плану.");
    if (updated) {
      setDetail(updated);
      refresh();
    }
  }

  async function unlinkPosition(positionId) {
    if (!selectedId) return;
    if (!window.confirm("Отвязать позицию от плана? Факты сделки не изменятся.")) return;
    const updated = await run(
      () => api.unlink(selectedId, positionId),
      "Позиция отвязана от плана.",
    );
    if (updated) {
      setDetail(updated);
      refresh();
    }
  }

  async function uploadFiles(files) {
    if (!selectedId || !files?.length) return;
    setBusy(true);
    setError("");
    try {
      for (const file of files) {
        const form = new FormData();
        form.append("file", file);
        await api.upload(selectedId, form);
      }
      const updated = await api.plan(selectedId);
      setDetail(updated);
      notifySuccess(files.length === 1 ? "Скриншот добавлен." : "Скриншоты добавлены.");
      refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function removeAttachment(attachmentId) {
    const result = await run(() => api.removeAttachment(attachmentId), "Скриншот удалён.");
    if (result) {
      setDetail((current) =>
        current
          ? {
              ...current,
              attachments: current.attachments.filter((item) => item.id !== attachmentId),
            }
          : current,
      );
    }
  }

  const loadAvailable = useCallback(
    async (search = "") => {
      setAvailableLoading(true);
      try {
        setAvailable(await api.availablePositions({ search }));
      } catch (err) {
        setError(err.message);
      } finally {
        setAvailableLoading(false);
      }
    },
    [setError],
  );

  function updateFilter(name, value) {
    setFilters((current) => ({ ...current, [name]: value }));
  }

  return {
    accounts,
    plans,
    filters,
    selectedId,
    detail,
    detailLoading,
    mode,
    seed,
    available,
    availableLoading,
    loading,
    busy,
    error,
    updateFilter,
    selectPlan,
    openCreate,
    cancelCreate,
    createPlan,
    updatePlan,
    deletePlan,
    linkPosition,
    unlinkPosition,
    uploadFiles,
    removeAttachment,
    loadAvailable,
    refresh,
  };
}
