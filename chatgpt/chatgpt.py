import json
import os
import re
import random
from typing import Optional

import openai
from openai.error import APIConnectionError, RateLimitError

from kts_backend.game.dataclasses import QuestionDC
from kts_backend.web.config import OpenAIConfig

THEMES = ['власть', 'музыкальные инструменты', 'женщины', 'оружие', 'религия', 'искусство', 'спорт', 'музыка',
          'история', 'кинематограф', 'чудеса природы', 'чудеса света', 'античный мир', 'история США', 'химия',
          'физика', 'биология', 'наука', 'собаки', 'кошки', 'домашние животные', 'мистика', 'алкоголь', 'юмор',
          'программирование', 'деньги', 'технологии', 'компьютер', 'chatGPT', 'фрукты', 'овощи']

FORMULA_NEW = [
    'Сгенерируйте вопрос для игры "Что? Где? Когда?" на тему [__THEME__], который будет состоять из тех частей.',
    'answer: ответа на этот вопрос длинной не более двух слов. Ответ не должен будет содержаться в остальных частях ни в какой форме. Это очень важно!',
    'story: короткого вступителения, которое может быть: исторической ретроспективой, стихотворением, аллегорией, притчей, историей о реальном человеке. Story должна быть похожа на загадку.',
    'question: краткого конкретного вопроса',
    'Вопрос должен начинаться с фразы "Внимание вопрос:"',
    'Вступление и вопрос должны быть построены так, чтобы ответ можно было найти с помощью логического поиска, но и с использованием каких-то знаний пряом не указанных в вопросе, но упомянутых намеком. По принципу загадки.',
    'Уровень сложности вопроса: __COMPLEX__/10',
    'Дай свой ответ в форме json объекта с полями story:str , question:str, answer: List[str].'
]

FORMULA_OLD = [
    'Ты ведущий интеллектуальной игры "Что? Где? Когда?".',
    'Тема игры: [__THEME__].',
    'Тебе нужно сформулировать вступительный текст или историю, вопрос и ответ.',
    'Вступительный текст должен быть сложным, коротким, парадоксальным, метафоричным, содержать историческую справку.',
    'Вступительный текст не должен содержать вопроса и ответа.',
    'Вопрос должен начинаться с фразы «Внимание вопрос». Вопрос не должен содержать ответ ни в какой форме.',
    'Ответ должен быть очень коротким. Не больше 128 символов.',
    'Сформулируй вступительный текст (story), вопрос (question) и ответ (answer) в форме json объекта с полями story:str , question:str, answer: List[str].',
]


def get_theme():
    return random.choice(THEMES)


TOKEN = os.getenv('OPENAI_TOKEN')
ORGID = os.getenv('OPENAI_ORGID')


class MasterOfTheGame:
    def __init__(self, config: OpenAIConfig):
        openai.organization = config.orgid
        openai.api_key = config.token
        self.chat_completion = openai.ChatCompletion
        self.base_model = 'gpt-3.5-turbo'
        self.system_context = 'Ты задаешь сложные вопросы интеллектуальной игры'

    @staticmethod
    def answer_in_question(question: QuestionDC):
        question_words = re.split(
            r'\W+',
            '. '.join([question.story, question.question]).lower()
        )
        answer_words = re.split(r'\W+', ' '.join(question.answers).lower())
        return any([answer_word in question_words for answer_word in answer_words])

    def get_question(self, kwargs):  # не **kwargs из-за какого-то несварения в обертке из loop.run_in_executor
        theme = kwargs.get('theme', None)
        count = kwargs.get('count', 5)
        complexity = kwargs.get('complexity', 8)
        sys_context = kwargs.get('sys_context', None)
        #
        try:
            theme = get_theme() if not theme else theme
            complexity = 10 if complexity > 10 else complexity
            complexity = 1 if complexity < 1 else complexity
            res = self._get_question(theme, count, complexity, sys_context)
        except RateLimitError:
            print('RateLimitError')
            return []
        except APIConnectionError as exp:
            print("Oh no! API error!", exp)
            return []
        except Exception as exp:
            print('Такого ты еще не видал..', exp)
            return []
        #
        return res

    #
    def _get_question(
            self,
            theme: str,
            count: int = 1,
            complexity: int = 8,
            sys_context: Optional[str] = None
    ):
        print('theme', theme)
        messages = [
            {
                'role': 'user',
                'content': formula_part
                    .replace('__THEME__', theme)
                    .replace('__COMPLEX__', str(complexity))
            }
            for formula_part in FORMULA_NEW
        ]

        if sys_context:
            messages.insert(0, {'role': 'system', 'content': sys_context})
        #
        completion = self.chat_completion.create(
            model=self.base_model,
            messages=messages,
            temperature=0.5,
            n=count
            # top_p=2,
        )
        #
        # print('messages:', messages, '\n')
        # print('completion', completion, '\n')
        # print('usage', completion.usage, '\n')
        #
        questions = []
        for version in completion.choices:
            try:
                version = json.loads(version.message.content)
                question = QuestionDC(
                    question=version['question'],
                    story=version['story'],
                    answers=version['answer'],
                    context=theme,
                    complexity=complexity,
                )
                if not self.answer_in_question(question):
                    questions.append(question)
            except Exception as exp:
                print(exp)
                # print('chatGPT result:', version)
                continue
        #
        return questions

    def check_answer(self, question: QuestionDC, team_answer: str):
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
        #
        try:
            completion = self.chat_completion.create(
                model=self.base_model,
                messages=messages
            )
        except RateLimitError:
            print('RateLimitError')
            return False
        except APIConnectionError:
            print('APIConnectionError')
            return False
        #
        try:
            result = json.loads(completion.choices[0].message.content)
            return result.get('answer', False)
        except Exception as exp:
            print(exp)
            print('chatGPT result:', completion.choices[0])
            return False


# gpt_master = MasterOfTheGame()
