"""
Author: Carlo Alberto Barbano <carlo.alberto.barbano@outlook.com>
Date: 15/02/25
"""

import config
import logging

from telegram.ext import MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes
from functools import partial
from transcriberbot.blueprints import commands, messages, voice
from transcriberbot.blueprints.commands import set_language

from telegram.ext.filters import VOICE
from transcriberbot.filters import ChatAdmin, FromPrivate


def run(bot_token: str):
    application = ApplicationBuilder().token(bot_token).build()

    logger = logging.getLogger(__name__)

    logging.info("Installing handlers")
    application.add_handler(CommandHandler('start', commands.start, filters=ChatAdmin()))
    application.add_handler(CommandHandler('help', commands.start, filters=ChatAdmin()))
    application.add_handler(CommandHandler('lang', commands.lang, filters=ChatAdmin()))
    application.add_handler(CommandHandler('rate', commands.rate, filters=ChatAdmin()))
    application.add_handler(CommandHandler('disable_voice', commands.disable_voice, filters=ChatAdmin()))
    application.add_handler(CommandHandler('enable_voice', commands.enable_voice, filters=ChatAdmin()))
    application.add_handler(CommandHandler('disable_photos', commands.disable_photos, filters=ChatAdmin()))
    application.add_handler(CommandHandler('enable_photos', commands.enable_photos, filters=ChatAdmin()))
    application.add_handler(CommandHandler('disable_qr', commands.disable_qr, filters=ChatAdmin()))
    application.add_handler(CommandHandler('enable_qr', commands.enable_qr, filters=ChatAdmin()))
    application.add_handler(CommandHandler('translate', commands.translate, filters=ChatAdmin()))
    application.add_handler(CommandHandler('donate', commands.donate, filters=ChatAdmin()))
    application.add_handler(CommandHandler('privacy', commands.privacy))

    logger.info("Installing language handlers..")
    for language in config.get_language_list():
        application.add_handler(
            CommandHandler(language, partial(set_language, language=language), filters=ChatAdmin())
        )

    application.add_handler(MessageHandler(VOICE, voice.voice_message))

    application.add_handler(MessageHandler(FromPrivate(), messages.private_message))

    logger.info("Starting bot..")
    application.run_polling()