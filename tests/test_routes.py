import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend import create_app


class FrontendRoutesTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        frontend = Path(temp.name)
        self.document = '<!doctype html><div id="root"></div>'
        (frontend / "index.html").write_text(self.document, encoding="utf-8")
        (frontend / "assets").mkdir()
        (frontend / "assets" / "app.js").write_text('console.log("app");', encoding="utf-8")
        frontend_patch = patch("backend.FRONTEND", frontend)
        frontend_patch.start()
        self.addCleanup(frontend_patch.stop)
        with (
            patch("backend.database.initialize"),
            patch("backend.load_config", return_value={}),
        ):
            self.app = create_app()
        self.client = self.app.test_client()

    def test_client_routes_work_without_a_server_route_list(self):
        # Include a new nested route: no frontend source or route manifest is needed.
        for path in ("/", "/monthly", "/journal", "/settings", "/data-transfer", "/new/page"):
            with self.subTest(path=path):
                with self.client.get(path) as response:
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.mimetype, "text/html")
                    self.assertEqual(response.get_data(as_text=True), self.document)

    def test_missing_api_and_assets_remain_not_found(self):
        for path in (
            "/api",
            "/api/missing",
            "/assets",
            "/assets/missing",
            "/assets/missing.js",
            "/missing.css",
            "/favicon.ico",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

    def test_existing_assets_are_served_as_files(self):
        with self.client.get("/assets/app.js") as response:
            self.assertEqual(response.status_code, 200)
            self.assertIn("javascript", response.mimetype)
            self.assertEqual(response.get_data(as_text=True), 'console.log("app");')

    def test_existing_api_routes_are_not_replaced_by_the_app(self):
        with patch("backend.api.trading.database.get_accounts", return_value=[]):
            response = self.client.get("/api/accounts")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [])

    def test_post_to_client_route_is_not_served_as_html(self):
        self.assertEqual(self.client.post("/new/page").status_code, 405)
