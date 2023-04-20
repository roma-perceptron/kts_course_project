import json
import aiohttp_jinja2

from aiohttp.web_exceptions import HTTPForbidden
from aiohttp_session import new_session

from kts_backend.utils import hash_it
from kts_backend.web.app import View
from kts_backend.web.utils import json_response
from aiohttp_apispec import request_schema, response_schema, querystring_schema

from kts_backend.api.schemes import BaseScheme, MakeQuestionScheme, LastGame, QuestionsScheme


async def get_payload(view_object: View):
    content_type = view_object.request.headers.get('Content-Type')
    if content_type == 'application/json':
        payload = await view_object.request.json()
    elif view_object.request.get("data", None):
        payload = view_object.request.get("data", None)
    else:
        payload = {k: int(v) if v.isdigit() else v for k, v in view_object.request.query.items()}
    return payload


class LoginView(View):
    async def post(self):
        print('ok, i\'m here:', self.__class__.__name__)
        payload = await get_payload(self)
        admin = await self.admin_manager.accessor.get_admin(
            email=payload.get('email', ''),
            password=hash_it(payload.get('password', ''))
        )
        if admin:
            admin = admin[0]
            session = await new_session(request=self.request)
            session['admin'] = True
            return json_response(data={'id': admin.id, 'email': admin.email})
        else:
            session = await new_session(request=self.request)
            session['admin'] = False
            raise HTTPForbidden


class TestView(View):
    @querystring_schema(BaseScheme)
    @response_schema(BaseScheme)
    async def get(self):
        print('ok, i\'m here:', self.__class__.__name__)
        payload = await get_payload(self)
        #
        return json_response(data=payload)


class GetLastGame(View):
    @querystring_schema(LastGame)
    async def get(self):
        print('ok, i\'m here:', self.__class__.__name__)
        payload = await get_payload(self)
        game = await self.manager.accessor.get_last_game()
        #
        return json_response(data=game.to_serializable() if game else [])


class GetPlayers(View):
    @querystring_schema(BaseScheme)
    async def get(self):
        print('ok, i\'m here:', self.__class__.__name__)
        payload = await get_payload(self)
        players = await self.manager.accessor.get_all_players()
        #
        return json_response(data=players)


class GetQuestions(View):
    @querystring_schema(BaseScheme)
    @response_schema(QuestionsScheme)
    async def get(self):
        print('ok, i\'m here:', self.__class__.__name__)
        payload = await get_payload(self) or {}
        questions_dc = await self.manager.accessor.get_questions_from_db__reused(**payload)
        questions = [question.__dict__ for question in questions_dc]
        print('\n', questions)
        #
        return json_response(data=questions)


class MakeQuestions(View):
    @querystring_schema(MakeQuestionScheme)
    async def get(self):
        print('ok, i\'m here:', self.__class__.__name__)
        payload = await get_payload(self) or {}
        questions_dc = await self.manager.accessor.make_new_questions(**payload)
        questions = [question.__dict__ for question in questions_dc]
        #
        return json_response(data=questions)


class IndexView(View):
    async def get(self):
        print('ok, i\'m here:', self.__class__.__name__)
        context = {}
        response = aiohttp_jinja2.render_template('index.html', self.request, context)
        return response
