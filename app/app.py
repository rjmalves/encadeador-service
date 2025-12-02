from fastapi import FastAPI

from app.internal.exception_handlers import register_exception_handlers
from app.routers import chain, health


def make_app(root_path: str = "/") -> FastAPI:
    app = FastAPI(
        title="Encadeador Service",
        description="Chaining service for DECOMP/NEWAVE model variables",
        version="2.0.0",
        root_path=root_path,
    )

    # Register exception handlers
    register_exception_handlers(app)

    # Include routers
    app.include_router(chain.router)
    app.include_router(health.router)
    return app
