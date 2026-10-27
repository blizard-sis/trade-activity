import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend import create_app
from backend.services import plans as plans_service
from backend.storage import database

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32


class PlansApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "plans.sqlite3"
        self.attachments = Path(self.temp.name) / "attachments"
        db_patch = patch.object(database, "DATABASE", self.path)
        db_patch.start()
        self.addCleanup(db_patch.stop)
        attachments_patch = patch.object(plans_service, "ATTACHMENTS_DIR", self.attachments)
        attachments_patch.start()
        self.addCleanup(attachments_patch.stop)
        with patch("backend.load_config", return_value={}):
            self.client = create_app().test_client()

        database.save_account({"id": "a", "name": "Test account"})
        database.save_trades(
            [
                self.trade("buy", "buy", 100, -100, "2026-09-01T10:00:00Z"),
                self.trade("sell", "sell", 110, 110, "2026-09-02T10:00:00Z"),
            ]
        )
        self.position_id = "a:instrument:buy:long"
        database.save_journal(
            self.position_id,
            {
                "entry_note": "План входа",
                "exit_note": "Вышел по тейку",
                "planned_stop": "95",
                "planned_take": "110",
            },
        )

    @staticmethod
    def trade(trade_id, side, price, payment, executed_at):
        trade = dict.fromkeys(database.TRADE_FIELDS, "")
        trade.update(
            account_id="a",
            trade_id=trade_id,
            operation_id=trade_id,
            instrument_uid="instrument",
            ticker="TEST",
            instrument_name="Test instrument",
            side=side,
            quantity=1,
            price=price,
            currency="rub",
            commission=1,
            commission_currency="rub",
            payment=payment,
            payment_currency="rub",
            executed_at=executed_at,
        )
        return trade

    def create_from_position(self):
        response = self.client.post("/api/plans", json={"position_id": self.position_id})
        self.assertEqual(response.status_code, 201, response.get_json())
        return response.get_json()

    def test_create_from_position_prefills_and_links(self):
        self.assertEqual(len(self.client.get("/api/plans/available-positions").get_json()), 1)
        plan = self.create_from_position()

        self.assertEqual(plan["thesis"], "План входа")
        self.assertEqual(plan["review"], "Вышел по тейку")
        self.assertEqual(plan["planned_stop"], 95.0)
        self.assertEqual(plan["planned_take"], 110.0)
        self.assertEqual(plan["direction"], "long")
        self.assertEqual(plan["account_id"], "a")
        self.assertEqual(plan["execution"]["provider"], "tbank")
        self.assertEqual([position["id"] for position in plan["positions"]], [self.position_id])
        self.assertEqual(plan["summary"]["net"], {"RUB": 8.0})
        self.assertEqual(self.client.get("/api/plans/available-positions").get_json(), [])

        listed = self.client.get("/api/plans").get_json()
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["id"], plan["id"])
        self.assertEqual(listed[0]["position_ids"], [self.position_id])

    def test_numeric_fields_accept_comma_and_return_numbers(self):
        response = self.client.post(
            "/api/plans",
            json={
                "direction": "long",
                "forecast_ticker": "TEST",
                "entry_zone": "65,5",
                "planned_stop": "4 126,18",
                "planned_take": "65.50",
            },
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        plan = response.get_json()
        self.assertEqual(plan["entry_zone"], 65.5)
        self.assertEqual(plan["planned_stop"], 4126.18)
        self.assertEqual(plan["planned_take"], 65.5)

        updated = self.client.put(f"/api/plans/{plan['id']}", json={"entry_zone": "106,07"})
        self.assertEqual(updated.status_code, 200, updated.get_json())
        self.assertEqual(updated.get_json()["entry_zone"], 106.07)

        rejected = self.client.put(f"/api/plans/{plan['id']}", json={"planned_stop": "не число"})
        self.assertEqual(rejected.status_code, 400)

    def test_create_edit_link_unlink_and_timeline(self):
        plan = self.create_from_position()
        plan_id = plan["id"]
        self.assertEqual(
            self.client.delete(f"/api/plans/{plan_id}/positions/{self.position_id}").status_code,
            200,
        )
        self.assertEqual(len(self.client.get("/api/plans/available-positions").get_json()), 1)

        response = self.client.post(
            f"/api/plans/{plan_id}/positions", json={"position_id": self.position_id}
        )
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(response.get_json()["positions"][0]["id"], self.position_id)

        updated = self.client.put(
            f"/api/plans/{plan_id}",
            json={"thesis": "Новый тезис", "change_note": "поправил"},
        )
        self.assertEqual(updated.status_code, 200, updated.get_json())
        body = updated.get_json()
        self.assertEqual(body["thesis"], "Новый тезис")
        self.assertEqual(self.client.get("/api/plans/missing").status_code, 404)

    def test_direction_and_account_cannot_disagree_with_linked_positions(self):
        plan = self.create_from_position()
        plan_id = plan["id"]
        self.assertEqual(
            self.client.put(f"/api/plans/{plan_id}", json={"direction": "short"}).status_code,
            400,
        )
        self.assertEqual(
            self.client.put(f"/api/plans/{plan_id}", json={"account_id": "other"}).status_code,
            400,
        )
        self.assertEqual(
            self.client.put(f"/api/plans/{plan_id}", json={"account_id": ""}).status_code,
            200,
        )

    def test_plan_levels_override_legacy_notes_in_positions_and_reports(self):
        plan = self.create_from_position()
        plan_id = plan["id"]

        position = self.client.get("/api/positions").get_json()[0]
        self.assertEqual(position["exit_assessment"]["reason"], "take")
        self.assertEqual(position["plan"]["id"], plan_id)

        response = self.client.put(f"/api/plans/{plan_id}", json={"planned_take": "115"})
        self.assertEqual(response.status_code, 200, response.get_json())
        position = self.client.get("/api/positions").get_json()[0]
        self.assertEqual(position["exit_assessment"]["reason"], "manual")
        report = self.client.get("/api/reports/trading?group_by=month").get_json()[0]
        self.assertEqual((report["takes"], report["stops"], report["manual"]), (0, 0, 1))
        self.assertIsNone(report["clean_win_rate"])

        self.client.put(f"/api/plans/{plan_id}", json={"planned_take": "110"})
        position = self.client.get("/api/positions").get_json()[0]
        self.assertEqual(position["exit_assessment"]["reason"], "take")
        report = self.client.get("/api/reports/trading?group_by=month").get_json()[0]
        self.assertEqual(report["takes"], 1)

    def test_create_from_scratch_validation_and_link_errors(self):
        response = self.client.post(
            "/api/plans",
            json={
                "direction": "short",
                "execution_ticker": "SBER",
                "forecast_ticker": "SBERF",
                "thesis": "Идея",
                "planned_stop": "100",
                "planned_take": "90",
            },
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        plan = response.get_json()
        self.assertEqual(plan["execution"]["ticker"], "SBER")
        self.assertEqual(plan["forecast"]["ticker"], "SBERF")
        self.assertEqual(plan["positions"], [])

        self.assertEqual(
            self.client.post(
                f"/api/plans/{plan['id']}/positions", json={"position_id": self.position_id}
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post("/api/plans", json={"direction": "sideways"}).status_code, 400
        )
        self.assertEqual(
            self.client.post(
                f"/api/plans/{plan['id']}/positions", json={"position_id": "missing"}
            ).status_code,
            404,
        )
        self.assertEqual(self.client.post("/api/plans", json=[]).status_code, 400)

    def test_delete_plan_without_positions_removes_attachments(self):
        plan = self.client.post(
            "/api/plans", json={"direction": "long", "forecast_ticker": "TEMP"}
        ).get_json()
        upload = self.client.post(
            f"/api/plans/{plan['id']}/attachments",
            data={"file": (io.BytesIO(PNG), "chart.png")},
            content_type="multipart/form-data",
        ).get_json()
        path = self.attachments / upload["path"]
        self.assertTrue(path.exists())

        response = self.client.delete(f"/api/plans/{plan['id']}")

        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(self.client.get(f"/api/plans/{plan['id']}").status_code, 404)
        self.assertEqual(self.client.get(f"/api/attachments/{upload['id']}").status_code, 404)
        self.assertFalse(path.exists())
        self.assertEqual(self.client.delete("/api/plans/missing").status_code, 404)

    def test_delete_plan_with_positions_is_rejected(self):
        plan = self.create_from_position()
        response = self.client.delete(f"/api/plans/{plan['id']}")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.get(f"/api/plans/{plan['id']}").status_code, 200)

    def test_attachment_upload_download_and_delete(self):
        plan = self.create_from_position()
        plan_id = plan["id"]
        response = self.client.post(
            f"/api/plans/{plan_id}/attachments",
            data={"file": (io.BytesIO(PNG), "chart.png"), "caption": "Вход"},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        attachment = response.get_json()
        self.assertEqual(attachment["mime"], "image/png")
        self.assertEqual(attachment["caption"], "Вход")
        self.assertTrue((self.attachments / plan_id).is_dir())

        with self.client.get(f"/api/attachments/{attachment['id']}") as downloaded:
            self.assertEqual(downloaded.status_code, 200)
            self.assertEqual(downloaded.mimetype, "image/png")
            self.assertEqual(downloaded.data, PNG)

        deleted = self.client.delete(f"/api/attachments/{attachment['id']}")
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(self.client.get(f"/api/attachments/{attachment['id']}").status_code, 404)
        self.assertFalse((self.attachments / attachment["path"]).exists())

        rejected = self.client.post(
            f"/api/plans/{plan_id}/attachments",
            data={"file": (io.BytesIO(b"not an image"), "note.txt")},
            content_type="multipart/form-data",
        )
        self.assertEqual(rejected.status_code, 400)
        self.assertEqual(
            self.client.post(
                f"/api/plans/{plan_id}/attachments", data={}, content_type="multipart/form-data"
            ).status_code,
            400,
        )


if __name__ == "__main__":
    unittest.main()
