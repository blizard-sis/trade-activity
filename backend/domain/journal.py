"""Estimate an exit from plan levels and fills, independently of storage or HTTP."""

from decimal import Decimal, InvalidOperation


JOURNAL_FIELDS = ("entry_note", "exit_note", "planned_stop", "planned_take")


def _number(value):
    try:
        # Grouping spaces include NBSP and narrow NBSP from copied prices.
        number = Decimal("".join(str(value).split()).replace(",", "."))
        return number if number.is_finite() else None
    except InvalidOperation:
        return None


def assess_exit(position):
    def result(reason, label, explanation, inferred=False):
        if reason == "unknown":
            return dict(reason="manual", label="Вышел руками",
                        explanation="По правилу журнала: если стоп или тейк не определён, выход считается ручным.",
                        inferred=True, source="default_rule")
        return dict(reason=reason, label=label, explanation=explanation,
                    inferred=inferred, source="plan_prices" if inferred else "insufficient_data")

    if position["status"] != "closed":
        return result("open", "Позиция открыта", "Причина выхода появится после полного закрытия.")

    stop = _number(position.get("planned_stop"))
    take = _number(position.get("planned_take"))
    prices = [_number(value) for value in position.get("exit_prices", [])]
    if not prices or any(price is None for price in prices):
        return result("unknown", "Не определено", "Нет цен исполнений выхода.")
    if stop is None and take is None:
        return result("unknown", "Не определено", "Укажите плановые стоп и тейк и сохраните разбор.")

    sign = 1 if position["direction"] == "long" else -1
    if stop is not None and take is not None and sign * stop >= sign * take:
        return result("unknown", "Не определено", "Проверьте уровни: для лонга стоп ниже тейка, для шорта — выше.")

    reasons = set()
    for price in prices:
        if stop is not None and sign * price <= sign * stop:
            reasons.add("stop")
        elif take is not None and sign * price >= sign * take:
            reasons.add("take")
        elif stop is not None and take is not None:
            reasons.add("manual")
        else:
            reasons.add("unknown")

    if len(reasons) > 1:
        return result("mixed", "Смешанный выход", "Части позиции закрыты в разных зонах плана; единую причину определить нельзя.", True)
    reason = reasons.pop()
    labels = {"stop": "Стоп-лосс", "take": "Тейк-профит", "manual": "Вышел руками"}
    if reason not in labels:
        return result("unknown", "Не определено", "Цена не достигла указанного уровня. Для оценки нужны оба уровня плана.")
    return result(reason, labels[reason], "Оценка по ценам всех исполнений и сохранённым уровням плана; тип заявки брокером не подтверждён.", True)
