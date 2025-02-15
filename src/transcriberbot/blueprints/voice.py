"""
Author: Carlo Alberto Barbano <carlo.alberto.barbano@outlook.com>
Date: 15/02/25
"""
import asyncio
import logging
import os
import traceback
import time

import telegram
from telegram import Update, Voice
from telegram.constants import ChatType
from telegram.ext import ContextTypes

import audiotools
import config
import resources as R
from database import TBDB

logger = logging.getLogger(__name__)



async def voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if TBDB.get_chat_voice_enabled(update.effective_chat.id) == 0:
        return

    task = asyncio.get_event_loop().create_task(
        process_media_voice(update, context, update.effective_message.voice, "voice")
    )

async def process_media_voice(update: Update, context: ContextTypes.DEFAULT_TYPE, media: Voice, name: str) -> None:
    chat_id = update.effective_chat.id
    file_size = media.file_size
    max_size = config.get_config_prop("app").get("max_media_voice_file_size", 20 * 1024 * 1024)

    if file_size > max_size:
        error_message = R.get_string_resource("file_too_big", TBDB.get_chat_lang(chat_id)).format(
            max_size / (1024 * 1024)) + "\n"
        await context.bot.send_message(
            chat_id, error_message, parse_mode="html", reply_to_message_id=update.effective_message.message_id
        )
        return

    file_id = media.file_id
    file_path = os.path.join(config.get_config_prop("app")["media_path"], file_id)
    file: telegram.File = await context.bot.get_file(file_id)
    await file.download_to_drive(file_path)

    try:
        await transcribe_audio_file(update, context, file_path)
    except Exception as e:
        logger.error("Exception handling %s from %d: %s", name, chat_id, traceback.format_exc())
    finally:
        os.remove(file_path)


async def transcribe_audio_file(update: Update, context: ContextTypes.DEFAULT_TYPE, path: str):
    chat_id = update.effective_chat.id
    lang = TBDB.get_chat_lang(chat_id)
    is_group = update.effective_chat.type != ChatType.PRIVATE

    api_key = config.get_config_prop("wit").get(lang, None)
    if api_key is None:
        logger.error("Language not found in wit.json %s", lang)
        await context.bot.send_message(
            chat_id, R.get_string_resource("unknown_api_key", lang).format(language=lang), parse_mode="html",
            reply_to_message_id=update.effective_message.message_id
        )
        return

    logger.debug("Using key %s for lang %s", api_key, lang)

    message = await context.bot.send_message(
        chat_id, R.get_string_resource("transcribing", lang), parse_mode="html",
        reply_to_message_id=update.effective_message.message_id
    )
    message_id = message.message_id

    # TranscriberBot.get().start_thread(message_id)
    logger.debug("Starting thread %d", message_id)

    # keyboard = InlineKeyboardMarkup(
    #  [[InlineKeyboardButton("Stop", callback_data=message_id)]]
    # )

    text = ""
    if is_group:
        text = R.get_string_resource("transcription_text", lang) + "\n"
    success = False

    try:
        for speech in audiotools.transcribe(path, api_key):
            retry = True
            retry_num = 0

            print("SPEECH:", speech)
            while retry:  # and TranscriberBot.get().thread_running(message_id):
                try:
                    if len(text + " " + speech) >= 4000:
                        text = R.get_string_resource("transcription_continues", lang) + "\n"
                        message = await context.bot.send_message(
                            chat_id, text + speech + " <b>[...]</b>",
                            reply_to_message_id=message_id, parse_mode="html"
                        )
                    else:
                        await context.bot.edit_message_text(
                            text + " " + speech + " <b>[...]</b>", chat_id=chat_id,
                            message_id=message_id, parse_mode="html"
                        )

                    text += " " + speech
                    retry = False
                    success = True

                except telegram.error.TimedOut as e:
                    print(e)
                    logger.error("Timeout error %s", traceback.format_exc())
                    retry_num += 1
                    if retry_num >= 3:
                        retry = False

                except telegram.error.RetryAfter as r:
                  logger.warning("Retrying after %d", r.retry_after)
                  time.sleep(r.retry_after)

                except telegram.error.TelegramError as te:
                  logger.error("Telegram error %s", traceback.format_exc())
                  retry = False

                except Exception as e:
                  logger.error("Exception %s", traceback.format_exc())
                  retry = False

    except Exception as e:
        logger.error("Could not transcribe audio")

    if not success:
        await context.bot.edit_message_text(
            R.get_string_resource("transcription_failed", lang), chat_id=chat_id,
            message_id=message_id, parse_mode="html"
        )

    # TranscriberBot.get().del_thread(message_id)






