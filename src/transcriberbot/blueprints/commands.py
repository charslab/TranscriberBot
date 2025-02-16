"""
Author: Carlo Alberto Barbano <carlo.alberto.barbano@outlook.com>
Date: 15/02/25
"""
import logging
import asyncio

from telegram import Update
from telegram.ext import ContextTypes

import config
import resources as R
import translator
from database import TBDB

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await welcome_message(update, context)


async def lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_lang = TBDB.get_chat_lang(update.effective_chat.id)
    await context.bot.send_message(
        update.effective_chat.id, R.get_string_resource("language_get", chat_lang).replace("{lang}", chat_lang)
    )


async def rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        update.effective_chat.id,
        R.get_string_resource("message_rate", TBDB.get_chat_lang(update.effective_chat.id))
    )


async def disable_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    TBDB.set_chat_voice_enabled(chat_id, 0)
    await context.bot.send_message(
        chat_id, R.get_string_resource("voice_disabled", TBDB.get_chat_lang(chat_id))
    )


async def enable_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    TBDB.set_chat_voice_enabled(chat_id, 1)
    await context.bot.send_message(
        chat_id, R.get_string_resource("voice_enabled", TBDB.get_chat_lang(chat_id))
    )


async def disable_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    TBDB.set_chat_photos_enabled(chat_id, 0)
    await context.bot.send_message(
        chat_id, R.get_string_resource("photos_disabled", TBDB.get_chat_lang(chat_id))
    )


async def enable_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    TBDB.set_chat_photos_enabled(chat_id, 1)
    await context.bot.send_message(
        chat_id, R.get_string_resource("photos_enabled", TBDB.get_chat_lang(chat_id))
    )


async def disable_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    TBDB.set_chat_qr_enabled(chat_id, 0)
    await context.bot.send_message(
        chat_id, R.get_string_resource("qr_disabled", TBDB.get_chat_lang(chat_id))
    )


async def enable_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    TBDB.set_chat_qr_enabled(chat_id, 1)
    await context.bot.send_message(
        chat_id, R.get_string_resource("qr_enabled", TBDB.get_chat_lang(chat_id))
    )


async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    lang = update.effective_message.text
    lang = lang.replace("/translate", "").strip()
    logger.debug("Language %s", lang)

    if not update.effective_message.reply_to_message:
        await context.bot.send_message(
            chat_id, R.get_string_resource("translate_reply_to_message", TBDB.get_chat_lang(chat_id))
        )
        return

    if not lang:
        await context.bot.send_message(
            chat_id, R.get_string_resource("translate_language_missing", TBDB.get_chat_lang(chat_id))
        )
        return

    if lang not in config.get_config_prop("app")["languages"]:
        await context.bot.send_message(
            chat_id, R.get_string_resource("translate_language_not_found", TBDB.get_chat_lang(chat_id)).format(lang)
        )
        return

    lang = config.get_config_prop("app")["languages"][lang].split('-')[0]
    translation = translator.translate(
        source=TBDB.get_chat_lang(chat_id),
        target=lang,
        text=update.effective_message.reply_to_message.text
    )

    await context.bot.send_message(
        chat_id, translation, reply_to_message_id=update.effective_message.reply_to_message.message_id
    )


async def donate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id, R.get_string_resource("message_donate", TBDB.get_chat_lang(chat_id)), parse_mode="html"
    )


async def privacy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id, R.get_string_resource("privacy_policy", TBDB.get_chat_lang(chat_id)), parse_mode="html"
    )


async def welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_record = TBDB.get_chat_entry(update.effective_chat.id)

    language = None
    if chat_record is not None:
        language = chat_record["lang"]
    elif update.effective_user.language_code is not None:
        # Channel posts do not have a language_code attribute
        logger.info("Language_code: %s", update.effective_user.language_code)
        language = update.effective_user.language_code

    message = R.get_string_resource("message_welcome", language)
    message = message.replace("{languages}",
                              "/" + "\n/".join(config.get_language_list()))  # Format them to be a list of commands

    await context.bot.send_message(update.effective_chat.id, message, "html")

    if chat_record is None:
        if language is None:
            language = "en-US"

        if len(language) < 5:
            language = R.iso639_2_to_639_1(language)

        logger.info("No record found for chat {}, creating one with lang {}".format(update.effective_chat.id, language))
        TBDB.create_default_chat_entry(update.effective_chat.id, language)


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE, language):
    chat_id = update.effective_chat.id
    lang_ = config.get_config_prop("app")["languages"][language]  # ISO 639-1 code for language
    TBDB.set_chat_lang(chat_id, lang_)
    message = R.get_string_resource("language_set", lang_).replace("{lang}", language)
    await context.bot.send_message(chat_id, message, parse_mode="html")
