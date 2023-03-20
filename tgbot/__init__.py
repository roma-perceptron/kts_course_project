from tgbot import tgbot


def setup_bot(updates_queue, answers_queue):
    return (
        tgbot.Poller(updates_queue=updates_queue),
        tgbot.Sender(answers_queue=answers_queue),
    )
