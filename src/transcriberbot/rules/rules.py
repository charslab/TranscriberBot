"""
Author: Carlo Alberto Barbano <carlo.alberto.barbano@outlook.com>
Date: 15/02/25
"""
import logging
from wonda.bot.rules.abc import ABCRule
from wonda.bot.updates import MessageUpdate
from wonda.types import ChatType
from wonda.types.objects import User


logger = logging.getLogger(__name__)


class Voice(ABCRule[MessageUpdate]):
    async def check(self, m: MessageUpdate, _) -> bool:
        return bool(m.voice)

class Audio(ABCRule[MessageUpdate]):
    async def check(self, m: MessageUpdate, _) -> bool:
        return bool(m.audio)


class VideoNote(ABCRule[MessageUpdate]):
    async def check(self, m: MessageUpdate, _) -> bool:
        return bool(m.video_note)


class Document(ABCRule[MessageUpdate]):
    """
    Checks if the message has voice media
    """

    def __init__(self, *allowed_exts) -> None:
        self.allowed_exts = allowed_exts
        if len(allowed_exts) == 0:
            logger.warning("No allowed extensions were provided. Documents will be disabled")

    async def check(self, m: MessageUpdate, _) -> bool:
        if m.document:
            filename = m.document.file_name
            ext = filename.split('.')[-1]
            return ext in self.allowed_exts

        return False


class FromPrivate(ABCRule[MessageUpdate]):
    """
    Checks if the message was sent in a channel.
    """

    async def check(self, m: MessageUpdate, _) -> bool:
        return m.chat.type == ChatType.PRIVATE


class ChatAdmin(ABCRule[MessageUpdate]):
    """
    Checks if the message was sent by a chat admin.
    """

    async def check(self, m: MessageUpdate, _) -> bool:
        if m.chat.type in (ChatType.PRIVATE, ChatType.CHANNEL):
            return True

        user: User = m.from_
        chat_admins = await m.ctx_api.get_chat_administrators(m.chat.id)

        is_admin = list(filter(lambda admin: admin.user.id == user.id, chat_admins))
        is_admin = len(is_admin) > 0

        return is_admin