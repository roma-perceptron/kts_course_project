from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class QuestionDC:
    context: str
    question: Optional[str] = ""
    answers: Optional[list[str]] = list
    story: Optional[str] = ""
    complexity: Optional[int] = 0
    id_db: Optional[int] = None


@dataclass
class PlayerDC:
    user_id: str
    first_name: str
    username: str = None
    last_name: str = None
    teams: Optional[list["TeamDC"]] = None


@dataclass
class TeamDC:
    chat_id: str
    players: list[PlayerDC]


@dataclass
class GameScoreDC:
    game_id: int
    game_result: int
    points_wins: int
    points_loss: int


@dataclass
class GameDC:
    id: int
    created_at: datetime
    team_id: int
    questions: list[QuestionDC]


""" Старая версия

@dataclass
class GameScoreDC:
    points: int


@dataclass
class PlayerDC:
    tg_id: str
    name: str
    last_name: str
    score: GameScoreDC


@dataclass
class GameDC:
    id: int
    created_at: datetime
    chat_id: str
    players: list[PlayerDC]

Старая версия """
