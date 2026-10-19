export const DIRECTION_LABELS = { long: "Лонг", short: "Шорт" };

export function directionLabel(direction) {
  return DIRECTION_LABELS[direction] || direction;
}

export function netParts(summary) {
  return Object.entries(summary?.net || {});
}

export function planMeta(plan) {
  const parts = [];
  const ticker = plan.forecast?.ticker || plan.execution?.ticker;
  if (ticker) parts.push(ticker);
  if (plan.direction) parts.push(directionLabel(plan.direction));
  const summary = plan.summary || {};
  if (summary.positions) {
    parts.push(`${summary.positions} поз.`);
  }
  return parts.join(" · ");
}
