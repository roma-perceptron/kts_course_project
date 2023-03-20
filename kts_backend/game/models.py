from kts_backend.store.database.sqlalchemy_base import db
from kts_backend.game.dataclasses import GameDC, PlayerDC, GameScoreDC

from sqlalchemy import Column, ForeignKey, Integer, VARCHAR, DateTime, func
from sqlalchemy.orm import relationship


class PlayerModel(db):
    __tablename__ = "Players"
    #
    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(VARCHAR(32), nullable=False)
    name = Column(VARCHAR(32))
    last_name = Column(VARCHAR(32))
    game_id = Column(
        Integer,
        ForeignKey("Games.game_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    score = relationship("GameScoreModel", cascade="all,delete")


class GameModel(db):
    __tablename__ = "Games"
    #
    game_id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    chat_id = Column(VARCHAR(32), nullable=False)
    players = relationship("PlayerModel", cascade="all,delete")

    def to_dataclass(self):
        return GameDC(
            id=self.game_id,
            created_at=self.created_at,
            chat_id=self.chat_id,
            players=[
                PlayerDC(
                    tg_id=p.tg_id,
                    name=p.name,
                    last_name=p.last_name,
                    score=GameScoreDC(points=p.score[-1].points),
                )
                for p in self.players
            ],
        )

    def to_serializable(self):
        return {
            "id": self.game_id,
            "created_at": str(self.created_at),
            "chat_id": self.chat_id,
            "players": [
                {
                    "tg_id": p.tg_id,
                    "name": p.name,
                    "last_name": p.last_name,
                    "score": {"points": p.score[-1].points},
                }
                for p in self.players
            ],
        }


class GameScoreModel(db):
    __tablename__ = "GameScores"
    #
    id = Column(Integer, primary_key=True)
    player_id = Column(
        Integer,
        ForeignKey("Players.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    game_id = Column(
        Integer,
        ForeignKey("Games.game_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    points = Column(Integer)
