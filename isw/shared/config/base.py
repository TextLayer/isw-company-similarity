import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).resolve().parents[3] / '.env'
load_dotenv(dotenv_path=env_path)


@dataclass
class BaseConfig:
    """Shared configuration across all apps"""

    # Environment
    env: str
    debug: bool
    testing: bool

    # API Key
    api_key: str

    # Celery
    celery_broker_url: str
    celery_task_ignore_result: bool
    celery_result_backend: str
    celery_task_always_eager: bool

    # RabbitMQ
    rabbitmq_username: str
    rabbitmq_password: str

    # Database
    database_url: str
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_echo: bool = False

    @staticmethod
    def get_env(key: str, default: Any = None, required: bool = False, type: Any = str):
        """Utility method for getting environment variables with type conversion"""
        value = os.environ.get(key, default)
        if required and value is None:
            raise ValueError(f"Environment variable {key} is required")

        if isinstance(value, type):
            return value

        if type is list:
            if not value or value.strip() == "":
                return default if default is not None else []
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return default if default is not None else []
        elif type is bool:
            return value.lower() == "true"
        elif type is float:
            return float(value)
        elif type is dict:
            return json.loads(value)
        elif type is tuple:
            return tuple(json.loads(value))

        return type(value)


    @classmethod
    def from_env(cls):
        """Create config from environment variables"""

        return cls(
            # Environment
            env=cls.get_env("ENV", default="development"),
            debug=cls.get_env("DEBUG", default=False, type=bool),
            testing=cls.get_env("TESTING", default=False, type=bool),
            # API Key
            api_key=cls.get_env("API_KEY", default=""),
            # Celery
            celery_broker_url=cls.get_env("CELERY_BROKER_URL", default="pyamqp://textlayer:admin@localhost:5672/"),
            celery_task_ignore_result=cls.get_env("CELERY_TASK_IGNORE_RESULT", default=False, type=bool),
            celery_task_always_eager=cls.get_env("CELERY_TASK_ALWAYS_EAGER", default=False, type=bool),
            celery_result_backend=cls.get_env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/0"),
            # RabbitMQ
            rabbitmq_username=cls.get_env("RABBITMQ_USERNAME", default="textlayer"),
            rabbitmq_password=cls.get_env("RABBITMQ_PASSWORD", default="admin"),
            # Database
            database_url=cls.get_env("DATABASE_URL", default="postgresql://insight_user:insight_password@localhost:5432/insight_db"),
            database_pool_size=cls.get_env("DATABASE_POOL_SIZE", default=5, type=int),
            database_max_overflow=cls.get_env("DATABASE_MAX_OVERFLOW", default=10, type=int),
            database_echo=cls.get_env("DATABASE_ECHO", default=False, type=bool),
        )
