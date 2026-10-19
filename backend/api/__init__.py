from .instruments import instruments_api
from .journal import journal_api
from .plans import attachments_api, plans_api
from .settings import settings_api
from .trading import trading_api


def register_api(app):
    for blueprint in (
        trading_api,
        journal_api,
        plans_api,
        attachments_api,
        settings_api,
        instruments_api,
    ):
        app.register_blueprint(blueprint)
