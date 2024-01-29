from fastapi import FastAPI
from app.routers import chain


def make_app(root_path: str = "/") -> FastAPI:
    app = FastAPI(root_path=root_path)
    app.include_router(chain.router)
    return app
