import asyncio
from typing import Optional

from sqlalchemy import select, func, not_, or_, update, delete
from sqlalchemy.engine import ChunkedIteratorResult
from sqlalchemy.exc import InvalidRequestError

from kts_backend.game.dataclasses import (
    QuestionDC,
    GameScoreDC,
)
from kts_backend.store.base_accessor import BaseAccessor

from kts_backend.game.models import (
    GameModel,
    PlayerModel,
    GameScoreModel,
    QuestionModel,
    UsedQuestionModel,
    TeamModel,
    GameQuestionModel,
    PlayerTeamModel,
)

from sqlalchemy.orm import selectinload, joinedload, subqueryload
from sqlalchemy.exc import DBAPIError


class BotAccessor(BaseAccessor):
    def __init__(self, app):
        super().__init__(app)

    async def update_game(self):
        pass

    # #
    # async def _create_game(self, chat_id: str) -> str:
    #     model_with_params = GameModel(chat_id=chat_id)
    #     game = await self.execute_query_creation(model_with_params)
    #     return game.game_id
    #
    # #
    # async def _create_players(self, game_id: str, players: list):
    #     player_ids = []
    #     for player in players:
    #         model_with_params = PlayerModel(
    #             game_id=game_id,
    #             tg_id=str(player["message"]["from"]["id"]),
    #             name=player["message"]["from"]["first_name"],
    #             last_name=player["message"]["from"]["last_name"],
    #         )
    #         player_id = await self.execute_query_creation(model_with_params)
    #         player_ids.append(player_id.id)
    #     #
    #     return player_ids
    #
    # #
    # async def create_game(self, chat_id: int, players: list):
    #     # сначала создаем запись в таблице Games, получаем game_id
    #     # создаем записи в табле Players, добавляем участников с game_id
    #     # возвращем game_id чтобы потом писать результаты..
    #     game_id = await self._create_game(str(chat_id))
    #     player_ids = await self._create_players(game_id, players)
    #     return game_id, player_ids
    #
    # #
    # async def create_score_OLD(self, game_id, player_ids, player_points):
    #     for player_id, player_score in zip(player_ids, player_points):
    #         print(player_id, player_score)
    #         model_with_params = GameScoreModel(
    #             player_id=player_id, game_id=game_id, points=player_score
    #         )
    #         await self.execute_query_creation(model_with_params)

    #
    # async def _get_game(self, game_id: int = 1):
    #     query = (
    #         select(GameModel)
    #             .where(GameModel.game_id == game_id)
    #             .options(
    #             subqueryload(GameModel.players).options(
    #                 subqueryload(PlayerModel.score)
    #             )
    #         )
    #     )
    #     data = await self.execute_query(query, only_last=True)
    #     return data
    #
    # #
    # async def get_last_game(self, chat_id: int):
    #     query = (
    #         select(GameModel.game_id)
    #             .order_by(GameModel.created_at.desc())
    #             .where(GameModel.chat_id == str(chat_id))
    #     )
    #     last_game_id = await self.execute_query(query, only_last=True)
    #     game_data = await self._get_game(game_id=last_game_id)
    #     return game_data
    #
    # #
    # async def get_all_players(self):
    #     query = select(
    #         PlayerModel.tg_id, PlayerModel.name, PlayerModel.last_name
    #     ).distinct()
    #     players = await self.execute_query(query)
    #     print('players:', players)
    #     return [
    #         {
    #             "tg_id": player.tg_id,
    #             "name": player.name,
    #             "last_name": player.last_name,
    #         }
    #         for player in players
    #     ]
    #
    # #
    # async def make_fake_game(self):
    #     game_id, player_ids = await self.create_game(
    #         chat_id=FAKE_CHAT_ID, players=FAKE_PLAYERS
    #     )
    #     print("setp1 ok")
    #     await self.create_score_OLD(
    #         game_id=game_id,
    #         player_ids=player_ids,
    #         player_points=get_random_scores(),
    #     )
    #     print("setp2 ok")
    #     return "Yeah, new fake game just created! Check the last game command.."

    #

    async def get_all_players(self, with_teams=False):
        if with_teams:
            query = select(PlayerModel).options(subqueryload(PlayerModel.teams))
        else:
            query = select(PlayerModel)
        players = await self.execute_query(query)
        players = [player[0].to_dataclass().__dict__ for player in players]
        return players

    #
    async def get_last_game(self):
        query = (
            select(GameModel)
            .options(subqueryload(GameModel.team))
            .options(subqueryload(GameModel.score))
            .options(subqueryload(GameModel.questions))
            .order_by(GameModel.id.desc())
        )
        async with self.database.session.begin() as session:
            result: ChunkedIteratorResult = await session.execute(query)
            result = result.fetchone()
            if result:
                return result[0]
            else:
                return None

    #
    async def set_question_to_db(self, raw_questions):
        questions = []
        for question in raw_questions:
            try:
                question_model = await self.execute_query_creation(
                    QuestionModel(
                        question=question.question,
                        answers=question.answers,
                        story=question.story,
                        context=question.context,
                        complexity=question.complexity
                    )
                )
                questions.append(question_model)
            except DBAPIError as exp:
                print("Error on sqlAlchemy:", exp)
                continue
        #
        questions = [question.to_dataclass() for question in questions]
        return questions

    #
    async def make_new_questions(self, **kwargs):
        # new_questions = gpt_master.get_question(**kwargs)
        loop = asyncio.get_event_loop()
        new_questions = await loop.run_in_executor(None, self.app.GPT_master.get_question, kwargs)
        questions = await self.set_question_to_db(raw_questions=new_questions)
        #
        return questions

    #
    async def get_questions_from_db__virgin(self, count=1):
        query = (
            select(QuestionModel)
            .where(QuestionModel.virgin)
            .order_by(func.random())
            .limit(count)
        )
        questions = await self.execute_query(query)

        # q[0] потому что приходит объект модели
        questions = [question[0].to_dataclass() for question in questions]
        return questions

    #
    async def get_questions_from_db__reused(
        self,
        count: int = 11,
        chat_id: Optional[str] = None,
        user_ids: Optional[list[str]] = (),
    ):
        query = (
            select(QuestionModel)
            .where(
                ~QuestionModel.used_questions.any(
                    or_(
                        UsedQuestionModel.chat_id == chat_id,
                        UsedQuestionModel.user_id.in_(user_ids),
                    )
                )
            )
            .order_by(func.random())
            .limit(count)
        )
        questions = await self.execute_query(query)

        questions = [
            question[0].to_dataclass()  # q[0] потому что приходит объект модели
            for question in questions
        ]
        return questions

    #
    async def mark_as_non_virgin(self, id_db: list[int]):
        query = (
            update(QuestionModel)
            .where(QuestionModel.id.in_(id_db))
            .values(virgin=False)
        )
        result = await self.execute_query(query, no_return=True)

    #
    async def add_questions_to_used(
        self, question: QuestionDC, chat_id: str, team: list[dict]
    ):
        for player in team:
            model_with_params = UsedQuestionModel(
                chat_id=chat_id,
                user_id=player["user_id"],
                question_id=question.id_db,
            )
            await self.execute_query_creation(model_with_params)

    #
    # Новые методы для новых моделей
    #
    async def create_new_team(self, chat_id):
        await self.execute_query_creation(TeamModel(chat_id=chat_id))

    #
    async def get_or_create_player(self, player_data: dict):
        player, created = await self.get_or_create(PlayerModel, **player_data)
        return player, created

    #
    async def get_current_team(self, chat_id: str):
        async with self.database.session.begin() as session:
            query = (
                select(TeamModel)
                .where(TeamModel.chat_id == chat_id)
                .options(subqueryload(TeamModel.players))
                .order_by(TeamModel.id.desc())
            )
            result = await session.execute(query)
            team = result.scalars().first()
            return team

    #
    async def get_current_game(self, team_id: int):
        async with self.database.session.begin() as session:
            query = (
                select(GameModel)
                .where(GameModel.team_id == team_id)
                .options(subqueryload(GameModel.questions))
                .options(subqueryload(GameModel.score))
            )
            result = await session.execute(query)
            game = result.scalars().one()
            return game

    #
    async def add_player_to_current_team__DEPRECATED(
        self, chat_id: str, player: PlayerModel
    ):
        # ужасно вымученный вариант..
        async with self.database.session.begin() as session:
            team: TeamModel = await self.get_current_team(chat_id)
            try:
                team.players.append(player)
            except InvalidRequestError:
                pass
            await session.commit()

    #
    async def add_player_to_current_team(
        self, chat_id: str, player: PlayerModel
    ):
        team: TeamModel = await self.get_current_team(chat_id)
        #
        model_with_params = PlayerTeamModel(
            team_id=team.id,
            player_id=player.user_id,
        )
        await self.execute_query_creation(model_with_params)

    #
    async def add_question_to_game(self, game_id: int, question_id: int):
        model_with_params = GameQuestionModel(
            game_id=game_id, question_id=question_id
        )
        await self.execute_query_creation(model_with_params)

    #
    async def update_or_create_current_game(
        self, chat_id: str, rounds: Optional[dict] = None
    ):
        team: TeamModel = await self.get_current_team(chat_id)
        game, created = await self.get_or_create(GameModel, team_id=team.id)
        #
        if rounds:
            # запись всех вопросов
            for game_round in rounds:
                await self.add_question_to_game(
                    game_id=game.id, question_id=game_round["question"].id_db
                )

            #  создание записи score
            await self.create_score(
                self.convert_rounds_to_score(game.id, rounds)
            )

    @staticmethod
    def convert_rounds_to_score(game_id: int, rounds: dict):
        points_wins = sum(game_round["score"] for game_round in rounds)
        points_loss = len(rounds) - points_wins
        if points_wins > points_loss:
            game_result = 1
        elif points_loss > points_wins:
            game_result = 0
        else:
            game_result = 2
        #
        return GameScoreModel(
            game_id=game_id,
            game_result=game_result,
            points_wins=points_wins,
            points_loss=points_loss,
        )

    #
    async def create_score(self, score: GameScoreDC):
        model_with_params = GameScoreModel(
            game_id=score.game_id,
            game_result=score.game_result,
            points_wins=score.points_wins,
            points_loss=score.points_loss,
        )
        await self.execute_query_creation(model_with_params)
