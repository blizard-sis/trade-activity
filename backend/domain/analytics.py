import re
from dataclasses import dataclass, field
from itertools import groupby

from .winrate import exit_category

FUTURES_TICKER = re.compile(r"^(.+)[FGHJKMNQUVXZ]\d$")


def ticker_family(ticker):
    match = FUTURES_TICKER.match(ticker)
    return match.group(1) if match else ticker


def price_precision(price):
    text = f"{price:.9f}".rstrip("0").rstrip(".")
    return len(text.split(".")[1]) if "." in text else 0


def allocated(value, trade, quantity):
    return value / trade["quantity"] * quantity if trade["quantity"] else 0


@dataclass
class OpenPosition:
    position_id: str
    account_id: str
    account_name: str
    instrument_uid: str
    ticker: str
    instrument_name: str
    direction: str
    entry_side: str
    entry_at: str
    entry_trade_id: str
    currency: str
    commission_currency: str
    result_currency: str
    entry_quantity: int = 0
    exit_quantity: int = 0
    remaining: int = 0
    entry_value: float = 0
    exit_value: float = 0
    commission: float = 0
    cash_flow: float = 0
    exit_at: str | None = None
    price_precision: int = 0
    orders: set = field(default_factory=set)
    exit_prices: list = field(default_factory=list)

    @classmethod
    def start(cls, trade, quantity):
        direction = "long" if trade["side"] == "buy" else "short"
        position = cls(
            position_id=f"{trade['account_id']}:{trade['instrument_uid']}:{trade['trade_id']}:{direction}",
            account_id=trade["account_id"],
            account_name=trade["account_name"],
            instrument_uid=trade["instrument_uid"],
            ticker=trade["ticker"],
            instrument_name=trade["instrument_name"],
            direction=direction,
            entry_side=trade["side"],
            entry_at=trade["executed_at"],
            entry_trade_id=trade["trade_id"],
            currency=trade["currency"],
            commission_currency=trade["commission_currency"],
            result_currency=trade["payment_currency"],
        )
        position.add_entry(trade, quantity)
        return position

    def add_entry(self, trade, quantity):
        self.entry_quantity += quantity
        self.remaining += quantity
        self.entry_value += trade["price"] * quantity
        self._add_costs(trade, quantity)

    def add_exit(self, trade, quantity):
        self.exit_prices.append(trade["price"])
        self.exit_quantity += quantity
        self.remaining -= quantity
        self.exit_value += trade["price"] * quantity
        self.exit_at = trade["executed_at"]
        self._add_costs(trade, quantity)

    def _add_costs(self, trade, quantity):
        self.commission += abs(allocated(trade["commission"], trade, quantity))
        self.cash_flow += allocated(trade["payment"], trade, quantity)
        self.price_precision = max(self.price_precision, price_precision(trade["price"]))
        self.orders.add(trade["operation_id"])

    def as_dict(self, status):
        closed = status == "closed"
        return {
            "id": self.position_id,
            "account_id": self.account_id,
            "account_name": self.account_name,
            "instrument_uid": self.instrument_uid,
            "ticker": self.ticker,
            "instrument_name": self.instrument_name,
            "direction": self.direction,
            "entry_at": self.entry_at,
            "entry_trade_id": self.entry_trade_id,
            "exit_at": self.exit_at,
            "entry_quantity": self.entry_quantity,
            "exit_quantity": self.exit_quantity,
            "remaining": self.remaining,
            "entry_price": self.entry_value / self.entry_quantity,
            "exit_price": self.exit_value / self.exit_quantity if self.exit_quantity else None,
            "exit_prices": self.exit_prices,
            "currency": self.currency,
            "price_precision": self.price_precision,
            "commission": self.commission,
            "commission_currency": self.commission_currency,
            "gross_result": self.cash_flow if closed else None,
            "net_result": self.cash_flow - self.commission if closed else None,
            "result_currency": self.result_currency,
            "order_count": len(self.orders),
            "status": status,
        }


def build_positions(trades):
    def group_key(trade):
        return trade["account_id"], trade["instrument_uid"]

    def sort_key(trade):
        return *group_key(trade), trade["executed_at"], trade["trade_id"]

    positions = []

    for _, instrument_trades in groupby(sorted(trades, key=sort_key), key=group_key):
        current = None

        for trade in instrument_trades:
            quantity = trade["quantity"]
            while quantity:
                if current is None:
                    current = OpenPosition.start(trade, quantity)
                    quantity = 0
                elif trade["side"] == current.entry_side:
                    current.add_entry(trade, quantity)
                    quantity = 0
                else:
                    closing_quantity = min(quantity, current.remaining)
                    current.add_exit(trade, closing_quantity)
                    quantity -= closing_quantity

                    if current.remaining == 0:
                        positions.append(current.as_dict("closed"))
                        current = None

        if current:
            positions.append(current.as_dict("open"))

    return positions


def filter_positions(positions, filters):
    predicates = {
        "direction": lambda item, value: item["direction"] == value,
        "status": lambda item, value: item["status"] == value,
        "from": lambda item, value: item["entry_at"] >= value,
        "to": lambda item, value: item["entry_at"][:10] <= value,
    }
    for name, predicate in predicates.items():
        if filters.get(name):
            positions = [item for item in positions if predicate(item, filters[name])]

    return positions


def sort_positions(positions, filters):
    sort_fields = {
        "date": "entry_at",
        "exit": "exit_at",
        "account": "account_name",
        "ticker": "ticker",
        "direction": "direction",
        "quantity": "entry_quantity",
        "remaining": "remaining",
        "entry": "entry_price",
        "exit_price": "exit_price",
        "gross_result": "gross_result",
        "commission": "commission",
        "net_result": "net_result",
        "status": "status",
        "order_count": "order_count",
    }
    exit_labels = {
        "stop": "Стоп-лосс",
        "take": "Тейк-профит",
        "manual": "Вышел руками",
        "mixed": "Смешанный выход",
        "unknown": "Не определено",
    }
    sort = filters.get("sort")
    field = sort_fields.get(sort, "entry_at")

    def sort_value(position):
        if sort == "exit_reason":
            return (
                exit_labels[exit_category(position)]
                if position["status"] == "closed"
                else "Позиция открыта"
            ).casefold()
        value = position.get(field)
        if field == "ticker":
            value = value or position.get("instrument_name")
        return value.casefold() if isinstance(value, str) else value

    # Partition first so missing values stay last in both sort directions.
    populated = []
    missing = []
    for position in positions:
        value = sort_value(position)
        if value is None or value == "":
            missing.append(position)
        else:
            populated.append((value, position))
    populated.sort(key=lambda item: item[0], reverse=filters.get("direction_sort") != "asc")
    return [position for _, position in populated] + missing
