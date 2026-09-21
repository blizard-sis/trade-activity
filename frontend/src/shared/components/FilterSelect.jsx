import { Select } from "@mantine/core";

export function FilterSelect({ value, onChange, ...props }) {
  return <Select value={value || null} onChange={(next) => onChange(next || "")} allowDeselect clearable {...props}
    nothingFoundMessage="Ничего не найдено" clearButtonProps={{ 'aria-label': 'Сбросить фильтр' }} />;
}
