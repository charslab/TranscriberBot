"""
Author: Carlo Alberto Barbano <carlo.alberto.barbano@outlook.com>
Date: 15/02/25
"""
import logging

from telegram.constants import ChatType
from telegram.ext.filters import UpdateFilter
from telegram import Update, ChatMember

logger = logging.getLogger(__name__)


# class Voice(ABCRule[MessageUpdate]):
#     async def check(self, m: MessageUpdate, _) -> bool:
#         return bool(m.voice)
#
# class Audio(ABCRule[MessageUpdate]):
#     async def check(self, m: MessageUpdate, _) -> bool:
#         return bool(m.audio)
#
#
# class VideoNote(ABCRule[MessageUpdate]):
#     async def check(self, m: MessageUpdate, _) -> bool:
#         return bool(m.video_note)
#
#
class AllowedDocument(UpdateFilter):
    """
    Checks if the message has document media with allowed extensions.
    """

    def __init__(self, allowed_exts) -> None:
        super().__init__()
        self.allowed_exts = allowed_exts
        if len(allowed_exts) == 0:
            logger.warning("No allowed extensions were provided. Documents will be disabled")

    def filter(self, update: Update) -> bool:
        if update.effective_message.document:
            filename = update.effective_message.document.file_name
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

    async def filter(self, update: Update) -> bool:
        if update.effective_chat.type in (ChatType.PRIVATE, ChatType.CHANNEL):
            return True

        user = update.effective_user
        chat_admins: list[ChatMember] = update.effective_chat.get_administrators()

        is_admin = list(filter(lambda admin: admin.user.id == user.id, chat_admins))
        is_admin = len(is_admin) > 0

        return is_admin
