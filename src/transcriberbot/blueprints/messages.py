"""
Author: Carlo Alberto Barbano <carlo.alberto.barbano@outlook.com>
Date: 15/02/25
"""
import resources as R

from telegram import Update
from telegram.ext import ContextTypes
from database import TBDB


async def private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        update.effective_chat.id,
        R.get_string_resource("message_private", TBDB.get_chat_lang(update.effective_chat.id))
    )
