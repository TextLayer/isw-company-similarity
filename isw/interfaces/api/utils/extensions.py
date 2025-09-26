import sentry_sdk
from flask_cors import CORS


class Sentry:
    def __init__(self):
        pass

    def init_app(self, config):
        """Initialize Sentry with config"""
        if config.env == "development":
            return

        sentry_sdk.init(
            dsn=config.sentry_backend_dsn,
            send_default_pii=True,
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
            environment=config.env,
        )


# Extension instances
sentry = Sentry()
cors = CORS()
