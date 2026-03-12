"""FastAPI application factory for Genesis Navigator.

The application is configured via a module-level ``_config`` dict that the CLI
(``genesis_nav.cli``) populates before calling ``uvicorn.run()``. This avoids
environment-variable coupling and keeps the config explicit.
"""

# Implements: REQ-F-API-001
# Implements: REQ-F-FEATDETAIL-001
# Implements: REQ-NFR-ARCH-002

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from genesis_nav.routers import detail as detail_router
from genesis_nav.routers import feature as feature_router
from genesis_nav.routers import gaps as gaps_router
from genesis_nav.routers import history as history_router
from genesis_nav.routers import projects as projects_router
from genesis_nav.routers import queue as queue_router

# ---------------------------------------------------------------------------
# Module-level config — set by cli.py before uvicorn starts
# ---------------------------------------------------------------------------
_config: dict[str, object] = {
    "root_dir": ".",
}


def get_root_dir() -> str:
    """Return the root directory currently configured for scanning.

    Returns:
        Absolute or relative path string set by the CLI at startup.
    """
    return str(_config.get("root_dir", "."))


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application.

    Sets up CORS to allow the Vite dev server (port 5173) and any other
    localhost origin, mounts all routers, and registers the /health endpoint.

    Returns:
        A fully configured :class:`fastapi.FastAPI` instance.
    """
    application = FastAPI(
        title="Genesis Navigator API",
        description="Read-only REST API for visualising Genesis project state.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_origin_regex=r"http://localhost:\d+",
        allow_credentials=False,
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["*"],
    )

    application.include_router(projects_router.router)
    application.include_router(detail_router.router)
    application.include_router(feature_router.router)
    application.include_router(gaps_router.router)
    application.include_router(queue_router.router)
    # history router: /runs/current must be registered before /runs/{run_id}
    application.include_router(history_router.router)

    @application.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        """Return a simple liveness probe.

        Returns:
            ``{"status": "ok"}``
        """
        return {"status": "ok"}

    return application


# Module-level app instance used by uvicorn when launched via cli.py
app = create_app()
