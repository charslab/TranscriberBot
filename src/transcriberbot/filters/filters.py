"""
Author: Carlo Alberto Barbano <carlo.alberto.barbano@outlook.com>
Date: 15/02/25
"""
import logging
import asyncio

from telegram.constants import ChatType
from telegram.ext import ContextTypes
from telegram.ext.filters import UpdateFilter
from telegram import Update, ChatMember

import config


class AllowedDocument(UpdateFilter):
    """
    Checks if the message has document media with allowed extensions.
    """

    def __init__(self, allowed_exts) -> None:
        super().__init__()
        self.allowed_exts = allowed_exts
        if len(allowed_exts) == 0:
            logging.warning("No allowed extensions were provided. Documents will be disabled")

    def filter(self, update: Update) -> bool:
        if update.effective_message.document:
            logging.debug("Received document %s", update.effective_message.document.file_id)
            filename = update.effective_message.document.file_name
            if '.' not in filename:  # No extension
                return False
            ext = filename.split('.')[-1]
            return ext in self.allowed_exts
        return False


class FromPrivate(UpdateFilter):
    """
    Checks if the message was sent in a private conversation.
    """

    def filter(self, update: Update) -> bool:
        return update.effective_chat.type == ChatType.PRIVATE


class ChatAdmin(UpdateFilter):
    """
    Checks if the message was sent by a chat admin.
    """

    def filter(self, update: Update) -> bool:
        if update.effective_chat.type in (ChatType.PRIVATE, ChatType.CHANNEL):
            return True

        user = update.effective_user
        chat_admins: list[ChatMember] = asyncio.get_event_loop().run_until_complete(
            update.effective_chat.get_administrators())

        is_admin = list(filter(lambda admin: admin.user.id == user.id, chat_admins))
        is_admin = len(is_admin) > 0

        return is_admin


async def chat_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, callback):

    if update.effective_chat.type in (ChatType.PRIVATE, ChatType.CHANNEL):
        is_admin = True
    else:
        user = update.effective_user

        if user.id == 1087968824: # Anonymous admin
            is_admin = True

        else:
            chat_admins: list[ChatMember] = await update.effective_chat.get_administrators()

            is_admin = list(filter(lambda admin: admin.user.id == user.id, chat_admins))
            is_admin = len(is_admin) > 0

    if is_admin:
        return await callback(update, context)


class BotAdmin(UpdateFilter):
    """
    Checks if the message was sent by the bot admin.
    """

    def filter(self, update: Update) -> bool:
        user = update.effective_user
        bot_admins = config.get_bot_admins()

        is_admin = list(filter(lambda admin_id: admin_id == user.id, bot_admins))
        is_admin = len(is_admin) > 0

        return is_admin
