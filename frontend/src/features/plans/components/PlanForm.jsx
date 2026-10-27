import { useState } from "react";
import {
  Button,
  Group,
  Paper,
  Select,
  SimpleGrid,
  Stack,
  Text,
  Textarea,
  TextInput,
} from "@mantine/core";
import { formatDate, formatMoney, formatPrice, resultClass } from "../../../shared/format";
import { DIRECTION_LABELS, directionLabel } from "../model";

const DIRECTION_OPTIONS = Object.entries(DIRECTION_LABELS).map(([value, label]) => ({
  value,
  label,
}));

const textValue = (value) => (value === null || value === undefined ? "" : String(value));

export function PlanForm({
  initial = {},
  seedPosition = null,
  accounts,
  busy,
  submitLabel,
  onSubmit,
  onCancel,
  beforeSubmit = null,
}) {
  const [values, setValues] = useState(() => ({
    direction: initial.direction || seedPosition?.direction || "long",
    account_id: initial.account_id || seedPosition?.account_id || "",
    forecast_ticker: initial.forecast?.ticker || seedPosition?.ticker || "",
    entry_zone: textValue(initial.entry_zone ?? seedPosition?.entry_zone),
    planned_take: textValue(initial.planned_take ?? seedPosition?.planned_take),
    planned_stop: textValue(initial.planned_stop ?? seedPosition?.planned_stop),
    thesis: initial.thesis || seedPosition?.entry_note || "",
  }));

  function update(name, value) {
    setValues((current) => ({ ...current, [name]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    if (busy) return;
    const updated = await onSubmit({
      ...values,
      account_id: values.account_id || null,
      position_id: seedPosition?.id,
    });
    if (updated) {
      setValues((current) => ({
        ...current,
        entry_zone: textValue(updated.entry_zone),
        planned_take: textValue(updated.planned_take),
        planned_stop: textValue(updated.planned_stop),
      }));
    }
  }

  return (
    <form onSubmit={submit}>
      <Stack gap="md">
        {seedPosition && (
          <Paper withBorder p="sm" bg="gray.0">
            <Text fw={600}>{seedPosition.ticker || seedPosition.instrument_name}</Text>
            <Text size="xs" c="dimmed">
              {seedPosition.account_name} · {directionLabel(seedPosition.direction)}
            </Text>
            <Text size="sm">
              Вход{" "}
              {formatPrice(
                seedPosition.entry_price,
                seedPosition.price_precision,
                seedPosition.currency,
              )}{" "}
              <Text component="span" size="xs" c="dimmed">
                {formatDate(seedPosition.entry_at)}
              </Text>
            </Text>
            <Text size="sm">
              Выход{" "}
              {formatPrice(
                seedPosition.exit_price,
                seedPosition.price_precision,
                seedPosition.currency,
              )}{" "}
              <Text component="span" size="xs" c="dimmed">
                {formatDate(seedPosition.exit_at)}
              </Text>
            </Text>
            <Text size="sm">
              Чистыми{" "}
              <span className={resultClass(seedPosition.net_result)}>
                {formatMoney(seedPosition.net_result, seedPosition.result_currency)}
              </span>
            </Text>
            <Text size="xs" c="dimmed">
              Позиция будет привязана к плану автоматически.
            </Text>
          </Paper>
        )}

        <SimpleGrid cols={{ base: 1, sm: 2 }}>
          <Select
            label="Платформа"
            placeholder="Выберите счёт"
            data={accounts.map((account) => ({ value: account.id, label: account.name }))}
            value={values.account_id || null}
            clearable
            searchable
            disabled={Boolean(seedPosition)}
            onChange={(value) => update("account_id", value || "")}
          />
          <Select
            label="Направление"
            data={DIRECTION_OPTIONS}
            value={values.direction}
            allowDeselect={false}
            disabled={Boolean(seedPosition)}
            onChange={(value) => update("direction", value || "long")}
          />
          <TextInput
            label="Тикер"
            placeholder="Например, BR1! или BRU6"
            maxLength={200}
            value={values.forecast_ticker}
            onChange={(event) => update("forecast_ticker", event.target.value)}
          />
          <TextInput
            label="Вход"
            placeholder="Например, 65.5"
            maxLength={1000}
            value={values.entry_zone}
            onChange={(event) => update("entry_zone", event.target.value)}
          />
          <TextInput
            label="Тейк"
            placeholder="Цена в единицах инструмента"
            maxLength={500}
            value={values.planned_take}
            onChange={(event) => update("planned_take", event.target.value)}
          />
          <TextInput
            label="Стоп"
            placeholder="Цена в единицах инструмента"
            maxLength={500}
            value={values.planned_stop}
            onChange={(event) => update("planned_stop", event.target.value)}
          />
        </SimpleGrid>

        <Textarea
          label="Описание для входа"
          placeholder="Сетап, контекст, что ожидаю от сделки"
          minRows={4}
          maxLength={50000}
          value={values.thesis}
          onChange={(event) => update("thesis", event.target.value)}
        />

        {beforeSubmit}

        <Group justify="flex-end">
          {onCancel && (
            <Button type="button" variant="default" disabled={busy} onClick={onCancel}>
              Отмена
            </Button>
          )}
          <Button type="submit" variant="filled" loading={busy}>
            {submitLabel}
          </Button>
        </Group>
      </Stack>
    </form>
  );
}
