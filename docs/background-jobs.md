# Local video inspection jobs

## Runtime and scope

A JobManager belongs to one application instance. It spawns one Python process
per inspection and monitors its bounded message queue from an app-owned thread.
OpenCV decoding and disk cleanup do not run on the HTTP event loop. At this
foundation milestone it is not yet connected to HTTP uploads or the interface.
The worker performs actual video inspection only; no ball detection is simulated.

There is one admission slot and no pending-job queue (capacity zero). A receiving,
running, or cancelling job occupies that slot. New work gets an explicit busy
error rather than growing a queue. At most eight job records are retained.

Job states: receiving -> running -> completed/failed; receiving can be cancelled
immediately; running -> cancelling -> cancelled. Runtime expiry ends in failed.
A completed job is finalized only after the child has exited and been joined.
Progress means decoded frames and source timestamp, not a made-up percentage.
Messages are bounded to 32; replaceable progress may be skipped when full, but
completed results contain the exact decoded count.

## Isolation and files

Each job has a random ID, separate bearer token, and private directory under the
ignored local-data/jobs directory. Source names are not used as paths. Public
status responses omit filesystem paths and tokens. Status, cancel, and removal
must check the token; an unknown ID and a wrong token share the same error.
The job root and job directories have mode 0700; media/results use mode 0600.
A POSIX advisory lock prevents two app instances from owning the same root.
Use one Uvicorn worker on the supported local macOS/Linux runtime.

The original user file is never removed: only the private job copy is managed.
Failed/cancelled jobs delete their artifacts after the worker stops. A failed
cleanup is exposed as cleanup_pending and retried, not falsely reported as done.
Completed inputs/results expire one hour after completion. Explicit discard
removes them sooner. Active files are never removed by expiry/discard.

Receiving reservations time out after 120 seconds total. Inspection runtime is
limited to 180 seconds. Cancellation checks between decoded frames. If a codec
blocks, terminate the child after two seconds, then kill if it remains alive.
Shutdown stops and joins workers before deleting their files and releasing the
root lock. Restart ends the old review session: orphaned job directories are
removed under the exclusive lock. No result/history survives a restart.

## Verification

Lifecycle checks exercise real generated video in a spawned OpenCV worker,
progress, cooperative cancellation, interrupted transfers, corrupt input, worker
crash, stuck-worker timeout, capacity, token isolation, retention, private file
permissions, explicit deletion, shutdown, root locking, and startup orphan cleanup.
No synthetic fixture is presented as a successful ball-tracking evaluation.
