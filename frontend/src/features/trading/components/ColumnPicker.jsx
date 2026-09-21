import { useState } from "react";
import { Button, Checkbox, Popover, ScrollArea, Stack, Text, TextInput } from "@mantine/core";
import { COLUMN_LABELS } from "../columns";

export function ColumnPicker({ visible, onToggle, onReset }) {
  const [search, setSearch] = useState("");
  const columns = Object.entries(COLUMN_LABELS).filter(([, label]) => label.toLocaleLowerCase("ru").includes(search.trim().toLocaleLowerCase("ru")));
  return <Popover width={280} position="bottom-end" shadow="md" onClose={() => setSearch("")} trapFocus>
    <Popover.Target><Button variant="default">Колонки</Button></Popover.Target>
    <Popover.Dropdown>
      <Stack gap="sm">
        <TextInput aria-label="Поиск колонки" placeholder="Найти колонку" value={search} onChange={(event) => setSearch(event.target.value)} data-autofocus />
        <ScrollArea.Autosize mah={300}>
          <Stack gap="sm">{columns.map(([key, label]) => <Checkbox key={key} label={label} checked={visible.includes(key)} onChange={() => onToggle(key)} />)}</Stack>
          {!columns.length && <Text c="dimmed" role="status">Ничего не найдено</Text>}
        </ScrollArea.Autosize>
        <Button variant="light" onClick={onReset}>Показать все</Button>
      </Stack>
    </Popover.Dropdown>
  </Popover>;
}
