import json
import os
from dataclasses import dataclass
from typing import Any


@dataclass
class BaseConfig:
    """Shared configuration across all apps"""

    # Environment
    env: str
    debug: bool
    testing: bool

    # API Key
    api_key: str

    # (removed) Ashby

    # AWS
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str

    # CDN
    cdn_url: str

    # Client
    client_url: str

    # Celery
    celery_broker_url: str
    celery_task_ignore_result: bool
    celery_result_backend: str
    celery_task_always_eager: bool

    # (removed) Doppler

    # JWT
    jwt_secret: str
    jwt_algorithm: str

    # (kept) GitHub app for prompts workflow
    github_app_id: str
    github_app_installation_id: str
    github_app_private_key: str

    # Evals
    evals_provider: str

    # (removed) Mail/SendGrid

    # (removed) OCR

    # (removed) Mistral OCR

    # RabbitMQ
    rabbitmq_username: str
    rabbitmq_password: str

    # Search
    search_provider: str
    opensearch_host: str
    opensearch_username: str
    opensearch_password: str
    search_default_results_per_page: int

    # Prompt
    prompt_provider: str
    prompt_label: str

    # Langfuse
    langfuse_public_key: str
    langfuse_secret_key: str
    langfuse_host: str
    langfuse_signing_secret_prompts: str

    # (removed) Recruitment

    # (removed) Onboarding

    # (removed) Research

    # Sentry
    sentry_backend_dsn: str
    sentry_auth_token: str

    # Storage
    storage_provider: str

    # LLM
    chat_models: list
    embedding_models: list
    embedding_dimension: int

    # OpenAI
    openai_api_key: str

    # Anthropic
    anthropic_api_key: str

    # Redis
    redis_url: str

    # (removed) Notion

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
    def init_observability(self):
        """Initialize observability"""
        import litellm

        from isw.core.services.observability.integrations import LiteLLMCallbackHandler

        handler = LiteLLMCallbackHandler()
        litellm.callbacks = [handler]

    @classmethod
    def from_env(cls):
        """Create config from environment variables"""
        cls.init_observability()

        return cls(
            # Environment
            env=cls.get_env("ENV", default="development"),
            debug=cls.get_env("DEBUG", default=False, type=bool),
            testing=cls.get_env("TESTING", default=False, type=bool),
            # API Key
            api_key=cls.get_env("API_KEY", default=""),
            # (removed) Ashby
            # AWS
            aws_access_key_id=cls.get_env("AWS_ACCESS_KEY_ID", default=""),
            aws_secret_access_key=cls.get_env("AWS_SECRET_ACCESS_KEY", default=""),
            aws_region=cls.get_env("AWS_REGION", default="us-east-1"),
            # CDN
            cdn_url=cls.get_env("CDN_URL", default="https://d1z9wo3a8yeq5u.cloudfront.net"),
            # Client
            client_url=cls.get_env("CLIENT_URL", default="https://textlayer.ai"),
            # Celery
            celery_broker_url=cls.get_env("CELERY_BROKER_URL", default="pyamqp://textlayer:admin@localhost:5672/"),
            celery_task_ignore_result=cls.get_env("CELERY_TASK_IGNORE_RESULT", default=False, type=bool),
            celery_task_always_eager=cls.get_env("CELERY_TASK_ALWAYS_EAGER", default=False, type=bool),
            celery_result_backend=cls.get_env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/0"),
            # (removed) Doppler
            # JWT
            jwt_algorithm=cls.get_env("JWT_ALGORITHM", default="HS256"),
            jwt_secret=cls.get_env("JWT_SECRET", default=""),
            # GitHub
            github_app_id=cls.get_env("GITHUB_APP_ID", default=""),
            github_app_installation_id=cls.get_env("GITHUB_APP_INSTALLATION_ID", default=""),
            github_app_private_key=cls.get_env("GITHUB_APP_PRIVATE_KEY", default=""),
            # Evals
            evals_provider=cls.get_env("EVALS_PROVIDER", default="langfuse"),
            # (removed) Mistral OCR
            # OpenSearch
            opensearch_host=cls.get_env("OPENSEARCH_HOST", default=""),
            opensearch_username=cls.get_env("OPENSEARCH_USER", default=""),
            opensearch_password=cls.get_env("OPENSEARCH_PASSWORD", default=""),
            # (removed) Recruitment
            # (removed) Onboarding
            # Search
            search_provider=cls.get_env("SEARCH_PROVIDER", default="opensearch"),
            search_default_results_per_page=cls.get_env("SEARCH_DEFAULT_RESULTS_PER_PAGE", default=24, type=int),
            # (removed) Mail/SendGrid/OCR
            # RabbitMQ
            rabbitmq_username=cls.get_env("RABBITMQ_USERNAME", default="textlayer"),
            rabbitmq_password=cls.get_env("RABBITMQ_PASSWORD", default="admin"),
            # Sentry
            sentry_backend_dsn=cls.get_env("SENTRY_BACKEND_DSN", default=""),
            sentry_auth_token=cls.get_env("SENTRY_AUTH_TOKEN", default=""),
            # Prompt
            prompt_provider=cls.get_env("PROMPT_PROVIDER", default="langfuse"),
            prompt_label=cls.get_env("PROMPT_LABEL", default=""),
            # Langfuse
            langfuse_public_key=cls.get_env("LANGFUSE_PUBLIC_KEY", default=""),
            langfuse_secret_key=cls.get_env("LANGFUSE_SECRET_KEY", default=""),
            langfuse_host=cls.get_env("LANGFUSE_HOST", default="https://cloud.langfuse.com"),
            langfuse_signing_secret_prompts=cls.get_env("LANGFUSE_WEBHOOK_SECRET_PROMPT", default=""),
            # (removed) Research
            # Storage
            storage_provider=cls.get_env("STORAGE_PROVIDER", default="aws_s3"),
            # LLM
            chat_models=json.loads(cls.get_env("CHAT_MODELS", default='["openai/gpt-4o"]')),
            embedding_models=json.loads(cls.get_env("EMBEDDING_MODELS", default='["openai/text-embedding-3-small"]')),
            embedding_dimension=cls.get_env("EMBEDDING_DIMENSION", default=1536, type=int),
            # OpenAI
            openai_api_key=cls.get_env("OPENAI_API_KEY", default=""),
            # Anthropic
            anthropic_api_key=cls.get_env("ANTHROPIC_API_KEY", default=""),
            # Redis
            redis_url=cls.get_env("REDIS_URL", default=""),
            # (removed) Notion
        )
