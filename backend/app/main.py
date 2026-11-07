import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from starlette.concurrency import run_in_threadpool

from app.config import Settings
from app.database import ensure_indexes
from app.routers import router


logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        client = MongoClient(
            settings.mongodb_uri.get_secret_value(),
            tz_aware=True,
            serverSelectionTimeoutMS=settings.mongodb_timeout_ms,
            connectTimeoutMS=settings.mongodb_timeout_ms,
            socketTimeoutMS=settings.mongodb_timeout_ms,
        )
        application.state.database = client[settings.mongodb_database]
        application.state.index_ready = False
        try:
            try:
                await run_in_threadpool(ensure_indexes, application.state.database)
                application.state.index_ready = True
            except PyMongoError:
                logger.warning("MongoDB indisponível no início; novas requisições tentarão novamente.")
            yield
        finally:
            client.close()

    application = FastAPI(
        title="Meteora API",
        version="1.0.0",
        description="Medições da estação ESP32 e dados do dashboard.",
        lifespan=lifespan,
        responses={503: {"description": "MongoDB indisponível"}},
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
    )

    @application.exception_handler(PyMongoError)
    async def database_error(request: Request, exc: PyMongoError) -> JSONResponse:
        # Não expor URI, credenciais ou os detalhes internos do driver.
        return JSONResponse(
            status_code=503, content={"detail": "MongoDB indisponível. Tente novamente."}
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        # O input original pode conter NaN/Infinity, que não são serializáveis em JSON.
        errors = [
            {"loc": error["loc"], "msg": error["msg"], "type": error["type"]}
            for error in exc.errors()
        ]
        return JSONResponse(status_code=422, content={"detail": errors})

    application.include_router(router)
    return application


app = create_app()
