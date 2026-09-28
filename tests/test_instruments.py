import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

from backend import create_app
from backend.brokers.tbank_mcp import TBankMCPClient
from backend.storage import database

SHARE = "INSTRUMENT_TYPE_SHARE"
FUTURE = "INSTRUMENT_TYPE_FUTURES"


class InstrumentLinksTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        db_patch = patch.object(database, "DATABASE", Path(temp.name) / "test.sqlite3")
        db_patch.start()
        self.addCleanup(db_patch.stop)
        with patch("backend.load_config", return_value={"tbank_token": "test-token"}):
            self.app = create_app()
        self.client = self.app.test_client()
        mcp_patch = patch("backend.services.instruments.TBankMCPClient")
        self.mcp = mcp_patch.start().return_value.__enter__.return_value
        self.addCleanup(mcp_patch.stop)
        self.mcp.instrument.side_effect = lambda uid, kind: {
            "uid": uid,
            "ticker": "SBER" if kind == SHARE else "SBERF",
            "name": "Сбербанк",
            "exchange": "moex_mrng_evng_e_wknd_dlr" if kind == SHARE else "forts_futures_weekend",
            "classCode": "TQBR" if kind == SHARE else "SPBFUT",
            "lot": 10,
            "minPriceIncrement": {"value": "0.01"},
            "minPriceIncrementAmount": {"value": "1"},
        }

    def select(self, uid, kind):
        response = self.client.post("/api/instruments/select", json={"id": uid, "kind": kind})
        self.assertEqual(response.status_code, 200)
        return response.get_json()

    def pair(self):
        return {
            "forecast": self.select("share-uid", SHARE),
            "execution": self.select("future-uid", FUTURE),
        }

    def test_persist_edit_refresh_delete_and_no_changes_to_trades(self):
        values = self.pair()
        response = self.client.post("/api/instruments/links", json=values)
        self.assertEqual(response.status_code, 201)
        link_id = response.get_json()["id"]
        database.initialize()
        saved = self.client.get("/api/instruments/links").get_json()[0]
        self.assertEqual(saved["forecast"]["exchange"], "MOEX")
        self.assertEqual(saved["execution"]["exchange_code"], "forts_futures_weekend")
        self.assertEqual(saved["execution"]["tick_value"], "1")
        self.assertNotIn("test-token", json.dumps(saved))
        values["execution"] = self.select("next-contract", FUTURE)
        updated = self.client.put(f"/api/instruments/links/{link_id}", json=values)
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.get_json()["id"], link_id)
        self.assertEqual(
            self.client.post(f"/api/instruments/links/{link_id}/refresh").status_code, 200
        )
        self.assertEqual(database.get_trades({}), [])
        self.assertEqual(self.client.delete(f"/api/instruments/links/{link_id}").status_code, 204)
        self.assertEqual(self.client.get("/api/instruments/links").get_json(), [])

    def test_duplicate_and_missing_links(self):
        pair = self.pair()
        self.assertEqual(self.client.post("/api/instruments/links", json=pair).status_code, 201)
        self.assertEqual(self.client.post("/api/instruments/links", json=pair).status_code, 400)
        self.assertEqual(
            self.client.put("/api/instruments/links/missing", json=pair).status_code, 404
        )
        self.assertEqual(self.client.delete("/api/instruments/links/missing").status_code, 404)
        self.assertEqual(
            self.client.post("/api/instruments/links/missing/refresh").status_code, 404
        )

    def test_only_selected_catalog_data_is_saved(self):
        for body in (
            None,
            [],
            {},
            {"forecast": "SBER"},
            {"forecast": {"provider": "tbank", "id": "missing"}},
        ):
            self.assertEqual(self.client.post("/api/instruments/links", json=body).status_code, 400)
        pair = self.pair()
        pair["forecast"]["exchange"] = "Forged exchange"
        pair["execution"]["ticker"] = "Forged ticker"
        saved = self.client.post("/api/instruments/links", json=pair).get_json()
        self.assertEqual(saved["forecast"]["exchange"], "MOEX")
        self.assertEqual(saved["execution"]["ticker"], "SBERF")

    def test_refresh_failure_keeps_both_previous_snapshots(self):
        saved = self.client.post("/api/instruments/links", json=self.pair()).get_json()
        original = self.client.get("/api/instruments/links").get_json()
        self.mcp.instrument.side_effect = [
            {"uid": "share-uid", "ticker": "CHANGED", "name": "New", "exchange": "moex"},
            RuntimeError("MCP unavailable"),
        ]
        response = self.client.post(f"/api/instruments/links/{saved['id']}/refresh")
        self.assertEqual(response.status_code, 502)
        self.assertEqual(self.client.get("/api/instruments/links").get_json(), original)

    def test_search_preserves_distinct_trading_modes(self):
        self.mcp.search.return_value = [
            dict(uid="one", ticker="SBER", name="Сбербанк", classCode="37M", instrumentKind=SHARE),
            dict(
                uid="two",
                ticker="SBER",
                name="Сбербанк",
                classCode="TQBR",
                instrumentKind=SHARE,
                apiTradeAvailableFlag=True,
            ),
        ]
        items = self.client.get("/api/instruments/search?q=SBER").get_json()
        self.assertEqual([item["id"] for item in items], ["two", "one"])
        self.assertEqual(self.client.get("/api/instruments/search?q=S").status_code, 400)


class MCPTransportTests(unittest.TestCase):
    @staticmethod
    def response(body, *, status=200, headers=None, lines=None):
        response = Mock()
        response.status_code = status
        response.headers = headers or {"Content-Type": "application/json"}
        response.json.return_value = body
        response.iter_lines.return_value = iter(lines or [])
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        return response

    def test_initialization_session_and_sse_ignores_notifications(self):
        responses = [
            self.response(
                {"id": 1, "result": {"protocolVersion": "2025-03-26"}},
                headers={"Mcp-Session-Id": "session-id"},
            ),
            self.response({}, status=202),
            self.response(
                {},
                headers={"Content-Type": "text/event-stream"},
                lines=[
                    b": keepalive",
                    b"",
                    b'data: {"method":"notifications/message"}',
                    b"",
                    b'data: {"id":2,"result":{"content":[{"type":"text","text":"{\\"instruments\\":[]}"}]}}',
                    b"",
                ],
            ),
        ]
        client = TBankMCPClient("secret")
        with patch.object(client.session, "post", side_effect=responses) as post:
            with client:
                self.assertEqual(client.search("SBER"), [])
                self.assertEqual(client.session.headers["Mcp-Session-Id"], "session-id")
        payloads = [call.kwargs["json"] for call in post.call_args_list]
        self.assertNotIn("id", payloads[1])
        self.assertEqual(payloads[2]["params"]["name"], "invest_find_instrument")

    def test_auth_network_and_tool_errors_do_not_expose_secrets(self):
        client = TBankMCPClient("secret")
        self.addCleanup(client.session.close)
        with patch.object(client.session, "post", return_value=self.response({}, status=401)):
            with self.assertRaisesRegex(RuntimeError, "авторизацию"):
                client._rpc("initialize")
        with patch.object(client.session, "post", side_effect=requests.ConnectionError("secret")):
            with self.assertRaises(RuntimeError) as caught:
                client._rpc("initialize")
            self.assertNotIn("secret", str(caught.exception))
        with patch.object(
            client,
            "_rpc",
            return_value={"isError": True, "content": [{"type": "text", "text": "secret"}]},
        ):
            with self.assertRaises(RuntimeError) as caught:
                client.search("SBER")
            self.assertNotIn("secret", str(caught.exception))

    def test_detail_accepts_missing_uid_but_rejects_conflicting_uid_and_unknown_exchange(self):
        client = TBankMCPClient("secret")
        self.addCleanup(client.session.close)
        with patch.object(
            client, "_tool", return_value={"instrument": {"ticker": "SBER", "exchange": "moex"}}
        ):
            self.assertEqual(client.instrument("expected", SHARE)["uid"], "expected")
        with patch.object(
            client,
            "_tool",
            return_value={"instrument": {"uid": "wrong", "ticker": "SBER", "exchange": "moex"}},
        ):
            with self.assertRaises(RuntimeError):
                client.instrument("expected", SHARE)
        with patch.object(
            client, "_tool", return_value={"instrument": {"ticker": "SBER", "exchange": "unknown"}}
        ):
            with self.assertRaises(ValueError):
                client.instrument("expected", SHARE)

    def test_only_read_only_catalog_tools_are_allowed(self):
        client = TBankMCPClient("secret")
        self.addCleanup(client.session.close)
        with self.assertRaises(ValueError):
            client._tool("invest_create_order", {})


if __name__ == "__main__":
    unittest.main()
