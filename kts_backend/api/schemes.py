from marshmallow import Schema, fields

    #

class BaseScheme(Schema):
    # key = fields.String(required=False)
    pass


class LastGame(Schema):
    chat_id = fields.String(required=False)


class MakeQuestionScheme(Schema):
    theme = fields.String(required=False)
    count = fields.Integer(required=False)
    complexity = fields.Int(required=False)


class AnswerScheme(Schema):
    answer = fields.String(required=False)


class QuestionScheme(Schema):
    context = fields.String(required=True)
    question = fields.String(required=False)
    answers = fields.Nested(AnswerScheme, many=True)
    story = fields.String(required=False)
    complexity = fields.Integer(required=False)
    id_db = fields.Integer(required=False)


class QuestionsScheme(Schema):
    questions = fields.Nested(QuestionScheme, many=True)

