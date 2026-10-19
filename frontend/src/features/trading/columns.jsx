import {
  formatDate,
  formatMoney,
  formatPrice,
  formatQuantity,
  resultClass,
} from "../../shared/format";

import { exitReasonLabel } from "./model";

export const POSITION_COLUMNS = [
  {
    key: "entry_at",
    label: "Вход",
    sort: "date",
    align: "text-left",
    render: (item) => formatDate(item.entry_at),
  },
  {
    key: "exit_at",
    label: "Выход",
    sort: "exit",
    align: "text-left",
    render: (item) => formatDate(item.exit_at),
  },
  {
    key: "account",
    label: "Платформа — счёт",
    sort: "account",
    align: "text-left",
    render: (item) => item.account_name,
  },
  {
    key: "instrument",
    label: "Инструмент",
    sort: "ticker",
    align: "text-left",
    render: (item) => item.ticker || item.instrument_name,
  },
  {
    key: "direction",
    label: "Направление",
    sort: "direction",
    render: (item) => (
      <span className={item.direction}>{item.direction === "long" ? "Лонг" : "Шорт"}</span>
    ),
  },
  {
    key: "entry_quantity",
    label: "Объём входа",
    sort: "quantity",
    render: (item) => formatQuantity(item.entry_quantity),
  },
  {
    key: "remaining",
    label: "Остаток",
    sort: "remaining",
    render: (item) => formatQuantity(item.remaining),
  },
  {
    key: "entry_price",
    label: "Цена входа",
    sort: "entry",
    render: (item) => formatPrice(item.entry_price, item.price_precision, item.currency),
  },
  {
    key: "exit_price",
    sort: "exit_price",
    label: "Цена выхода",
    render: (item) => formatPrice(item.exit_price, item.price_precision, item.currency),
  },
  {
    key: "gross_result",
    sort: "gross_result",
    label: "Результат",
    render: (item) => formatMoney(item.gross_result, item.result_currency),
  },
  {
    key: "commission",
    sort: "commission",
    label: "Комиссия",
    render: (item) => formatMoney(item.commission, item.commission_currency),
  },
  {
    key: "net_result",
    sort: "net_result",
    label: "Чистыми",
    render: (item) => (
      <span className={resultClass(item.net_result)}>
        {formatMoney(item.net_result, item.result_currency)}
      </span>
    ),
  },
  {
    key: "status",
    label: "Статус",
    sort: "status",
    render: (item) => (
      <span className={item.status}>{item.status === "closed" ? "Закрыта" : "Открыта"}</span>
    ),
  },
  {
    key: "exit_reason",
    sort: "exit_reason",
    label: "Причина выхода",
    align: "text-left",
    render: exitReasonLabel,
  },
  {
    key: "order_count",
    label: "Ордеров",
    sort: "order_count",
    render: (item) => item.order_count ?? "—",
  },
  {
    key: "journal",
    label: "План",
    align: "text-left",
    render: (item) => {
      const href = item.plan
        ? `/journal?plan=${encodeURIComponent(item.plan.id)}`
        : `/journal?position=${encodeURIComponent(item.id)}`;
      return (
        <a className="journal-link" href={href}>
          {item.plan ? "Открыть план ↗" : "Создать план ↗"}
        </a>
      );
    },
  },
];

export const COLUMN_LABELS = Object.fromEntries(
  POSITION_COLUMNS.map(({ key, label }) => [key, label]),
);
export const DEFAULT_COLUMNS = Object.keys(COLUMN_LABELS);
