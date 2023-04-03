from kts_backend.web.app import View
from kts_backend.web.utils import json_response


async def get_payload(view_object: View):
    content_type = view_object.request.headers.get('Content-Type')
    if content_type == 'application/json':
        payload = await view_object.request.json()
    else:
        payload = view_object.request.get("data", None)
    return payload


class TestView(View):
    async def get(self):
        print('ok, i\'m here:', self.__class__.__name__)
        payload = await get_payload(self)
        print(payload)
        #
        return json_response(data=payload)


class GetLastGame(View):
    async def get(self):
        print('ok, i\'m here:', self.__class__.__name__)
        payload = await get_payload(self)
        game = await self.manager.accessor.get_last_game()
        print(payload)
        #
        return json_response(data=game.to_serializable())


class GetPlayers(View):
    async def get(self):
        print('ok, i\'m here:', self.__class__.__name__)
        payload = await get_payload(self)
        players = await self.manager.accessor.get_all_players()
        print(payload)
        #
        return json_response(data=players)


class GetQuestions(View):
    async def get(self):
        print('ok, i\'m here:', self.__class__.__name__)
        payload = await get_payload(self) or {}
        questionsDC = await self.manager.accessor.get_questions_from_db__reused(**payload)
        questions = [question.__dict__ for question in questionsDC]
        print(payload)
        print('\n', questions)
        #
        return json_response(data=questions)
