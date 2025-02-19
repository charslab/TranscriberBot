"""
Author: Carlo Alberto Barbano <carlo.alberto.barbano@outlook.com>
Date: 15/02/25
"""
import asyncio
import logging
import os
import traceback
import datetime
from asyncio import CancelledError

import telegram
from telegram import Update, Voice, InlineKeyboardMarkup, InlineKeyboardButton, VideoNote, Document
from telegram.constants import ChatType
from telegram.ext import ContextTypes

import audiotools
import config
import resources as R
from database import TBDB

logger = logging.getLogger(__name__)


# TODO: check if cpu usage is too high, if so, use ProcessPoolExecutor


async def voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if TBDB.get_chat_voice_enabled(update.effective_chat.id) == 0:
        return

    await run_voice_task(update, context, update.effective_message.voice, "voice")


async def audio_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if TBDB.get_chat_voice_enabled(update.effective_chat.id) == 0:
        return

    await run_voice_task(update, context, update.effective_message.audio, "audio")


async def video_note_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if TBDB.get_chat_voice_enabled(update.effective_chat.id) == 0:
        return

    await run_voice_task(update, context, update.effective_message.video_note, "video_note")


async def document_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if TBDB.get_chat_voice_enabled(update.effective_chat.id) == 0:
        return

    await run_voice_task(update, context, update.effective_message.document, "document")


async def stop_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    task_id = int(update.callback_query.data)
    task: asyncio.Task = context.bot_data.get(task_id)["task"]

    if task is not None:
        task.cancel()
        context.bot_data.pop(task_id)
    else:
        logging.warning("Task not found")


async def wait_for_task_queue(context: ContextTypes.DEFAULT_TYPE):
    # wait until there are less than N tasks in bot_data
    context.bot_data['queue_len'] = context.bot_data.get('queue_len', 0) + 1

    while len(context.bot_data) >= config.get_config_prop("app")["voice_max_threads"] + 1:
        logging.debug("Waiting for tasks to finish")
        await asyncio.sleep(1)

    context.bot_data['queue_len'] -= 1
    logging.debug("Task queue has available space")


async def run_voice_task(update: Update, context: ContextTypes.DEFAULT_TYPE, media: Voice,
                         name):
    await wait_for_task_queue(context)

    try:
        task = asyncio.create_task(process_media_voice(update, context, media, name))
        context.bot_data[update.effective_message.message_id] = {
            'task': task,
            'duration': media.duration,
            'time': datetime.datetime.now(datetime.timezone.utc)
        }
        await asyncio.gather(task)
    finally:
        context.bot_data.pop(update.effective_message.message_id)


async def process_media_voice(update: Update, context: ContextTypes.DEFAULT_TYPE, media: [Voice | VideoNote | Document],
                              name: str) -> None:
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
    except Exception:
        logger.error("Exception handling %s from %d: %s", name, chat_id, traceback.format_exc())
    finally:
        os.remove(file_path)


async def transcribe_audio_file(update: Update, context: ContextTypes.DEFAULT_TYPE, path: str):
    chat_id = update.effective_chat.id
    task_id = update.effective_message.message_id
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

    logger.debug("Starting task %d", task_id)
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Stop", callback_data=task_id)]]
    )

    text = ""
    if is_group:
        text = R.get_string_resource("transcription_text", lang) + "\n"

    try:
        async for idx, speech, n_chunks in audiotools.transcribe(path, api_key):
            logging.debug(f"Transcription idx={idx} n_chunks={n_chunks}, text={speech}")
            suffix = f" <b>[{idx + 1}/{n_chunks}]</b>" if idx < n_chunks - 1 else ""
            reply_markup = keyboard if idx < n_chunks - 1 else None

            if len(text + " " + speech) >= 4000:
                text = R.get_string_resource("transcription_continues", lang) + "\n"
                message = await context.bot.send_message(
                    chat_id, f"{text} {speech} {suffix}",
                    reply_to_message_id=message.message_id, parse_mode="html",
                    reply_markup=reply_markup
                )
            else:
                message = await context.bot.edit_message_text(
                    f"{text} {speech} {suffix}", chat_id=chat_id,
                    message_id=message.message_id, parse_mode="html",
                    reply_markup=reply_markup
                )

            text = f"{text} {speech}"

            # retry_num = 0
            # retry = True
            # while retry:  # Retry loop
            #     try:
            #         if len(text + " " + speech) >= 4000:
            #             text = R.get_string_resource("transcription_continues", lang) + "\n"
            #             message = await context.bot.send_message(
            #                 chat_id, f"{text} {speech} {suffix}",
            #                 reply_to_message_id=message.message_id, parse_mode="html",
            #                 reply_markup=keyboard
            #             )
            #         else:
            #             message = await context.bot.edit_message_text(
            #                 f"{text} {speech} {suffix}", chat_id=chat_id,
            #                 message_id=message.message_id, parse_mode="html",
            #                 reply_markup=keyboard
            #             )
            #
            #         text += " " + speech
            #         retry = False
            #
            #     except telegram.error.TimedOut as e:
            #         print(e)
            #         logger.error("Timeout error %s", traceback.format_exc())
            #         retry_num += 1
            #         if retry_num >= 3:
            #             retry = False
            #
            #     except telegram.error.RetryAfter as r:
            #         logger.warning("Retrying after %d", r.retry_after)
            #         await asyncio.sleep(r.retry_after)
            #
            #     except telegram.error.TelegramError:
            #         logger.error("Telegram error %s", traceback.format_exc())
            #         retry = False


    except CancelledError:
        logging.debug("Task cancelled")
        await context.bot.edit_message_text(
            message.text + " " + R.get_string_resource("transcription_stopped", lang), chat_id=chat_id,
            message_id=message.message_id, parse_mode="html"
        )
        return

    except Exception as e:
        logger.error("Could not transcribe audio")

        await context.bot.edit_message_text(
            R.get_string_resource("transcription_failed", lang), chat_id=chat_id,
            message_id=message.message_id, parse_mode="html"
        )

        raise e
