from .journal import journal_api
from .settings import settings_api
from .trading import trading_api


def register_api(app):
    for blueprint in (trading_api, journal_api, settings_api):
        app.register_blueprint(blueprint)
