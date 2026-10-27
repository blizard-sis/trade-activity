import { Button, Group, Paper, Stack, Tabs, Text, Title } from "@mantine/core";
import { directionLabel } from "../model";
import { NetValue } from "./NetValue";
import { PlanAttachments } from "./PlanAttachments";
import { PlanForm } from "./PlanForm";
import { PlanPositions } from "./PlanPositions";
import { PlanReview } from "./PlanReview";

export function PlanDetail({
  plan,
  accounts,
  busy,
  onUpdate,
  onDelete,
  onLink,
  onUnlink,
  onUpload,
  onRemoveAttachment,
}) {
  const account = accounts.find((item) => item.id === plan.account_id);
  const summary = plan.summary || {};

  function paste(event) {
    const files = Array.from(event.clipboardData?.files || []).filter((file) =>
      file.type.startsWith("image/"),
    );
    if (!files.length) return;
    event.preventDefault();
    onUpload(files);
  }

  return (
    <div className="plan-detail" onPaste={paste}>
      <Paper withBorder p="lg">
        <Group justify="space-between" align="flex-start" gap="lg">
          <div>
            <Group gap="xs" align="center">
              <Title order={2} size="h3">
                {plan.title}
              </Title>
            </Group>
            <Text size="sm" c="dimmed" mt={4}>
              {[
                plan.forecast?.ticker || plan.execution?.ticker,
                directionLabel(plan.direction),
                account?.name || plan.account_id,
              ]
                .filter(Boolean)
                .join(" · ")}
            </Text>
            <Group gap="lg" mt="sm" className="plan-summary">
              <span>
                Позиций <strong>{summary.positions || 0}</strong>
              </span>
              <span>
                Открытых <strong>{summary.open || 0}</strong>
              </span>
              <span>
                Чистыми{" "}
                <strong>
                  <NetValue summary={summary} />
                </strong>
              </span>
            </Group>
          </div>
          <Group gap="xs">
            <Button
              type="button"
              variant="subtle"
              color="red"
              disabled={busy || plan.positions.length > 0}
              title={
                plan.positions.length ? "Сначала отвяжите привязанные позиции" : "Удалить план"
              }
              onClick={() => {
                if (
                  window.confirm(
                    "Удалить план? Это также удалит его скриншоты. Действие нельзя отменить.",
                  )
                )
                  onDelete();
              }}
            >
              Удалить план
            </Button>
          </Group>
        </Group>

        <Tabs defaultValue="plan" mt="lg">
          <Tabs.List>
            <Tabs.Tab value="plan">План</Tabs.Tab>
            <Tabs.Tab value="execution">Исполнение ({plan.positions.length})</Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="plan" pt="md">
            <Stack gap="xl">
              <PlanForm
                key={plan.updated_at}
                initial={plan}
                accounts={accounts}
                busy={busy}
                submitLabel="Сохранить план"
                onSubmit={onUpdate}
                beforeSubmit={
                  <PlanAttachments
                    plan={plan}
                    busy={busy}
                    onUpload={onUpload}
                    onRemove={onRemoveAttachment}
                  />
                }
              />
            </Stack>
          </Tabs.Panel>
          <Tabs.Panel value="execution" pt="md">
            <Stack gap="xl">
              <PlanPositions plan={plan} busy={busy} onLink={onLink} onUnlink={onUnlink} />
              <Paper withBorder p="md">
                <PlanReview plan={plan} busy={busy} onSave={onUpdate} />
              </Paper>
            </Stack>
          </Tabs.Panel>
        </Tabs>
      </Paper>
    </div>
  );
}
