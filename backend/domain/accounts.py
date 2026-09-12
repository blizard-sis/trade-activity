def selected_accounts(filters):
    if hasattr(filters, "getlist"):
        values = filters.getlist("account")
    else:
        values = filters.get("account") or []
        if isinstance(values, str):
            values = [values]
    return list(dict.fromkeys(value for value in values if value))


def account_source(account):
    platform = "TradingView" if account["id"].startswith("tradingview:") else "T-Bank"
    name = account["name"]
    if platform == "TradingView":
        name = name.removeprefix("TradingView · ")
    return {**account, "platform": platform, "account_name": name, "name": f"{platform} — {name}"}
