import { useState } from "react";
import { Button, Group, Stack, Text } from "@mantine/core";
import { Dropzone } from "@mantine/dropzone";

const MAX_SIZE = 15 * 1024 * 1024;
const ACCEPT = {
  "image/png": [".png"],
  "image/jpeg": [".jpg", ".jpeg"],
  "image/webp": [".webp"],
};

export function PlanAttachments({ plan, busy, onUpload, onRemove }) {
  const [error, setError] = useState("");

  async function drop(files) {
    setError("");
    await onUpload(files);
  }

  function reject() {
    setError("Можно добавить PNG, JPEG или WebP размером до 15 МБ.");
  }

  return (
    <Stack gap="md">
      <div>
        <Text fw={600}>Скриншоты плана</Text>
        <Text size="sm" c="dimmed">
          Перетащите файлы в зону или нажмите на неё. Можно вставить изображение из буфера.
        </Text>
      </div>

      <Dropzone
        accept={ACCEPT}
        maxSize={MAX_SIZE}
        maxFiles={12}
        multiple
        loading={busy}
        onDrop={drop}
        onReject={reject}
        p="lg"
        aria-label="Скриншоты плана"
      >
        <Stack gap="xs" align="center" ta="center" py="md" style={{ pointerEvents: "none" }}>
          <Dropzone.Idle>
            <Text fw={500}>Перетащите скриншоты сюда или нажмите для выбора</Text>
          </Dropzone.Idle>
          <Dropzone.Accept>
            <Text fw={500} c="blue">
              Отпустите файлы, чтобы добавить их в план
            </Text>
          </Dropzone.Accept>
          <Dropzone.Reject>
            <Text fw={500} c="red">
              Нужны PNG, JPEG или WebP до 15 МБ
            </Text>
          </Dropzone.Reject>
          <Text size="xs" c="dimmed">
            До 12 файлов за раз, каждый до 15 МБ
          </Text>
        </Stack>
      </Dropzone>
      {error && (
        <Text c="red" size="sm" role="alert">
          {error}
        </Text>
      )}

      <div className="plan-attachments-grid">
        {plan.attachments.map((attachment) => (
          <figure key={attachment.id} className="plan-attachment">
            <a href={attachment.url} target="_blank" rel="noopener noreferrer">
              <img
                src={attachment.url}
                alt={attachment.caption || "Скриншот плана"}
                loading="lazy"
                className="plan-thumb"
              />
            </a>
            <figcaption>
              <Group justify="flex-end">
                <Button
                  type="button"
                  size="compact-xs"
                  variant="subtle"
                  color="red"
                  disabled={busy}
                  onClick={() => onRemove(attachment.id)}
                >
                  Удалить
                </Button>
              </Group>
            </figcaption>
          </figure>
        ))}
      </div>
      {!plan.attachments.length && (
        <Text c="dimmed" size="sm">
          Скриншотов пока нет.
        </Text>
      )}
    </Stack>
  );
}
