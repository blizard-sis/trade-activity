"""Read-only instrument lookup through the official T-Invest MCP server."""

import json

import requests
import truststore

truststore.inject_into_ssl()
MCP_URL = "https://invest-public-api.tbank.ru/mcp"
INSTRUMENT_TOOLS = {
    "INSTRUMENT_TYPE_SHARE": "invest_get_share",
    "INSTRUMENT_TYPE_FUTURES": "invest_get_future",
    "INSTRUMENT_TYPE_BOND": "invest_get_bond",
    "INSTRUMENT_TYPE_CURRENCY": "invest_get_currency",
    "INSTRUMENT_TYPE_ETF": "invest_get_etf",
    "INSTRUMENT_TYPE_OPTION": "invest_get_option",
}


class TBankMCPClient:
    def __init__(self, token):
        if not token:
            raise RuntimeError("Для справочника нужен токен Т-Банка в config.json")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json, text/event-stream",
            }
        )
        self.sequence = 0

    def __enter__(self):
        try:
            result = self._rpc(
                "initialize",
                {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "trade-activity", "version": "1.0"},
                },
            )
            if result.get("protocolVersion") != "2025-03-26":
                raise RuntimeError("MCP Т-Банка вернул неподдерживаемую версию протокола")
            self._rpc("notifications/initialized", notification=True)
            return self
        except Exception:
            self.session.close()
            raise

    def __exit__(self, *args):
        self.session.close()

    def _rpc(self, method, params=None, *, notification=False):
        body = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            body["params"] = params
        if not notification:
            self.sequence += 1
            body["id"] = self.sequence
        try:
            with self.session.post(
                MCP_URL, json=body, timeout=(5, 25), stream=True, allow_redirects=False
            ) as response:
                if response.status_code in (401, 403):
                    raise RuntimeError(
                        "MCP Т-Банка отклонил авторизацию. Проверьте токен в config.json"
                    )
                if not 200 <= response.status_code < 300:
                    raise RuntimeError(f"MCP Т-Банка недоступен (HTTP {response.status_code})")
                session_id = response.headers.get("Mcp-Session-Id")
                if session_id:
                    self.session.headers["Mcp-Session-Id"] = session_id
                if notification:
                    return {}
                if "text/event-stream" in response.headers.get("Content-Type", ""):
                    message = self._read_event(response, body["id"])
                else:
                    message = response.json()
                if not isinstance(message, dict) or message.get("id") != body["id"]:
                    raise RuntimeError("Некорректный ответ MCP Т-Банка")
                if "error" in message:
                    raise RuntimeError("MCP Т-Банка не смог выполнить запрос справочника")
                if not isinstance(message.get("result"), dict):
                    raise RuntimeError("MCP Т-Банка не вернул результат")
                return message["result"]
        except requests.RequestException:
            raise RuntimeError(
                "Не удалось соединиться с MCP Т-Банка. Повторите запрос позже"
            ) from None
        except (ValueError, KeyError, TypeError):
            raise RuntimeError("Некорректный ответ MCP Т-Банка") from None

    @staticmethod
    def _read_event(response, request_id):
        data = []
        for raw in response.iter_lines():
            line = raw.decode("utf-8")
            if line.startswith("data:"):
                data.append(line[5:].lstrip(" "))
            elif not line and data:
                message = json.loads("\n".join(data))
                data = []
                if message.get("id") == request_id:
                    return message
        raise RuntimeError("MCP Т-Банка закрыл соединение без результата")

    def _tool(self, name, arguments):
        if name not in {"invest_find_instrument", *INSTRUMENT_TOOLS.values()}:
            raise ValueError("Метод не относится к справочнику инструментов")
        result = self._rpc("tools/call", {"name": name, "arguments": arguments})
        if result.get("isError"):
            raise RuntimeError("MCP Т-Банка не смог получить инструмент. Повторите поиск")
        if isinstance(result.get("structuredContent"), dict):
            return result["structuredContent"]
        for block in result.get("content", []):
            if block.get("type") == "text":
                try:
                    data = json.loads(block["text"])
                except (ValueError, KeyError):
                    continue
                if isinstance(data, dict):
                    return data
        raise RuntimeError("MCP Т-Банка не вернул данные инструмента")

    def search(self, query):
        result = self._tool(
            "invest_find_instrument",
            {
                "query": query,
                "responseView": ["IDENTIFIERS", "STATIC_DATA", "TRADING_FLAGS"],
            },
        )
        return [
            item
            for item in result.get("instruments", [])
            if item.get("instrumentKind") in INSTRUMENT_TOOLS
        ]

    def instrument(self, uid, kind):
        if kind not in INSTRUMENT_TOOLS:
            raise ValueError("Этот тип инструмента пока не поддерживается справочником")
        result = self._tool(
            INSTRUMENT_TOOLS[kind],
            {
                "instrumentId": uid,
                "idType": "INSTRUMENT_ID_TYPE_UID",
                "responseView": ["FULL"],
            },
        )
        instrument = result.get("instrument", {})
        if (
            instrument.get("uid", uid) != uid
            or not instrument.get("exchange")
            or not instrument.get("ticker")
        ):
            raise RuntimeError("MCP Т-Банка не вернул идентификатор, тикер или биржу инструмента")
        if instrument["exchange"].lower() == "unknown":
            raise ValueError(
                "У этого инструмента не определена биржа. Выберите другой режим торгов"
            )
        return {**instrument, "uid": uid, "instrumentKind": kind}
