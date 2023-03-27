import logging
import typing

if typing.TYPE_CHECKING:
    from app import Application


def setup_logging(app: "Application") -> None:
    """Здесь происходит настройка логирования"""
    logging.basicConfig(level=logging.DEBUG)
    app.logger.info("Starting logging")
