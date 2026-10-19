import { useEffect, useState } from "react";
import { Button, Group, Paper, Select, Stack, Tabs, Text, TextInput, Title } from "@mantine/core";
import { Layout } from "../../app/Layout";
import { Message } from "../../shared/components/Message";
import { usePlans } from "./usePlans";
import { PlanDetail } from "./components/PlanDetail";
import { PlanFilesPicker } from "./components/PlanFilesPicker";
import { PlanForm } from "./components/PlanForm";
import { PlanList } from "./components/PlanList";
import { UnplannedList } from "./components/UnplannedList";
import "./plans.css";

export function PlansPage() {
  const {
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
    linkPosition,
    unlinkPosition,
    uploadFiles,
    removeAttachment,
    synchronize,
    loadAvailable,
  } = usePlans();
  const [tab, setTab] = useState("plans");
  const [pendingFiles, setPendingFiles] = useState([]);

  function startCreate(position = null) {
    setPendingFiles([]);
    openCreate(position);
  }

  function cancelCreateForm() {
    setPendingFiles([]);
    cancelCreate();
  }

  async function create(values) {
    const result = await createPlan(values, pendingFiles);
    if (result) setPendingFiles([]);
    return result;
  }

  useEffect(() => {
    if (tab === "unplanned") loadAvailable(filters.search);
  }, [tab, filters.search, loadAvailable]);

  const actions = (
    <Group gap="xs">
      <Button variant="default" onClick={() => startCreate()}>
        Новый план
      </Button>
      <Button variant="filled" loading={busy} onClick={synchronize}>
        Синхронизировать
      </Button>
    </Group>
  );

  return (
    <Layout title="Дневник трейдера" subtitle="Планы, шаги, позиции и скриншоты" action={actions}>
      {error && <Message>{error}</Message>}
      <div className="plans-workspace">
        <aside className="plans-sidebar">
          <Tabs value={tab} onChange={setTab}>
            <Tabs.List grow>
              <Tabs.Tab value="plans">Планы</Tabs.Tab>
              <Tabs.Tab value="unplanned">Без плана</Tabs.Tab>
            </Tabs.List>
          </Tabs>
          <Stack gap="xs" p="sm">
            <TextInput
              type="search"
              aria-label="Поиск планов"
              placeholder="Поиск по плану или тезису"
              value={filters.search}
              onChange={(event) => updateFilter("search", event.target.value)}
            />
            {tab === "plans" && (
              <Select
                aria-label="Счёт"
                placeholder="Все счета"
                data={accounts.map((account) => ({ value: account.id, label: account.name }))}
                value={filters.account || null}
                clearable
                searchable
                onChange={(value) => updateFilter("account", value || "")}
              />
            )}
          </Stack>
          <div className="plan-list-scroll">
            {tab === "plans" ? (
              loading ? (
                <Text c="dimmed" size="sm" p="md">
                  Загрузка планов…
                </Text>
              ) : (
                <PlanList plans={plans} selectedId={selectedId} onSelect={selectPlan} />
              )
            ) : (
              <UnplannedList
                positions={available}
                loading={availableLoading}
                onCreate={startCreate}
              />
            )}
          </div>
        </aside>

        <section className="plans-main">
          {mode === "create" && (
            <Paper withBorder p="lg">
              <Title order={2} size="h3" mb="md">
                Новый план
              </Title>
              <PlanForm
                seedPosition={seed}
                accounts={accounts}
                busy={busy}
                submitLabel="Создать план"
                onSubmit={create}
                onCancel={cancelCreateForm}
                beforeSubmit={
                  <PlanFilesPicker files={pendingFiles} onChange={setPendingFiles} busy={busy} />
                }
              />
            </Paper>
          )}
          {mode === "detail" && detail && (
            <PlanDetail
              plan={detail}
              accounts={accounts}
              busy={busy}
              onUpdate={updatePlan}
              onLink={linkPosition}
              onUnlink={unlinkPosition}
              onUpload={uploadFiles}
              onRemoveAttachment={removeAttachment}
            />
          )}
          {mode === "detail" && !detail && detailLoading && <Message>Загрузка плана…</Message>}
          {mode === "detail" && !detail && !detailLoading && (
            <Message>Не удалось загрузить план. Обновите страницу или выберите другой.</Message>
          )}
          {mode === "empty" && (
            <Paper withBorder p="xl" className="plan-placeholder">
              <Title order={2} size="h3">
                Выберите план
              </Title>
              <Text c="dimmed" mt="xs">
                Откройте план слева, создайте новый или разберите позицию без плана.
              </Text>
              <Button mt="md" onClick={() => startCreate()}>
                Новый план
              </Button>
            </Paper>
          )}
        </section>
      </div>
    </Layout>
  );
}
