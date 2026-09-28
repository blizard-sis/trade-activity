import { useEffect, useState } from "react";
import { Button, Group, SimpleGrid, Stack } from "@mantine/core";
import { InstrumentPicker } from "./InstrumentPicker";

export function InstrumentLinkForm({ initial, busy, onSave, onCancel }) {
  const [forecast, setForecast] = useState(initial?.forecast || null);
  const [execution, setExecution] = useState(initial?.execution || null);
  const changed =
    forecast !== (initial?.forecast || null) || execution !== (initial?.execution || null);

  useEffect(() => {
    if (!changed) return;
    const guard = (event) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", guard);
    return () => window.removeEventListener("beforeunload", guard);
  }, [changed]);

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        if (forecast && execution && !busy) onSave({ forecast, execution }, initial?.id);
      }}
    >
      <Stack>
        <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="xl">
          <InstrumentPicker
            label="Инструмент прогноза"
            value={forecast}
            onChange={setForecast}
            disabled={busy}
          />
          <InstrumentPicker
            label="Инструмент работы"
            value={execution}
            onChange={setExecution}
            disabled={busy}
          />
        </SimpleGrid>
        <Group justify="flex-end">
          <Button
            type="button"
            variant="default"
            disabled={busy}
            onClick={() => {
              if (!changed || window.confirm("Отменить несохранённые изменения связки?"))
                onCancel();
            }}
          >
            Отмена
          </Button>
          <Button type="submit" loading={busy} disabled={!forecast || !execution}>
            Сохранить
          </Button>
        </Group>
      </Stack>
    </form>
  );
}
