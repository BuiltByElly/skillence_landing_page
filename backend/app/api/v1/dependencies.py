from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import init_async_db

session_deps = Annotated[AsyncSession, Depends(init_async_db)]
