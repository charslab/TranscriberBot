"""
Author: Carlo Alberto Barbano <carlo.alberto.barbano@outlook.com>
Date: 16/02/25
"""
import logging
import config

from telegram import Update, ChatMember
from telegram.ext import ContextTypes

from database import TBDB


async def chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    logging.log(config.APP_LOG, "Chat {chat_id} member update: %s", update)

    left = update.my_chat_member.new_chat_member.status in (ChatMember.LEFT, ChatMember.BANNED)

    if left:
        TBDB.set_chat_active(chat_id, False)
        logging.log(config.APP_LOG, f"Chat {chat_id} deactivated")
    else:
        chat_record = TBDB.get_chat_entry(chat_id)
        if chat_record:
            TBDB.set_chat_active(chat_id, 1)
            logging.log(config.APP_LOG, f"Chat {chat_id} reactivated")
