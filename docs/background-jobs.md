# Local video inspection jobs

## Runtime and scope

A JobManager belongs to one application instance. It spawns one Python process
per inspection and monitors its bounded message queue from an app-owned thread.
OpenCV decoding and disk cleanup do not run on the HTTP event loop. HTTP controllers now accept bounded video transfers and expose status/cancel/
removal. The browser interface provides Inspect, Cancel, Clear, and status retry controls.
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

## Local HTTP contract

- POST /api/inspections reserves the single slot and returns id plus token.
- PUT /api/inspections/{id}/video accepts a raw MP4/WebM/MOV or octet-stream body.
- GET /api/inspections/{id} returns progress, lifecycle state, and completed result.
- POST /api/inspections/{id}/cancel requests cancellation.
- DELETE /api/inspections/{id} removes a terminal job and its retained artifacts.

All job-specific routes require Authorization: Bearer with the returned token.
Do not put tokens in URLs, logs, tracked files, or shared screenshots. Reservations
and job routes reject foreign Origin and Sec-Fetch-Site: cross-site requests.
The source filename is neither required nor used as a storage path. A reservation
accepts only one transfer, preventing simultaneous requests from mixing bytes.

Upload writes and all manager calls run in worker threads. Both declared length
and actual streamed byte count are bounded. Unsupported, empty, oversized, and
interrupted transfers release the slot and remove partial files. Video decoding
validates real dimensions, FPS, duration/frame budget, and content in the child.
Raw file contents are not trusted based on Content-Type or browser metadata.

Errors: 404 for absent/incorrect access, 409 for busy or duplicate transfer, 413
for oversized uploads, 415 for unsupported media type, 400 for invalid lifecycle
operations. The job root and copied media are never served by HTTP. Multiple
Uvicorn workers are unsupported; the exclusive root lock enforces one owner.

## Browser verification on 2026-10-25

33 automated checks passed (job lifecycle, API, geometry, reader, and HTTP policies).
Using the actual supplied preview, the browser displayed progress at 288 decoded
frames / source time 9.576 s, then completed with 360 frames, 768x432 dimensions,
11.979 s last-frame time, and zero FPS fallback frames. Error/warning logs were
empty in the final completion flow.

Clear inspection removed the private input and result: job-directory/input counts
went from one to zero; the original Downloads file remained present. A second
real inspection was cancelled through the interface, reached the cancelled state,
and left zero private input files. Removing the video during another active
inspection also left zero private job directories and no stale result on screen.
The final completion screenshot stays outside Git with other local UI evidence.

Choosing a clip still only creates a browser object URL. Inspect explicitly sends
a temporary local copy; the privacy text precedes that action. On replacing a
clip, the frontend cancels the old job and briefly polls for its terminal state
before deleting the job record. Navigation requests are best effort; the server
still finalizes cancellation and enforces expiry even if the browser disappears.
Status polling is serialized and stops on terminal states or errors. Network
errors expose a retry/cancel path instead of pretending inspection succeeded.

Ball detection, tracking, contacts, rallies, camera-motion validation, and a
manually annotated evaluation set are not implemented or evaluated by this stage.
