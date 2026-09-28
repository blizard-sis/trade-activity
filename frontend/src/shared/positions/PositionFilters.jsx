import { TextInput } from "@mantine/core";
import { AccountPicker } from "../components/AccountPicker";
import { FilterSelect } from "../components/FilterSelect";

const DIRECTIONS = [
  { value: "long", label: "Лонг" },
  { value: "short", label: "Шорт" },
];
const STATUSES = [
  { value: "closed", label: "Закрытые" },
  { value: "open", label: "Открытые" },
];

export function PositionFilters({ accounts, filters, onChange, withLabels = false }) {
  return (
    <>
      <AccountPicker
        accounts={accounts}
        value={filters.account}
        label={withLabels ? "Платформы и счета" : undefined}
        onChange={(value) => onChange("account", value)}
      />
      <FilterSelect
        value={filters.direction}
        onChange={(value) => onChange("direction", value)}
        label={withLabels ? "Направление" : undefined}
        aria-label="Направление"
        placeholder="Лонг и шорт"
        data={DIRECTIONS}
      />
      <FilterSelect
        value={filters.status}
        onChange={(value) => onChange("status", value)}
        label={withLabels ? "Статус позиции" : undefined}
        aria-label="Статус позиции"
        placeholder="Все позиции"
        data={STATUSES}
      />
      <TextInput
        type="date"
        aria-label="Дата входа от"
        label={withLabels ? "Дата входа от" : undefined}
        value={filters.from}
        onChange={(event) => onChange("from", event.target.value)}
      />
      <TextInput
        type="date"
        aria-label="Дата входа до"
        label={withLabels ? "Дата входа до" : undefined}
        value={filters.to}
        onChange={(event) => onChange("to", event.target.value)}
      />
      <TextInput
        className="search"
        type="search"
        aria-label="Поиск инструмента"
        label={withLabels ? "Инструмент" : undefined}
        placeholder="Тикер или инструмент"
        value={filters.search}
        onChange={(event) => onChange("search", event.target.value)}
      />
    </>
  );
}
