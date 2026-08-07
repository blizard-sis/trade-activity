const quantity = new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 9 });
const money = new Intl.NumberFormat("ru-RU", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});


export function formatQuantity(value) {
  return quantity.format(value);
}


export function formatMoney(value) {
  return value === null ? "—" : `${money.format(value)} ₽`;
}


export function formatPrice(value, precision, currency) {
  if (value === null) return "—";
  const formatted = new Intl.NumberFormat("ru-RU", {
    maximumFractionDigits: precision,
  }).format(value);
  return `${formatted} ${currency}`;
}


export function formatDate(value) {
  return value ? new Date(value).toLocaleString("ru-RU") : "—";
}


export function formatMonth(value) {
  return new Date(`${value}-01T00:00:00`).toLocaleDateString("ru-RU", {
    month: "long",
    year: "numeric",
  });
}


export function resultClass(value) {
  if (value > 0) return "positive";
  if (value < 0) return "negative";
  return "";
}

