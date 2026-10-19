const EXIT_LABELS = {
  stop: "Стоп-лосс",
  take: "Тейк-профит",
  manual: "Вышел руками",
  mixed: "Смешанный выход",
};

export function exitReasonLabel(position) {
  if (position.status !== "closed") return "Позиция открыта";
  const assessment = position.exit_assessment;
  // Match report statistics: the legacy default is not evidence of a manual exit.
  if (assessment?.source === "default_rule") return "Не определено";
  return EXIT_LABELS[assessment?.reason] || "Не определено";
}
