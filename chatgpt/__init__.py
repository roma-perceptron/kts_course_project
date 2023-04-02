from dataclasses import dataclass
from typing import Optional


@dataclass
class Question:
    question: Optional[str] = ''
    answers: list[str] = list
    context: Optional[str] = ''
    story: Optional[str] = ''

FAKE_QUESTION = Question(
    question="Почему сосиски продаются по 10 штук в пачке, а хот-доги по 9?",
    answers=['42', 'ave ChatGPT', 'потому что гладиолус!'],
    context='Тупой вопрос',
    story='В 1786 году, в кафе на берегу Женевского озера встретили два видных представителя..'
)