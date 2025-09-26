import logging
import logging.config
import os


class EnvironFilter(logging.Filter):
    """
    Records the application environment (DEV, TEST, PROD) within logs to allow filtering
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.app_environment = os.environ.get("FLASK_CONFIG", "DEV")
        return True


LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "environ_filter": {
            "()": EnvironFilter,
        },
    },
    "formatters": {
        "BASE_FORMAT": {
            "format": (
                "[%(app_environment)s][%(name)s.%(module)s.%(funcName)s:%(lineno)d][%(levelname)s] -- %(message)s"
            ),
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": os.environ.get("LOG_LEVEL", "DEBUG"),
            "formatter": "BASE_FORMAT",
            "filters": ["environ_filter"],
        }
    },
    "loggers": {
        "textlayer": {
            "handlers": ["console"],
            "level": os.environ.get("LOG_LEVEL", "DEBUG"),
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.environ.get("LOG_LEVEL", "DEBUG"),
    },
}

# Configure logging with the config
logging.config.dictConfig(LOG_CONFIG)

# Create and export the logger instance
logger = logging.getLogger("textlayer")
