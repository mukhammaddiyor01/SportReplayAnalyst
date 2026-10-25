from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from backend.config import JOB_DIRECTORY, STATIC_DIRECTORY
from backend.inspection_routes import router as inspection_router
from backend.jobs import JobBusy, JobError, JobManager, JobNotFound, UploadTooLarge
from backend.routes import router


def create_app(*, job_directory: Path | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app):
        manager = await run_in_threadpool(JobManager, job_directory or JOB_DIRECTORY)
        app.state.jobs = manager
        try:
            yield
        finally:
            await run_in_threadpool(manager.close)

    app = FastAPI(lifespan=lifespan, title="Sports Replay Analyst", debug=False,
                  docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])

    @app.middleware("http")
    async def browser_policies(request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' blob:; media-src 'self' blob:; connect-src 'self'; "
            "object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        )
        return response

    @app.exception_handler(JobError)
    async def job_error_response(request, error):
        status = 400
        if isinstance(error, JobNotFound):
            status = 404
        elif isinstance(error, JobBusy):
            status = 409
        elif isinstance(error, UploadTooLarge):
            status = 413
        return JSONResponse({"detail": str(error)}, status_code=status)

    app.include_router(inspection_router)
    app.mount("/static", StaticFiles(directory=STATIC_DIRECTORY), name="static")
    app.include_router(router)
    return app


app = create_app()
