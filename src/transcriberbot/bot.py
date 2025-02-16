"""
Author: Carlo Alberto Barbano <carlo.alberto.barbano@outlook.com>
Date: 15/02/25
"""
from telegram import Update

import config
import logging

from telegram.ext import MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, \
    ChatMemberHandler
from functools import partial
from transcriberbot.blueprints import commands, messages, voice, chat_handlers
from transcriberbot.blueprints.commands import set_language

from telegram.ext.filters import VOICE, VIDEO_NOTE, AUDIO
from transcriberbot.filters import ChatAdmin, FromPrivate, AllowedDocument, BotAdmin


def run(bot_token: str):
    application = (ApplicationBuilder()
                   .token(bot_token)
                   .concurrent_updates(True)
                   .build())

    logging.log(config.APP_LOG, "Installing handlers")
    application.add_handler(CallbackQueryHandler(voice.stop_task))

    # application.add_handler(ChatMemberHandler(chat_handlers.chat_member_update))
    application.add_handler(ChatMemberHandler(
        chat_handlers.chat_member_update,
        chat_member_types=ChatMemberHandler.MY_CHAT_MEMBER
    ))

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

    logging.log(config.APP_LOG, "Installing admin controls")
    application.add_handler(CommandHandler("users", commands.users, filters=BotAdmin()))
    application.add_handler(CommandHandler("broadcast", commands.broadcast, filters=BotAdmin()))

    logging.log(config.APP_LOG, "Installing language handlers..")
    for language in config.get_language_list():
        application.add_handler(
            CommandHandler(language, partial(set_language, language=language), filters=ChatAdmin())
        )

    application.add_handler(MessageHandler(VOICE, voice.voice_message))
    application.add_handler(MessageHandler(AUDIO, voice.audio_message))
    application.add_handler(MessageHandler(VIDEO_NOTE, voice.video_note_message))
    application.add_handler(MessageHandler(AllowedDocument(config.get_document_extensions()), voice.document_message))

    application.add_handler(MessageHandler(FromPrivate(), messages.private_message))

    logging.log(config.APP_LOG, "Starting bot..")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
