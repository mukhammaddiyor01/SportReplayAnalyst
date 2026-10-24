import unittest

import httpx

from backend.main import create_app


class AppTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=create_app()),
                                       base_url="http://127.0.0.1")

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_workspace_and_public_styles(self):
        response = await self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("No video loaded", response.text)
        self.assertEqual((await self.client.get("/static/css/styles.css")).status_code, 200)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertIn("frame-ancestors 'none'", response.headers["content-security-policy"])

    async def test_private_files_are_not_served(self):
        for path in ["/AGENTS.md", "/.git/config", "/.env", "/static/../AGENTS.md"]:
            self.assertEqual((await self.client.get(path)).status_code, 404)

    async def test_unexpected_hosts_are_rejected(self):
        response = await self.client.get("/", headers={"host": "untrusted.example"})
        self.assertEqual(response.status_code, 400)

    async def test_health(self):
        self.assertEqual((await self.client.get("/health")).json(), {"status": "ok"})
