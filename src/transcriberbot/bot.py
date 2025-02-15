"""
Author: Carlo Alberto Barbano <carlo.alberto.barbano@outlook.com>
Date: 15/02/25
"""

import wonda
import config
import logging

from functools import partial
from wonda import Command
from wonda.api.utils import Token
from transcriberbot.blueprints import blueprints
from transcriberbot.blueprints.command import set_language
from transcriberbot.rules import ChatAdmin


def run(bot_token: str):
    bot = wonda.Bot(Token(bot_token))

    logger = logging.getLogger(__name__)
    logger.info("Installing language handlers..")
    for language in config.get_language_list():
        bot.on.message(Command(language) & ChatAdmin())(lambda m, l=language: set_language(m, l))
        bot.on.channel_post(Command(language) & ChatAdmin())(lambda m, l=language: set_language(m, l))

    logger.info("Installing blueprints..")
    for bp in blueprints:
        bp.load_into(bot)

    logger.info("Starting bot..")
    bot.run_forever()