import { useState } from "react";
import { Alert, Button, CloseButton, Group, Paper, Stack, Text } from "@mantine/core";
import { Dropzone } from "@mantine/dropzone";

const MAX_FILES = 6;
const MAX_SIZE = 20 * 1024 * 1024;
const CSV_TYPES = { "text/csv": [".csv"] };

export function TradingViewFiles({ files, onChange, loading }) {
  const [error, setError] = useState("");

  function selectFiles(accepted, rejected) {
    if (rejected.length) {
      setError("Выберите только CSV-файлы: не более 6 файлов общим размером до 20 МБ.");
      return;
    }
    if (accepted.reduce((size, file) => size + file.size, 0) > MAX_SIZE) {
      setError("Общий размер файлов не должен превышать 20 МБ.");
      return;
    }
    setError("");
    onChange(accepted);
  }

  function removeFile(index) {
    setError("");
    onChange(files.filter((_, fileIndex) => fileIndex !== index));
  }

  return (
    <Stack gap="sm">
      <Dropzone
        accept={CSV_TYPES}
        maxFiles={MAX_FILES}
        maxSize={MAX_SIZE}
        multiple
        loading={loading}
        onDropAny={selectFiles}
        onDrop={() => {}}
        aria-label="CSV-файлы TradingView"
        inputProps={{ "aria-label": "Выбрать CSV-файлы TradingView" }}
        p="xl"
      >
        <Stack gap="xs" align="center" ta="center" py="lg" style={{ pointerEvents: "none" }}>
          <Dropzone.Idle>
            <Text fw={600}>Перетащите CSV-файлы сюда или нажмите для выбора</Text>
          </Dropzone.Idle>
          <Dropzone.Accept>
            <Text fw={600} c="blue">
              Отпустите файлы для загрузки
            </Text>
          </Dropzone.Accept>
          <Dropzone.Reject>
            <Text fw={600} c="red">
              Эти файлы не подходят для импорта
            </Text>
          </Dropzone.Reject>
          <Text size="sm" c="dimmed">
            До 6 CSV-файлов, не более 20 МБ суммарно
          </Text>
          {files.length > 0 && (
            <Text size="xs" c="dimmed">
              Новый выбор заменит текущий список
            </Text>
          )}
        </Stack>
      </Dropzone>
      {error && (
        <Alert color="red" role="alert">
          {error}
        </Alert>
      )}
      {files.length > 0 && (
        <Stack gap="xs">
          <Group justify="space-between">
            <Text size="sm" fw={500}>
              Выбрано файлов: {files.length}
            </Text>
            <Button
              type="button"
              variant="subtle"
              size="compact-sm"
              disabled={loading}
              onClick={() => {
                setError("");
                onChange([]);
              }}
            >
              Очистить список
            </Button>
          </Group>
          {files.map((file, index) => (
            <Paper key={`${file.name}-${index}`} withBorder p="sm">
              <Group justify="space-between" wrap="nowrap">
                <Stack gap={0} style={{ minWidth: 0 }}>
                  <Text size="sm" truncate title={file.name}>
                    {file.name}
                  </Text>
                  <Text size="xs" c="dimmed">
                    {(file.size / 1024).toLocaleString("ru-RU", { maximumFractionDigits: 1 })} КБ
                  </Text>
                </Stack>
                <CloseButton
                  type="button"
                  disabled={loading}
                  aria-label={`Удалить ${file.name}`}
                  onClick={() => removeFile(index)}
                />
              </Group>
            </Paper>
          ))}
        </Stack>
      )}
    </Stack>
  );
}
