from dataclasses import dataclass
from datetime import datetime


@dataclass
class GameScoreDC:
    points: int


@dataclass
class PlayerDC:
    tg_id: int
    name: str
    last_name: str
    score: GameScoreDC


@dataclass
class GameDC:
    id: int
    created_at: datetime
    chat_id: int
    players: list[PlayerDC]
