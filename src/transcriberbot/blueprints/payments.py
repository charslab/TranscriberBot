"""
Author: Carlo Alberto Barbano <carlo.barbano@unito.it>
Date: 20/02/25
"""
import config
import resources as R

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database import TBDB


async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    premium_join_link = config.get_premium_join_link()

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Join", url=premium_join_link)]]
    )

    await update.effective_message.reply_text(
        R.get_string_resource(
            "premium_join_message",
            TBDB.get_chat_lang(update.effective_chat.id)
        ).replace("{invite_url}", premium_join_link),
        reply_markup=keyboard
    )


