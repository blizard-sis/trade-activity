import { useEffect, useRef, useState } from "react";
import { Alert, Button, Group, Select, Stack, Text, TextInput } from "@mantine/core";
import { api } from "./api";

export function InstrumentPicker({ label, value, onChange, disabled }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [searched, setSearched] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const request = useRef(null);

  useEffect(() => () => request.current?.abort(), []);

  async function run(operation) {
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    setBusy(true);
    setError("");
    try {
      await operation(controller.signal);
    } catch (err) {
      if (!controller.signal.aborted) setError(err.message);
    } finally {
      if (!controller.signal.aborted) setBusy(false);
    }
  }

  function search() {
    setResults([]);
    setSearched(false);
    onChange(null);
    return run(async (signal) => {
      const items = await api.search(query.trim(), signal);
      if (!signal.aborted) {
        setResults(items);
        setSearched(true);
      }
    });
  }

  function select(id) {
    onChange(null);
    const item = results.find((row) => row.id === id);
    if (!item) return;
    return run(async (signal) => {
      const full = await api.select(item, signal);
      if (!signal.aborted) onChange(full);
    });
  }

  return (
    <Stack gap="xs">
      <Text fw={600}>{label}</Text>
      <Group align="end" wrap="nowrap">
        <TextInput
          label="Поиск в Т-Банке"
          placeholder="Тикер или название"
          value={query}
          maxLength={100}
          style={{ flex: 1 }}
          disabled={disabled || busy}
          onChange={(event) => setQuery(event.currentTarget.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              if (query.trim().length >= 2 && !busy) search();
            }
          }}
        />
        <Button
          variant="light"
          type="button"
          disabled={disabled || query.trim().length < 2}
          loading={busy}
          onClick={search}
        >
          Найти
        </Button>
      </Group>
      {results.length > 0 && (
        <Select
          label="Результаты поиска"
          placeholder="Выберите инструмент и режим торгов"
          searchable
          disabled={disabled || busy}
          value={results.some((row) => row.id === value?.id) ? value.id : null}
          onChange={select}
          data={results.map((row) => ({
            value: row.id,
            label: `${row.ticker} · ${row.class_code} · ${row.name}`,
          }))}
          nothingFoundMessage="Не найдено"
        />
      )}
      {searched && !results.length && (
        <Text c="dimmed" size="sm">
          Инструменты не найдены. Попробуйте другой запрос.
        </Text>
      )}
      {error && (
        <Alert color="red" role="alert">
          {error}
        </Alert>
      )}
      {value && (
        <Text size="sm">
          {value.ticker} · {value.name} · {value.class_code}
        </Text>
      )}
      <TextInput
        label="Биржа"
        readOnly
        value={value?.exchange || ""}
        placeholder="Определяется по выбранному инструменту"
      />
      {value?.expiration_at && (
        <Text size="xs" c="dimmed">
          Экспирация: {value.expiration_at.slice(0, 10)}
        </Text>
      )}
    </Stack>
  );
}
