import logging
from contextlib import asynccontextmanager
from typing import cast

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_offline import FastAPIOffline
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.types import ExceptionHandler

from app.api.v1.api import api_router
from app.core.database import async_engine
from app.core.middleware import ReqAndResLoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger("uvicorn.access").disabled = True
    yield
    await async_engine.dispose()


limiter = Limiter(key_func=get_remote_address)  # rate limit by IP
app = FastAPIOffline(lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded, cast(ExceptionHandler, _rate_limit_exceeded_handler)
)

app.add_middleware(ReqAndResLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
