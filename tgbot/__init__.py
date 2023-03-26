from tgbot import tgbot


def setup_poller(app):
    return tgbot.Poller(app)


def setup_sender(app):
    return tgbot.Sender(app)
