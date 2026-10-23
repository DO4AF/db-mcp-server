import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient


class HostValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with patch.dict(os.environ, {
            "CUSTOM_DOMAIN": "mcp.example.com",
            "CLOUD_RUN_URL": "https://service.run.app:443",
            "ALLOWED_HOSTS": " deutschebahn-mcp, 192.168.16.10, ,",
        }):
            from main import app
        cls.client = cls.enterClassContext(TestClient(app))

    def initialize(self, client: TestClient, host: str, **headers: str):
        return client.post(
            "/mcp",
            headers={
                "host": host,
                "accept": "application/json, text/event-stream",
                **headers,
            },
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "regression", "version": "1.0"},
                },
            },
        )

    def test_configured_hosts_reach_both_layers(self) -> None:
        for host in (
            "localhost:8080", "127.0.0.1:8080", "mcp.example.com",
            "mcp.example.com:8443", "service.run.app",
            "deutschebahn-mcp:8080", "192.168.16.10:8080",
        ):
            with self.subTest(host=host):
                self.assertEqual(self.client.get("/health", headers={"host": host}).status_code, 200)
                response = self.initialize(self.client, host)
                self.assertEqual(response.status_code, 200, response.text)
                self.assertIn('"serverInfo"', response.text)

    def test_unknown_hosts_remain_blocked(self) -> None:
        response = self.initialize(self.client, "untrusted.example.com")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.text, "Invalid host header")

    def test_untrusted_origin_remains_blocked(self) -> None:
        response = self.initialize(self.client, "deutschebahn-mcp:8080", origin="https://untrusted.example.com")
        self.assertEqual(response.status_code, 403)

    def test_configured_origins_are_accepted(self) -> None:
        for origin in ("https://mcp.example.com", "http://deutschebahn-mcp:8080", "https://claude.ai"):
            with self.subTest(origin=origin):
                response = self.initialize(self.client, "deutschebahn-mcp:8080", origin=origin)
                self.assertEqual(response.status_code, 200, response.text)

    def test_openapi_is_not_an_mcp_endpoint(self) -> None:
        headers = {"host": "deutschebahn-mcp:8080"}
        self.assertEqual(self.client.get("/openapi.json", headers=headers).status_code, 200)
        self.assertEqual(self.client.get("/mcp/openapi.json", headers=headers).status_code, 404)