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
from transcriberbot.filters import chat_admin, FromPrivate, AllowedDocument, BotAdmin


def run(bot_token: str):
    application = (ApplicationBuilder()
                   .token(bot_token)
                   .concurrent_updates(True)
                   .build())

    logging.log(config.APP_LOG, "Installing handlers")
    application.add_handler(CallbackQueryHandler(voice.stop_task))

    application.add_handler(ChatMemberHandler(
        chat_handlers.chat_member_update,
        chat_member_types=ChatMemberHandler.MY_CHAT_MEMBER
    ))

    chat_admin_handlers = {
        'start': commands.start,
        'help': commands.start,
        'lang': commands.lang,
        'rate': commands.rate,
        'disable_voice': commands.disable_voice,
        'enable_voice': commands.enable_voice,
        'disable_photos': commands.disable_photos,
        'enable_photos': commands.enable_photos,
        'disable_qr': commands.disable_qr,
        'enable_qr': commands.enable_qr,
        'translate': commands.translate,
        'donate': commands.donate,
        'privacy': commands.privacy
    }

    for command, callback in chat_admin_handlers.items():
        application.add_handler(CommandHandler(command, lambda u, c, cb=callback: chat_admin(u, c, cb)))

    logging.log(config.APP_LOG, "Installing language handlers..")
    for language in config.get_language_list():
        callback = partial(set_language, language=language)
        application.add_handler(
            CommandHandler(language, lambda u, c, cb=callback: chat_admin(u, c, cb))
        )

    logging.log(config.APP_LOG, "Installing admin controls")
    application.add_handler(CommandHandler("users", commands.users, filters=BotAdmin()))
    application.add_handler(CommandHandler("broadcast", commands.broadcast, filters=BotAdmin()))

    logging.log(config.APP_LOG, "Installing message handlers")
    application.add_handler(MessageHandler(VOICE, voice.voice_message))
    application.add_handler(MessageHandler(AUDIO, voice.audio_message))
    application.add_handler(MessageHandler(VIDEO_NOTE, voice.video_note_message))
    application.add_handler(MessageHandler(AllowedDocument(config.get_document_extensions()), voice.document_message))

    application.add_handler(MessageHandler(FromPrivate(), messages.private_message))

    logging.log(config.APP_LOG, "Starting bot..")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
