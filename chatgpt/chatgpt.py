import json
import os
from typing import Optional

import openai

from kts_backend.game.dataclasses import QuestionDC

import random

THEMES = ['власть', 'музыкальные инструменты', 'женщины', 'оружие', 'религия', 'искусство', 'спорт', 'музыка',
          'история', 'кинематограф', 'чудеса природы', 'античный мир', 'история США', 'химия', 'физика', 'биология',
          'наука', 'собаки', 'кошки', 'домашние животные', 'мистика', 'алкоголь', 'юмор', 'программирование',
          'деньги', 'технологии', 'компьютер', 'chatGPT', 'фрукты', 'овощи']


def get_theme():
    return random.choice(THEMES)


TOKEN = os.getenv('OPENAI_TOKEN')
ORGID = os.getenv('OPENAI_ORGID')


class MasterOfTheGame:
    def __init__(self):
        openai.organization = ORGID
        openai.api_key = TOKEN
        self.chat_completion = openai.ChatCompletion
        self.base_model = 'gpt-3.5-turbo'
        self.system_context = 'Ты задаешь сложные вопросы интеллектуальной игры'

    def get_question(self, theme: str, count: int = 1, sys_context: Optional[str] = None):
        return self._get_question(theme, count, sys_context)

    def _get_question(self, theme: str, count: int = 1, sys_context: Optional[str] = None):
        messages = [
            # {
            #     'role': 'user',
            #     'content': f'Ты ведущий интеллектуальной игры "Что? Где? Когда?". Тема игры: {quest.context}. Тебе нужно сформулировать вступительный текст или историю, вопрос и ответ. Вступительный текст должен быть сложным, коротким, парадоксальным, метафоричным, содержать историческую справку. Вступительный текст не должен содержать вопроса и ответа. Вопрос должен начинаться с фразы «Внимание вопрос» и не должен содержать ответа. Ответ должен быть очень коротким. Сформулируй вступительный текст(story), вопрос (question) и ответ (answer) в форме json объекта с полями story:str , question:str, answer: List[str].'
            # }
            {
                'role': 'user',
                'content': 'Ты ведущий интеллектуальной игры "Что? Где? Когда?".'
            },
            {
                'role': 'user',
                'content': f'Тема игры: {theme}.'
            },
            {
                'role': 'user',
                'content': 'Тебе нужно сформулировать вступительный текст или историю, вопрос и ответ.'
            },
            {
                'role': 'user',
                'content': 'Вступительный текст должен быть сложным, коротким, парадоксальным, метафоричным, содержать историческую справку.'
            },
            {
                'role': 'user',
                'content': 'Вступительный текст не должен содержать вопроса и ответа.'
            },
            {
                'role': 'user',
                'content': 'Вопрос должен начинаться с фразы «Внимание вопрос». Вопрос не должен содержать ответ ни в какой форме.'
            },
            {
                'role': 'user',
                'content': 'Ответ должен быть очень коротким. Не больше 128 символов.'
            },
            {
                'role': 'user',
                'content': 'Сформулируй вступительный текст (story), вопрос (question) и ответ (answer) в форме json объекта с полями story:str , question:str, answer: List[str].'
            }
        ]
        if sys_context:
            messages.insert(0, {'role': 'system', 'content': sys_context})
        #
        completion = self.chat_completion.create(
            model=self.base_model,
            messages=messages,
            # top_p=2,
            temperature=0.85,
            n=count
        )
        #
        print('messages:', messages, '\n')
        print('completion', completion, '\n')
        print('usage', completion.usage, '\n')
        #
        questions = []
        for version in completion.choices:
            try:
                version = json.loads(version.message.content)
                question = QuestionDC(
                    question=version['question'],
                    story=version['story'],
                    answers=version['answer'],
                    context=theme
                )
                questions.append(question)
            except Exception as exp:
                print(exp)
                print('chatGPT result:', version)
                continue
        #
        return questions

    async def check_answer(self, question: QuestionDC, team_answer: str):
        messages = [
            {
                'role': 'user',
                'content': f'Вопрос: {question.story} {question.question}'
            },
            {
                'role': 'user',
                'content': f'Ответ: {team_answer}.'
            },
            {
                'role': 'user',
                'content': 'Это правильный ответ? Напиши в виде json в формате answer: bool.'
            },
        ]
        completion = self.chat_completion.create(
            model=self.base_model,
            messages=messages
        )
        try:
            result = json.loads(completion.choices[0].message.content)
            print("CHAT GPT FACTCHECK RESULT:", result)
            return result.get('answer', False)
        except Exception as exp:
            print(exp)
            print('chatGPT result:', completion.choices[0])
            return False


gpt_master = MasterOfTheGame()