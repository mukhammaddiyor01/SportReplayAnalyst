import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import cv2
import httpx
import numpy as np

from backend.main import create_app
from test_jobs import waiting_worker


class InspectionApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = TemporaryDirectory()
        self.root = Path(self.directory.name) / "jobs"
        self.app = create_app(job_directory=self.root)
        self.lifespan = self.app.router.lifespan_context(self.app)
        await self.lifespan.__aenter__()
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app),
                                       base_url="http://127.0.0.1:8014")

    async def asyncTearDown(self):
        await self.client.aclose()
        await self.lifespan.__aexit__(None, None, None)
        self.directory.cleanup()

    async def reserve(self):
        response = await self.client.post("/api/inspections")
        self.assertEqual(response.status_code, 201, response.text)
        handle = response.json()
        headers = {"Authorization": "Bearer " + handle["token"], "Content-Type": "video/mp4"}
        return handle, "/api/inspections/" + handle["id"], headers

    async def wait_for_terminal(self, path, headers):
        for _ in range(400):
            response = await self.client.get(path, headers=headers)
            self.assertEqual(response.status_code, 200)
            state = response.json()
            if state["status"] in {"completed", "failed", "cancelled"}:
                return state
            await asyncio.sleep(.02)
        self.fail("Inspection did not finish.")

    def sample_video(self):
        path = Path(self.directory.name) / "original.mp4"
        writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 20, (64, 48))
        self.assertTrue(writer.isOpened())
        for _ in range(20):
            writer.write(np.zeros((48, 64, 3), np.uint8))
        writer.release()
        return path.read_bytes()

    async def test_real_upload_inspection_and_delete(self):
        handle, path, headers = await self.reserve()
        response = await self.client.put(path + "/video", content=self.sample_video(), headers=headers)
        self.assertEqual(response.status_code, 202, response.text)
        state = await self.wait_for_terminal(path, headers)
        self.assertEqual(state["status"], "completed", state)
        self.assertEqual(state["result"]["decoded_frames"], 20)
        self.assertNotIn("token", state)
        self.assertEqual((await self.client.get("/local-data/jobs/" + handle["id"] + "/input.video")).status_code, 404)
        self.assertEqual((await self.client.delete(path, headers=headers)).status_code, 204)
        self.assertFalse((self.root / handle["id"]).exists())
        self.assertTrue((Path(self.directory.name) / "original.mp4").exists())
        self.assertEqual((await self.client.get(path, headers=headers)).status_code, 404)

    async def test_busy_and_foreign_tokens_cannot_mutate_job(self):
        handle, path, headers = await self.reserve()
        self.assertEqual((await self.client.post("/api/inspections")).status_code, 409)
        for method, suffix in [("GET", ""), ("POST", "/cancel"), ("DELETE", ""), ("PUT", "/video")]:
            response = await self.client.request(method, path + suffix,
                                                 headers={"Authorization": "Bearer wrong"})
            self.assertEqual(response.status_code, 404)
        self.assertEqual((await self.client.get(path)).status_code, 404)
        self.assertEqual((await self.client.get(path, headers=headers)).json()["status"], "receiving")
        self.assertEqual((await self.client.post(path + "/cancel", headers=headers)).json()["status"], "cancelled")

    async def test_cross_origin_and_cross_site_reservations_are_rejected(self):
        for headers in [{"Origin": "https://other.example"}, {"Sec-Fetch-Site": "cross-site"}]:
            response = await self.client.post("/api/inspections", headers=headers)
            self.assertEqual(response.status_code, 403)
        self.assertEqual(len(self.app.state.jobs.jobs), 0)

    async def test_streamed_size_limit_cleans_partial_file(self):
        async def chunks():
            yield b"1234"
            yield b"5678"
        handle, path, headers = await self.reserve()
        with patch("backend.jobs.MAX_VIDEO_BYTES", 6):
            response = await self.client.put(path + "/video", content=chunks(), headers=headers)
        self.assertEqual(response.status_code, 413)
        self.assertFalse((self.root / handle["id"]).exists())
        self.assertEqual((await self.client.get(path, headers=headers)).json()["status"], "failed")

    async def test_declared_size_empty_and_unsupported_media_are_cleaned(self):
        for content, extra_headers, expected in [(b"1234", {"Content-Length": "999999999"}, 413),
                                                 (b"", {}, 400),
                                                 (b"abc", {"Content-Type": "text/plain"}, 415)]:
            handle, path, headers = await self.reserve()
            response = await self.client.put(path + "/video", content=content, headers=headers | extra_headers)
            self.assertEqual(response.status_code, expected, response.text)
            self.assertFalse((self.root / handle["id"]).exists())

    async def test_interrupted_stream_cleans_partial_file(self):
        handle, path, headers = await self.reserve()
        incoming = iter([{"type": "http.request", "body": b"partial video", "more_body": True},
                         {"type": "http.disconnect"}])
        async def receive():
            return next(incoming, {"type": "http.disconnect"})
        async def send(message):
            return None
        scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
                 "method": "PUT", "scheme": "http", "path": path + "/video",
                 "raw_path": (path + "/video").encode(), "query_string": b"",
                 "root_path": "", "server": ("127.0.0.1", 8014), "client": ("127.0.0.1", 12345),
                 "headers": [(b"host", b"127.0.0.1:8014")] +
                            [(name.lower().encode(), value.encode()) for name, value in headers.items()]}
        await self.app(scope, receive, send)
        self.assertFalse((self.root / handle["id"]).exists())
        self.assertEqual((await self.client.get(path, headers=headers)).json()["status"], "cancelled")

    async def test_duplicate_upload_does_not_cancel_existing_transfer(self):
        handle, path, headers = await self.reserve()
        self.app.state.jobs.claim_upload(handle["id"], handle["token"])
        response = await self.client.put(path + "/video", content=b"duplicate", headers=headers)
        self.assertEqual(response.status_code, 409)
        self.assertEqual((await self.client.get(path, headers=headers)).json()["status"], "receiving")

    async def test_running_worker_keeps_health_responsive_and_can_cancel(self):
        self.app.state.jobs.worker_target = waiting_worker
        handle, path, headers = await self.reserve()
        self.assertEqual((await self.client.put(path + "/video", content=b"fixture", headers=headers)).status_code, 202)
        response = await asyncio.wait_for(self.client.get("/health"), timeout=1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual((await self.client.delete(path, headers=headers)).status_code, 409)
        response = await self.client.post(path + "/cancel", headers=headers)
        self.assertEqual(response.json()["status"], "cancelling")
        self.assertEqual((await self.wait_for_terminal(path, headers))["status"], "cancelled")
        self.assertFalse((self.root / handle["id"]).exists())
