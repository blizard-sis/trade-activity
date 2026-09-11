from ..domain.analytics import build_positions, filter_positions, monthly_report
from ..storage import database


def get_positions(filters):
    return filter_positions(build_positions(database.get_trades(filters)), filters)


def get_monthly_report(filters):
    return monthly_report(build_positions(database.get_trades(filters)), filters)
