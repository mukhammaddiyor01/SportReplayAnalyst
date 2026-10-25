"""Controllers for bounded local video transfer and worker status."""
from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.concurrency import run_in_threadpool
from starlette.requests import ClientDisconnect

from backend.config import MAX_VIDEO_BYTES
from backend.jobs import JobNotFound
from backend.security import check_local_origin

router = APIRouter(prefix="/api/inspections", dependencies=[Depends(check_local_origin)])
SUPPORTED_MEDIA_TYPES = {"video/mp4", "video/webm", "video/quicktime", "application/octet-stream"}


def access_token(request: Request) -> str:
    authorization = request.headers.get("authorization", "")
    if not authorization.startswith("Bearer ") or len(authorization) > 200:
        raise JobNotFound("Inspection not found or access expired.")
    return authorization[7:]


def abort_receiving(manager, identifier: str, token: str) -> None:
    try:
        state = manager.status(identifier, token)
        if state["status"] == "receiving":
            manager.cancel(identifier, token)
    except JobNotFound:
        # Expiry or another explicit removal may already have cleaned this job.
        return


@router.post("", status_code=201)
async def reserve_inspection(request: Request):
    return await run_in_threadpool(request.app.state.jobs.begin)


@router.put("/{identifier}/video", status_code=202)
async def receive_video(identifier: str, request: Request):
    token = access_token(request)
    manager = request.app.state.jobs
    await run_in_threadpool(manager.claim_upload, identifier, token)
    try:
        media_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
        if media_type not in SUPPORTED_MEDIA_TYPES:
            raise HTTPException(415, "Send a supported video file as the request body.")
        declared_length = request.headers.get("content-length")
        if declared_length is not None:
            try:
                length = int(declared_length)
            except ValueError as error:
                raise HTTPException(400, "Invalid video content length.") from error
            if length < 0:
                raise HTTPException(400, "Invalid video content length.")
            if length > MAX_VIDEO_BYTES:
                raise HTTPException(413, "Video exceeds the 100 MiB upload limit.")
        async for chunk in request.stream():
            if chunk:
                await run_in_threadpool(manager.append, identifier, token, chunk)
        return await run_in_threadpool(manager.start, identifier, token)
    except ClientDisconnect as error:
        raise HTTPException(400, "Video transfer was interrupted.") from error
    finally:
        await run_in_threadpool(abort_receiving, manager, identifier, token)


@router.get("/{identifier}")
async def inspection_status(identifier: str, request: Request):
    return await run_in_threadpool(request.app.state.jobs.status, identifier, access_token(request))


@router.post("/{identifier}/cancel")
async def cancel_inspection(identifier: str, request: Request):
    return await run_in_threadpool(request.app.state.jobs.cancel, identifier, access_token(request))


@router.delete("/{identifier}", status_code=204)
async def remove_inspection(identifier: str, request: Request):
    await run_in_threadpool(request.app.state.jobs.discard, identifier, access_token(request))
