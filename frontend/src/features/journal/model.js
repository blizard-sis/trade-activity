export const FIELDS = ["entry_note", "exit_note", "planned_stop", "planned_take"];

export function exitLabel(position) {
  const labels = { stop: "Стоп-лосс", take: "Тейк-профит", manual: "Вышел руками", mixed: "Смешанный выход", open: "Позиция открыта" };
  return labels[position.exit_assessment?.reason] || (position.status === "closed" ? "Вышел руками" : "Позиция открыта");
}

export function exitTone(position) {
  if (position.status !== "closed" || !Number.isFinite(position.net_result) || position.net_result === 0) return "";
  const direction = position.net_result > 0 ? "profit" : "loss";
  const intensity = ["take", "stop"].includes(position.exit_assessment?.reason) ? "strong" : "soft";
  return `exit-${direction}-${intensity}`;
}
