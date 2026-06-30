from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import logging
from pathlib import Path
from . import routes, version, config

logger = logging.getLogger("plant_ai")
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Plant Intelligence Capability...")
    await routes.initialize_resources()
    logger.info("Startup complete.")
    yield
    logger.info("Shutting down Plant Intelligence Capability...")
    await routes.shutdown_resources()


app = FastAPI(
    title="Plant Intelligence Capability",
    version=version.VERSION,
    lifespan=lifespan,
)

# Mount static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
else:
    logger.warning("Static directory not found at %s", static_dir)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "message": "An unexpected error occurred."},
    )


@app.get("/", tags=["Web UI"])
async def serve_ui():
    """Serve the web UI for plant image analysis."""
    static_dir = Path(__file__).parent / "static"
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse(
        status_code=404,
        content={"error": "UI not found"},
    )


app.include_router(routes.router)
