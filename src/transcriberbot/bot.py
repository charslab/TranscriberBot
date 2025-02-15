"""
Author: Carlo Alberto Barbano <carlo.alberto.barbano@outlook.com>
Date: 15/02/25
"""

import wonda
import config

from wonda.api.utils import Token
from transcriberbot.blueprints import blueprints
from transcriberbot.middlewares import ChatAdminMiddleware


def run(bot_token: str):
    bot = wonda.Bot(Token(bot_token))

    for bp in blueprints:
        bp.load_into(bot)

    bot.run_forever()