import sys
import warnings
from typing import Optional

from flask import Flask

from isw.core.services.observability import obs
from isw.interfaces.api.middleware.proxy_fix_middleware import init_proxy_fix
from isw.interfaces.api.routes import routes
from isw.interfaces.api.utils.extensions import cors, sentry
from isw.shared.config import get_config, set_config
from isw.shared.config.flask_adapter import get_flask_config


def silence_warnings(config):
    """Silence warnings in production"""
    if config.flask_config == "PROD" and not sys.warnoptions:
        warnings.simplefilter("ignore")


def create_app(config_name: Optional[str] = None):
    """Create and configure the Flask application.

    Args:
        config_name: Optional config name ('DEV', 'TEST', 'STAGING', 'PROD').
                    If not provided, reads from FLASK_CONFIG env var
    """
    app = Flask(__name__)

    # Get the specific config for the app
    config = get_flask_config(config_name)

    # Set the config for the app context
    set_config(config)

    # Set the required Flask config
    app.config.update(config.to_flask_dict())

    routes.init_routes(app)

    silence_warnings(config)
    init_proxy_fix(app)

    obs.init(
        exporters=["langfuse", "console"],
        app_name="textlayer-api",
        environment=config.env,
        version="1.0.0",
    )

    cors.init_app(app)
    sentry.init_app(config)

    return app
