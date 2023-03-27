from typing import Optional
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import declarative_base

from base.base_accessor import BaseAccessor
from store.database.sqlalchemy_base import db

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

import os


class Database(BaseAccessor):
    _engine: Optional[AsyncEngine] = None
    _db: Optional[declarative_base] = None
    session: Optional[AsyncSession] = None

    def _init_(self):
        self.DATABASE_URL = "postgresql+asyncpg://" + os.environ.get("KTS_DB_CREDENTIALS",
                                                                     "USERNAME:PASSWORD@HOST:5432/DB_NAME")

        self.logger.info(f"{self.DATABASE_URL=}")
        self.logger.info(f"{self.app.settings.postgres.dsn}")

    async def connect(self, *_: list, **__: dict) -> None:
        self._db = db
        self._engine = create_async_engine(self.DATABASE_URL, echo=True, future=True)
        self.session = sessionmaker(bind=self._engine, expire_on_commit=False, class_=AsyncSession)
        self.logger.info("ok, connected!")

    async def disconnect(self, *_: list, **__: dict) -> None:
        pass
