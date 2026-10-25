"""One app-owned video worker, bounded retention, and private job files."""
from dataclasses import dataclass, field
import fcntl
import json
import logging
import multiprocessing
import os
from pathlib import Path
from queue import Empty
import re
import secrets
import shutil
import threading
import time

from backend.adapters.inspection_worker import inspect_worker
from backend.config import (CANCEL_GRACE_SECONDS, JOB_RETENTION_SECONDS,
                            JOB_TIMEOUT_SECONDS, MAX_RETAINED_JOBS,
                            MAX_VIDEO_BYTES, UPLOAD_TIMEOUT_SECONDS)

ACTIVE_STATES = {"receiving", "running", "cancelling"}
JOB_DIRECTORY_NAME = re.compile(r"[0-9a-f]{32}")
logger = logging.getLogger(__name__)


class JobError(ValueError):
    pass


class JobBusy(JobError):
    pass


class JobNotFound(JobError):
    pass


class UploadTooLarge(JobError):
    pass


@dataclass
class Job:
    identifier: str
    token: str
    directory: Path
    status: str = "receiving"
    created: float = field(default_factory=time.monotonic)
    finished: float | None = None
    started: float | None = None
    cancel_requested: float | None = None
    terminated_at: float | None = None
    upload_claimed: bool = False
    received_bytes: int = 0
    decoded_frames: int = 0
    timestamp_seconds: float | None = None
    error: str | None = None
    result: dict | None = None
    cleanup_pending: bool = False
    process: object = None
    cancel_event: object = None
    messages: object = None
    outcome: dict | None = None


class JobManager:
    def __init__(self, root: Path, *, worker_target=inspect_worker):
        self.root = root
        self.worker_target = worker_target
        self.jobs: dict[str, Job] = {}
        self.lock = threading.RLock()
        self.context = multiprocessing.get_context("spawn")
        self.closed = False
        self.stop_event = threading.Event()
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        root.chmod(0o700)
        self.file_lock = (root / ".lock").open("a")
        os.chmod(root / ".lock", 0o600)
        try:
            fcntl.flock(self.file_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            self.file_lock.close()
            raise JobBusy("Another application instance owns the job directory.") from error
        try:
            # A restart ends the previous review session; results are not durable.
            for directory in root.iterdir():
                if JOB_DIRECTORY_NAME.fullmatch(directory.name) and directory.is_dir() and not directory.is_symlink():
                    shutil.rmtree(directory)
        except OSError:
            self.file_lock.close()
            raise
        self.monitor = threading.Thread(target=self._monitor, name="video-jobs", daemon=True)
        self.monitor.start()

    def begin(self) -> dict:
        with self.lock:
            if self.closed:
                raise JobBusy("The application is shutting down.")
            if any(job.status in ACTIVE_STATES for job in self.jobs.values()):
                raise JobBusy("Another video is being received or inspected. Try again when it finishes.")
            if len(self.jobs) >= MAX_RETAINED_JOBS:
                raise JobBusy("Remove an old inspection before starting another.")
            identifier = secrets.token_hex(16)
            directory = self.root / identifier
            directory.mkdir(mode=0o700)
            job = Job(identifier, secrets.token_urlsafe(32), directory)
            self.jobs[identifier] = job
            return {"id": identifier, "token": job.token, "status": job.status}

    def _get(self, identifier: str, token: str) -> Job:
        job = self.jobs.get(identifier)
        if job is None or not secrets.compare_digest(job.token.encode(), token.encode()):
            raise JobNotFound("Inspection not found or access expired.")
        return job

    def claim_upload(self, identifier: str, token: str) -> None:
        with self.lock:
            job = self._get(identifier, token)
            if job.status != "receiving" or job.upload_claimed:
                raise JobBusy("This inspection already has a video transfer.")
            job.upload_claimed = True

    def append(self, identifier: str, token: str, chunk: bytes) -> None:
        with self.lock:
            job = self._get(identifier, token)
            if job.status != "receiving":
                raise JobError("This inspection is no longer accepting video data.")
            if job.received_bytes + len(chunk) > MAX_VIDEO_BYTES:
                self._finish(job, "failed", "Video exceeds the 100 MiB upload limit.")
                raise UploadTooLarge("Video exceeds the 100 MiB upload limit.")
            try:
                with (job.directory / "input.video").open("ab") as destination:
                    destination.write(chunk)
                (job.directory / "input.video").chmod(0o600)
            except OSError as error:
                self._finish(job, "failed", "The local video copy could not be written.")
                raise JobError(job.error) from error
            job.received_bytes += len(chunk)

    def start(self, identifier: str, token: str) -> dict:
        with self.lock:
            job = self._get(identifier, token)
            if job.status != "receiving":
                raise JobError("This inspection cannot be started again.")
            if job.received_bytes == 0:
                self._finish(job, "failed", "The video is empty.")
                raise JobError(job.error)
            job.cancel_event = self.context.Event()
            job.messages = self.context.Queue(maxsize=32)
            job.process = self.context.Process(
                target=self.worker_target,
                args=(str(job.directory / "input.video"), job.cancel_event, job.messages),
                name="video-inspection",
            )
            try:
                job.process.start()
            except Exception:
                logger.exception("Could not start inspection process")
                job.messages.close()
                job.process = None
                self._finish(job, "failed", "The inspection worker could not start.")
                raise JobError(job.error)
            job.started = time.monotonic()
            job.status = "running"
            return self._snapshot(job)

    def status(self, identifier: str, token: str) -> dict:
        with self.lock:
            return self._snapshot(self._get(identifier, token))

    def cancel(self, identifier: str, token: str) -> dict:
        with self.lock:
            job = self._get(identifier, token)
            if job.status == "receiving":
                self._finish(job, "cancelled")
            elif job.status == "running":
                job.status = "cancelling"
                job.cancel_requested = time.monotonic()
                job.cancel_event.set()
            return self._snapshot(job)

    def discard(self, identifier: str, token: str) -> None:
        with self.lock:
            job = self._get(identifier, token)
            if job.status in ACTIVE_STATES:
                raise JobBusy("Cancel the inspection and wait for it to stop before removing it.")
            self._remove_files(job)
            if job.cleanup_pending:
                raise JobError("Temporary files could not be removed; cleanup will retry.")
            del self.jobs[identifier]

    def _snapshot(self, job: Job) -> dict:
        return {"id": job.identifier, "status": job.status,
                "received_bytes": job.received_bytes, "decoded_frames": job.decoded_frames,
                "timestamp_seconds": job.timestamp_seconds, "error": job.error,
                "result": job.result, "cleanup_pending": job.cleanup_pending,
                "retention_seconds": JOB_RETENTION_SECONDS}

    def _remove_files(self, job: Job) -> None:
        try:
            if job.directory.exists():
                shutil.rmtree(job.directory)
            job.cleanup_pending = False
        except OSError:
            if not job.cleanup_pending:
                logger.exception("Temporary job file cleanup failed; will retry")
            job.cleanup_pending = True

    def _finish(self, job: Job, status: str, error: str | None = None) -> None:
        job.status = status
        job.error = error
        job.finished = time.monotonic()
        if status != "completed":
            job.result = None
            self._remove_files(job)

    def _read_messages(self, job: Job) -> None:
        while True:
            try:
                message = job.messages.get_nowait()
            except Empty:
                break
            if message["kind"] == "progress":
                job.decoded_frames = message["decoded_frames"]
                job.timestamp_seconds = message["timestamp_seconds"]
            else:
                job.outcome = message

    def _refresh(self, job: Job, now: float) -> None:
        if job.status == "receiving" and now - job.created > UPLOAD_TIMEOUT_SECONDS:
            self._finish(job, "failed", "Video transfer timed out.")
        if job.process is None:
            return
        self._read_messages(job)
        if job.status == "running" and now - job.started > JOB_TIMEOUT_SECONDS:
            job.error = "Video inspection exceeded its runtime limit."
            job.status = "cancelling"
            job.cancel_requested = now
            job.cancel_event.set()
        if job.status == "cancelling" and now - job.cancel_requested > CANCEL_GRACE_SECONDS:
            # A blocked decoder may not reach the cooperative frame checkpoint.
            if job.process.is_alive() and job.terminated_at is None:
                job.process.terminate()
                job.terminated_at = now
            elif job.process.is_alive() and now - job.terminated_at > CANCEL_GRACE_SECONDS:
                job.process.kill()
        if job.process.is_alive():
            return
        job.process.join()
        self._read_messages(job)
        exitcode = job.process.exitcode
        job.process.close()
        job.process = None
        job.messages.close()
        job.messages = None
        if job.status == "cancelling":
            self._finish(job, "failed" if job.error else "cancelled", job.error)
            return
        outcome = job.outcome or {"kind": "failed", "error": "The inspection worker stopped unexpectedly."}
        if exitcode != 0:
            outcome = {"kind": "failed", "error": "The inspection worker stopped unexpectedly."}
        if outcome["kind"] == "completed":
            job.result = outcome["result"]
            job.decoded_frames = job.result["decoded_frames"]
            job.timestamp_seconds = job.result["last_timestamp_seconds"]
            try:
                result_file = job.directory / "result.json"
                result_file.write_text(json.dumps(job.result))
                result_file.chmod(0o600)
            except OSError:
                logger.exception("Could not store inspection result")
                self._finish(job, "failed", "The inspection result could not be saved locally.")
                return
        self._finish(job, outcome["kind"], outcome.get("error"))

    def _monitor(self) -> None:
        while not self.stop_event.wait(.05):
            with self.lock:
                now = time.monotonic()
                for identifier, job in list(self.jobs.items()):
                    self._refresh(job, now)
                    if job.cleanup_pending:
                        self._remove_files(job)
                    if job.finished is not None and now - job.finished >= JOB_RETENTION_SECONDS:
                        self._remove_files(job)
                        if not job.cleanup_pending:
                            del self.jobs[identifier]

    def close(self) -> None:
        with self.lock:
            if self.closed:
                return
            self.closed = True
            for job in self.jobs.values():
                if job.status == "running":
                    job.cancel_event.set()
        self.stop_event.set()
        self.monitor.join()
        with self.lock:
            for job in self.jobs.values():
                if job.process is not None:
                    job.process.join(timeout=CANCEL_GRACE_SECONDS)
                    if job.process.is_alive():
                        job.process.terminate()
                        job.process.join(timeout=CANCEL_GRACE_SECONDS)
                    if job.process.is_alive():
                        job.process.kill()
                        job.process.join()
                    job.process.close()
                    job.messages.close()
                self._remove_files(job)
            self.jobs.clear()
            fcntl.flock(self.file_lock, fcntl.LOCK_UN)
            self.file_lock.close()
