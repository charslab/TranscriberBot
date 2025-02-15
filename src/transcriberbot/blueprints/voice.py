"""
Author: Carlo Alberto Barbano <carlo.alberto.barbano@outlook.com>
Date: 15/02/25
"""
import logging

import resources as R
import config
import time
import transcriberbot.multiprocessing as tbmp
import transcriberbot.rules
import os
import requests
import traceback
import asyncio

import audiotools

from wonda.types import Audio, Voice, Document, ChatType, ReplyParameters
from wonda import Blueprint, Message, Command, APIException
from database import TBDB

logger = logging.getLogger(__name__)
bp = Blueprint()


async def transcribe_audio_file(m: Message, path):
    chat_id = m.chat.id
    lang = TBDB.get_chat_lang(chat_id)
    is_group = m.chat.type != ChatType.PRIVATE

    api_key = config.get_config_prop("wit").get(lang, None)
    if api_key is None:
        logger.error("Language not found in wit.json %s", lang)
        await m.reply(R.get_string_resource("unknown_api_key", lang).format(language=lang), parse_mode="html")
        return

    logger.debug("Using key %s for lang %s", api_key, lang)

    print("CTX API", m.ctx_api)
    message = await m.reply(R.get_string_resource("transcribing", lang), parse_mode="html")
    print("CTX API", message.ctx_api)
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
            # logger.debug("Thread %d running: %r", message_id, TranscriberBot.get().thread_running(message_id))
            # if TranscriberBot.get().thread_running(message_id) is False:
            #   TranscriberBot.get().del_thread(message_id)
            #   return

            retry = True
            retry_num = 0

            while retry:  # and TranscriberBot.get().thread_running(message_id):
                try:
                    if len(text + " " + speech) >= 4000:
                        text = R.get_string_resource("transcription_continues", lang) + "\n"
                        message = await message.ctx_api.send_message(
                            text=text + " " + speech + " <b>[...]</b>", chat_id=chat_id,
                            reply_parameters=ReplyParameters(message_id=message_id, chat_id=chat_id), parse_mode="html"
                        )
                    else:
                        message = await message.ctx_api.edit_message_text(
                            text + " " + speech, chat_id=chat_id, message_id=message_id, parse_mode="html"
                        )

                    text += " " + speech
                    retry = False
                    success = True

                except APIException[51] as e:
                    logger.error("Network error")
                    retry = False

                except APIException as e:
                    print(e)
                    logger.error("Timeout error %s", traceback.format_exc())
                    retry_num += 1
                    if retry_num >= 3:
                        retry = False

                # except telegram.error.RetryAfter as r:
                #   logger.warning("Retrying after %d", r.retry_after)
                #   time.sleep(r.retry_after)
                #
                # except telegram.error.TelegramError as te:
                #   logger.error("Telegram error %s", traceback.format_exc())
                #   retry = False
                #
                # except Exception as e:
                #   logger.error("Exception %s", traceback.format_exc())
                #   retry = False
    except Exception as e:
        logger.error("Could not transcribe audio")

    if not success:
        await message.ctx_api.edit_message_text(
            R.get_string_resource("transcription_failed", lang), chat_id=chat_id,
            message_id=message_id, parse_mode="html"
        )

    # TranscriberBot.get().del_thread(message_id)


def download_file(file_id, output_path):
    print("Downloading file id:", file_id)
    bot_token = config.bot_token()
    url = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
    response = requests.get(url)
    file_path = response.json()["result"]["file_path"]
    file_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
    response = requests.get(file_url)

    with open(output_path, "wb") as f:
        f.write(response.content)


async def process_media_voice(m: Message, media: Voice, name):
    chat_id = m.chat.id
    file_size = media.file_size
    max_size = config.get_config_prop("app").get("max_media_voice_file_size", 20 * 1024 * 1024)

    if file_size > max_size:
        error_message = R.get_string_resource("file_too_big", TBDB.get_chat_lang(chat_id)).format(
            max_size / (1024 * 1024)) + "\n"
        await m.reply(error_message, parse_mode="html")
        return

    file_id = media.file_id
    file_path = os.path.join(config.get_config_prop("app")["media_path"], file_id)
    download_file(file_id, file_path)

    try:
        await transcribe_audio_file(m, file_path)
    except Exception as e:
        logger.error("Exception handling %s from %d: %s", name, chat_id, traceback.format_exc())
    finally:
        os.remove(file_path)

def wrapper(message, voice, name):
    asyncio.run(process_media_voice(message, voice, name))

@bp.on.message(transcriberbot.rules.Voice())
@bp.on.channel_post(transcriberbot.rules.Voice())
async def handler(m: Message) -> None:
    if TBDB.get_chat_voice_enabled(m.chat.id) == 0:
        return

    task = asyncio.get_event_loop().create_task(process_media_voice(m, m.voice, "voice"))
    # tbmp.voice_pool().submit(wrapper, m, m.voice, "voice")
