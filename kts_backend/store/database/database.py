from typing import Optional, TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import declarative_base

from kts_backend.store.database.sqlalchemy_base import db

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

import os


if TYPE_CHECKING:
    from kts_backend.web.app import Application


class Database:
    def __init__(self, app: "Application"):
        self.app = app
        self._engine: Optional[AsyncEngine] = None
        self._db: Optional[declarative_base] = None
        self.session: Optional[AsyncSession] = None
        self.DATABASE_URL = f"postgresql+asyncpg://" \
                            f"{self.app.config.database.user}:" \
                            f"{self.app.config.database.password}@" \
                            f"{self.app.config.database.host}:" \
                            f"{self.app.config.database.port}/" \
                            f"{self.app.config.database.database}"
        # self.DATABASE_URL = "postgresql+asyncpg://" + os.environ.get(
        #     "KTS_DB_CREDENTIALS", "USERNAME:PASSWORD@HOST:PORT/DB_NAME"
        # )

        self.app.on_startup.append(self.connect)
        self.app.on_cleanup.append(self.disconnect)

    async def connect(self, *_: list, **__: dict) -> None:
        self._db = db
        self._engine = create_async_engine(
            self.DATABASE_URL, echo=True, future=True
        )
        self.session = sessionmaker(
            bind=self._engine, expire_on_commit=False, class_=AsyncSession
        )
        print(" " * 3, "ok database, connected!")

    async def disconnect(self, *_: list, **__: dict) -> None:
        await self._engine.dispose()
        self._db = None
