import os
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest
from unittest.mock import patch

import cv2
import numpy as np

from backend.jobs import JobBusy, JobError, JobManager, JobNotFound, UploadTooLarge


def waiting_worker(path, cancel, messages):
    messages.put({"kind": "progress", "decoded_frames": 12, "timestamp_seconds": .4})
    cancel.wait(10)
    messages.put({"kind": "cancelled"})


def crashing_worker(path, cancel, messages):
    os._exit(7)


def stuck_worker(path, cancel, messages):
    time.sleep(10)


class JobTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "jobs"
        self.manager = None

    def manager_for(self, **kwargs):
        self.manager = JobManager(self.root, **kwargs)
        self.addCleanup(self.manager.close)
        return self.manager

    def wait_until(self, handle, statuses, timeout=8):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            state = self.manager.status(handle["id"], handle["token"])
            if state["status"] in statuses:
                return state
            time.sleep(.02)
        self.fail(f"Job did not reach {statuses}; last state: {state}")

    def video_bytes(self):
        path = Path(self.temporary.name) / "original.mp4"
        writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 20, (64, 48))
        self.assertTrue(writer.isOpened())
        for _ in range(20):
            writer.write(np.zeros((48, 64, 3), np.uint8))
        writer.release()
        return path.read_bytes()

    def start_job(self, content=b"worker fixture"):
        handle = self.manager.begin()
        self.manager.append(handle["id"], handle["token"], content)
        self.manager.start(handle["id"], handle["token"])
        return handle

    def test_real_video_completes_and_explicit_removal_preserves_original(self):
        manager = self.manager_for()
        content = self.video_bytes()
        handle = self.start_job(content)
        state = self.wait_until(handle, {"completed", "failed"})
        self.assertEqual(state["status"], "completed", state)
        self.assertEqual(state["decoded_frames"], 20)
        self.assertEqual(state["result"]["source_dimensions"], [64, 48])
        self.assertTrue((self.root / handle["id"] / "result.json").is_file())
        self.assertEqual((self.root / handle["id"]).stat().st_mode & 0o777, 0o700)
        self.assertNotIn("token", state)
        self.assertNotIn("directory", state)
        manager.discard(handle["id"], handle["token"])
        self.assertFalse((self.root / handle["id"]).exists())
        self.assertEqual((Path(self.temporary.name) / "original.mp4").read_bytes(), content)
        with self.assertRaises(JobNotFound):
            manager.status(handle["id"], handle["token"])

    def test_busy_access_isolation_and_receiving_cancel(self):
        manager = self.manager_for()
        handle = manager.begin()
        manager.append(handle["id"], handle["token"], b"partial")
        with self.assertRaises(JobBusy):
            manager.begin()
        for action in [manager.status, manager.cancel, manager.discard]:
            with self.assertRaises(JobNotFound):
                action(handle["id"], "wrong token")
        self.assertTrue((self.root / handle["id"]).exists())
        self.assertEqual(manager.cancel(handle["id"], handle["token"])["status"], "cancelled")
        self.assertFalse((self.root / handle["id"]).exists())
        with self.assertRaises(JobError):
            manager.append(handle["id"], handle["token"], b"late")
        second = manager.begin()
        self.assertNotEqual(second["id"], handle["id"])

    def test_progress_cooperative_cancel_and_active_file_protection(self):
        manager = self.manager_for(worker_target=waiting_worker)
        handle = self.start_job()
        deadline = time.monotonic() + 8
        while manager.status(handle["id"], handle["token"])["decoded_frames"] == 0:
            self.assertLess(time.monotonic(), deadline)
            time.sleep(.02)
        with self.assertRaises(JobBusy):
            manager.discard(handle["id"], handle["token"])
        self.assertTrue((self.root / handle["id"]).exists())
        manager.cancel(handle["id"], handle["token"])
        state = self.wait_until(handle, {"cancelled"})
        self.assertEqual(state["decoded_frames"], 12)
        self.assertFalse((self.root / handle["id"]).exists())

    def test_decoder_failure_removes_private_copy(self):
        self.manager_for()
        handle = self.start_job(b"not a video")
        state = self.wait_until(handle, {"failed"})
        self.assertIsNotNone(state["error"])
        self.assertIsNone(state["result"])
        self.assertFalse((self.root / handle["id"]).exists())

    def test_worker_crash_releases_capacity(self):
        self.manager_for(worker_target=crashing_worker)
        handle = self.start_job()
        state = self.wait_until(handle, {"failed"})
        self.assertIn("unexpectedly", state["error"])
        self.assertFalse((self.root / handle["id"]).exists())
        self.manager.begin()

    def test_runtime_timeout_terminates_a_stuck_worker(self):
        self.manager_for(worker_target=stuck_worker)
        with patch("backend.jobs.JOB_TIMEOUT_SECONDS", .1), patch("backend.jobs.CANCEL_GRACE_SECONDS", .1):
            handle = self.start_job()
            state = self.wait_until(handle, {"failed"})
        self.assertIn("runtime", state["error"])
        self.assertFalse((self.root / handle["id"]).exists())

    def test_limits_and_empty_input_cleanup(self):
        manager = self.manager_for()
        handle = manager.begin()
        with patch("backend.jobs.MAX_VIDEO_BYTES", 4):
            manager.append(handle["id"], handle["token"], b"1234")
            with self.assertRaises(UploadTooLarge):
                manager.append(handle["id"], handle["token"], b"5")
        self.assertFalse((self.root / handle["id"]).exists())
        empty = manager.begin()
        with self.assertRaises(JobError):
            manager.start(empty["id"], empty["token"])
        self.assertFalse((self.root / empty["id"]).exists())

    def test_retention_expires_results_but_never_deletes_active_job(self):
        manager = self.manager_for(worker_target=waiting_worker)
        with patch("backend.jobs.JOB_RETENTION_SECONDS", .1):
            active = self.start_job()
            time.sleep(.2)
            self.assertTrue((self.root / active["id"]).exists())
            manager.cancel(active["id"], active["token"])
            self.wait_until(active, {"cancelled"})
            time.sleep(.2)
            with self.assertRaises(JobNotFound):
                manager.status(active["id"], active["token"])

    def test_receiving_timeout_and_bounded_history(self):
        manager = self.manager_for()
        with patch("backend.jobs.UPLOAD_TIMEOUT_SECONDS", .05):
            handle = manager.begin()
            manager.append(handle["id"], handle["token"], b"partial")
            self.wait_until(handle, {"failed"})
        self.assertFalse((self.root / handle["id"]).exists())
        with patch("backend.jobs.MAX_RETAINED_JOBS", 1):
            with self.assertRaises(JobBusy):
                manager.begin()

    def test_cleanup_failure_is_visible_and_retried(self):
        manager = self.manager_for()
        handle = manager.begin()
        manager.append(handle["id"], handle["token"], b"partial")
        with self.assertLogs("backend.jobs", level="ERROR"):
            with patch("backend.jobs.shutil.rmtree", side_effect=PermissionError("test failure")):
                state = manager.cancel(handle["id"], handle["token"])
                self.assertTrue(state["cleanup_pending"])
        deadline = time.monotonic() + 2
        while manager.status(handle["id"], handle["token"])["cleanup_pending"]:
            self.assertLess(time.monotonic(), deadline)
            time.sleep(.02)
        self.assertFalse((self.root / handle["id"]).exists())

    def test_instance_lock_shutdown_and_orphan_cleanup(self):
        self.root.mkdir()
        orphan = self.root / ("a" * 32)
        orphan.mkdir()
        (orphan / "input.video").write_bytes(b"orphan")
        manager = self.manager_for(worker_target=waiting_worker)
        self.assertFalse(orphan.exists())
        with self.assertRaises(JobBusy):
            JobManager(self.root)
        active = self.start_job()
        manager.close()
        self.assertFalse((self.root / active["id"]).exists())
        self.assertFalse(manager.monitor.is_alive())
        restarted = JobManager(self.root)
        restarted.close()
