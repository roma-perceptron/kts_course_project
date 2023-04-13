import yaml
import typing
from dataclasses import dataclass

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application


@dataclass
class DatabaseConfig:
    host: str = 'localhost'
    port: int = 5432
    user: str = 'postgres'
    password: str = 'postgres'
    database: str = 'postgres'


@dataclass
class SessionConfig:
  key: str


@dataclass
class AdminConfig:
  email: str
  password: str


@dataclass
class BotConfig:
    token: str
    bot_name: str


@dataclass
class OpenAIConfig:
    token: str
    orgid: str


@dataclass
class Config:
    database: DatabaseConfig
    bot: BotConfig
    openai: OpenAIConfig
    session: SessionConfig
    admin: AdminConfig


def get_config(config_path: str = 'config.yml'):
    with open(config_path, mode='r') as f:
        raw_config = yaml.safe_load(f)

    return Config(
        database=DatabaseConfig(
            host=raw_config['database']['host'],
            port=raw_config['database']['port'],
            user=raw_config['database']['user'],
            password=raw_config['database']['password'],
            database=raw_config['database']['database'],
        ),
        bot=BotConfig(
            token=raw_config['bot']['token'],
            bot_name=raw_config['bot']['bot_name'],
        ),
        openai=OpenAIConfig(
            token=raw_config['openai']['token'],
            orgid=raw_config['openai']['orgid'],
        ),
        session=SessionConfig(
            key=raw_config['session']['key'],
        ),
        admin=AdminConfig(
            email=raw_config['admin']['email'],
            password=raw_config['admin']['password'],
        ),
    )


def setup_config(app: 'Application', config_path: str):
    app.config = get_config(config_path)
