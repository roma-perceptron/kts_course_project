from kts_backend.store.database.sqlalchemy_base import db
from sqlalchemy import Column, Integer, VARCHAR


class AdminModel(db):
    __tablename__ = "admins"
    #
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(VARCHAR(32), nullable=True, unique=True)
    password = Column(VARCHAR(512), nullable=True)
