"""
Author: Carlo Alberto Barbano <carlo.alberto.barbano@outlook.com>
Date: 15/02/25
"""
import logging
import resources as R
import config
import translator

from wonda import Blueprint, Message, Command
from wonda.bot.rules import Text
from database import TBDB
from transcriberbot.rules import ChatAdmin

logger = logging.getLogger(__name__)
bp = Blueprint()


@bp.on.message(Command("start", "help"))
async def start(m: Message):
    await welcome_message(m)


@bp.on.message(Command("rate") & ChatAdmin())
async def rate(m: Message):
    await m.answer(R.get_string_resource("message_rate", TBDB.get_chat_lang(m.chat.id)))


@bp.on.message(Command("disable_voice") & ChatAdmin())
async def disable_voice(m: Message):
    chat_id = m.chat.id
    TBDB.set_chat_voice_enabled(chat_id, 0)
    await m.answer(R.get_string_resource("voice_disabled", TBDB.get_chat_lang(chat_id)))


@bp.on.message(Command("enable_voice") & ChatAdmin())
async def enable_voice(m: Message):
    chat_id = m.chat.id
    TBDB.set_chat_voice_enabled(chat_id, 1)
    await m.answer(R.get_string_resource("voice_enabled", TBDB.get_chat_lang(chat_id)))


@bp.on.message(Command("disable_photos") & ChatAdmin())
async def disable_photos(m: Message):
    chat_id = m.chat.id
    TBDB.set_chat_photos_enabled(chat_id, 0)
    await m.answer(R.get_string_resource("photos_disabled", TBDB.get_chat_lang(chat_id)))


@bp.on.message(Command("enable_photos") & ChatAdmin())
async def enable_photos(m: Message):
    chat_id = m.chat.id
    TBDB.set_chat_photos_enabled(chat_id, 1)
    await m.answer(R.get_string_resource("photos_enabled", TBDB.get_chat_lang(chat_id)))


@bp.on.message(Command("disable_qr") & ChatAdmin())
async def disable_qr(m: Message):
    chat_id = m.chat.id
    TBDB.set_chat_qr_enabled(chat_id, 0)
    await m.answer(R.get_string_resource("qr_disabled", TBDB.get_chat_lang(chat_id)))


@bp.on.message(Command("enable_qr") & ChatAdmin())
async def enable_qr(m: Message):
    chat_id = m.chat.id
    TBDB.set_chat_qr_enabled(chat_id, 1)
    await m.answer(R.get_string_resource("qr_enabled", TBDB.get_chat_lang(chat_id)))


@bp.on.message(Command("translate") & ChatAdmin())
async def translate(m: Message):
    chat_id = m.chat.id

    lang = m.text
    lang = lang.replace("/translate", "").strip()
    logger.debug("Language %s", lang)

    if not m.reply_to_message:
        await m.reply(R.get_string_resource("translate_reply_to_message", TBDB.get_chat_lang(chat_id)))
        return

    if not lang:
        await m.reply(R.get_string_resource("translate_language_missing", TBDB.get_chat_lang(chat_id)))
        return

    if lang not in config.get_config_prop("app")["languages"]:
        await m.reply(R.get_string_resource("translate_language_not_found", TBDB.get_chat_lang(chat_id)).format(lang))
        return

    lang = config.get_config_prop("app")["languages"][lang].split('-')[0]
    translation = translator.translate(
        source=TBDB.get_chat_lang(chat_id),
        target=lang,
        text=m.reply_to_message.text
    )

    await m.reply(translation)


@bp.on.message(Command("donate") & ChatAdmin())
async def donate(m: Message):
    chat_id = m.chat.id
    await m.reply(R.get_string_resource("message_donate", TBDB.get_chat_lang(chat_id)), parse_mode="html")


@bp.on.message(Command("privacy"))
async def privacy(m: Message):
    chat_id = m.chat.id
    await m.reply(R.get_string_resource("privacy_policy", TBDB.get_chat_lang(chat_id)), parse_mode='html')


def get_language_list():
  return config.get_config_prop("app")["languages"].keys()


async def welcome_message(m: Message):
    chat_record = TBDB.get_chat_entry(m.chat.id)

    language = None
    if chat_record is not None:
        language = chat_record["lang"]
    elif m.from_.language_code is not None:
        # Channel posts do not have a language_code attribute
        logger.info("Language_code: %s", m.from_.language_code)
        language = m.from_.language_code

    message = R.get_string_resource("message_welcome", language)
    message = message.replace("{languages}",
                              "/" + "\n/".join(get_language_list()))  # Format them to be a list of commands

    await m.reply(
        text=message,
        parse_mode="html"
    )

    if chat_record is None:
        if language is None:
            language = "en-US"

        if len(language) < 5:
            language = R.iso639_2_to_639_1(language)

        logger.info("No record found for chat {}, creating one with lang {}".format(m.chat.id, language))
        TBDB.create_default_chat_entry(m.chat.id, language)

