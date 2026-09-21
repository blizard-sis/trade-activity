import { MultiSelect } from "@mantine/core";

export function AccountPicker({ accounts, value, onChange }) {
  return <MultiSelect
    aria-label="Платформы и счета"
    placeholder="Все платформы и счета"
    data={accounts.map(({ id, name }) => ({ value: id, label: name }))}
    value={Array.isArray(value) ? value : value ? [value] : []}
    onChange={onChange}
    searchable clearable hidePickedOptions={false}
    nothingFoundMessage="Ничего не найдено"
    clearButtonProps={{ 'aria-label': 'Все платформы и счета' }}
    className="account-filter"
  />;
}
