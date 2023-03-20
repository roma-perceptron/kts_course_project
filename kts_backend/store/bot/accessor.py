from sqlalchemy import select

from kts_backend.store.base_accessor import BaseAccessor

from kts_backend.game.models import GameModel, PlayerModel, GameScoreModel

from sqlalchemy.orm import selectinload, joinedload, subqueryload
from sqlalchemy.orm import Bundle


class BotAccessor(BaseAccessor):
    async def update_game(self):
        pass

    async def _create_game(self, chat_id: str) -> str:
        model_with_params = GameModel(chat_id=chat_id)
        game = await self.execute_query_creation(model_with_params)
        return game.game_id

    async def _create_players(self, game_id: str, players: list):
        player_ids = []
        for player in players:
            model_with_params = PlayerModel(
                game_id=game_id,
                tg_id=str(player["message"]["from"]["id"]),
                name=player["message"]["from"]["first_name"],
                last_name=player["message"]["from"]["last_name"],
            )
            player_id = await self.execute_query_creation(model_with_params)
            player_ids.append(player_id.id)
        #
        return player_ids

    async def create_game(self, chat_id: int, players: list):
        # сначала создаем запись в таблице Games, получаем game_id
        # создаем записи в табле Players, добавляем участников с game_id
        # возвращем game_id чтобы потом писать результаты..
        game_id = await self._create_game(str(chat_id))
        player_ids = await self._create_players(game_id, players)
        return game_id, player_ids

    async def create_score(self, game_id, player_ids, player_points):
        for player_id, player_score in zip(player_ids, player_points):
            print(player_id, player_score)
            model_with_params = GameScoreModel(
                player_id=player_id, game_id=game_id, points=player_score
            )
            await self.execute_query_creation(model_with_params)

    async def _get_game(self, game_id: int = 1):
        query = (
            select(GameModel)
            .where(GameModel.game_id == game_id)
            .options(
                subqueryload(GameModel.players).options(
                    subqueryload(PlayerModel.score)
                )
            )
        )
        data = await self.execute_query(query, only_last=True)
        return data

    async def get_last_game(self, chat_id: int):
        query = (
            select(GameModel.game_id)
            .order_by(GameModel.created_at.desc())
            .where(GameModel.chat_id == str(chat_id))
        )
        last_game_id = await self.execute_query(query, only_last=True)
        game_data = await self._get_game(game_id=last_game_id)
        return game_data

    async def get_all_players(self):
        query = select(
            PlayerModel.tg_id, PlayerModel.name, PlayerModel.last_name
        ).distinct()
        players = await self.execute_query(query)
        return [
            {
                "tg_id": player.tg_id,
                "name": player.name,
                "last_name": player.last_name,
            }
            for player in players
        ]
