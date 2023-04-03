from kts_backend.store.database.sqlalchemy_base import db
from kts_backend.game.dataclasses import GameDC, PlayerDC, GameScoreDC
from kts_backend.game.dataclasses import QuestionDC

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    VARCHAR,
    DateTime,
    func,
    TEXT,
    ARRAY,
    BOOLEAN,
    LargeBinary,
)
from sqlalchemy.orm import relationship


class PlayerModel(db):
    __tablename__ = "players"
    #
    user_id = Column(VARCHAR(32), primary_key=True, nullable=False)
    username = Column(VARCHAR(32))
    first_name = Column(VARCHAR(32))
    last_name = Column(VARCHAR(32))
    teams = relationship(
        "TeamModel",
        secondary="_players_teams",
        back_populates="players",
        cascade="all,delete",
    )

    def to_dataclass(self):
        return PlayerDC(
            user_id=self.user_id,
            first_name=self.first_name,
            username=self.username,
            last_name=self.last_name,
        )


class TeamModel(db):
    __tablename__ = "teams"
    #
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(VARCHAR(32), nullable=False)
    players = relationship(
        "PlayerModel", secondary="_players_teams", back_populates="teams"
    )
    games = relationship(
        "GameModel", back_populates="team", cascade="all,delete"
    )


class GameModel(db):
    __tablename__ = "games"
    #
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    team_id = Column(
        Integer,
        ForeignKey("teams.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    team = relationship(
        "TeamModel", cascade="all,delete", back_populates="games"
    )
    #
    questions = relationship(
        "QuestionModel",
        secondary="_games_questions",
        back_populates="games",
        cascade="all,delete",
    )
    score = relationship(
        "GameScoreModel", back_populates="game", cascade="all,delete"
    )

    #
    def to_serializable(self):
        from sqlalchemy.orm.state import InstanceState
        return {
            'id': self.id,
            'created_at': str(self.created_at),
            'team_id': self.team_id,
            'questions1': [
                {k: v for k, v in question.__dict__.items() if not isinstance(v, InstanceState)}
                for question in self.questions
            ],
            'score': {k: v for k, v in self.score[-1].__dict__.items() if not isinstance(v, InstanceState)} if self.score else {},
            'team': {k: v for k, v in self.team.__dict__.items() if not isinstance(v, InstanceState)},
        }


class GameScoreModel(db):
    __tablename__ = "game_scores"
    #
    id = Column(Integer, primary_key=True)
    game_result = Column(Integer)
    points_wins = Column(Integer)
    points_loss = Column(Integer)
    game_id = Column(
        Integer,
        ForeignKey("games.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    game = relationship("GameModel", back_populates="score")


# для хранения вопросов
class QuestionModel(db):
    __tablename__ = "questions"
    #
    id = Column(Integer, primary_key=True)
    virgin = Column(BOOLEAN, default=True)
    context = Column(VARCHAR(32), nullable=False)
    question = Column(VARCHAR(512), nullable=False, unique=True)
    story = Column(TEXT, nullable=True)
    answers = Column(ARRAY(VARCHAR(256)))
    used_questions = relationship(
        "UsedQuestionModel", cascade="all,delete", back_populates="questions"
    )
    games = relationship(
        "GameModel", secondary="_games_questions", back_populates="questions"
    )

    def to_dataclass(self):
        return QuestionDC(
            question=self.question,
            context=self.context,
            story=self.story,
            answers=self.answers,
            id_db=self.id,
        )


class UsedQuestionModel(db):
    __tablename__ = "used_questions"
    #
    id = Column(Integer, primary_key=True)
    question_id = Column(
        Integer,
        ForeignKey("questions.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    chat_id = Column(VARCHAR(32), nullable=False)
    user_id = Column(VARCHAR(32), nullable=False)
    questions = relationship(
        "QuestionModel", cascade="all,delete", back_populates="used_questions"
    )


# пара технических моделек для реализации many-2-many связей
class PlayerTeamModel(db):
    __tablename__ = "_players_teams"
    #
    player_id = Column(
        VARCHAR(32), ForeignKey("players.user_id"), primary_key=True
    )
    team_id = Column(Integer, ForeignKey("teams.id"), primary_key=True)


class GameQuestionModel(db):
    __tablename__ = "_games_questions"

    game_id = Column(Integer, ForeignKey("games.id"), primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id"), primary_key=True)


# для хранения данных текущего состояния
class CurrentParamsModel(db):
    __tablename__ = "current"
    #
    current = Column(LargeBinary, primary_key=True)

    # {'id': 18, 'created_at': datetime.datetime(2023, 4, 1, 23, 33, 5, 754870, tzinfo=datetime.timezone.utc), 'team_id': 126,
    # 'team': <kts_backend.game.models.TeamModel object at 0x10bd80eb0>,
    # 'questions': [<kts_backend.game.models.QuestionModel object at 0x10bdaea60>, <kts_backend.game.models.QuestionModel object at 0x10bdaea90>],
    # 'score': [<kts_backend.game.models.GameScoreModel object at 0x10bddd6a0>]}


""" Старая версия

class PlayerModel(db):
    __tablename__ = 'Players'
    #
    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(VARCHAR(32), nullable=False)
    name = Column(VARCHAR(32))
    last_name = Column(VARCHAR(32))
    game_id = Column(
        Integer,
        ForeignKey('Games.game_id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False,
    )
    score = relationship('GameScoreModel', cascade='all,delete')


class GameModel(db):
    __tablename__ = 'Games'
    #
    game_id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    chat_id = Column(VARCHAR(32), nullable=False)
    players = relationship('PlayerModel', cascade='all,delete')

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
            'id': self.game_id,
            'created_at': str(self.created_at),
            'chat_id': self.chat_id,
            'players': [
                {
                    'tg_id': p.tg_id,
                    'name': p.name,
                    'last_name': p.last_name,
                    'score': {'points': p.score[-1].points},
                }
                for p in self.players
            ],
        }


class GameScoreModel(db):
    __tablename__ = 'GameScores'
    #
    id = Column(Integer, primary_key=True)
    player_id = Column(
        Integer,
        ForeignKey('Players.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False,
    )
    game_id = Column(
        Integer,
        ForeignKey('Games.game_id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False,
    )
    points = Column(Integer)


Старая версия """
