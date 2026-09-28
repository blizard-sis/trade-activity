import { useState } from "react";
import { Alert, Button, Group, Modal, Paper, Table, Tabs, Text, Tooltip } from "@mantine/core";
import { Layout } from "../../app/Layout";
import { InstrumentLinkForm } from "./InstrumentLinkForm";
import { useInstrumentLinks } from "./useInstrumentLinks";

function instrumentCell(item) {
  const expired =
    item.expiration_at && item.expiration_at.slice(0, 10) < new Date().toISOString().slice(0, 10);
  return (
    <>
      <Text fw={600}>{item.ticker}</Text>
      <Text size="sm">{item.name}</Text>
      <Text size="xs" c="dimmed">
        {item.class_code} · Т-Банк
      </Text>
      {item.expiration_at && (
        <Text size="xs" c={expired ? "orange" : "dimmed"}>
          {expired ? "Истёк" : "Экспирация"}: {item.expiration_at.slice(0, 10)}
        </Text>
      )}
    </>
  );
}

function exchangeCell(item) {
  return (
    <Tooltip label={`Получено через MCP: ${new Date(item.updated_at).toLocaleString("ru-RU")}`}>
      <Text size="sm">{item.exchange}</Text>
    </Tooltip>
  );
}

export function SettingsPage() {
  const { links, loading, busy, error, reload, save, remove, refresh } = useInstrumentLinks();
  const [editing, setEditing] = useState(null);
  return (
    <Layout title="Настройки" subtitle="Инструменты для прогнозов и исполнения сделок">
      <Tabs defaultValue="instruments">
        <Tabs.List>
          <Tabs.Tab value="instruments">Инструменты</Tabs.Tab>
        </Tabs.List>
        <Tabs.Panel value="instruments" pt="lg">
          <Alert title="Справочник Т-Банка · MCP" mb="md">
            Поиск и обновление получают данные из Т-Банка. Сохранённые связки доступны без
            подключения. TradingView пока не подключён.
          </Alert>
          <Group justify="space-between" mb="md">
            <Text size="sm" c="dimmed">
              Свяжите инструмент, по которому строите прогноз, с инструментом исполнения.
            </Text>
            <Button disabled={loading || busy || Boolean(error)} onClick={() => setEditing({})}>
              Добавить связку
            </Button>
          </Group>
          {error && (
            <Alert color="red" mb="md">
              {error}
              <Button ml="md" size="xs" variant="light" onClick={reload} disabled={busy}>
                Повторить загрузку
              </Button>
            </Alert>
          )}
          <Paper withBorder p="md">
            <Table.ScrollContainer minWidth={700}>
              <Table>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Инструмент прогноза</Table.Th>
                    <Table.Th>Биржа прогноза</Table.Th>
                    <Table.Th>Инструмент работы</Table.Th>
                    <Table.Th>Биржа работы</Table.Th>
                    <Table.Th>Действия</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {links.map((link) => (
                    <Table.Tr key={link.id}>
                      <Table.Td>{instrumentCell(link.forecast)}</Table.Td>
                      <Table.Td>{exchangeCell(link.forecast)}</Table.Td>
                      <Table.Td>{instrumentCell(link.execution)}</Table.Td>
                      <Table.Td>{exchangeCell(link.execution)}</Table.Td>
                      <Table.Td>
                        <Group gap="xs">
                          <Button
                            size="xs"
                            variant="light"
                            disabled={busy || loading}
                            onClick={() => setEditing(link)}
                          >
                            Изменить
                          </Button>
                          <Button
                            size="xs"
                            variant="subtle"
                            disabled={busy || loading}
                            onClick={() => refresh(link.id)}
                          >
                            Обновить
                          </Button>
                          <Button
                            size="xs"
                            variant="subtle"
                            color="red"
                            disabled={busy || loading}
                            onClick={() => {
                              if (
                                window.confirm(
                                  `Удалить связку ${link.forecast.ticker} → ${link.execution.ticker}?`,
                                )
                              )
                                remove(link.id);
                            }}
                          >
                            Удалить
                          </Button>
                        </Group>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                  {!links.length && (
                    <Table.Tr>
                      <Table.Td colSpan={5}>
                        <Text c="dimmed" ta="center" py="xl">
                          {loading
                            ? "Загрузка связок…"
                            : error
                              ? "Не удалось загрузить связки."
                              : "Связки инструментов пока не добавлены."}
                        </Text>
                      </Table.Td>
                    </Table.Tr>
                  )}
                </Table.Tbody>
              </Table>
            </Table.ScrollContainer>
          </Paper>
        </Tabs.Panel>
      </Tabs>
      <Modal
        opened={editing !== null}
        onClose={() => {}}
        withCloseButton={false}
        closeOnClickOutside={false}
        closeOnEscape={false}
        title={editing?.id ? "Изменить связку" : "Новая связка инструментов"}
        size="xl"
      >
        {editing !== null && (
          <InstrumentLinkForm
            key={editing.id || "new"}
            initial={editing}
            busy={busy}
            onCancel={() => setEditing(null)}
            onSave={async (values, id) => {
              if (await save(values, id)) setEditing(null);
            }}
          />
        )}
      </Modal>
    </Layout>
  );
}
