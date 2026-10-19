import { useEffect, useState } from "react";
import { Button, Group, Modal, ScrollArea, Stack, Table, Text, TextInput } from "@mantine/core";
import {
  formatDate,
  formatMoney,
  formatPrice,
  formatQuantity,
  resultClass,
} from "../../../shared/format";
import { api } from "../api";
import { directionLabel } from "../model";

function LinkPositionModal({ opened, onClose, plan, busy, onLink }) {
  const [query, setQuery] = useState("");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!opened) return undefined;
    let active = true;
    setLoading(true);
    const timer = setTimeout(async () => {
      try {
        const positions = await api.availablePositions({ search: query });
        if (!active) return;
        setItems(
          positions.filter(
            (position) =>
              (!plan.direction || position.direction === plan.direction) &&
              (!plan.account_id || position.account_id === plan.account_id),
          ),
        );
        setError("");
      } catch (err) {
        if (active) setError(err.message);
      } finally {
        if (active) setLoading(false);
      }
    }, 150);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [opened, query, plan.direction, plan.account_id]);

  return (
    <Modal opened={opened} onClose={onClose} title="Привязать позицию" size="lg">
      <Stack gap="sm">
        <TextInput
          label="Поиск"
          placeholder="Тикер или инструмент"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          data-autofocus
        />
        {error && (
          <Text c="red" size="sm">
            {error}
          </Text>
        )}
        <ScrollArea.Autosize mah={380}>
          <Stack gap="xs">
            {items.map((position) => (
              <Button
                key={position.id}
                type="button"
                variant="subtle"
                justify="space-between"
                disabled={busy}
                onClick={() => {
                  onLink(position.id);
                  onClose();
                }}
              >
                <span>
                  {position.ticker || position.instrument_name} ·{" "}
                  {directionLabel(position.direction)} · {formatDate(position.entry_at)}
                </span>
                <span>{position.status === "closed" ? "Закрыта" : "Открыта"}</span>
              </Button>
            ))}
            {!loading && !items.length && !error && (
              <Text c="dimmed" size="sm">
                Нет свободных позиций для этого плана.
              </Text>
            )}
            {loading && (
              <Text c="dimmed" size="sm">
                Загрузка позиций…
              </Text>
            )}
          </Stack>
        </ScrollArea.Autosize>
      </Stack>
    </Modal>
  );
}

export function PlanPositions({ plan, busy, onLink, onUnlink }) {
  const [linking, setLinking] = useState(false);
  return (
    <Stack gap="sm">
      <Group justify="space-between">
        <Text fw={600}>Позиции</Text>
        <Button type="button" variant="light" disabled={busy} onClick={() => setLinking(true)}>
          Привязать позицию
        </Button>
      </Group>

      <div className="table-card">
        <Table striped highlightOnHover withTableBorder horizontalSpacing="md" verticalSpacing="sm">
          <Table.Thead>
            <Table.Tr>
              <Table.Th className="text-left">Инструмент</Table.Th>
              <Table.Th className="text-left">Направление</Table.Th>
              <Table.Th className="text-left">Вход</Table.Th>
              <Table.Th className="text-left">Выход</Table.Th>
              <Table.Th>Объём</Table.Th>
              <Table.Th>Чистыми</Table.Th>
              <Table.Th />
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {plan.positions.map((position) => (
              <Table.Tr key={position.id}>
                <Table.Td className="text-left">
                  <Text fw={600} size="sm">
                    {position.ticker || position.instrument_name}
                  </Text>
                  <Text size="xs" c="dimmed">
                    {position.account_name}
                  </Text>
                </Table.Td>
                <Table.Td className="text-left">{directionLabel(position.direction)}</Table.Td>
                <Table.Td className="text-left">
                  <Text size="sm" fw={500}>
                    {formatPrice(position.entry_price, position.price_precision, position.currency)}
                  </Text>
                  <Text size="xs" c="dimmed">
                    {formatDate(position.entry_at)}
                  </Text>
                </Table.Td>
                <Table.Td className="text-left">
                  <Text size="sm" fw={500}>
                    {formatPrice(position.exit_price, position.price_precision, position.currency)}
                  </Text>
                  <Text size="xs" c="dimmed">
                    {formatDate(position.exit_at)}
                  </Text>
                </Table.Td>
                <Table.Td>{formatQuantity(position.entry_quantity)}</Table.Td>
                <Table.Td>
                  <span className={resultClass(position.net_result)}>
                    {formatMoney(position.net_result, position.result_currency)}
                  </span>
                </Table.Td>
                <Table.Td>
                  <Button
                    type="button"
                    size="compact-xs"
                    variant="subtle"
                    color="red"
                    disabled={busy}
                    onClick={() => onUnlink(position.id)}
                  >
                    Отвязать
                  </Button>
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </div>
      {!plan.positions.length && (
        <Text c="dimmed" size="sm">
          К плану пока не привязано ни одной позиции.
        </Text>
      )}

      <LinkPositionModal
        opened={linking}
        onClose={() => setLinking(false)}
        plan={plan}
        busy={busy}
        onLink={onLink}
      />
    </Stack>
  );
}
