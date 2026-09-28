import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend import create_app
from backend.config import ROOT


class FrontendRoutesTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        frontend = Path(temp.name)
        self.document = '<!doctype html><div id="root"></div>'
        (frontend / "index.html").write_text(self.document, encoding="utf-8")
        frontend_patch = patch("backend.FRONTEND", frontend)
        frontend_patch.start()
        self.addCleanup(frontend_patch.stop)
        with (
            patch("backend.database.initialize"),
            patch("backend.load_config", return_value={}),
        ):
            self.app = create_app()
        self.client = self.app.test_client()
        self.routes = json.loads((ROOT / "routes.json").read_text(encoding="utf-8"))

    def test_every_navigation_route_serves_the_app_on_direct_visit(self):
        self.assertEqual(len({route["id"] for route in self.routes}), len(self.routes))
        self.assertEqual(len({route["path"] for route in self.routes}), len(self.routes))
        for route in self.routes:
            with self.subTest(path=route["path"]):
                response = self.client.get(route["path"])
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.mimetype, "text/html")
                self.assertEqual(response.get_data(as_text=True), self.document)
                response.close()

    def test_unknown_routes_and_missing_assets_remain_not_found(self):
        for path in ("/missing", "/api/missing", "/assets/missing.js"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)
