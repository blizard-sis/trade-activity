import { formatDate, formatMoney, formatPrice, formatQuantity, resultClass } from "../../shared/format";

export function createColumns() {
  return [
    { key: "entry_at", label: "Вход", sort: "date", align: "text-left", render: (item) => formatDate(item.entry_at) },
    { key: "exit_at", label: "Выход", sort: "exit", align: "text-left", render: (item) => formatDate(item.exit_at) },
    { key: "account", label: "Счёт", sort: "account", align: "text-left", render: (item) => item.account_name },
    { key: "instrument", label: "Инструмент", sort: "ticker", align: "text-left", render: (item) => item.ticker || item.instrument_name },
    { key: "direction", label: "Направление", sort: "direction", render: (item) => <span className={item.direction}>{item.direction === "long" ? "Лонг" : "Шорт"}</span> },
    { key: "entry_quantity", label: "Объём входа", sort: "quantity", render: (item) => formatQuantity(item.entry_quantity) },
    { key: "remaining", label: "Остаток", render: (item) => formatQuantity(item.remaining) },
    { key: "entry_price", label: "Цена входа", sort: "entry", render: (item) => formatPrice(item.entry_price, item.price_precision, item.currency) },
    { key: "exit_price", label: "Цена выхода", render: (item) => formatPrice(item.exit_price, item.price_precision, item.currency) },
    { key: "gross_result", label: "Результат", render: (item) => formatMoney(item.gross_result) },
    { key: "commission", label: "Комиссия", render: (item) => formatMoney(item.commission) },
    { key: "net_result", label: "Чистыми", render: (item) => <span className={resultClass(item.net_result)}>{formatMoney(item.net_result)}</span> },
    { key: "status", label: "Статус", sort: "status", render: (item) => <span className={item.status}>{item.status === "closed" ? "Закрыта" : "Открыта"}</span> },
    { key: "order_count", label: "Ордеров", render: (item) => item.order_count },
  ];
}



export const COLUMN_LABELS = Object.fromEntries(createColumns().map(({ key, label }) => [key, label]));
export const DEFAULT_COLUMNS = Object.keys(COLUMN_LABELS);
