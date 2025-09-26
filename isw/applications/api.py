import os

from isw.interfaces.api import create_app

app = create_app(os.getenv("FLASK_CONFIG"))
