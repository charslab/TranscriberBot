"""
Author: Carlo Alberto Barbano <carlo.alberto.barbano@outlook.com>
Date: 15/02/25
"""
import html
import logging
import os
import traceback

import telegram
from telegram import Update
from telegram.constants import ChatType
from telegram.ext import ContextTypes

import config
import phototools
import resources as R
from database import TBDB


async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_enabled = update.effective_chat.type == ChatType.PRIVATE or TBDB.get_chat_photos_enabled(update.effective_chat.id)
    qr_enabled = update.effective_chat.type == ChatType.PRIVATE or TBDB.get_chat_qr_enabled(update.effective_chat.id)

    if not photo_enabled and not qr_enabled:
        return

    message = update.message or update.channel_post
    await process_media_photo(update, context, message.photo)


async def process_media_photo(update: Update, context: ContextTypes.DEFAULT_TYPE, photo):
    chat_id = update.effective_chat.id
    message_id = update.effective_message.id
    lang = TBDB.get_chat_lang(chat_id)

    file_id = photo[-1].file_id
    file_path = os.path.join(config.get_config_prop("app")["media_path"], file_id)
    file: telegram.File = await context.bot.get_file(file_id)
    await file.download_to_drive(file_path)

    try:
        if update.effective_chat.type == ChatType.PRIVATE or TBDB.get_chat_qr_enabled(update.effective_chat.id):
            qr = phototools.read_qr(file_path)
            if qr is not None:
                qr = R.get_string_resource("qr_result", lang) + f"\n{qr}"

                await context.bot.send_message(
                    chat_id=chat_id, text=qr, reply_to_message_id=message_id,
                    parse_mode="html"
                )
                return

        if update.effective_chat.type == ChatType.PRIVATE or TBDB.get_chat_photos_enabled(update.effective_chat.id):
            text = phototools.image_ocr(file_path, lang)
            if text is not None:
                text = R.get_string_resource("ocr_result", lang) + "\n" + html.escape(text)
                await context.bot.send_message(
                    text=text, chat_id=chat_id, reply_to_message_id=message_id,
                    parse_mode="html",
                )
                return


        await context.bot.send_message(
            text=R.get_string_resource("photo_no_text", lang),
            chat_id=chat_id, reply_to_message_id=message_id,
            parse_mode="html",
        )

    except Exception as e:
        logging.error("Exception handling photo from %d: %s", chat_id, traceback.format_exc())

    finally:
        os.remove(file_path)
