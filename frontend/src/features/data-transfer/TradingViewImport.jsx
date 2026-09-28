import { useState } from "react";
import { Button, FileInput, Paper, SimpleGrid, Stack, Text, TextInput, Title } from "@mantine/core";

export function TradingViewImport({ importing, onImport }) {
  const [files, setFiles] = useState([]);
  const [accountName, setAccountName] = useState("Paper Trading");

  function submit(event) {
    event.preventDefault();
    onImport(files, accountName);
  }

  return (
    <Paper component="form" withBorder p="lg" onSubmit={submit}>
      <Stack>
        <Title order={2} size="h3">
          Импорт TradingView
        </Title>
        <Text size="sm" c="dimmed">
          Выберите CSV «История сделок» (trade-history) из Paper Trading. Можно выбрать сразу все 6
          файлов: история заявок уточнит время, история баланса — результат и валюту цены.
        </Text>
        <Text size="sm" c="dimmed">
          Для повторной загрузки используйте то же название счёта. Для другого демо-счёта или после
          сброса баланса укажите новое. Время сохраняется как в выгрузке.
        </Text>
        <SimpleGrid cols={{ base: 1, sm: 2 }}>
          <TextInput
            label="Название демо-счёта"
            required
            maxLength={100}
            value={accountName}
            disabled={importing}
            onChange={(event) => setAccountName(event.target.value)}
          />
          <FileInput
            label="CSV-файлы"
            accept=".csv,text/csv"
            multiple
            required
            disabled={importing}
            value={files}
            onChange={setFiles}
            placeholder="Выберите CSV-файлы"
            aria-label="CSV-файлы TradingView"
          />
        </SimpleGrid>
        <Button
          type="submit"
          variant="filled"
          loading={importing}
          disabled={!files.length}
          style={{ alignSelf: "flex-start" }}
        >
          Импортировать
        </Button>
      </Stack>
    </Paper>
  );
}
