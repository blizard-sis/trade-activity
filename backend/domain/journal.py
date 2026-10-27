"""Estimate an exit from plan levels and fills, independently of storage or HTTP."""

from decimal import Decimal

from .numbers import parse_number

JOURNAL_FIELDS = ("entry_note", "exit_note", "planned_stop", "planned_take")
EXIT_REASON_LABELS = {
    "take": "Тейк-профит",
    "stop": "Стоп-лосс",
    "manual": "Вышел руками",
    "mixed": "Смешанный выход",
    "unknown": "Не определено",
}
TOLERANCE_TICKS = 2


def _number(value):
    return parse_number(value)


def _tick_size(*values):
    places = 0
    for value in values:
        number = _number(value)
        if number is None:
            continue
        exponent = number.as_tuple().exponent
        if exponent < 0:
            places = max(places, -exponent)
    return Decimal(1).scaleb(-places) if places else Decimal(1)


def assess_exit(position):
    def result(reason, label, explanation, inferred=False):
        if reason == "unknown":
            return dict(
                reason="manual",
                label="Вышел руками",
                explanation="По правилу журнала: если стоп или тейк не определён, выход считается ручным.",
                inferred=True,
                source="default_rule",
            )
        return dict(
            reason=reason,
            label=label,
            explanation=explanation,
            inferred=inferred,
            source="plan_prices" if inferred else "insufficient_data",
        )

    if position["status"] != "closed":
        return result("open", "Позиция открыта", "Причина выхода появится после полного закрытия.")

    stop = _number(position.get("planned_stop"))
    take = _number(position.get("planned_take"))
    prices = [_number(value) for value in position.get("exit_prices", [])]
    if not prices or any(price is None for price in prices):
        return result("unknown", "Не определено", "Нет цен исполнений выхода.")
    if stop is None and take is None:
        return result(
            "unknown", "Не определено", "Укажите плановые стоп и тейк и сохраните разбор."
        )

    direction = position["direction"]
    sign = Decimal(1) if direction == "long" else Decimal(-1)
    if stop is not None and take is not None and sign * stop >= sign * take:
        return result(
            "unknown",
            "Не определено",
            "Проверьте уровни: для лонга стоп ниже тейка, для шорта — выше.",
        )

    planned_entry = _number(position.get("planned_entry"))
    actual_entry = _number(position.get("entry_price"))
    if planned_entry is None:
        planned_entry = actual_entry
    if planned_entry is None or actual_entry is None:
        return result("unknown", "Не определено", "Не хватает цены входа.")

    take_distance = sign * (take - planned_entry) if take is not None else None
    stop_distance = sign * (planned_entry - stop) if stop is not None else None
    if (take_distance is not None and take_distance <= 0) or (
        stop_distance is not None and stop_distance <= 0
    ):
        return result(
            "unknown",
            "Не определено",
            "Проверьте уровни: стоп и тейк должны быть по разные стороны от входа.",
        )

    tolerance = _tick_size(planned_entry, stop, take) * TOLERANCE_TICKS
    reasons = set()
    for price in prices:
        move = sign * (price - actual_entry)
        if take_distance is not None and move >= take_distance - tolerance:
            reasons.add("take")
        elif stop_distance is not None and move <= -stop_distance + tolerance:
            reasons.add("stop")
        else:
            reasons.add("manual")

    if len(reasons) > 1:
        return result(
            "mixed",
            "Смешанный выход",
            "Части позиции закрыты в разных зонах плана; единую причину определить нельзя.",
            True,
        )
    reason = reasons.pop()
    if reason == "take":
        explanation = (
            "Фактическое движение от входа дошло до планового тейка "
            f"(допуск {TOLERANCE_TICKS} тика)."
        )
    elif reason == "stop":
        explanation = (
            "Фактическое движение от входа дошло до планового стопа "
            f"(допуск {TOLERANCE_TICKS} тика)."
        )
    else:
        explanation = "Фактическое движение от входа осталось между плановыми стопом и тейком."
    return result(reason, EXIT_REASON_LABELS[reason], explanation, True)
