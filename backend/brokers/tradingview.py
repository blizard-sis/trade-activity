"""Read TradingView's paired trade report without recomputing futures PnL."""
import csv
import io
import math
import re
from datetime import datetime


def number(value):
    try:
        result = float(value)
    except (ValueError, TypeError):
        raise ValueError(f"Некорректное число: {value}") from None
    if not math.isfinite(result):
        raise ValueError("Число должно быть конечным")
    return result


def timestamp(value):
    # CSV contains wall-clock time without a timezone. Preserve it as exported.
    for pattern in ("%b %d, %Y, %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, pattern).isoformat()
        except ValueError:
            pass
    raise ValueError(f"Неизвестный формат даты: {value}")


def parse_files(files, account_id, account_name):
    reports, orders, balances, ignored = [], {}, [], []
    currency = None
    for filename, content in files:
        try:
            reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
            headers = set(reader.fieldnames or [])
            rows = list(reader)
        except (UnicodeError, csv.Error):
            raise ValueError(f"{filename}: ожидается CSV в UTF-8") from None
        if any(None in row or None in row.values() for row in rows):
            raise ValueError(f"{filename}: повреждённая строка CSV")
        if {"Trade number", "Type", "Date and time", "Symbol", "Order ID", "Price", "Size (qty)"} <= headers:
            pnl = [h for h in headers if re.fullmatch(r"Net PnL [A-Z]{3}", h)]
            if len(pnl) != 1 or f"Commission {pnl[0][-3:]}" not in headers:
                raise ValueError("В истории сделок нужны Net PnL и Commission с валютой")
            if currency and currency != pnl[0][-3:]:
                raise ValueError("Загрузите историю одного счёта с одной валютой")
            currency = pnl[0][-3:]
            reports.extend(rows)
        elif {"Order ID", "Closing time", "Fill price", "Status"} <= headers:
            orders.update({r["Order ID"]: r for r in rows if r["Status"] == "Filled"})
        elif {"Time", "Action", "Realized PnL (value)", "Realized PnL (currency)"} <= headers:
            balances.extend(rows)
        elif ({"Time", "Text"} <= headers or {"Unrealized PnL (value)", "Avg fill price"} <= headers
              or {"Order ID", "Status", "Expiry"} <= headers):
            ignored.append(filename)
        else:
            raise ValueError(f"{filename}: неизвестная вкладка TradingView")
    if not reports:
        raise ValueError("Добавьте непустой файл paper-trading-trade-history…csv (История сделок)")
    groups = {}
    for row in reports:
        group = groups.setdefault((row["Symbol"], row["Trade number"]), {})
        kind = row["Type"]
        if kind not in ("Entry long", "Entry short", "Exit long", "Exit short"):
            raise ValueError(f"Неизвестный тип сделки: {kind}")
        role = kind.split()[0]
        if role in group and group[role] != row:
            raise ValueError("Повторяющиеся номера сделок с разными данными: загрузите одну выгрузку счёта")
        group[role] = row
    positions = []
    for (symbol, _), pair in groups.items():
        if set(pair) != {"Entry", "Exit"}:
            raise ValueError(f"{symbol}: отсутствует строка входа или выхода")
        entry, closing = pair["Entry"], pair["Exit"]
        direction = entry["Type"].split()[1]
        if closing["Type"] != f"Exit {direction}" or not entry["Order ID"]:
            raise ValueError(f"{symbol}: несогласованные вход и выход")
        qty = number(entry["Size (qty)"])
        if qty <= 0 or qty != number(closing["Size (qty)"]):
            raise ValueError(f"{symbol}: неподдерживаемые количества входа и выхода")
        closed = closing["Date and time"] != "Open"
        entry_at = timestamp(entry["Date and time"])
        exit_at = timestamp(closing["Date and time"]) if closed else None
        for row, role in ((entry, "entry"), (closing, "exit")):
            order = orders.get(row["Order ID"])
            if order and order.get("Symbol") == symbol:
                exact = timestamp(order["Closing time"])
                if exact[:16] == (entry_at if role == "entry" else exit_at or "")[:16]:
                    if role == "entry":
                        entry_at = exact
                    else:
                        exit_at = exact
        if closed and exit_at < entry_at:
            raise ValueError(f"{symbol}: выход раньше входа")
        net = number(closing[f"Net PnL {currency}"]) if closed else None
        commission = number(closing[f"Commission {currency}"])
        if commission < 0:
            raise ValueError("Отрицательная комиссия не поддерживается")
        price = number(entry["Price"])
        exit_price = number(closing["Price"]) if closed else None
        price_currency = ""
        matches = []
        for balance in balances:
            match = re.fullmatch(r"Close (long|short) position for symbol (\S+) at price (\S+) for (\S+) units\. Position AVG Price was (\S+), currency: ([A-Z]{3}), rate: (\S+), point value: (\S+)", balance["Action"])
            if not match or match[2] != symbol:
                continue
            price_currency = match[6]
            if (closed and match[1] == direction and timestamp(balance["Time"])[:16] == exit_at[:16]
                    and number(match[3]) == exit_price and number(match[4]) == qty
                    and math.isclose(number(match[5]), price, abs_tol=0.000001)
                    and balance["Realized PnL (currency)"] == currency):
                matches.append(balance)
        if len(matches) == 1 and commission == 0:
            exact_net = number(matches[0]["Realized PnL (value)"])
            if abs(exact_net - net) > 0.011:
                raise ValueError(f"{symbol}: результат расходится с историей баланса")
            net = exact_net
            exit_at = timestamp(matches[0]["Time"])
        positions.append(dict(
            id=f"{account_id}:{symbol}:{entry['Order ID']}:{direction}", account_id=account_id,
            account_name=account_name, instrument_uid=f"tradingview:{symbol}", ticker=symbol,
            instrument_name=symbol, direction=direction, entry_at=entry_at, exit_at=exit_at,
            entry_quantity=qty, exit_quantity=qty if closed else 0, remaining=0 if closed else qty,
            entry_price=price, exit_price=exit_price, exit_prices=[exit_price] if closed else [],
            currency=price_currency, price_precision=9, commission=commission,
            commission_currency=currency, gross_result=net + commission if closed else None,
            net_result=net, result_currency=currency, order_count=None,
            status="closed" if closed else "open",
        ))
    if len({p["id"] for p in positions}) != len(positions):
        raise ValueError("Несколько позиций с одним входом: этот формат частичных выходов пока не поддерживается")
    return positions, ignored
