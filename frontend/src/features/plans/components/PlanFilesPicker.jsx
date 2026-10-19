import { useState } from "react";
import { Button, Group, Stack, Text } from "@mantine/core";
import { Dropzone } from "@mantine/dropzone";

const MAX_SIZE = 15 * 1024 * 1024;
const ACCEPT = {
  "image/png": [".png"],
  "image/jpeg": [".jpg", ".jpeg"],
  "image/webp": [".webp"],
};

export function PlanFilesPicker({ files, onChange, busy }) {
  const [error, setError] = useState("");

  function add(selected) {
    setError("");
    onChange([...files, ...selected]);
  }

  function remove(index) {
    onChange(files.filter((_, fileIndex) => fileIndex !== index));
  }

  return (
    <Stack gap="sm">
      <div>
        <Text fw={600}>Скриншоты плана</Text>
        <Text size="sm" c="dimmed">
          Перетащите файлы в зону или нажмите на неё. Они загрузятся после создания плана.
        </Text>
      </div>

      <Dropzone
        accept={ACCEPT}
        maxSize={MAX_SIZE}
        maxFiles={12}
        multiple
        loading={busy}
        onDrop={add}
        onReject={() => setError("Можно добавить PNG, JPEG или WebP размером до 15 МБ.")}
        p="lg"
        aria-label="Скриншоты нового плана"
      >
        <Stack gap="xs" align="center" ta="center" py="md" style={{ pointerEvents: "none" }}>
          <Dropzone.Idle>
            <Text fw={500}>Перетащите скриншоты сюда или нажмите для выбора</Text>
          </Dropzone.Idle>
          <Dropzone.Accept>
            <Text fw={500} c="blue">
              Отпустите файлы, чтобы добавить их к плану
            </Text>
          </Dropzone.Accept>
          <Dropzone.Reject>
            <Text fw={500} c="red">
              Нужны PNG, JPEG или WebP до 15 МБ
            </Text>
          </Dropzone.Reject>
          <Text size="xs" c="dimmed">
            До 12 файлов, каждый до 15 МБ
          </Text>
        </Stack>
      </Dropzone>
      {error && (
        <Text c="red" size="sm" role="alert">
          {error}
        </Text>
      )}

      {files.length > 0 && (
        <Stack gap="xs">
          {files.map((file, index) => (
            <Group key={`${file.name}-${index}`} justify="space-between" wrap="nowrap">
              <Text size="sm" truncate title={file.name}>
                {file.name}
              </Text>
              <Button
                type="button"
                size="compact-xs"
                variant="subtle"
                color="red"
                disabled={busy}
                onClick={() => remove(index)}
              >
                Убрать
              </Button>
            </Group>
          ))}
        </Stack>
      )}
    </Stack>
  );
}
